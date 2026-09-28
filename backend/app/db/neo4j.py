from neo4j import GraphDatabase
from app.core.config import settings

_driver = None

def get_driver():
    global _driver
    if _driver is None:
        _driver = GraphDatabase.driver(
            settings.NEO4J_URL,
            auth=(settings.NEO4J_USER, settings.NEO4J_PASSWORD),
        )
    return _driver

def get_neo4j_session():
    driver = get_driver()
    session = driver.session()
    try:
        yield session
    finally:
        session.close()

def insert_document_graph(document_id: str, title: str, authors: str, year: int):
    driver = get_driver()
    with driver.session() as session:
        session.run(
            "MERGE (d:Document {id: $id}) SET d.title = $title, d.year = $year",
            id=document_id, title=title, year=year
        )
        if authors:
            for author in [a.strip() for a in authors.replace(';', ',').split(',') if a.strip()][:20]:
                session.run(
                    """
                    MERGE (a:Author {name: $name})
                    MERGE (d:Document {id: $doc_id})
                    MERGE (a)-[:WROTE]->(d)
                    """,
                    name=author, doc_id=document_id
                )

def delete_document_graph(document_id: str):
    driver = get_driver()
    with driver.session() as session:
        session.run("MATCH (d:Document {id: $id}) DETACH DELETE d", id=document_id)
