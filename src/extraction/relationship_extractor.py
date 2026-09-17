"""
Stage 4: Relationship Extraction

Kya hai: Ab hum LLM se poochte hain "in entities ke beech kya relationship
hai?" (e.g. Ahmed Islam --WORKS_IN--> Artificial Intelligence Department).

Kyun chahiye: Graph mein sirf nodes (entities) kaafi nahi, unko jodne
waali "edges" (relationships) bhi chahiye. Yehi edges hain jo baad mein
graph traversal/retrieval mein kaam aayengi (e.g. "Ahmed kis project pe
kaam karta hai?" jaise sawaalon ke liye).

Input: ek chunk ka text + usi chunk mein mili entities ki list
Output: list of relationships: {"source": ..., "relation": ..., "target": ...}
"""

from src.config import RELATIONSHIP_TYPES
from src.llm.llm_client import generate_json

RELATIONSHIP_PROMPT_TEMPLATE = """You are an information extraction system.
Given the TEXT and the list of ENTITIES already found in it, extract the
relationships between those entities.

Only use these relationship types: {relationship_types}

Rules:
- source and target must be from the ENTITIES list (use exact names).
- Only extract relationships explicitly stated or clearly implied in the text.
- Return ONLY a JSON array in this exact format:
[{{"source": "Entity A", "relation": "RELATION_TYPE", "target": "Entity B"}}]
- If no relationships are found, return [].

ENTITIES:
{entities}

TEXT:
\"\"\"{chunk_text}\"\"\"

JSON:
"""


def extract_relationships_from_chunk(chunk_text: str, entities: list[dict]) -> list[dict]:
    """Ek chunk se relationships nikaalta hai, sirf diye gaye entities ke beech."""

    if len(entities) < 2:
        return []  # relationship banane ke liye kam se kam 2 entities chahiye

    entity_names = ", ".join(f'"{e["name"]}"' for e in entities)

    prompt = RELATIONSHIP_PROMPT_TEMPLATE.format(
        relationship_types=", ".join(RELATIONSHIP_TYPES),
        entities=entity_names,
        chunk_text=chunk_text,
    )

    result = generate_json(prompt)

    if not isinstance(result, list):
        return []

    entity_name_set = {e["name"] for e in entities}
    valid_relationships = []

    for item in result:
        if not isinstance(item, dict):
            continue
        source = str(item.get("source", "")).strip()
        relation = str(item.get("relation", "")).strip().upper()
        target = str(item.get("target", "")).strip()

        if (
            source in entity_name_set
            and target in entity_name_set
            and relation in RELATIONSHIP_TYPES
            and source != target
        ):
            valid_relationships.append(
                {"source": source, "relation": relation, "target": target}
            )

    return valid_relationships


def extract_relationships(chunks: list, per_chunk_entities: list[list[dict]]) -> list[dict]:
    """
    Saare chunks se relationships nikaalta hai.

    per_chunk_entities: entity_extractor.extract_entities() se mila
    per-chunk entity list (index se chunks ke sath match hota hai).
    Isse har chunk ki relationships sirf usi chunk ke entities tak
    mehdood rehti hain — isse galat/random relationships banne ka
    chance kam ho jaata hai, aur entity extraction dobara nahi karni padti.
    """

    seen = set()
    unique_relationships = []

    for i, chunk in enumerate(chunks):
        print(f"[relationship_extractor] Chunk {i + 1}/{len(chunks)} process ho raha hai...")

        chunk_entities = per_chunk_entities[i]
        relationships = extract_relationships_from_chunk(chunk.page_content, chunk_entities)

        for rel in relationships:
            key = (rel["source"].lower(), rel["relation"], rel["target"].lower())
            if key not in seen:
                seen.add(key)
                unique_relationships.append(rel)

    print(f"[relationship_extractor] Total {len(unique_relationships)} unique relationships mile.")
    return unique_relationships


if __name__ == "__main__":
    from src.ingestion.document_loader import load_documents, split_documents
    from src.extraction.entity_extractor import extract_entities

    docs = load_documents()
    doc_chunks = split_documents(docs)
    _, chunk_entities_list = extract_entities(doc_chunks)
    found_relationships = extract_relationships(doc_chunks, chunk_entities_list)

    for r in found_relationships:
        print(r)
