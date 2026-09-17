"""
Stage 5: Knowledge Graph Building

Kya hai: Extracted entities aur relationships ko Neo4j mein daalte hain.
Har entity ek "node" ban jaati hai (uske type ke label ke saath, e.g.
:PERSON), aur har relationship ek "edge" (e.g. -[:WORKS_IN]->).

Kyun chahiye: Yehi asal knowledge graph hai. Isके baad hum Cypher
queries se graph traverse kar ke sawaalon ke jawab dhoond sakte hain
(e.g. "Ahmed kis department mein hai?" -> graph traversal).

Input: unique_entities, relationships (dono extraction stage se aaye)
Output: kuch nahi (Neo4j database mein data insert ho jaata hai)
"""

from src.graph.neo4j_client import Neo4jClient


def add_entities(client: Neo4jClient, entities: list[dict]):
    """
    Har entity ke liye ek node banata hai (MERGE se duplicate nahi banti).

    Note: entity['type'] aur rel['relation'] neeche query string mein
    seedhe daal rahe hain (Cypher labels ko parameter ki tarah pass nahi
    kiya ja sakta). Yeh safe hai kyunki dono hamesha extraction stage ke
    fixed ENTITY_TYPES/RELATIONSHIP_TYPES list se validate ho kar aate
    hain — kabhi bhi raw user input seedha yahan nahi aata.
    """

    for entity in entities:
        query = f"""
        MERGE (n:{entity['type']} {{name: $name}})
        """
        client.run_query(query, {"name": entity["name"]})

    print(f"[graph_builder] {len(entities)} entity nodes bana diye.")


def add_relationships(client: Neo4jClient, relationships: list[dict]):
    """Har relationship ke liye do existing nodes ke beech ek edge banata hai."""

    for rel in relationships:
        query = f"""
        MATCH (a {{name: $source}})
        MATCH (b {{name: $target}})
        MERGE (a)-[:{rel['relation']}]->(b)
        """
        client.run_query(query, {"source": rel["source"], "target": rel["target"]})

    print(f"[graph_builder] {len(relationships)} relationships bana diye.")


def build_graph(entities: list[dict], relationships: list[dict], clear_first: bool = True):
    """Poora graph build karne ka entry point."""

    client = Neo4jClient()

    if not client.verify_connection():
        client.close()
        raise RuntimeError(
            "Neo4j se connect nahi ho saka. .env mein NEO4J_URI/NEO4J_USER/"
            "NEO4J_PASSWORD check karein aur Neo4j chal raha hai ya nahi confirm karein."
        )

    try:
        if clear_first:
            client.clear_graph()

        add_entities(client, entities)
        add_relationships(client, relationships)
    finally:
        client.close()

    print("[graph_builder] Knowledge graph successfully ban gaya.")
