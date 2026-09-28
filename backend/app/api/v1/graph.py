from fastapi import APIRouter, Depends
from neo4j import Session as Neo4jSession
from app.db.neo4j import get_neo4j_session

router = APIRouter()

@router.get("")
def get_graph(session: Neo4jSession = Depends(get_neo4j_session)):
    result = session.run("""
        MATCH (a:Author)-[:WROTE]->(d:Document)
        RETURN a.name AS author, d.id AS doc_id, d.title AS doc_title, d.year AS year
        ORDER BY d.year DESC LIMIT 500
    """)
    nodes, edges = {}, []
    edge_id = 0
    for r in result:
        ak = f"author-{r['author']}"
        if ak not in nodes:
            nodes[ak] = {"id": ak, "type": "author", "position": {"x": 0, "y": 0},
                         "data": {"label": r["author"], "nodeType": "Author"}}
        dk = f"doc-{r['doc_id']}"
        if dk not in nodes:
            nodes[dk] = {"id": dk, "type": "document", "position": {"x": 0, "y": 0},
                         "data": {"label": (r["doc_title"] or "Untitled")[:55], "year": r["year"], "docId": r["doc_id"], "nodeType": "Document"}}
        edges.append({"id": f"e{edge_id}", "source": ak, "target": dk, "label": "WROTE", "animated": False})
        edge_id += 1

    authors_n = sum(1 for n in nodes.values() if n["type"] == "author")
    docs_n = sum(1 for n in nodes.values() if n["type"] == "document")
    return {"nodes": list(nodes.values()), "edges": edges,
            "stats": {"total_authors": authors_n, "total_documents": docs_n}}

@router.get("/author/{name}")
def get_author_papers(name: str, session: Neo4jSession = Depends(get_neo4j_session)):
    result = session.run("""
        MATCH (a:Author {name: $name})-[:WROTE]->(d:Document)
        RETURN d.id AS doc_id, d.title AS title, d.year AS year ORDER BY d.year DESC
    """, name=name)
    papers = [{"id": r["doc_id"], "title": r["title"], "year": r["year"]} for r in result]
    return {"author": name, "papers": papers, "total": len(papers)}
