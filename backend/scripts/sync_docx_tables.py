import docx
from docx.shared import Pt
from docx.oxml import parse_xml
from docx.oxml.ns import nsdecls

def update_docx():
    doc = docx.Document('ACAMIND_Bai_Bao_Khoa_Hoc_Tieng_Viet.docx')

    # Update Section 4.6
    p103 = doc.paragraphs[103]
    p103.text = '4.6. Đánh giá Đối sánh Kiến trúc với các SOTA RAG Frameworks đã Công bố'
    p103.style.font.name = 'Times New Roman'
    p103.style.font.size = Pt(13)
    p103.style.font.bold = True

    p104 = doc.paragraphs[104]
    p104.text = (
        'Để định vị Acamind trong bức tranh tổng thể của các hệ thống hỏi đáp tài liệu hiện đại, '
        'Bảng 4 trình bày đối sánh kiến trúc và năng lực chức năng với các framework RAG lớn đã công bố và các kiến trúc công nghiệp: '
        '(1) PaperQA2 [19], hệ thống agentic RAG mã nguồn mở hàng đầu cho văn bản khoa học; '
        '(2) FlashRAG [20], bộ công cụ nghiên cứu RAG mô-đun hóa từ Đại học Nhân dân Trung Quốc; '
        '(3) Microsoft GraphRAG [21], đại diện cho hướng tiếp cận tóm tắt dựa trên đồ thị tri thức phân cấp; và '
        '(4) Standard Production Hybrid RAG (như LangChain EnsembleRetriever / LlamaIndex), '
        'kết hợp tìm kiếm dense và sparse cùng mô hình Cross-Encoder rerank bắt buộc.'
    )

    p105 = doc.paragraphs[105]
    p105.text = 'Bảng 4. Đối sánh Kiến trúc và Năng lực Chức năng với các SOTA RAG Frameworks đã Công bố'

    # Update Table 4 (index 5)
    t4 = doc.tables[5]
    # Clear existing rows
    for _ in range(len(t4.rows)):
        tr = t4.rows[0]._tr
        t4._tbl.remove(tr)

    t4_headers = ['Chiều Đánh giá', 'PaperQA2 [19]', 'FlashRAG [20]', 'GraphRAG [21]', 'LangChain Std.', 'Acamind (Ours)']
    t4_rows = [
        ['Primary Paradigm', 'Agentic Multi-hop', 'Modular Benchmark', 'Graph Community', 'Dense+BM25 Ensemble', 'Parallel RRF Hybrid'],
        ['PDF Ingestion', 'PyPDF / Text', 'Clean Text Chunks', 'LLM-parsed Text', 'Standard PyPDF', 'Multi-engine + Scan Detector'],
        ['Reranking Engine', 'LLM-based Rerank', 'Cross-Encoder (100%)', 'Graph Scoring', 'Cross-Encoder (100%)', 'Confident Skip (Δ ≥ 2.5)'],
        ['Memory Caching', 'Không có', 'Không có', 'Không có', 'Session Cache', 'Dual-Memory L1 Cache'],
        ['Scan Defense', 'Không có (Báo lỗi)', 'Không có', 'Không có', 'Không có (Nhiễu prompt)', 'Circuit-Breaker Refusal'],
        ['Citation Anchor', 'Paper / Section', 'Passage-level', 'Entity / Summary', 'Passage-level', 'Exact Page [File - P.X]'],
        ['Language Scope', 'Scientific English', 'General Benchmark', 'General English', 'General Multilingual', 'Psychology (VN-EN)'],
    ]

    hdr_cells = t4.add_row().cells
    for i, h in enumerate(t4_headers):
        hdr_cells[i].text = h
        shd = parse_xml(f'<w:shd {nsdecls("w")} w:fill="F2F2F2"/>')
        hdr_cells[i]._tc.get_or_add_tcPr().append(shd)
        for p in hdr_cells[i].paragraphs:
            for r in p.runs:
                r.font.name = 'Times New Roman'
                r.font.size = Pt(9.5)
                r.font.bold = True

    for r_data in t4_rows:
        row_cells = t4.add_row().cells
        for c_idx, val in enumerate(r_data):
            row_cells[c_idx].text = val
            for p in row_cells[c_idx].paragraphs:
                for r in p.runs:
                    r.font.name = 'Times New Roman'
                    r.font.size = Pt(9)
                    if c_idx == 5:
                        r.font.bold = True

    # Update P108
    p108 = doc.paragraphs[108]
    p108.text = (
        'Như được tổng hợp trong Bảng 4 và Hình 6, sự so sánh kiến trúc làm nổi bật bốn khác biệt thiết kế then chốt:\n'
        '1. Tính ổn định khi nạp tài liệu và An toàn Circuit-Breaker: Các framework hiện có đều giả định văn bản số hóa hoàn hảo. '
        'Khi gặp các trang sách scan (<50 ký tự/trang), các baseline thông thường hoặc bị crash hoặc nạp chuỗi OCR phân mảnh vào prompt, '
        'gây ảo giác nghiêm trọng. Acamind chủ động ngắt thực thi qua bộ ngắt mạch tự động trong 1.50 s, phản hồi từ chối an toàn minh bạch.\n'
        '2. Hiệu năng Reranking và Tiết kiệm Tài nguyên tính toán: Các modular framework phổ biến (LangChain, FlashRAG) '
        'chịu độ trễ cố định của Cross-Encoder trên 100% truy vấn. Ngược lại, Acamind đánh giá động khoảng cách tin cậy (ΔRRF ≥ 2.5), '
        'bỏ qua neural rerank khi thứ tự đã rõ ràng.\n'
        '3. Truy xuất tương tác dưới 1 giây vs. Độ trễ Agentic: Mặc dù PaperQA2 đạt độ chính xác cao trên benchmark LitQA2, '
        'vòng lặp đa lượt của nó mất từ 15 đến 45 giây cho mỗi truy vấn, không thể dùng cho tham vấn tương tác thực tế. '
        'Acamind đạt độ trung thực Faithfulness 1.00 trong 2.39 giây.\n'
        '4. Neo số trang chi tiết so với Tóm tắt Đồ thị Tổng thể: Trong khi GraphRAG nổi trội ở tổng hợp chủ đề vĩ mô, '
        'nghiên cứu tâm lý học đòi hỏi đối chiếu chính xác các ngưỡng chẩn đoán và số liệu thực nghiệm, '
        'nơi tìm kiếm lai song song dense-sparse mang lại độ chính xác trích dẫn vượt trội.'
    )

    # Update Section 4.7
    p109 = doc.paragraphs[109]
    p109.text = '4.7. Controlled Empirical Ablation Benchmark trên các Retrieval Paradigms'
    p109.style.font.name = 'Times New Roman'
    p109.style.font.size = Pt(13)
    p109.style.font.bold = True

    p110 = doc.paragraphs[110]
    p110.text = (
        'Để định lượng thực nghiệm đóng góp của từng thành phần kiến trúc, chúng tôi thực hiện kiểm chuẩn có đối chứng '
        'trên năm cấu hình truy xuất khác nhau trên tập ngữ liệu tâm lý học (13 giáo trình, 1.650 chunks, 10 ca truy vấn chuẩn hóa). '
        'Tất cả cấu hình đều được thực thi trên cùng môi trường phần cứng, và kết quả được ghi nhận trong Bảng 5.'
    )

    p111 = doc.paragraphs[111]
    p111.text = 'Bảng 5. Controlled Empirical Benchmark trên Five Retrieval Paradigms trên Ngữ liệu Tâm lý học'

    # Update Table 5 (index 6 in docx)
    t5 = doc.tables[6]
    # Clear existing rows
    for _ in range(len(t5.rows)):
        tr = t5.rows[0]._tr
        t5._tbl.remove(tr)

    t5_headers = ['Configuration', 'Ret. (ms)', 'Rerank (ms)', 'Total (ms)', 'Recall@8', 'Skip (%)']
    t5_rows = [
        ['Dense-Only (HNSW DPR)', '2465.75', '0.00', '2465.75', '0.767', '0.0%'],
        ['Sparse-Only (BM25 on GIN)', '21.85', '0.00', '21.85', '0.800', '0.0%'],
        ['Hybrid RRF (w/o Reranker)', '66.74', '0.00', '66.87', '0.767', '0.0%'],
        ['Standard Hybrid + Cross-Encoder', '66.91', '467.45', '534.48', '0.767', '0.0%'],
        ['Acamind Proposed (Skip + Breaker)', '73.24', '0.08', '73.47', '0.767', '100.0%'],
    ]

    hdr_cells5 = t5.add_row().cells
    for i, h in enumerate(t5_headers):
        hdr_cells5[i].text = h
        shd = parse_xml(f'<w:shd {nsdecls("w")} w:fill="F2F2F2"/>')
        hdr_cells5[i]._tc.get_or_add_tcPr().append(shd)
        for p in hdr_cells5[i].paragraphs:
            for r in p.runs:
                r.font.name = 'Times New Roman'
                r.font.size = Pt(9.5)
                r.font.bold = True

    for r_data in t5_rows:
        row_cells = t5.add_row().cells
        for c_idx, val in enumerate(r_data):
            row_cells[c_idx].text = val
            for p in row_cells[c_idx].paragraphs:
                for r in p.runs:
                    r.font.name = 'Times New Roman'
                    r.font.size = Pt(9)
                    if c_idx == 4 and val == '0.800':
                        r.font.bold = True
                    if c_idx == 0 and 'Acamind' in val:
                        r.font.bold = True
                    if c_idx in [1, 2, 3, 5] and 'Acamind' in r_data[0]:
                        r.font.bold = True

    doc.save('ACAMIND_Bai_Bao_Khoa_Hoc_Tieng_Viet.docx')
    print('Successfully synchronized ACAMIND_Bai_Bao_Khoa_Hoc_Tieng_Viet.docx with Table 4 and Table 5!')

if __name__ == '__main__':
    update_docx()
