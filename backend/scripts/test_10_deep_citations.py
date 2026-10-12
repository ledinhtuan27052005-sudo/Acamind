import sys
import os
import re
import json
from pathlib import Path

# Ensure backend root is on sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.db.postgres import SessionLocal
from app.services.retriever import retrieve
from app.services.generator import generate_answer

def run_tests():
    sys.stdout.reconfigure(encoding='utf-8')
    
    # 10 kịch bản câu hỏi kiểm tra độ sâu trích dẫn (Introduction, Methods, Results, Discussion, Phác đồ...)
    scenarios = [
        {
            "id": 1,
            "title": "Phác đồ điều trị tâm thần phân liệt và liều lượng can thiệp",
            "query": "Các giai đoạn điều trị và phác đồ can thiệp dùng thuốc đối với bệnh tâm thần phân liệt theo phác đồ hướng dẫn là gì?",
            "target_section": "Phác đồ lâm sàng, liều dùng chi tiết từng loại thuốc (Trang 85, 89)",
        },
        {
            "id": 2,
            "title": "Hiệu quả can thiệp CBT và tỷ lệ thuyên giảm triệu chứng trầm cảm",
            "query": "Các nghiên cứu thực nghiệm về ứng dụng Trí tuệ nhân tạo và CBT cho thấy tỷ lệ cải thiện và thuyên giảm triệu chứng trầm cảm (thang BDI-II hoặc PHQ-9) như thế nào?",
            "target_section": "Kết quả thực nghiệm lâm sàng, tỷ lệ % thuyên giảm (Trang 3, 11)",
        },
        {
            "id": 3,
            "title": "Công cụ đo lường và thang đo chánh niệm (FFMQ, PSS) trong nghiên cứu thực nghiệm",
            "query": "Trong nghiên cứu thực nghiệm về chánh niệm và mức độ stress cảm nhận (Perceived Stress), các tác giả đã sử dụng những thang đo công cụ nào (như FFMQ, PSS) và mô hình phân tích autoregressive/cross-lagged ra sao?",
            "target_section": "Phương pháp và công cụ đo lường (Methods & Instruments - Trang 4)",
        },
        {
            "id": 4,
            "title": "Phân loại 15 dạng méo mó nhận thức (Cognitive Distortions) trong văn bản",
            "query": "Các dạng méo mó nhận thức (cognitive distortions) nào được nhận diện và phân loại trong các mô hình xử lý ngôn ngữ tự nhiên về sức khỏe tâm thần?",
            "target_section": "Thực nghiệm phân loại và thảo luận (Evaluation & Discussion - Trang 5, 8)",
        },
        {
            "id": 5,
            "title": "Hệ số tương quan và mô hình SEM giữa nhu cầu tâm lý và trì hoãn học tập",
            "query": "Nghiên cứu về mối liên hệ giữa sự thỏa mãn các nhu cầu tâm lý cơ bản, động lực học tập và trì hoãn học tập ở sinh viên đưa ra kết quả thống kê và hệ số tương quan như thế nào?",
            "target_section": "Kết quả thống kê và phân tích đường dẫn (Results & Path Analysis - Trang 26, 43)",
        },
        {
            "id": 6,
            "title": "Quy trình sơ cứu tâm lý ban đầu (Psychological First Aid - PFA)",
            "query": "Quy trình và nguyên tắc hành động cốt lõi trong sơ cứu tâm lý khẩn cấp (PFA) gồm những bước nào đối với người bị sang chấn?",
            "target_section": "Quy trình hành động cốt lõi (Look, Listen, Link - Trang 24, 60)",
        },
        {
            "id": 7,
            "title": "Động cơ và mức độ sử dụng mạng xã hội ở sinh viên (Cỡ mẫu N=818 và mô hình hồi quy)",
            "query": "Nghiên cứu khảo sát trên sinh viên về mức độ sử dụng mạng xã hội trong Tạp chí Nghiên cứu giáo dục số 6/2023 có cỡ mẫu bao nhiêu, tương quan Pearson và mô hình hồi quy tuyến tính chỉ ra điều gì?",
            "target_section": "Bảng tương quan và mô hình hồi quy (Bảng 7, 8 - Trang 115, 116)",
        },
        {
            "id": 8,
            "title": "Đặc điểm bệnh nhân và phân tích hồi quy sức khỏe tâm thần tích cực (PMH)",
            "query": "Trong nghiên cứu về sức khỏe tâm thần tích cực (Positive Mental Health - PMH) ở bệnh nhân rối loạn loạn thần (psychotic disorder), cỡ mẫu khảo sát là bao nhiêu, tỷ lệ dùng thuốc điều trị và kết quả hồi quy STATA ra sao?",
            "target_section": "Đặc điểm lâm sàng và phân tích hồi quy STATA (Results - Trang 5, 11)",
        },
        {
            "id": 9,
            "title": "Quy luật phản xạ có điều kiện và củng cố hành vi trong giáo trình tâm lý",
            "query": "Trong giáo trình tâm lý học và tâm lý học hành vi, quy luật hình thành phản xạ có điều kiện và các chế độ củng cố (reinforcement schedules) được giải thích chi tiết như thế nào?",
            "target_section": "Chương lý thuyết học tập và điều kiện hóa (Theory - Trang 97, 98 và Trang 59, 73)",
        },
        {
            "id": 10,
            "title": "Thảo luận về rủi ro đạo đức, ảo giác và hạn chế lâm sàng của LLM",
            "query": "Các bài báo tổng quan về mô hình ngôn ngữ lớn (LLM) trong sức khỏe tâm thần chỉ ra những rủi ro đạo đức, ảo giác (hallucination) và hạn chế lâm sàng nào trong phần thảo luận?",
            "target_section": "Phần Thảo luận và Hạn chế nghiên cứu (Discussion & Limitations - Trang 9, 19)",
        }
    ]

    results = []

    with SessionLocal() as db:
        for sc in scenarios:
            print(f"\n=======================================================")
            print(f"[*] ĐANG CHẠY KỊCH BẢN #{sc['id']}: {sc['title']}")
            print(f"Câu hỏi: {sc['query']}")
            print(f"Khu vực nội dung mục tiêu: {sc['target_section']}")
            
            # 1. Truy xuất Hybrid (Vector + BM25 + Rerank + Parent Context)
            chunks = retrieve(sc["query"], document_ids=None, db=db, top_k=8)
            print(f"-> Thu được {len(chunks)} chunks liên quan.")
            
            chunk_details = []
            for idx, c in enumerate(chunks[:5], 1):
                doc_name = c.get("doc_filename") or c.get("doc_title") or "Unknown"
                page = c.get("page_number", "?")
                content_preview = (c.get("content") or "")[:150].replace("\n", " ")
                print(f"   [Chunk {idx}] Doc: {doc_name} | Trang: {page}")
                chunk_details.append({
                    "doc": doc_name,
                    "page": page,
                    "preview": content_preview,
                })
                
            # 2. Sinh câu trả lời với trích dẫn
            try:
                answer = generate_answer(sc["query"], chunks, lang="vi")
            except Exception as e:
                answer = f"Lỗi sinh câu trả lời: {e}"

            # 3. Phân tích các trích dẫn trong câu trả lời
            citation_pattern = re.compile(r'\[([^\]]+)\]')
            matches = citation_pattern.findall(answer)
            parsed_citations = []
            pages_cited = []
            for m in matches:
                sub_parts = m.split(";")
                for sub in sub_parts:
                    p_match = re.search(r'([^\[]+?)\s*-\s*(?:Page|Trang)\s+(\d+)', sub, re.IGNORECASE)
                    if p_match:
                        fn = p_match.group(1).strip()
                        pg = int(p_match.group(2))
                        parsed_citations.append(f"[{fn} - Trang {pg}]")
                        pages_cited.append((fn, pg))

            print(f"\n-> Các trích dẫn được sinh trong bài:")
            unique_citations = list(dict.fromkeys(parsed_citations))
            for uc in unique_citations:
                print(f"   * {uc}")

            non_abstract_citations = [p for p in pages_cited if p[1] > 1]
            deep_body_citations = [p for p in pages_cited if p[1] >= 3]
            
            print(f"-> Tổng số trích dẫn: {len(pages_cited)}")
            print(f"-> Trích dẫn ngoài Abstract (Trang > 1): {len(non_abstract_citations)} / {len(pages_cited)}")
            print(f"-> Trích dẫn sâu trong thân bài (Trang >= 3): {len(deep_body_citations)} / {len(pages_cited)}")
            
            results.append({
                "scenario_id": sc["id"],
                "title": sc["title"],
                "query": sc["query"],
                "target_section": sc["target_section"],
                "retrieved_chunks": chunk_details,
                "citations": unique_citations,
                "pages_cited": pages_cited,
                "answer_snippet": answer[:400].replace("\n", " "),
                "full_answer": answer
            })

    output_path = Path(__file__).resolve().parent / "test_10_scenarios_results_final.json"
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    print(f"\n[V] Đã hoàn thành kiểm thử 10 kịch bản hoàn chỉnh! Kết quả lưu tại: {output_path}")

if __name__ == "__main__":
    run_tests()
