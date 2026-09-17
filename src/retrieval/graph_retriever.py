"""
Stage 7 (part 1): Graph Retrieval

Kya hai: User ke sawaal mein se pehle woh entity names dhoondte hain jo
graph mein maujood hain (e.g. sawaal "Ahmed Islam kis project pe kaam
karta hai?" mein "Ahmed Islam" match hoga). Phir us entity ke 1-hop
neighbors (seedha connected nodes) Neo4j se nikaal ke "facts" ki tarah
return karte hain.

Kyun chahiye: Vector search sirf "similar text" deta hai, lekin
structured relationship-based sawaalon (kaun kis department mein hai,
kaun kis project ko manage karta hai) ke liye graph traversal zyada
accurate hai.

Input: user ka query (plain text)
Output: list of fact strings, e.g. "Ahmed Islam -[WORKS_IN]-> AI Department"
"""

from src.graph.neo4j_client import Neo4jClient


def get_all_entity_names(client: Neo4jClient) -> list[str]:
    rows = client.run_query("MATCH (n) RETURN DISTINCT n.name AS name")
    return [row["name"] for row in rows if row.get("name")]


def find_mentioned_entities(query: str, all_entity_names: list[str]) -> list[str]:
    """
    Query ke text mein se woh entity names dhoondta hai jo mention hui hain.

    Exact full-name match ke ilawa, entity ke individual words (e.g.
    "Ahmed" ya "Islam" alag se "Ahmed Islam" mein se) bhi match karte
    hain — taake user ka sawaal poora naam na likhne par bhi kaam kare.
    """

    query_lower = query.lower()
    query_words = set(query_lower.split())

    matched = []
    for name in all_entity_names:
        name_lower = name.lower()
        name_words = set(name_lower.split())

        if name_lower in query_lower or name_words & query_words:
            matched.append(name)

    return matched


def get_entity_facts(client: Neo4jClient, entity_name: str) -> list[str]:
    """Ek entity ke saare 1-hop relationships (dono directions) nikaalta hai."""

    query = """
    MATCH (n {name: $name})-[r]->(m)
    RETURN n.name AS source, type(r) AS relation, m.name AS target
    UNION
    MATCH (m)-[r]->(n {name: $name})
    RETURN m.name AS source, type(r) AS relation, n.name AS target
    """

    rows = client.run_query(query, {"name": entity_name})

    return [f"{row['source']} -[{row['relation']}]-> {row['target']}" for row in rows]


def retrieve_graph_facts(query: str) -> list[str]:
    """Graph retrieval ka entry point: query lo, related facts wapas do."""

    client = Neo4jClient()

    try:
        all_names = get_all_entity_names(client)
        mentioned = find_mentioned_entities(query, all_names)

        facts = []
        for entity_name in mentioned:
            facts.extend(get_entity_facts(client, entity_name))

        # duplicates hata do
        return list(dict.fromkeys(facts))
    finally:
        client.close()


if __name__ == "__main__":
    example_query = "What projects does Ahmed Islam work on?"
    found_facts = retrieve_graph_facts(example_query)
    for f in found_facts:
        print(f)
