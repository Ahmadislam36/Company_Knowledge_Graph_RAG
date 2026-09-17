# Company Knowledge Graph RAG

Chota learning project: company documents se ek Knowledge Graph (Neo4j) banata hai,
saath hi vector search bhi karta hai, aur dono ko mila kar (Hybrid GraphRAG) sawaalon
ke jawab deta hai.

## Pipeline Stages

1. **Document Loading & Splitting** (`src/ingestion/document_loader.py`)
   `data/documents/*.md` files load karke chote chunks mein todta hai.

2. **Entity Extraction** (`src/extraction/entity_extractor.py`)
   Har chunk se entities nikaalta hai (PERSON, DEPARTMENT, PROJECT, TECHNOLOGY, ROLE, COMPANY).

3. **Relationship Extraction** (`src/extraction/relationship_extractor.py`)
   Entities ke beech relationships nikaalta hai (WORKS_IN, WORKS_ON, MANAGES, USES, etc).

4. **Knowledge Graph Build** (`src/graph/`)
   Entities ko nodes aur relationships ko edges ki tarah Neo4j mein store karta hai.

5. **Vector Store** (`src/embeddings/vector_store.py`)
   Chunks ko Gemini embeddings se convert karke Chroma (local vector DB) mein save karta hai.

6. **Hybrid Retrieval + Answer Generation** (`src/retrieval/`)
   User ke sawaal ke liye graph facts + similar chunks nikaal kar Gemini se final jawab banata hai.

7. **UI** (`app.py`) — Streamlit chat interface.

## Setup

```bash
pip install -r requirements.txt
cp .env.example .env
# .env mein apni GEMINI_API_KEY aur Neo4j credentials daalein
```

Neo4j chalane ke do tareeqe:
- Free cloud instance: https://neo4j.com/cloud/aura
- Ya Neo4j Desktop se local database

## Run

Pehle pura pipeline chalayein (documents -> graph + vector store):

```bash
python main.py build
```

Phir command line se sawaal poochein:

```bash
python main.py ask
```

Ya Streamlit UI chalayein:

```bash
streamlit run app.py
```
(UI mein bhi sidebar se "Build Knowledge Graph" button hai, pehli dafa wahi click karein.)

## Sample Data

`data/documents/` mein "Nexora Technologies" naam ki fictional company ka data hai —
employees, departments, projects, aur technologies. Isi pe test kar sakte hain, e.g.:

- "Ahmed Islam kis department mein kaam karta hai?"
- "InsightAI project mein kaunsi technologies use hoti hain?"
- "Hamza Salman kaunse projects manage karta hai?"

## Project Structure

```
Company_Knowledge_Graph_RAG/
├── main.py                 # CLI: pipeline build + ask loop
├── app.py                  # Streamlit UI
├── data/documents/         # Sample company markdown files
├── src/
│   ├── config.py           # Settings, entity/relationship schema
│   ├── ingestion/           # Stage 1: load + split documents
│   ├── extraction/          # Stage 2-3: entities + relationships
│   ├── graph/               # Stage 4: Neo4j client + graph builder
│   ├── embeddings/          # Stage 5: Chroma vector store
│   ├── retrieval/           # Stage 6-7: graph retrieval + hybrid RAG
│   └── llm/                 # Gemini wrapper (text + embeddings)
└── requirements.txt
```

## Notes / Possible Improvements (baad mein)

- Entity resolution (e.g. "Ahmed" aur "Ahmed Islam" ko same node maan na)
- Graph visualization (pyvis / neo4j browser)
- Reranking retrieved chunks
- Community detection / graph summarization
- Evaluation set bana kar accuracy check karna
