"""
main.py — poori pipeline ek jagah se chalane ke liye.

Do cheezein karta hai:
1. `python main.py build`  -> saari stages chalata hai: documents load,
   split, entities/relationships extract, Neo4j graph build, vector
   store build.
2. `python main.py ask`    -> ek chota CLI chat loop khol deta hai jahan
   aap sawaal type kar sakte hain aur hybrid GraphRAG jawab dega.

Pehli dafa "build" chalana zaroori hai, uske baad "ask" jitni baar
chahein chala sakte hain (jab tak data change na ho).
"""

import sys

from src.ingestion.document_loader import load_documents, split_documents
from src.extraction.entity_extractor import extract_entities
from src.extraction.relationship_extractor import extract_relationships
from src.graph.graph_builder import build_graph
from src.embeddings.vector_store import build_vector_store
from src.retrieval.hybrid_retriever import answer_question


def build_pipeline():
    print("\n===== Stage 1: Documents Load & Split =====")
    documents = load_documents()
    chunks = split_documents(documents)

    print("\n===== Stage 2: Entity Extraction =====")
    entities, per_chunk_entities = extract_entities(chunks)

    print("\n===== Stage 3: Relationship Extraction =====")
    relationships = extract_relationships(chunks, per_chunk_entities)

    print("\n===== Stage 4: Knowledge Graph Build (Neo4j) =====")
    build_graph(entities, relationships)

    print("\n===== Stage 5: Vector Store Build (Chroma) =====")
    build_vector_store(chunks)

    print("\nPipeline complete ho gayi! Ab 'python main.py ask' chala kar sawaal pooch sakte hain.")


def ask_loop():
    print("\nCompany Knowledge Graph RAG - sawaal poochein ('exit' likhein band karne ke liye)\n")

    while True:
        question = input("Aapka sawaal: ").strip()
        if question.lower() in {"exit", "quit"}:
            break
        if not question:
            continue

        result = answer_question(question)

        print("\n--- Jawab ---")
        print(result["answer"])

        print("\n--- Graph Facts Use Hue ---")
        for fact in result["graph_facts"]:
            print(f"  {fact}")
        print()


if __name__ == "__main__":
    command = sys.argv[1] if len(sys.argv) > 1 else "build"

    if command == "build":
        build_pipeline()
    elif command == "ask":
        ask_loop()
    else:
        print("Usage: python main.py [build|ask]")
