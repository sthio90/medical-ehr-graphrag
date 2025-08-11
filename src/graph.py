from src.custom_neo4j import SimpleNeo4jGraph
from src.config import NEO4J_URI, NEO4J_USERNAME, NEO4J_PASSWORD, NEO4J_DATABASE

def connect_to_graph():
    """Initialize and return a Neo4j graph connection."""
    graph = SimpleNeo4jGraph(
        url=NEO4J_URI,
        username=NEO4J_USERNAME,
        password=NEO4J_PASSWORD,
        database=NEO4J_DATABASE
    )
    return graph