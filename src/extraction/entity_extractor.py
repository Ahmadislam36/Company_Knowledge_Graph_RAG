"""
Stage 3: Entity Extraction

Kya hai: Har text chunk ko LLM ke paas bhejte hain aur usse poochte hain
"is text mein kaunse entities (log, department, project, technology, etc)
hain?". LLM humein JSON list return karta hai.

Kyun chahiye: Knowledge graph banane ke liye pehle humein "nodes" (yani
entities) chahiye. Bina entities ke graph khaali hoga.

Input: chunks (document_loader.split_documents() ka output)
Output: list of unique entities, har entity: {"name": ..., "type": ...}
"""

from src.config import ENTITY_TYPES
from src.llm.llm_client import generate_json

ENTITY_PROMPT_TEMPLATE = """You are an information extraction system.
Read the TEXT below and extract every named entity that matches one of
these types: {entity_types}.

Rules:
- Only extract entities that are explicitly mentioned in the text.
- Use the exact name as written in the text (e.g. "Ahmed Islam", not "Ahmed").
- Return ONLY a JSON array, no explanation, in this exact format:
[{{"name": "Entity Name", "type": "ENTITY_TYPE"}}]
- If no entities are found, return [].

TEXT:
\"\"\"{chunk_text}\"\"\"

JSON:
"""


def extract_entities_from_chunk(chunk_text: str) -> list[dict]:
    """Ek chunk se entities nikaalta hai."""

    prompt = ENTITY_PROMPT_TEMPLATE.format(
        entity_types=", ".join(ENTITY_TYPES),
        chunk_text=chunk_text,
    )

    result = generate_json(prompt)

    if not isinstance(result, list):
        return []

    valid_entities = []
    for item in result:
        if not isinstance(item, dict):
            continue
        name = str(item.get("name", "")).strip()
        etype = str(item.get("type", "")).strip().upper()
        if name and etype in ENTITY_TYPES:
            valid_entities.append({"name": name, "type": etype})

    return valid_entities


def extract_entities(chunks: list) -> tuple[list[dict], list[list[dict]]]:
    """
    Saare chunks se entities nikaalta hai aur duplicates hata deta hai.
    Same naam + same type wali entity sirf ek dafa rakhi jaati hai.

    Do cheezein return karta hai:
    1. unique_entities: pura unique entity list (graph ke nodes banane ke liye)
    2. per_chunk_entities: har chunk ke against uski apni entities (relationship
       extraction stage inhe use karega, taake dobara LLM call na karni pade)
    """

    seen = {}  # key: (name.lower(), type) -> entity dict
    per_chunk_entities = []

    for i, chunk in enumerate(chunks):
        print(f"[entity_extractor] Chunk {i + 1}/{len(chunks)} process ho raha hai...")
        entities = extract_entities_from_chunk(chunk.page_content)
        per_chunk_entities.append(entities)

        for entity in entities:
            key = (entity["name"].lower(), entity["type"])
            if key not in seen:
                seen[key] = entity

    unique_entities = list(seen.values())

    unique_entities, per_chunk_entities = resolve_duplicate_entities(
        unique_entities, per_chunk_entities
    )

    print(f"[entity_extractor] Total {len(unique_entities)} unique entities mile.")
    return unique_entities, per_chunk_entities


def resolve_duplicate_entities(
    unique_entities: list[dict], per_chunk_entities: list[list[dict]]
) -> tuple[list[dict], list[list[dict]]]:
    """
    Short-name duplicates ko unke full-name version mein merge karta hai.

    Kabhi kabhi LLM ek chunk mein poora naam nikaalta hai (e.g. "Sara Khan")
    aur doosre chunk mein sirf short form (e.g. "Sara"), jis se graph mein
    do alag nodes ban jaate hain jo asal mein ek hi insaan/entity hain.
    Yeh function same-type entities mein se short name ko uske matching
    longer/full name mein remap karta hai (agar short name ke saare words
    full name mein maujood hon).
    """

    names_by_type: dict[str, list[str]] = {}
    for entity in unique_entities:
        names_by_type.setdefault(entity["type"], []).append(entity["name"])

    name_map = {}  # (name.lower(), type) -> canonical name

    for etype, names in names_by_type.items():
        sorted_by_length = sorted(names, key=len, reverse=True)

        for name in names:
            name_words = name.lower().split()
            canonical = name

            for candidate in sorted_by_length:
                if candidate == name:
                    continue
                candidate_words = candidate.lower().split()
                if len(candidate_words) > len(name_words) and all(
                    w in candidate_words for w in name_words
                ):
                    canonical = candidate
                    break

            name_map[(name.lower(), etype)] = canonical

    def _dedupe(entities: list[dict]) -> list[dict]:
        merged = {}
        for entity in entities:
            canonical_name = name_map.get(
                (entity["name"].lower(), entity["type"]), entity["name"]
            )
            key = (canonical_name.lower(), entity["type"])
            if key not in merged:
                merged[key] = {"name": canonical_name, "type": entity["type"]}
        return list(merged.values())

    resolved_entities = _dedupe(unique_entities)
    resolved_per_chunk = [_dedupe(chunk_entities) for chunk_entities in per_chunk_entities]

    return resolved_entities, resolved_per_chunk


if __name__ == "__main__":
    from src.ingestion.document_loader import load_documents, split_documents

    docs = load_documents()
    doc_chunks = split_documents(docs)
    found_entities, _ = extract_entities(doc_chunks)

    for e in found_entities:
        print(e)
