"""
Neo4j connection ka simple wrapper.

Kya hai: Neo4j ek graph database hai jahan hum entities ko "nodes" aur
relationships ko "edges" ki tarah store karte hain. Yeh file Neo4j se
connect karne aur Cypher queries chalane ka common code rakhti hai.

Neo4j kaise chalayein:
1. Free "Neo4j Aura" cloud instance banayein (neo4j.com/cloud/aura), YA
2. Neo4j Desktop install karke local database chalayein.
Dono cases mein aapko URI, username, password milega — wahi .env mein daalna hai.
"""

from neo4j import GraphDatabase

from src.config import NEO4J_URI, NEO4J_USER, NEO4J_PASSWORD


class Neo4jClient:
    def __init__(self):
        self.driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD))

    def close(self):
        self.driver.close()

    def run_query(self, query: str, parameters: dict | None = None):
        """Ek Cypher query chalata hai aur results ki list return karta hai."""

        with self.driver.session() as session:
            result = session.run(query, parameters or {})
            return [record.data() for record in result]

    def clear_graph(self):
        """Poora graph khaali kar deta hai (fresh build ke liye)."""

        self.run_query("MATCH (n) DETACH DELETE n")
        print("[neo4j_client] Purana graph clear kar diya.")

    def verify_connection(self) -> bool:
        try:
            self.run_query("RETURN 1")
            return True
        except Exception as exc:
            print(f"[neo4j_client] Connection fail hui: {exc}")
            return False
