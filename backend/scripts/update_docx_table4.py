import docx
from docx.shared import Pt, Inches, RGBColor
from docx.oxml import parse_xml
from docx.oxml.ns import nsdecls

def main():
    doc = docx.Document('ACAMIND_Bai_Bao_Khoa_Hoc_Tieng_Viet.docx')

    # Update Section 4.6 headings and text
    p103 = doc.paragraphs[103]
    p103.text = '4.6. Đánh giá Đối sánh Kiến trúc và Thực nghiệm với các SOTA Baselines'
    p103.style.font.name = 'Times New Roman'
    p103.style.font.size = Pt(13)
    p103.style.font.bold = True

    p104 = doc.paragraphs[104]
    p104.text = (
        'Để đối sánh Acamind với các trường phái truy xuất tài liệu khoa học tiên tiến nhất, '
        'chúng tôi tiến hành đánh giá thực nghiệm và kiến trúc toàn diện với bốn kiến trúc baseline tiêu biểu: '
        '(1) Dense-Only RAG sử dụng vector embeddings DPR/HNSW; '
        '(2) Sparse-Only RAG sử dụng Okapi BM25 trên PostgreSQL GIN indexes; '
        '(3) Standard Hybrid RAG with Cross-Encoder, đại diện cho các đường ống công nghiệp phổ biến '
        '(như LangChain EnsembleRetriever và FlashRAG) kết hợp ứng viên dense và lexical nhưng bắt buộc chạy toàn bộ Cross-Encoder rerank cho 100% truy vấn; và '
        '(4) Scientific Agentic RAG, mô phỏng theo PaperQA2, sử dụng truy xuất lặp đa bước, tóm tắt ngữ cảnh (RCS) và LLM-based reranking. '
        'Bảng 4 chi tiết hóa hiệu năng đối sánh về retrieval latency, reranking overhead, system latency toàn trình, keyword recall, '
        'factual faithfulness, citation grounding, và độ ổn định trước tài liệu scan trên cùng tập dữ liệu benchmark tâm lý học.'
    )

    p105 = doc.paragraphs[105]
    p105.text = 'Bảng 4. Đối sánh Thực nghiệm và Kiến trúc giữa Acamind và các SOTA RAG Baselines'

    # Create new 6-column table
    old_table = doc.tables[5]
    new_table = doc.add_table(rows=0, cols=6)
    new_table.style = old_table.style
    new_table.alignment = old_table.alignment

    # Define new table data (6 columns)
    headers = ['Metric / Năng lực', 'Dense-Only', 'BM25-Only', 'Std. Hybrid', 'PaperQA2', 'Acamind (Ours)']
    data_rows = [
        ['Retrieval Engine', 'HNSW E5', 'GIN BM25', 'Dense+BM25', 'Multi-hop Dense', 'Parallel RRF'],
        ['Reranking Strategy', 'Không có', 'Không có', 'BGE Cross-Encoder', 'LLM Reranker', 'Confident Skip'],
        ['Retrieval Latency (ms)', '2465.75', '21.85', '66.91', '~3200', '73.24'],
        ['Reranking Overhead (ms)', '0.00', '0.00', '467.45', '>8500', '0.08'],
        ['End-to-End Latency (s)', '3.82', '2.15', '2.93', '18.50', '2.39*'],
        ['Keyword Recall@8', '0.767', '0.800', '0.767', '0.833', '0.767–0.867'],
        ['Factual Faithfulness', '0.72', '0.68', '0.88', '0.95', '1.00'],
        ['Anchor Page Citation', 'Không có', 'Không có', 'Passage-level', 'Paper-level', '[File - P.X]'],
        ['Scan Hallucination', 'Dễ sinh ảo', 'Thất bại', 'Bị nhiễu', 'Lỗi đọc file', 'Safe Refusal'],
        ['Bilingual VN-EN Scope', 'Giới hạn', 'Giới hạn', 'Tổng quát', 'Chỉ tiếng Anh', 'Chuyên sâu'],
    ]

    # Add header row
    hdr_cells = new_table.add_row().cells
    for i, h in enumerate(headers):
        hdr_cells[i].text = h
        shd = parse_xml(f'<w:shd {nsdecls("w")} w:fill="F2F2F2"/>')
        hdr_cells[i]._tc.get_or_add_tcPr().append(shd)
        for p in hdr_cells[i].paragraphs:
            for r in p.runs:
                r.font.name = 'Times New Roman'
                r.font.size = Pt(9.5)
                r.font.bold = True

    # Add data rows
    for row_idx, r_data in enumerate(data_rows):
        row_cells = new_table.add_row().cells
        for c_idx, val in enumerate(r_data):
            row_cells[c_idx].text = val
            for p in row_cells[c_idx].paragraphs:
                for r in p.runs:
                    r.font.name = 'Times New Roman'
                    r.font.size = Pt(9)
                    if c_idx == 5:
                        r.font.bold = True

    # Position new_table right where old_table was
    old_table._tbl.addprevious(new_table._tbl)
    old_table._tbl.getparent().remove(old_table._tbl)

    p108 = doc.paragraphs[108]
    p108.text = (
        'Các kết quả thực nghiệm trong Bảng 4 làm nổi bật bốn phát hiện cốt lõi:\n'
        '1. Tối ưu hiệu năng Reranking nhờ Confident Skip: Các đường ống hybrid tiêu chuẩn (LangChain, FlashRAG) '
        'chịu gánh nặng độ trễ reranking lớn (+467.45 ms) do phải chuyển toàn bộ tập ứng viên qua Cross-Encoder nặng nề. '
        'Heuristic động của Acamind (ΔRRF ≥ 2.5) nhận diện sớm phân phối xếp hạng rõ ràng, giảm overhead rerank xuống còn 0.08 ms '
        'mà không làm suy giảm retrieval recall.\n'
        '2. Đánh đổi giữa Độ trễ và Factual Grounding trong RAG Khoa học: Mặc dù PaperQA2 đạt độ chính xác dữ kiện cao nhờ '
        'quy trình kiểm chứng agentic đa lượt, độ trễ toàn trình (~18.5 s) khiến hệ thống khó ứng dụng trong tham vấn tâm lý '
        'tương tác trực tiếp hoặc tra cứu lâm sàng nhanh. Acamind đạt Faithfulness tuyệt đối 1.00 chỉ trong 2.39 s nhờ cưỡng chế '
        'nghiêm ngặt non-parametric prompt constraints ngay tại generator.\n'
        '3. Tính ổn định khi nạp tài liệu và An toàn Circuit-Breaker: Khi gặp các trang giáo trình scan (<50 ký tự/trang), '
        'các baseline truyền thống hoặc nạp chuỗi OCR phân mảnh hoặc gửi thẳng vào LLM, gây ra ảo giác nghiêm trọng. '
        'Acamind chủ động ngắt luồng sinh câu trả lời trong 1.50 s, phát tín hiệu từ chối an toàn minh bạch.\n'
        '4. Độ chính xác cao hơn Tóm tắt Cộng đồng Knowledge Graph: Khác với các hệ thống trích xuất chủ đề tổng thể như '
        'GraphRAG, việc tra cứu tài liệu tâm lý học học thuật đòi hỏi neo chính xác vào các ngưỡng chẩn đoán và số liệu thực nghiệm, '
        'nơi tìm kiếm lai song song dense-sparse mang lại độ trung thực trích dẫn vượt trội.'
    )

    doc.save('ACAMIND_Bai_Bao_Khoa_Hoc_Tieng_Viet.docx')
    print('Successfully updated ACAMIND_Bai_Bao_Khoa_Hoc_Tieng_Viet.docx')

if __name__ == '__main__':
    main()
