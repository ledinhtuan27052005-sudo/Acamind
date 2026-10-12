from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import text
from app.db.postgres import get_db
import logging
import re

logger = logging.getLogger(__name__)
router = APIRouter()

# Danh mục Thực thể Học thuật Chuẩn cho GraphRAG Tâm lý học
ACADEMIC_METHODS = {
    "cbt": "Cognitive Behavioral Therapy (CBT)",
    "mindfulness": "Mindfulness & Thiền định",
    "therapy": "Tâm lý trị liệu (Psychotherapy)",
    "llm": "AI & Mô hình Ngôn ngữ lớn (LLM)",
    "dialogue": "Hệ thống Đối thoại Lâm sàng",
    "digital": "Sức khỏe Tâm thần Số (Digital Health)",
}

ACADEMIC_CONDITIONS = {
    "depression": "Trầm cảm (Depression)",
    "anxiety": "Rối loạn Lo âu (Anxiety)",
    "stress": "Căng thẳng & Stress (Perceived Stress)",
    "trauma": "Sang chấn & PTSD (Trauma Recovery)",
    "sleep": "Rối loạn Giấc ngủ (Sleep Disorder)",
    "psychotic": "Rối loạn Loạn thần (Psychotic Disorder)",
    "distortion": "Sai lệch Nhận thức (Cognitive Distortion)",
}

# Ánh xạ Phương pháp -> Điều trị -> Bệnh chứng
TREATMENT_RELATIONS = [
    ("cbt", "depression", "TREATS"),
    ("cbt", "anxiety", "TREATS"),
    ("cbt", "distortion", "CORRECTS"),
    ("mindfulness", "stress", "REDUCES"),
    ("mindfulness", "anxiety", "ALLEVIATES"),
    ("mindfulness", "sleep", "IMPROVES"),
    ("llm", "depression", "DIAGNOSES"),
    ("llm", "anxiety", "SCREENS"),
    ("dialogue", "therapy", "FACILITATES"),
]


def _build_graph_from_db(db: Session) -> dict:
    """Tự động tổng hợp Đồ thị Tri thức Học thuật (GraphRAG) trực tiếp từ PostgreSQL."""
    docs = db.execute(text("""
        SELECT id, title, authors, year, filename 
        FROM documents 
        WHERE status = 'ready' 
        ORDER BY created_at DESC 
        LIMIT 100
    """)).fetchall()

    nodes = {}
    edges = []
    edge_idx = 0

    # 1. Tạo các Node Phương pháp (Method) & Bệnh chứng (Condition)
    for m_key, m_name in ACADEMIC_METHODS.items():
        nid = f"method-{m_key}"
        nodes[nid] = {
            "id": nid,
            "type": "method",
            "position": {"x": 0, "y": 0},
            "data": {"label": m_name, "nodeType": "Method", "category": "Intervention"}
        }

    for c_key, c_name in ACADEMIC_CONDITIONS.items():
        nid = f"condition-{c_key}"
        nodes[nid] = {
            "id": nid,
            "type": "condition",
            "position": {"x": 0, "y": 0},
            "data": {"label": c_name, "nodeType": "Condition", "category": "Disorder"}
        }

    # 2. Tạo các Cạnh Điều trị (TREATS / REDUCES / CORRECTS)
    for m_key, c_key, rel_type in TREATMENT_RELATIONS:
        source_id = f"method-{m_key}"
        target_id = f"condition-{c_key}"
        if source_id in nodes and target_id in nodes:
            edges.append({
                "id": f"e-treat-{edge_idx}",
                "source": source_id,
                "target": target_id,
                "label": rel_type,
                "animated": True,
            })
            edge_idx += 1

    # 3. Tạo Node Document và liên kết STUDIES tới Concept
    doc_concepts = {}
    for r in docs:
        doc_id = str(r.id)
        d_key = f"doc-{doc_id}"
        d_title = (r.title or r.filename or "Untitled")[:60]
        nodes[d_key] = {
            "id": d_key,
            "type": "document",
            "position": {"x": 0, "y": 0},
            "data": {
                "label": d_title,
                "docId": doc_id,
                "year": r.year or 2024,
                "nodeType": "Document"
            }
        }

        # Quét tiêu đề và filename để tìm Concept liên quan
        haystack = f"{r.title or ''} {r.filename or ''}".lower()
        matched_methods = [k for k in ACADEMIC_METHODS if k in haystack]
        matched_conditions = [k for k in ACADEMIC_CONDITIONS if k in haystack]

        doc_concepts[doc_id] = matched_methods + matched_conditions

        for m in matched_methods:
            edges.append({
                "id": f"e-study-{edge_idx}",
                "source": d_key,
                "target": f"method-{m}",
                "label": "STUDIES",
                "animated": False,
            })
            edge_idx += 1

        for c in matched_conditions:
            edges.append({
                "id": f"e-study-{edge_idx}",
                "source": d_key,
                "target": f"condition-{c}",
                "label": "INVESTIGATES",
                "animated": False,
            })
            edge_idx += 1

        # Tạo Author nodes và cạnh WROTE
        if r.authors:
            for author in [a.strip() for a in r.authors.replace(";", ",").split(",") if a.strip()][:3]:
                ak = f"author-{author}"
                if ak not in nodes:
                    nodes[ak] = {
                        "id": ak,
                        "type": "author",
                        "position": {"x": 0, "y": 0},
                        "data": {"label": author, "nodeType": "Author"}
                    }
                edges.append({
                    "id": f"e-wrote-{edge_idx}",
                    "source": ak,
                    "target": d_key,
                    "label": "WROTE",
                    "animated": False,
                })
                edge_idx += 1

    # 4. Tạo cạnh CROSS_REFERENCES giữa các bài báo có chung chủ đề nghiên cứu
    doc_ids = list(doc_concepts.keys())
    for i in range(len(doc_ids)):
        for j in range(i + 1, min(i + 4, len(doc_ids))):
            d1, d2 = doc_ids[i], doc_ids[j]
            shared = set(doc_concepts[d1]).intersection(set(doc_concepts[d2]))
            if shared:
                edges.append({
                    "id": f"e-cross-{edge_idx}",
                    "source": f"doc-{d1}",
                    "target": f"doc-{d2}",
                    "label": "CROSS_REFERENCES",
                    "animated": False,
                })
                edge_idx += 1

    stats = {
        "total_documents": sum(1 for n in nodes.values() if n["type"] == "document"),
        "total_authors": sum(1 for n in nodes.values() if n["type"] == "author"),
        "total_methods": len(ACADEMIC_METHODS),
        "total_conditions": len(ACADEMIC_CONDITIONS),
        "total_edges": len(edges),
    }

    return {"nodes": list(nodes.values()), "edges": edges, "stats": stats}


