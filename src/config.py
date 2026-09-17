"""
Central config file.
Yahan pe saari settings hain jo pura project use karta hai:
- API keys (.env se load hoti hain)
- Neo4j connection details
- Entity/Relationship types jo LLM ko batate hain kya extract karna hai
- Folder paths
"""

import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

# ---------- Paths ----------
BASE_DIR = Path(__file__).resolve().parent.parent
DOCUMENTS_PATH = BASE_DIR / "data" / "documents"
PROCESSED_PATH = BASE_DIR / "data" / "processed"
VECTOR_DB_PATH = str(PROCESSED_PATH / "chroma_db")

PROCESSED_PATH.mkdir(parents=True, exist_ok=True)


def _clean_env(name: str, default: str = "") -> str:
    """
    .env se value nikaalta hai aur usse "network-safe" bana deta hai.

    Kyun chahiye: agar koi env value mein stray whitespace, surrounding
    quotes, ya koi non-ASCII/invisible character (e.g. "…" copy-paste se,
    ya smart-quotes) reh jaaye, to wo value jab HTTP header (Authorization/
    API key) ya Neo4j auth mein use hoti hai to Python ka http.client
    'latin-1' codec se encode karne ki koshish karta hai aur crash ho jaata
    hai — us waqt ka error message (`UnicodeEncodeError` deep inside
    http.client.py) bilkul batata nahi ke asal masla .env mein hai.

    Isliye yahan value ko load karte hi clean + validate kar dete hain,
    taake agar koi bad character ho to hum abhi, ek clear error ke sath,
    ruk jaayein — na ke baad mein Groq/Neo4j call ke andar crash ho.
    """

    raw = os.getenv(name, default)

    # Surrounding whitespace aur accidental quotes hata dein
    # (python-dotenv already ek layer of quotes strip karta hai, yeh extra safety hai)
    cleaned = raw.strip().strip('"').strip("'").strip()

    if not cleaned:
        return cleaned

    # Sirf printable ASCII allowed hai in values mein (API keys/passwords/URIs
    # kabhi bhi legitimately non-ASCII nahi hote). Agar koi bad character mile
    # (e.g. "…" U+2026, smart quotes, non-breaking space, etc.) to abhi hi
    # ruk jaayein, ek samajh aane wale error ke sath.
    bad_chars = sorted({c for c in cleaned if not (32 <= ord(c) < 127)})

    if bad_chars:
        bad_display = ", ".join(f"{c!r} (U+{ord(c):04X})" for c in bad_chars)
        raise RuntimeError(
            f".env mein '{name}' ki value mein invalid character(s) mil gaye: "
            f"{bad_display}\n"
            f"Aksar yeh tab hota hai jab koi key/URL/password kahin se "
            f"copy-paste kiya jaaye aur UI ka truncation ellipsis ('…') ya "
            f"'smart quotes' saath mein aa jaayein. Groq Console "
            f"(https://console.groq.com/keys) se fresh value copy "
            f"karke .env mein dobara daalein — bina extra spaces/quotes ke."
        )

    return cleaned


# ---------- Groq (LLM) ----------
GROQ_API_KEY = _clean_env("GROQ_API_KEY")
GROQ_MODEL_NAME = _clean_env("GROQ_MODEL_NAME", "openai/gpt-oss-120b")

# ---------- Embeddings (local, via fastembed — Groq embeddings API nahi deta) ----------
# Yeh model CPU pe locally chalta hai (ONNX ke zariye), koi API key ya
# internet call nahi chahiye. Pehli baar chalane par model auto-download
# hoga (~130MB) aur phir cache ho jayega.
EMBEDDING_MODEL_NAME = _clean_env("EMBEDDING_MODEL_NAME", "BAAI/bge-small-en-v1.5")

# ---------- Neo4j ----------
# Backward compatible: purane .env files "NEO4J_USER" use karte the,
# kuch templates "NEO4J_USERNAME" use karte hain — dono support karte hain.
NEO4J_URI = _clean_env("NEO4J_URI", "neo4j://127.0.0.1:7687")
NEO4J_USER = _clean_env("NEO4J_USER") or _clean_env("NEO4J_USERNAME", "neo4j")
NEO4J_PASSWORD = _clean_env("NEO4J_PASSWORD")

# ---------- Entity / Relationship schema ----------
# Chota aur fixed schema rakha hai taake LLM confuse na ho aur graph clean rahe.
ENTITY_TYPES = [
    "PERSON",       # e.g. Ahmed Islam
    "COMPANY",      # e.g. Nexora Technologies
    "DEPARTMENT",   # e.g. Artificial Intelligence Department
    "PROJECT",      # e.g. InsightAI
    "TECHNOLOGY",   # e.g. LangChain, PostgreSQL
    "ROLE",         # e.g. AI Engineer, Project Manager
]

RELATIONSHIP_TYPES = [
    "WORKS_IN",      # Person -> Department
    "WORKS_ON",      # Person -> Project
    "MANAGES",       # Person -> Project
    "LEADS",         # Person -> Project (technical lead)
    "HAS_ROLE",      # Person -> Role
    "USES",          # Project/Department -> Technology
    "PART_OF",       # Department -> Company
    "BASED_IN",      # Company -> Location
]

# Kitne top chunks vector search se lene hain
VECTOR_TOP_K = 10
