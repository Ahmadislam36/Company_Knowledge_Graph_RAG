"""
Stage 6: Vector Search

Kya hai: Har chunk ko ek embedding (numbers ki list) mein convert karte
hain aur Chroma (local vector database) mein store karte hain. Query
ke waqt query ko bhi embed karte hain aur "meaning" mein sabse similar
chunks dhoondte hain (semantic search — sirf keyword matching nahi).

Kyun chahiye: Graph humein "structured facts" deta hai (Ahmed WORKS_IN
AI Department), lekin document ke andar likha detailed context (jaise
"Ahmed evaluates AI responses") graph mein exact edge ki tarah nahi hota.
Vector search yeh detailed/free-text context dhoondne ke liye hai. Aage
Stage 7 mein hum graph facts + vector context dono ko mila kar (hybrid)
behtar jawab denge.

Chroma local hai, koi extra server/API key nahi chahiye. Embeddings bhi
local (fastembed) hain, isliye is stage ke liye koi API key ya internet
call bilkul zaroori nahi hai.
"""

import chromadb

from src.config import VECTOR_DB_PATH
from src.llm.llm_client import embed_text

COLLECTION_NAME = "company_chunks"


def _get_collection():
    client = chromadb.PersistentClient(path=VECTOR_DB_PATH)
    return client.get_or_create_collection(name=COLLECTION_NAME)


def build_vector_store(chunks: list, clear_first: bool = True):
    """Saare chunks embed kar ke Chroma mein store karta hai."""

    client = chromadb.PersistentClient(path=VECTOR_DB_PATH)

    if clear_first:
        try:
            client.delete_collection(COLLECTION_NAME)
        except Exception:
            pass  # collection pehle se nahi thi, koi masla nahi

    collection = client.get_or_create_collection(name=COLLECTION_NAME)

    ids, embeddings, documents, metadatas = [], [], [], []

    for i, chunk in enumerate(chunks):
        print(f"[vector_store] Chunk {i + 1}/{len(chunks)} embed ho raha hai...")
        embeddings.append(embed_text(chunk.page_content))
        documents.append(chunk.page_content)
        metadatas.append({"source": str(chunk.metadata.get("source", "unknown"))})
        ids.append(f"chunk-{i}")

    collection.add(
        ids=ids,
        embeddings=embeddings,
        documents=documents,
        metadatas=metadatas,
    )

    print(f"[vector_store] {len(chunks)} chunks vector store mein save ho gaye.")


def search_similar_chunks(query: str, top_k: int = 4) -> list[dict]:
    """Query se sabse milte-julte chunks dhoondta hai."""

    collection = _get_collection()
    query_embedding = embed_text(query)

    results = collection.query(
        query_embeddings=[query_embedding],
        n_results=top_k,
    )

    matches = []
    documents = results.get("documents", [[]])[0]
    metadatas = results.get("metadatas", [[]])[0]

    for doc, meta in zip(documents, metadatas):
        matches.append({"text": doc, "source": meta.get("source", "unknown")})

    return matches


if __name__ == "__main__":
    from src.ingestion.document_loader import load_documents, split_documents

    docs = load_documents()
    doc_chunks = split_documents(docs)
    build_vector_store(doc_chunks)

    test_results = search_similar_chunks("Who works on InsightAI?")
    for r in test_results:
        print(r)