@router.get("")
def get_graph(db: Session = Depends(get_db)):
    """Trả về toàn bộ đồ thị tri thức (GraphRAG) với khả năng tự phục hồi."""
    try:
        from app.db.neo4j import get_driver
        driver = get_driver()
        with driver.session() as session:
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

            if nodes:
                authors_n = sum(1 for n in nodes.values() if n["type"] == "author")
                docs_n = sum(1 for n in nodes.values() if n["type"] == "document")
                return {"nodes": list(nodes.values()), "edges": edges,
                        "stats": {"total_authors": authors_n, "total_documents": docs_n}}
    except Exception as e:
        logger.info("Neo4j not active, using synthesized PostgreSQL GraphRAG: %s", e)

    return _build_graph_from_db(db)


@router.get("/academic")
def get_academic_graph(db: Session = Depends(get_db)):
    """Trả về đồ thị thực thể học thuật phân nhóm (Method, Condition, Document, Treatment)."""
    return _build_graph_from_db(db)


@router.get("/author/{name}")
def get_author_papers(name: str, db: Session = Depends(get_db)):
    """Truy vấn danh sách công trình của tác giả."""
    try:
        from app.db.neo4j import get_driver
        driver = get_driver()
        with driver.session() as session:
            result = session.run("""
                MATCH (a:Author {name: $name})-[:WROTE]->(d:Document)
                RETURN d.id AS doc_id, d.title AS title, d.year AS year ORDER BY d.year DESC
            """, name=name)
            papers = [{"id": r["doc_id"], "title": r["title"], "year": r["year"]} for r in result]
            if papers:
                return {"author": name, "papers": papers, "total": len(papers)}
    except Exception:
        pass

    # Fallback PostgreSQL
    docs = db.execute(text("""
        SELECT id, title, year 
        FROM documents 
        WHERE authors ILIKE :name 
        ORDER BY created_at DESC
    """), {"name": f"%{name}%"}).fetchall()
    papers = [{"id": str(r.id), "title": r.title or "Untitled", "year": r.year or 2024} for r in docs]
    return {"author": name, "papers": papers, "total": len(papers)}
