"""
Stage 8: Streamlit UI

Chalane ka tareeqa:
    streamlit run app.py

Yeh UI teen cheezein deta hai:
1. Sidebar mein "Build Knowledge Graph" button — pehli dafa (ya data
   change hone par) data pipeline chalane ke liye.
2. Ek chat-jaisa box jahan sawaal type karke jawab lein.
3. Har jawab ke sath, "sources" expander mein woh graph facts aur
   document chunks dikhte hain jo jawab banane mein use hue.
"""

import streamlit as st

from src.ingestion.document_loader import load_documents, split_documents
from src.extraction.entity_extractor import extract_entities
from src.extraction.relationship_extractor import extract_relationships
from src.graph.graph_builder import build_graph
from src.embeddings.vector_store import build_vector_store
from src.retrieval.hybrid_retriever import answer_question

st.set_page_config(page_title="Company Knowledge Graph RAG", page_icon="🔎")

st.title("🔎 Company Knowledge Graph RAG")
st.caption("GraphRAG demo — Neo4j knowledge graph + vector search + Groq")

with st.sidebar:
    st.header("Setup")
    st.write(
        "Pehli dafa yahan click karein taake documents se knowledge graph "
        "aur vector store ban jaaye. Data change hone par dobara chalayein."
    )

    if st.button("Build Knowledge Graph", use_container_width=True):
        with st.spinner("Pipeline chal rahi hai... (documents -> entities -> graph -> vectors)"):
            documents = load_documents()
            chunks = split_documents(documents)
            entities, per_chunk_entities = extract_entities(chunks)
            relationships = extract_relationships(chunks, per_chunk_entities)
            build_graph(entities, relationships)
            build_vector_store(chunks)
        st.success(
            f"Ban gaya! {len(entities)} entities aur {len(relationships)} "
            f"relationships graph mein daal diye."
        )

if "history" not in st.session_state:
    st.session_state.history = []

for turn in st.session_state.history:
    with st.chat_message(turn["role"]):
        st.write(turn["content"])
        if turn["role"] == "assistant" and turn.get("sources"):
            with st.expander("Sources"):
                st.markdown("**Graph facts:**")
                for fact in turn["sources"]["graph_facts"]:
                    st.write(f"- {fact}")
                st.markdown("**Document context:**")
                for chunk in turn["sources"]["document_context"]:
                    st.write(f"- ({chunk['source']}) {chunk['text'][:150]}...")

question = st.chat_input("Company ke baare mein sawaal poochein...")

if question:
    st.session_state.history.append({"role": "user", "content": question})
    with st.chat_message("user"):
        st.write(question)

    with st.chat_message("assistant"):
        with st.spinner("Soch raha hoon..."):
            result = answer_question(question)
            st.write(result["answer"])
            with st.expander("Sources"):
                st.markdown("**Graph facts:**")
                for fact in result["graph_facts"]:
                    st.write(f"- {fact}")
                st.markdown("**Document context:**")
                for chunk in result["document_context"]:
                    st.write(f"- ({chunk['source']}) {chunk['text'][:150]}...")

    st.session_state.history.append(
        {
            "role": "assistant",
            "content": result["answer"],
            "sources": {
                "graph_facts": result["graph_facts"],
                "document_context": result["document_context"],
            },
        }
    )
