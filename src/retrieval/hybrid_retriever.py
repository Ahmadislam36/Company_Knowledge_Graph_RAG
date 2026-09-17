"""
Stage 7 (part 2): Hybrid GraphRAG

Kya hai: Yeh poore project ka "final answer generation" step hai. User
ka sawaal aata hai, hum do jagah se context ikattha karte hain:
1. Graph facts (structured relationships) - graph_retriever se
2. Vector search chunks (free-text context) - vector_store se
Dono ko ek prompt mein combine kar ke Groq ko dete hain, jo un dono ke
base pe final natural-language jawab likhta hai.

Kyun "hybrid"?: Graph accurate structured facts deta hai (kaun kis
project pe hai), vector search un cheezon ka context deta hai jo graph
mein exact edge ki tarah nahi capture hui (e.g. responsibilities ki
detail). Dono milake behtar, complete jawab banta hai.
"""

from src.retrieval.graph_retriever import retrieve_graph_facts
from src.embeddings.vector_store import search_similar_chunks
from src.config import VECTOR_TOP_K
from src.llm.llm_client import generate_text

ANSWER_PROMPT_TEMPLATE = """You are a helpful assistant answering questions about
a company called Nexora Technologies, using the context provided below.

GRAPH FACTS (structured relationships from the knowledge graph):
{graph_facts}

DOCUMENT CONTEXT (relevant text snippets):
{document_context}

QUESTION: {question}

Answer the question clearly and concisely using only the information
above. If the information is not present, say you don't have enough
information.

ANSWER:
"""


def answer_question(question: str) -> dict:
    """
    Hybrid GraphRAG ka entry point.
    Return karta hai: {"answer": ..., "graph_facts": [...], "document_context": [...]}
    (facts/context bhi return karte hain taake UI mein "sources" dikhaye ja sakein)
    """

    graph_facts = retrieve_graph_facts(question)
    similar_chunks = search_similar_chunks(question, top_k=VECTOR_TOP_K)

    graph_facts_text = "\n".join(graph_facts) if graph_facts else "No related graph facts found."
    document_context_text = (
        "\n---\n".join(chunk["text"] for chunk in similar_chunks)
        if similar_chunks
        else "No related document context found."
    )

    prompt = ANSWER_PROMPT_TEMPLATE.format(
        graph_facts=graph_facts_text,
        document_context=document_context_text,
        question=question,
    )

    answer = generate_text(prompt)

    return {
        "answer": answer,
        "graph_facts": graph_facts,
        "document_context": similar_chunks,
    }


if __name__ == "__main__":
    result = answer_question("Who is the technical lead of InsightAI and what technologies does it use?")
    print("ANSWER:\n", result["answer"])
    print("\nGRAPH FACTS:\n", result["graph_facts"])
