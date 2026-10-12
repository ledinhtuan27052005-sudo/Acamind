# -*- coding: utf-8 -*-
"""
Script sinh 1.000 kịch bản kiểm thử (Test Cases) chuyên sâu cho hệ thống Acamind,
tập trung tối đa vào TÍNH NĂNG PHÂN TÍCH LIÊN BÀI (Cross-Article Analysis).
"""

import json
import os
import random
import psycopg2

def main():
    # 1. Kết nối PostgreSQL lấy toàn bộ danh sách tài liệu thực tế
    conn = psycopg2.connect("postgresql://admin:secret@localhost:5432/rag_db")
    cur = conn.cursor()
    cur.execute("SELECT id, filename, title FROM documents ORDER BY created_at DESC;")
    rows = cur.fetchall()
    conn.close()

    documents = []
    for r in rows:
        documents.append({
            "id": str(r[0]),
            "filename": r[1] or "",
            "title": r[2] or r[1] or "Tài liệu tâm lý học"
        })

    print(f"Loaded {len(documents)} real documents from database.")
    if len(documents) < 5:
        raise ValueError("Cần ít nhất 5 tài liệu trong database để tạo bài test.")

    # 2. Phân nhóm tài liệu theo các cụm chủ đề y văn tâm lý học
    clusters = {
        "cbt_intervention": [],
        "mindfulness_stress": [],
        "adolescent_student": [],
        "depression_anxiety": [],
        "cognitive_theory": [],
        "ai_digital_health": [],
        "general_psychology": []
    }

    for d in documents:
        fn = (d["filename"] + " " + d["title"]).lower()
        if "cbt" in fn or "phac-do" in fn or "tri-lieu" in fn or "intervention" in fn or "therapy" in fn:
            clusters["cbt_intervention"].append(d)
        elif "mindfulness" in fn or "chanh-niem" in fn or "stress" in fn or "sleep" in fn or "trauma" in fn:
            clusters["mindfulness_stress"].append(d)
        elif "student" in fn or "adolescent" in fn or "sinh-vien" in fn or "hoc-sinh" in fn or "social_network" in fn or "giao_duc" in fn:
            clusters["adolescent_student"].append(d)
        elif "depression" in fn or "anxiety" in fn or "tram-cam" in fn or "lo-au" in fn or "tam-than" in fn:
            clusters["depression_anxiety"].append(d)
        elif "distortion" in fn or "mind" in fn or "emotion" in fn or "affective" in fn or "hanh-vi" in fn:
            clusters["cognitive_theory"].append(d)
        elif "llm" in fn or "ai" in fn or "digital" in fn or "dialogue" in fn or "reconnaissance" in fn:
            clusters["ai_digital_health"].append(d)
        else:
            clusters["general_psychology"].append(d)

    # Đảm bảo mỗi cluster đều có tài liệu (fallback nếu rỗng)
    for cname, clist in clusters.items():
        if not clist:
            clusters[cname] = random.sample(documents, min(3, len(documents)))

    test_cases = []
    case_idx = 1

    # ─────────────────────────────────────────────────────────────────────────
    # NHÓM 1: MA TRẬN PHÂN TÍCH ĐỐI CHIẾU LIÊN BÀI (CROSS-ARTICLE MATRIX) — 400 ca
    # Endpoint: POST /api/v1/library/analysis
    # ─────────────────────────────────────────────────────────────────────────
    print("Generating Category 1: Cross-Article Matrix (400 cases)...")
    matrix_topics = [
        ("So sánh phác đồ CBT và phương pháp Chánh niệm (Mindfulness) trong điều trị lo âu", ["cbt_intervention", "mindfulness_stress"]),
        ("Đối chiếu tác động của méo mó nhận thức và áp lực học đường ở thanh thiếu niên", ["cognitive_theory", "adolescent_student"]),
        ("So sánh hiệu quả của can thiệp tâm lý truyền thống và ứng dụng AI/LLM sức khỏe tâm thần", ["cbt_intervention", "ai_digital_health"]),
        ("Đánh giá sự khác biệt giữa trầm cảm học đường và rối loạn cảm xúc ở người trưởng thành", ["adolescent_student", "depression_anxiety"]),
        ("So sánh các công cụ đo lường stress, chất lượng giấc ngủ và khả năng tự điều hòa cảm xúc", ["mindfulness_stress", "cognitive_theory"]),
        ("Đối chiếu các nghiên cứu thực nghiệm định lượng và nghiên cứu tổng quan y văn tâm lý", ["general_psychology", "depression_anxiety"]),
        ("Đánh giá khoảng trống nghiên cứu (Research Gaps) trong can thiệp tâm lý vị thành niên", ["adolescent_student", "cbt_intervention"]),
        ("So sánh chỉ số hiệu quả lâm sàng và độ bền vững sau can thiệp tâm lý", ["cbt_intervention", "depression_anxiety"]),
    ]

    for i in range(400):
        topic_title, preferred_clusters = matrix_topics[i % len(matrix_topics)]
        # Chọn số lượng bài báo so sánh: 2 (40%), 3 (30%), 4 (15%), 5-8 (15%)
        rand_val = random.random()
        if rand_val < 0.40:
            doc_count = 2
        elif rand_val < 0.70:
            doc_count = 3
        elif rand_val < 0.85:
            doc_count = 4
        else:
            doc_count = random.randint(5, min(8, len(documents)))

        # Chọn tài liệu từ các cluster liên quan
        chosen_docs = []
        c_pool = []
        for c in preferred_clusters:
            c_pool.extend(clusters[c])
        random.shuffle(c_pool)
        for d in c_pool:
            if d not in chosen_docs:
                chosen_docs.append(d)
            if len(chosen_docs) >= doc_count:
                break
        
        while len(chosen_docs) < doc_count:
            d = random.choice(documents)
            if d not in chosen_docs:
                chosen_docs.append(d)

        test_cases.append({
            "case_id": f"ACAMIND-TEST-{case_idx:04d}",
            "category": "cross_article_matrix",
            "test_type": "Comparative Analysis Matrix",
            "name": f"[Matrix-{doc_count}Docs] {topic_title} (Biến thể {i+1})",
            "target_endpoint": "/api/v1/library/analysis",
            "method": "POST",
            "document_count": doc_count,
            "document_ids": [d["id"] for d in chosen_docs],
            "document_titles": [d["title"] for d in chosen_docs],
            "payload": {
                "article_ids": [d["id"] for d in chosen_docs]
            },
            "expected_fields": ["summary", "common_themes", "differences", "comparison_table", "research_gaps", "recommendation"],
            "validation_checks": {
                "min_themes": 1,
                "min_differences": 1,
                "min_comparison_factors": 2,
                "min_research_gaps": 1,
                "must_have_citations": True
            },
            "expected_status": 200
        })
        case_idx += 1

    # ─────────────────────────────────────────────────────────────────────────
    # NHÓM 2: HỎI ĐÁP RAG ĐA TÀI LIỆU CÓ KHỬ TRÙNG LẶP (MULTI-DOC RAG Q&A) — 350 ca
    # Endpoint: POST /api/v1/chat
    # ─────────────────────────────────────────────────────────────────────────
    print("Generating Category 2: Multi-Doc RAG Q&A (350 cases)...")
    qa_templates = [
        ("Dựa trên các bài báo được chọn, hãy phân tích điểm giống và khác nhau về phương pháp can thiệp tâm lý giữa các nghiên cứu?", ["cbt_intervention", "mindfulness_stress"]),
        ("Các nghiên cứu này đưa ra bằng chứng thực nghiệm nào về mối quan hệ giữa méo mó nhận thức và trầm cảm?", ["cognitive_theory", "depression_anxiety"]),
        ("Có sự mâu thuẫn hay đồng thuận nào về hiệu quả của liệu pháp chánh niệm đối với giấc ngủ và kiểm soát stress?", ["mindfulness_stress", "adolescent_student"]),
        ("Tổng hợp các tiêu chuẩn chẩn đoán và công cụ đo lường tâm lý được áp dụng xuyên suốt các tài liệu này?", ["cbt_intervention", "depression_anxiety"]),
        ("Hãy chỉ rõ các hạn chế về cỡ mẫu hoặc phương pháp luận mà các tác giả đã thừa nhận trong các nghiên cứu này?", ["general_psychology", "adolescent_student"]),
        ("Theo các nghiên cứu đã chọn, những yếu tố môi trường xã hội nào ảnh hưởng mạnh nhất đến sức khỏe tinh thần thanh thiếu niên?", ["adolescent_student", "mindfulness_stress"]),
        ("So sánh cơ chế tác động thần kinh - nhận thức được đề cập giữa các tài liệu đối với rối loạn lo âu?", ["cognitive_theory", "depression_anxiety"]),
    ]

    for i in range(350):
        q_text, pref_clusters = qa_templates[i % len(qa_templates)]
        doc_count = random.choice([2, 2, 3, 3, 4, 5])
        chosen_docs = []
        c_pool = []
        for c in pref_clusters:
            c_pool.extend(clusters[c])
        random.shuffle(c_pool)
        for d in c_pool:
            if d not in chosen_docs:
                chosen_docs.append(d)
            if len(chosen_docs) >= doc_count:
                break
        while len(chosen_docs) < doc_count:
            d = random.choice(documents)
            if d not in chosen_docs:
                chosen_docs.append(d)

        test_cases.append({
            "case_id": f"ACAMIND-TEST-{case_idx:04d}",
            "category": "multi_doc_rag_qa",
            "test_type": "Multi-Document Grounded Q&A",
            "name": f"[MultiRAG-{doc_count}Docs] Q&A đối chiếu liên bài #{i+1}",
            "target_endpoint": "/api/v1/chat",
            "method": "POST",
            "document_count": doc_count,
            "document_ids": [d["id"] for d in chosen_docs],
            "document_titles": [d["title"] for d in chosen_docs],
            "payload": {
                "query": f"{q_text} (Kiểm thử thực nghiệm #{i+1})",
                "document_ids": [d["id"] for d in chosen_docs],
                "mode": "multi"
            },
            "validation_checks": {
                "verify_cross_doc_dedup": True,
                "must_contain_citations": True,
                "no_hallucination_marker": True,
                "min_response_tokens": 80
            },
            "expected_status": 200
        })
        case_idx += 1

    # ─────────────────────────────────────────────────────────────────────────
    # NHÓM 3: TỰ ĐỘNG SINH TỔNG QUAN TÀI LIỆU (LITERATURE REVIEW) — 150 ca
    # Endpoint: POST /api/v1/features/literature-review
    # ─────────────────────────────────────────────────────────────────────────
    print("Generating Category 3: Literature Review Synthesis (150 cases)...")
    lit_focuses = [
        "Hiệu quả can thiệp của Liệu pháp Hành vi Nhận thức (CBT) đối với rối loạn lo âu và trầm cảm học đường",
        "Vai trò của thực hành Chánh niệm (Mindfulness) trong điều hòa căng thẳng và phục hồi chấn thương tâm lý",
        "Mối tương quan giữa mạng xã hội, lòng tự trắc ẩn và chất lượng giấc ngủ ở học sinh sinh viên",
        "Ứng dụng trí tuệ nhân tạo và mô hình ngôn ngữ lớn (LLMs) trong hỗ trợ tư vấn sức khỏe tâm thần",
        "Các mô hình nhận thức về cơ chế tự vệ, méo mó nhận thức và phục hồi tâm lý tích cực",
    ]

    for i in range(150):
        focus = lit_focuses[i % len(lit_focuses)]
        doc_count = random.randint(3, min(10, len(documents)))
        chosen_docs = random.sample(documents, doc_count)

        test_cases.append({
            "case_id": f"ACAMIND-TEST-{case_idx:04d}",
            "category": "literature_review_synthesis",
            "test_type": "Automated Literature Review Generation",
            "name": f"[LiteratureReview-{doc_count}Docs] Tổng quan: {focus[:45]}...",
            "target_endpoint": "/api/v1/features/literature-review",
            "method": "POST",
            "document_count": doc_count,
            "document_ids": [d["id"] for d in chosen_docs],
            "document_titles": [d["title"] for d in chosen_docs],
            "payload": {
                "document_ids": [d["id"] for d in chosen_docs],
                "focus": f"{focus} (Test Run #{i+1})"
            },
            "validation_checks": {
                "required_sections": [
                    "1. Giới thiệu",
                    "2. Các chủ đề chính",
                    "3. Phương pháp nghiên cứu",
                    "4. Kết quả và phát hiện",
                    "5. Khoảng trống nghiên cứu",
                    "6. Kết luận"
                ],
                "citation_format_check": True
            },
            "expected_status": 200
        })
        case_idx += 1

    # ─────────────────────────────────────────────────────────────────────────
    # NHÓM 4: KIỂM THỬ GIỚI HẠN & CIRCUIT-BREAKER (BOUNDARY & STRESS) — 100 ca
    # ─────────────────────────────────────────────────────────────────────────
    print("Generating Category 4: Boundary & Stress Cases (100 cases)...")
    for i in range(100):
        btype = i % 4
        if btype == 0:
            # So sánh 2 tài liệu hoàn toàn không cùng chủ đề (Disparate Topic Comparison)
            d1 = random.choice(clusters["cbt_intervention"])
            d2 = random.choice(clusters["ai_digital_health"])
            t_name = "[Stress-Disparate] So sánh hai tài liệu phân kỳ chủ đề"
            payload = {"article_ids": [d1["id"], d2["id"]]}
            endpoint = "/api/v1/library/analysis"
            d_count = 2
            c_docs = [d1, d2]
        elif btype == 1:
            # Ngưỡng tối đa 8 tài liệu trong ma trận phân tích (Max Matrix Capacity)
            c_docs = random.sample(documents, min(8, len(documents)))
            d_count = len(c_docs)
            t_name = "[Stress-Max8Docs] Kiểm tra tải tối đa ma trận đối chiếu 8 tài liệu"
            payload = {"article_ids": [d["id"] for d in c_docs]}
            endpoint = "/api/v1/library/analysis"
        elif btype == 2:
            # Ngưỡng tối đa 10 tài liệu trong Literature Review (Max Lit Review Capacity)
            c_docs = random.sample(documents, min(10, len(documents)))
            d_count = len(c_docs)
            t_name = "[Stress-Max10Docs] Kiểm tra tải tối đa Literature Review 10 tài liệu"
            payload = {
                "document_ids": [d["id"] for d in c_docs],
                "focus": "Tổng quan toàn diện các hướng tiếp cận y văn tâm lý học đương đại"
            }
            endpoint = "/api/v1/features/literature-review"
        else:
            # Câu hỏi ngoài phạm vi tài liệu (Out-of-Scope Multi-Doc Query)
            c_docs = random.sample(documents, 3)
            d_count = 3
            t_name = "[Stress-SafeRefusal] Truy vấn nằm ngoài phạm vi tài liệu đã chọn"
            payload = {
                "query": "Các tài liệu này nói gì về công thức chế tạo động cơ tên lửa không gian?",
                "document_ids": [d["id"] for d in c_docs],
                "mode": "multi"
            }
            endpoint = "/api/v1/chat"

        test_cases.append({
            "case_id": f"ACAMIND-TEST-{case_idx:04d}",
            "category": "cross_boundary_stress",
            "test_type": "Boundary and Edge Case Stress Test",
            "name": f"{t_name} #{i+1}",
            "target_endpoint": endpoint,
            "method": "POST",
            "document_count": d_count,
            "document_ids": [d["id"] for d in c_docs],
            "document_titles": [d["title"] for d in c_docs],
            "payload": payload,
            "validation_checks": {
                "handle_gracefully": True,
                "no_unhandled_crash": True
            },
            "expected_status": 200
        })
        case_idx += 1

    # 3. Xuất ra file JSON
    out_file = r"data/operational_test_1000_cross_article.json"
    os.makedirs("data", exist_ok=True)
    with open(out_file, "w", encoding="utf-8") as f:
        json.dump(test_cases, f, ensure_ascii=False, indent=2)

    print(f"\n[DONE] Successfully created {len(test_cases)} cross-article test cases!")
    print(f"Saved to: {os.path.abspath(out_file)}")

if __name__ == "__main__":
    main()
