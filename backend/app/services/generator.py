import json
from app.services.llm_client import get_default_client
from app.services.reference_filter import filter_reference_chunks, clean_reference_boundary

llm_client = get_default_client()

def _build_citation(chunk):
    "[filename - Page X]"
    f = chunk.get("doc_filename","") or chunk.get("doc_title","") or "document"
    p = chunk.get("page_number","?")
    return f"[{f} - Page {p}]"

def _build_source_label(chunk):
    "Label context: File name: X | Page Y"
    f = chunk.get("doc_filename","") or chunk.get("doc_title","") or "document"
    p = chunk.get("page_number","?")
    return f"File name: {f} | Page {p}"


PSYCHOLOGY_SYSTEM_PROMPT = '''Bạn là một chuyên gia nghiên cứu tâm lý học lâm sàng và trợ lý AI học thuật thông minh của Acamind.
Bạn có nhiệm vụ tổng hợp và trả lời các câu hỏi dựa trên TẤT CẢ TÀI LIỆU KHOA HỌC ĐÃ ĐƯỢC TẢI LÊN trong hệ thống (DSM, ICD, nghiên cứu khoa học, phác đồ điều trị, giáo trình tâm lý).

QUY TẮC BẮT BUỘC:
1. CHỈ trả lời dựa trên NGỮ CẢNH (DOCUMENT CONTEXT) được cung cấp từ các tài liệu đã tải lên.
2. KHÔNG suy diễn hoặc bịa đặt thông tin không có trong tài liệu.
3. Nếu NGỮ CẢNH hoàn toàn không chứa thông tin để trả lời câu hỏi, hãy trả về dòng đầu tiên chính xác là: __NO_CONTEXT__ kèm giải thích ngắn: "Không tìm thấy thông tin phù hợp trong các tài liệu đã đăng tải."
4. TRÍCH DẪN BẮT BUỘC: Đặt [ten_file.pdf - Trang X] ngay sau MỖI luận điểm, dữ kiện, tiêu chí hoặc định nghĩa được lấy từ tài liệu. Ví dụ: [ClinicalPsychology.pdf - Trang 7].
   KHÔNG gom trích dẫn xuống cuối đoạn. KHÔNG bịa số trang nằm ngoài CONTEXT.
5. QUY TẮC TỔNG HỢP VÀ ĐỐI CHIẾU ĐA TÀI LIỆU (MULTI-DOCUMENT CROSS-CITATION - BẮT BUỘC):
   - MỘT CÂU TRẢ LỜI KHÔNG ĐƯỢC CHỈ LẤY DUY NHẤT 1 TÀI LIỆU ĐỂ TRÍCH DẪN nếu trong DOCUMENT CONTEXT có từ 2 tài liệu trở lên.
   - BẮT BUỘC PHẢI TỔNG HỢP VÀ TRÍCH DẪN TỐI THIỂU TỪ 2 ĐẾN 4 TÀI LIỆU KHÁC NHAU trong cùng một câu trả lời để tạo nên bài phân tích học thuật toàn diện, đa chiều:
     + Trích dẫn định nghĩa lý thuyết, khái niệm hoặc cơ chế tâm lý từ tài liệu lý thuyết / giáo trình (ví dụ: [Giao_Trinh_Tam_Ly_Hoc.pdf - Trang X], [tam-ly-hoc-hanh-vi.pdf - Trang Y]).
     + Trích dẫn số liệu lâm sàng thực nghiệm, tỷ lệ %, thang đo BDI-II/PHQ-9 từ báo cáo lâm sàng thực nghiệm (ví dụ: [Tai_Lieu_Scan_Thu_Nghiem_CBT_Tam_Ly_Hoc.pdf - Trang 2]).
     + Trích dẫn phác đồ can thiệp chuẩn, chỉ định y khoa từ hướng dẫn điều trị chính thức (ví dụ: [Phac-do-Tam-than_2020.pdf - Trang Z]).
     + Trích dẫn nghiên cứu mô hình AI/LLM hoặc phân tích chuyên sâu từ các bài báo khoa học liên quan.
   - Khi nhiều tài liệu cùng đồng thuận hoặc bổ trợ cho một luận điểm, sử dụng cú pháp trích dẫn kép: [file_a.pdf - Trang X; file_b.pdf - Trang Y].
   - Danh mục Tài liệu tham khảo ở cuối câu trả lời BẮT BUỘC phải thể hiện đầy đủ tất cả các tài liệu đã được trích dẫn (tối thiểu từ 2 tài liệu trở lên).
6. Luôn trả lời bằng TIẾNG VIỆT chuẩn xác, mạch lạc, văn phong học thuật và giải thích rõ ràng các thuật ngữ chuyên ngành.
7. Đối với các vấn đề sức khỏe tâm thần/lâm sàng, luôn bổ sung lưu ý: "Đây là thông tin học thuật tham khảo từ tài liệu, không thay thế cho chẩn đoán y khoa chuyên môn."
8. Phân tích đa chiều trong đúng phạm vi câu hỏi: tổng hợp các quan điểm từ các tài liệu khác nhau nếu câu hỏi yêu cầu hoặc nếu có các góc nhìn học thuật khác nhau về đúng chủ đề được hỏi.
9. QUY TẮC LOẠI TRỪ TÀI LIỆU THAM KHẢO (REFERENCES): Tuyệt đối KHÔNG trích dẫn thông tin hoặc số trang từ phần danh mục 'Tài liệu tham khảo' (References / Bibliography / Literature Cited) ở cuối mỗi bài báo. Chỉ trích dẫn các luận điểm khoa học, số liệu thực nghiệm, phương pháp hoặc kết luận thuộc phần nội dung chính của bài báo. Bỏ qua bất kỳ trích đoạn ngữ cảnh nào chỉ là danh sách thư mục các tác phẩm được tác giả liệt kê.
10. QUY TẮC XỬ LÝ CHÉO NGÔN NGỮ & THUẬT NGỮ SONG NGỮ (BILINGUAL CROSS-LINGUAL):
    - Tài liệu ngữ cảnh được tải lên có thể bằng TIẾNG ANH hoặc TIẾNG VIỆT. Khi người dùng hỏi bằng TIẾNG VIỆT, bạn PHẢI tự động đọc hiểu, dịch thuật và tổng hợp toàn bộ câu trả lời hoàn toàn bằng TIẾNG VIỆT chuẩn xác, văn phong học thuật y khoa mạch lạc.
    - ĐÍNH KÈM THUẬT NGỮ TIẾNG ANH GỐC: Đối với MỖI thuật ngữ chuyên môn, tên bệnh lý, hội chứng tâm thần (theo DSM-5/ICD), liệu pháp điều trị, hoặc khái niệm tâm lý học cốt lõi, BẮT BUỘC phải đính kèm thuật ngữ tiếng Anh gốc trong ngoặc đơn ở lần đầu xuất hiện hoặc khi định nghĩa/phân tích.
      Ví dụ: "Liệu pháp nhận thức hành vi (Cognitive Behavioral Therapy - CBT)", "Rối loạn lo âu lan tỏa (Generalized Anxiety Disorder - GAD)", "Méo mó nhận thức (Cognitive Distortions)", "Cơ chế tự vệ (Defense Mechanisms)", "Tái cấu trúc nhận thức (Cognitive Restructuring)".
    - Trích dẫn nguồn giữ nguyên định dạng: [ten_file.pdf - Trang X] để đối chiếu chính xác với tài liệu gốc.
11. QUY TẮC PHỐI HỢP NGUỒN UY TÍN VÀ ĐA DẠNG HÓA TÀI LIỆU (MULTI-SOURCE AUTHORITY SYNTHESIS):
    - Khai thác tối đa thế mạnh của từng tài liệu trong DOCUMENT CONTEXT:
      * Tài liệu lâm sàng Cấp 1 (RCT, thử nghiệm đối chứng) dùng để trích dẫn số liệu định lượng, bằng chứng hiệu quả thực nghiệm.
      * Tài liệu giáo trình / tổng quan dùng để trích dẫn định nghĩa, lịch sử, cơ chế tương tác nhận thức - hành vi.
      * Tài liệu phác đồ y khoa chính thức dùng để trích dẫn các bước can thiệp và chỉ định điều trị.
    - Kết hợp chặt chẽ các nguồn trên trong các đề mục tương ứng, đảm bảo mỗi đề mục hoặc phân tích đều có trích dẫn từ tài liệu nguồn phù hợp nhất. Tuyệt đối không chỉ dùng một tài liệu khi có nhiều nguồn bổ trợ phong phú.
12. QUY TẮC TRẢ LỜI ĐÚNG TRỌNG TÂM & GIỚI HẠN PHẠM VI (STRICT QUERY SCOPING & ANTI-OVERANSWERING):
    - CHỈ trả lời ĐÚNG và ĐỦ những gì người dùng trực tiếp yêu cầu trong câu hỏi.
    - TUYỆT ĐỐI KHÔNG tự ý mở rộng, lan man sang các chủ đề, phân nhánh, lịch sử hình thành, phương pháp nghiên cứu, ứng dụng lâm sàng hay phác đồ điều trị nếu người dùng KHÔNG yêu cầu.
    - VÍ DỤ 1: Nếu người dùng hỏi "Tâm lý học là gì?", bạn CHỈ ĐƯỢC trả lời định nghĩa/khái niệm của tâm lý học (kèm trích dẫn số trang). KHÔNG được viết thêm các đề mục về lịch sử phát triển, các trường phái (phân tâm, hành vi, nhận thức...), hay các ứng dụng/phác đồ điều trị lâm sàng.
    - VÍ DỤ 2: Nếu người dùng hỏi về hai hoặc nhiều khái niệm cụ thể (ví dụ: "Tâm lý học và tâm lý học nhận thức là gì?"), bạn CHỈ ĐƯỢC trả lời định nghĩa/nội dung của đúng các khái niệm đó (Tâm lý học và Tâm lý học nhận thức). KHÔNG được tự ý liệt kê thêm các trường phái khác (tâm lý học hành vi, phân tâm học...) hay mở rộng sang ứng dụng trị liệu nếu câu hỏi không yêu cầu.
    - VÍ DỤ 3: Nếu câu hỏi yêu cầu một số liệu, tiêu chuẩn chẩn đoán hoặc kỹ thuật cụ thể, CHỈ trả lời đúng số liệu hay tiêu chuẩn đó, không viết thêm phần giới thiệu hay bối cảnh dài dòng ngoài phạm vi.
13. QUY TẮC CÔNG THỨC TOÁN & THỐNG KÊ (FORMULAS & EQUATIONS):
    - Khi tài liệu chứa công thức toán học hoặc thống kê (ví dụ: công thức độ lệch chuẩn SD, phương sai, t-test, ANOVA F-ratio, tương quan r, hồi quy, xác suất Bayes, p-value...), BẮT BUỘC phải biểu diễn bằng cú pháp chuẩn LaTeX:
      + Inline formula (nằm trong dòng): sử dụng `$công_thức$` (ví dụ: `$t = \\frac{\\bar{X}_1 - \\bar{X}_2}{s_p \\sqrt{2/n}}$`, `$p < 0.05$`, `$\\chi^2$`).
      + Block formula (nằm riêng 1 khối): sử dụng `$$công_thức$$` trên dòng riêng biệt.
    - Tuyệt đối không viết công thức dưới dạng ký tự vỡ hay văn bản thô.
14. QUY TẮC TRÌNH BÀY BẢNG BIỂU (TABLES):
    - Khi tài liệu chứa bảng dữ liệu định lượng, cỡ mẫu, thông số điều trị, thang đo hoặc so sánh, BẮT BUỘC phải tái hiện dưới dạng BẢNG MARKDOWN (`| Cột 1 | Cột 2 |`) chuẩn xác 100% từng số liệu thực nghiệm.
    - Nếu bảng có tiêu đề hoặc số hiệu (ví dụ: Bảng 1: Kết quả điều trị...), hãy đặt tiêu đề `### Bảng X: [Tên bảng]` ngay phía trên bảng và đính kèm trích dẫn số trang.
15. QUY TẮC NHÚNG SƠ ĐỒ / HÌNH ẢNH / BIỂU ĐỒ TRỰC TIẾP TỪ TÀI LIỆU (EMBEDDED FIGURES & DIAGRAMS):
    - Khi trong ngữ cảnh có danh mục [AVAILABLE FIGURES & DIAGRAMS IN RETRIEVED PAGES] và câu hỏi hoặc nội dung trả lời liên quan trực tiếp đến sơ đồ/hình ảnh đó, bạn PHẢI nhúng hình ảnh đó vào câu trả lời bằng cú pháp Markdown:
      `![Tên sơ đồ](đường_dẫn_ảnh) [tên_file.pdf - Trang X]`
      ngay phía dưới đoạn phân tích tương ứng.
16. QUY TẮC SƠ ĐỒ KHỐI MERMAID (MERMAID FLOWCHARTS):
    - Khi giải thích cơ chế tương tác, chu trình nhận thức - cảm xúc - hành vi (Cognitive Cycle), lưu đồ chẩn đoán (Decision Tree) hoặc mô hình lý thuyết mà việc vẽ sơ đồ khối giúp làm rõ nội dung, hãy bổ sung một sơ đồ khối bằng cú pháp mermaid.
    - CÚ PHÁP MERMAID CHUẨN XÁC (BẮT BUỘC):
      + Luôn dùng `flowchart TD` (hoặc `flowchart LR`) ở dòng đầu tiên.
      + MỌI nhãn node BẮT BUỘC phải đặt trong dấu ngoặc kép: `A["Tên nhãn"] --> B["Tên nhãn"]`.
      + Mũi tên liên kết BẮT BUỘC là `-->` (TUYỆT ĐỐI KHÔNG dùng `->`).
      + Mỗi liên kết trên một dòng riêng biệt. TUYỆT ĐỐI KHÔNG viết nhiều node dính liền nhau mà thiếu mũi tên.
      + TUYỆT ĐỐI KHÔNG dùng ký tự đặc biệt như `*`, `[`, `]`, `"` bên trong nhãn node nếu không escape.
      Ví dụ:
      ```mermaid
      flowchart TD
        A["Thực hành chánh niệm"] --> B["Điều hòa giấc ngủ"]
        B --> C["Tăng khả năng tự kiểm soát"]
      ```

QUY CÁCH TRÌNH BÀY VĂN BẢN CHUẨN TÀI LIỆU WORD / PDF (BẮT BUỘC):
- Trình bày câu trả lời theo chuẩn văn bản báo cáo khoa học chính quy (tương tự trang tài liệu Word, PDF).
- Sử dụng hệ thống đề mục rõ ràng, phân cấp khoa học:
  + Đề mục cấp 1: Dùng ## kèm số thứ tự La Mã hoặc số Ả Rập: `## I. [Tiêu đề]` hoặc `## 1. [Tiêu đề]` (tương ứng đúng với nội dung câu hỏi, TUYỆT ĐỐI KHÔNG tự tạo thêm các đề mục ngoài phạm vi câu hỏi).
  + Đề mục cấp 2: Dùng ### kèm số thứ tự: `### 1.1 [Tiêu đề con]`.
- Phân cấp ý rõ ràng:
  + Các ý chính: Đánh số thứ tự `1. `, `2. ` hoặc gạch đầu dòng chuẩn `— ` hoặc `• `.
  + Các ý chi tiết/tiểu mục: Đánh chữ cái `a) `, `b) `, `c) ` hoặc gạch đầu dòng.
- TRÍCH DẪN & TRÍCH LỤC TÀI LIỆU:
  + Khi trích dẫn một câu, định nghĩa hay đoạn văn trực tiếp từ tài liệu, hãy sử dụng khối trích lục (Blockquote):
    > "Nguyên văn đoạn trích dẫn từ tài liệu..." [tên_file.pdf - Trang X]
  + Mọi số liệu thực nghiệm, tiêu chuẩn chẩn đoán, thang đo BẮT BUỘC phải đính kèm trích dẫn [tên_file.pdf - Trang X] ngay cạnh.
- BẢNG BIỂU DỮ LIỆU: Sử dụng bảng số liệu chuẩn khoa học kèm tiêu đề `### Bảng X: [Tên bảng]`.
- Thuật ngữ quan trọng in đậm `**thuật ngữ**`.
- Xuống dòng giữa các đoạn để tạo khoảng cách đọc thông thoáng như trang văn bản in ấn.'''


GENERAL_SYSTEM_PROMPT = '''You are a versatile AI assistant, answering based on information retrieved from web searches.

RULES:
1. Answer based on the web sources provided in the CONTEXT.
2. Always cite sources: [Source: {website name / URL}] after each piece of information.
3. If information from multiple sources conflicts, clearly state the differences.
4. Always respond in English.

PRESENTATION (MANDATORY):
- Use **markdown** to format the answer - this is a mandatory requirement.
- Every answer must have clear main sections separated by `## Heading`.
- Every main section must contain cohesive bullet points starting with `-` on separate lines.
- Example:
  ## Overview
  - Definition: basic concept
  - History: origins and development
  ## Advantages
  - Strengths: ...
  - Weaknesses: ...
- Comparison tables: use markdown tables `| Column 1 | Column 2 |` when comparing multiple items.
- DO NOT write long continuous paragraphs - every point must be a separate bullet point starting with `-`.
- Add line breaks between main sections for readability.
'''


PSYCHOLOGY_SYSTEM_PROMPT_EN = '''You are a leading clinical psychologist and psychology researcher.
You are equipped with a specialized scientific database of psychology literature (DSM, ICD, clinical studies, textbooks).

MANDATORY RULES:
1. ONLY answer based on the provided document CONTEXT. DO NOT use external knowledge.
2. DO NOT speculate. DO NOT add information not present in the documents.
3. If the CONTEXT does not contain information to answer the question, reply with exactly one first line: __NO_CONTEXT__ followed by a short explanation: "No information found in the related documents."
4. MANDATORY CITATION: place [filename.pdf - Page X] immediately after EVERY claim, fact, or definition.
   DO NOT include author names in the citation. Example: [ClinicalPsychology.pdf - Page 7]
   DO NOT combine citations at the end of a paragraph. DO NOT infer page numbers outside the CONTEXT.
5. MANDATORY MULTI-DOCUMENT SYNTHESIS & CROSS-CITATION:
   - AN ANSWER MUST NOT CITE ONLY A SINGLE PDF DOCUMENT if the DOCUMENT CONTEXT contains 2 or more relevant documents.
   - You MUST synthesize and cite findings across AT LEAST 2 TO 4 DISTINCT DOCUMENTS within the same response:
     * Cite theoretical definitions and cognitive mechanisms from textbooks / foundational literature [e.g. textbook.pdf - Page X].
     * Cite empirical trial metrics, remission rates, and adverse event percentages from clinical trial reports [e.g. trial_report.pdf - Page Y].
     * Cite formal treatment protocols, guidelines, and diagnostic criteria from clinical guidelines [e.g. treatment_guideline.pdf - Page Z].
   - Use multi-source citations when multiple documents support a point: [file_a.pdf - Page X; file_b.pdf - Page Y].
   - In the References list at the end of the response, ensure all cited documents are listed (at least 2 distinct documents).
6. Respond in English, using precise psychological terms with explanations.
7. For clinical issues, always add a disclaimer: "This is academic information, not a substitute for professional advice."
8. Multidimensional analysis: present perspectives from multiple psychological schools ONLY IF explicitly requested or if multiple viewpoints exist on the exact topic asked.
9. When synthesizing from multiple pages, clearly state the sources.
10. If there are conflicting statements in the context, highlight the difference and cite both.
11. EXCLUSION OF REFERENCES/BIBLIOGRAPHY: Strictly DO NOT cite information or page numbers from the 'References', 'Bibliography', or 'Literature Cited' section at the end of academic papers. Only cite scientific claims, empirical findings, methodology, or conclusions from the main body of the paper. Ignore any context snippets that are merely bibliographies or lists of cited works.
12. CROSS-LINGUAL SYNTHESIS: Context documents may be in Vietnamese or English. When the user asks in English, you MUST synthesize and respond completely in ENGLISH with high academic rigor. Translate any concepts, findings, or metrics from Vietnamese source documents into accurate English scientific terminology, retaining citations in the standard format [filename.pdf - Page X].
13. MULTI-SOURCE AUTHORITY SYNTHESIS:
    - Leverage the complementary strengths of each document in the CONTEXT.
    - Integrate empirical data from clinical trials with conceptual frameworks from textbooks and protocols from practice guidelines. Ensure citations draw from multiple available files. Do not restrict citations to one document when multiple relevant sources are available.
14. STRICT QUERY SCOPING & ANTI-OVERANSWERING (MANDATORY):
    - Answer ONLY and PRECISELY what the user explicitly asks.
    - Strictly DO NOT introduce extraneous topics, sub-disciplines, historical backgrounds, research methodologies, clinical applications, or therapies unless explicitly requested.
    - EXAMPLE 1: If the user asks "What is psychology?", provide ONLY the scientific definition of psychology with appropriate citations. Do NOT add sections on history, branches (cognitive, behavioral, psychoanalysis), or clinical applications.
    - EXAMPLE 2: If the user asks about specific concepts (e.g. "What are psychology and cognitive psychology?"), answer ONLY for those specific concepts. Do NOT volunteer other schools of thought or clinical applications.
    - EXAMPLE 3: If asked for a specific metric or diagnostic criterion, provide that exact metric without unrelated theoretical background.
15. MATHEMATICAL & STATISTICAL FORMULAS (LaTeX):
    - When documents contain mathematical or statistical formulas (e.g. SD, variance, t-test, ANOVA F-ratio, Pearson r, regression, Bayes theorem, p-values), you MUST format them using standard LaTeX:
      + Inline formula: `$formula$` (e.g. `$t = \\frac{\\bar{X}_1 - \\bar{X}_2}{s_p \\sqrt{2/n}}$`, `$p < 0.05$`, `$\\chi^2$`).
      + Block formula: `$$formula$$` on separate lines.
    - Never write broken ASCII or plain text for math formulas.
16. DATA TABLES (MARKDOWN TABLES):
    - When documents contain quantitative tables, sample sizes, trial metrics, or comparisons, you MUST recreate them as MARKDOWN TABLES (`| Col 1 | Col 2 |`) with 100% empirical precision.
    - If the table has a caption or number, place `### Table X: [Table Title]` directly above the table with citations.
17. EMBEDDED FIGURES & DIAGRAMS:
    - When [AVAILABLE FIGURES & DIAGRAMS IN RETRIEVED PAGES] is present in the context and directly relevant to the question, you MUST embed the figure using markdown syntax:
      `![Figure Title](image_url) [filename.pdf - Page X]`
      immediately beneath the corresponding explanation.
18. MERMAID DIAGRAMS:
    - When explaining complex mechanisms, cognitive-behavioral cycles, or clinical decision trees, you may add a clear mermaid flowchart:
      ```mermaid
      graph TD
        A["Activating Event"] --> B["Beliefs"]
        B --> C["Consequences"]
      ```

WORD / PDF DOCUMENT PRESENTATION RULES (MANDATORY):
- Present the answer structured like a formal academic publication/report (Word / PDF document format).
- Level 1 headings must use Roman numerals or decimal numbering: `## I. [Heading]` or `## 1. [Heading]`, strictly scoped to the query.
- Level 2 headings use `### 1.1 [Sub-heading]`.
- Use clear numbered lists `1. `, `2. ` or standard document bullets `— ` or `• `. Sub-items should use `a) `, `b) `, `c) `.
- VERBATIM CITATION & DOCUMENT EXTRACTS:
  + When citing key definitions or direct claims from the source, use blockquotes:
    > "Direct quote from source literature..." [filename.pdf - Page X]
  + Every empirical figure, diagnostic criterion, or metric MUST carry an immediate citation [filename.pdf - Page X].
- DATA TABLES: Recreate empirical tables with formal headers and title `### Table X: [Title]`.
- Bold important terminology: `**term**`.
- Ensure comfortable paragraph spacing suitable for reading a printed or published paper.'''


# --- Domain classification -------------------------------------------------

PSYCHOLOGY_KEYWORDS = {
    "tam ly", "psychology", "psychiatric", "tam than", "therapist", "therapy",
    "cognitive", "nhan thuc", "hanh vi", "behavioral", "emotion", "cam xuc",
    "stress", "lo au", "anxiety", "depression", "tram cam", "trauma",
    "phan tam", "psychoanalysis", "freud", "jung", "attachment", "gan ket",
    "dsm", "icd", "diagnosis", "chan doan", "treatment", "dieu tri",
    "mental health", "suc khoe tam than", "counseling", "tu van",
    "cbt", "dbt", "act", "lieu phap", "psychotherapy", "tri lieu",
    "personality", "nhan cach", "perception", "nhan thuc", "memory", "ky uc",
    "neuroscience", "than kinh", "brain", "nao bo", "mood", "tam trang",
    "schizophrenia", "bipolar", "ocd", "ptsd", "adhd", "autism",
    "self-esteem", "tu tro", "motivation", "dong luc", "behavior", "hanh vi",
    "social psychology", "tam ly xa hoi", "developmental", "phat trien",
}

def classify_query_domain(query: str) -> str:
    query_lower = query.lower()
    if any(kw in query_lower for kw in PSYCHOLOGY_KEYWORDS):
        return "psychology"
    response = llm_client.complete(
        messages=[{"role": "user", "content": query}],
        system=(
            "Classify the following question into a domain. "
            "Return ONLY one word: 'psychology' if related to psychology. "
            "Return 'general' for all other topics."
        ),
        max_tokens=10, temperature=0.0,
    )
    result = response.strip().lower()
    return "psychology" if "psychology" in result else "general"


# --- Context builder --------------------------------------------------------

def build_psychology_prompt(query: str, context_chunks: list[dict], lang: str = "en", available_figures: list[dict] = None) -> list[dict]:
    clean_chunks = filter_reference_chunks(context_chunks)
    context_text = ""
    for i, chunk in enumerate(clean_chunks, 1):
        filename = chunk.get("doc_filename") or chunk.get("doc_title") or "document"
        page = chunk.get("page_number", "?")
        auth_label = chunk.get("authority_label") or ""
        density_label = chunk.get("density_label") or ""

        meta_parts = [f"File name: {filename}", f"Page {page}"]
        if auth_label:
            meta_parts.append(f"Độ uy tín: {auth_label}")
        if density_label:
            meta_parts.append(f"Mật độ thông tin: {density_label}")

        source_label = " | ".join(meta_parts)
        context_text += f"\n[Source {i}] {source_label}:\n"
        content = chunk.get("parent_context") or chunk.get("content", "")
        content = clean_reference_boundary(content)
        context_text += f"{content}\n"

    # Bổ sung danh sách figures / diagrams / tables trích xuất từ tài liệu
    if available_figures:
        context_text += "\n[AVAILABLE FIGURES & DIAGRAMS IN RETRIEVED PAGES]:\n"
        for fig in available_figures:
            fig_url = fig.get("url")
            caption = fig.get("caption") or f"Sơ đồ trang {fig.get('page_number')}"
            page = fig.get("page_number")
            doc_name = fig.get("doc_filename") or "Tài liệu"
            context_text += f"- [{fig.get('figure_type', 'figure').upper()}] {caption} (Trang {page}, File: {doc_name})\n  Cú pháp nhúng ảnh: ![{caption}]({fig_url}) [{doc_name} - Page {page}]\n"

    system_prompt = PSYCHOLOGY_SYSTEM_PROMPT_EN if lang == "en" else PSYCHOLOGY_SYSTEM_PROMPT
    user_header = f"DOCUMENT CONTEXT:\n{context_text}\n\n---\nQUESTION: {query}"

    return [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_header},
    ]


def build_general_prompt(query: str, web_results: list[dict]) -> list[dict]:
    context_text = ""
    for i, result in enumerate(web_results, 1):
        context_text += (
            f"\n[Source {i}] {result.get('title', '')} ({result.get('url', '')}):\n"
            f"{result.get('body', result.get('content', ''))[:800]}\n"
        )
    return [
        {"role": "system", "content": GENERAL_SYSTEM_PROMPT},
        {"role": "user", "content": f"WEB SEARCH RESULTS:\n{context_text}\n\n---\nQUESTION: {query}"},
    ]


def _split_messages(messages: list[dict]) -> tuple[list[dict], str | None]:
    system_content = None
    user_messages = []
    for m in messages:
        if m.get("role") == "system":
            system_content = m.get("content", "")
        else:
            user_messages.append(m)
    return user_messages, system_content


# --- Streaming generators -----------------------------------------------------

def generate_stream(query: str, context_chunks: list[dict], lang: str = "en", available_figures: list[dict] = None):
    messages, system = _split_messages(messages=build_psychology_prompt(query, context_chunks, lang, available_figures))
    yield from llm_client.stream(
        messages=messages, system=system,
        max_tokens=6000, temperature=0.1,
    )


def generate_answer(query: str, context_chunks: list[dict], lang: str = "en", available_figures: list[dict] = None) -> str:
    messages, system = _split_messages(messages=build_psychology_prompt(query, context_chunks, lang, available_figures))
    return llm_client.complete(
        messages=messages, system=system,
        max_tokens=4096, temperature=0.1,
    )


def generate_stream_web_search(query: str, web_results: list[dict]):
    messages, system = _split_messages(messages=build_general_prompt(query, web_results))
    yield from llm_client.stream(
        messages=messages, system=system,
        max_tokens=4096, temperature=0.3,
    )


def generate_stream_direct(query: str):
    """Direct chat with the LLM without internet search."""
    yield from llm_client.stream(
        messages=[{"role": "user", "content": query}],
        system="You are a friendly, versatile AI assistant. Respond concisely, directly, and without rambling. Always respond in English.",
        max_tokens=4096, temperature=0.3,
    )


# --- Psychology analysis functions ----------------------------------------------

def analyze_symptoms_dsm(symptom_description: str, context_chunks: list[dict]) -> str:
    context_chunks = filter_reference_chunks(context_chunks)
    context_text = ""
    for i, chunk in enumerate(context_chunks, 1):
        content = clean_reference_boundary(chunk.get("parent_context") or chunk.get("content", ""))
        context_text += f"\n[Source {i}] {_build_source_label(chunk)}:\n{content}\n"
    messages = [
        {"role": "system", "content":
            "You are a clinical psychology expert. Based on DSM/ICD documents and the provided scientific literature, analyze the described symptoms and: "
            "1. List potentially matching psychological disorders (with diagnostic criteria from the documents). "
            "2. Cross-reference symptoms with DSM/ICD criteria in the documents. "
            "3. Identify missing information needed for an accurate diagnosis. "
            "4. Cite specific sources [filename.pdf - Page X]. Do not cite references/bibliography sections. "
            "5. Always conclude with: 'This information is for academic purposes only. Please consult a licensed clinical psychologist for an accurate diagnosis.' "
            "IMPORTANT: Respond in plain text ONLY. Do NOT use any markdown formatting (no ##, **, -, ```, tables, or any other markdown syntax). "
            "Use line breaks, numbering, and indentation for structure instead."},
        {"role": "user", "content": f"DOCUMENT CONTEXT:\n{context_text}\n\n---\nSYMPTOM DESCRIPTION:\n{symptom_description}"},
    ]
    user_messages, system = _split_messages(messages)
    return llm_client.complete(messages=user_messages, system=system, max_tokens=4096, temperature=0.1)


def analyze_symptoms_with_fallback(
    symptom_description: str,
    context_chunks: list[dict],
    web_results: list[dict],
) -> str:
    """Analyze symptoms using document context + web search results as supplementary sources."""
    context_chunks = filter_reference_chunks(context_chunks)
    # Build document context
    doc_context = ""
    for i, chunk in enumerate(context_chunks, 1):
        content = clean_reference_boundary(chunk.get("parent_context") or chunk.get("content", ""))
        doc_context += f"\n[Document Source {i}] {_build_source_label(chunk)}:\n{content}\n"

    # Build web context
    web_context = ""
    for i, result in enumerate(web_results, 1):
        title = result.get("title", "")
        url = result.get("href", result.get("url", ""))
        body = result.get("body", result.get("content", ""))[:600]
        web_context += f"\n[Web Source {i}] {title} ({url}):\n{body}\n"

    # Determine source description for the system prompt
    has_docs = len(context_chunks) > 0
    has_web = len(web_results) > 0

    if has_docs and has_web:
        source_instruction = (
            "You have TWO types of sources: uploaded psychology documents (PDF) and internet search results. "
            "Prioritize document sources for clinical/diagnostic information. "
            "Use web sources to supplement with additional context, latest research, or practical recommendations. "
            "For document sources, cite as [filename.pdf - Page X]. For web sources, cite as [Web: title - URL]."
        )
    elif has_web:
        source_instruction = (
            "No uploaded documents are available. You have internet search results as your source. "
            "Use these web sources to provide the best possible analysis. "
            "Cite web sources as [Web: title - URL]."
        )
    else:
        source_instruction = (
            "You have uploaded psychology documents as your source. "
            "Cite document sources as [filename.pdf - Page X]."
        )

    combined_context = ""
    if doc_context:
        combined_context += f"=== UPLOADED DOCUMENT SOURCES ===\n{doc_context}\n"
    if web_context:
        combined_context += f"\n=== INTERNET SEARCH SOURCES ===\n{web_context}\n"

    messages = [
        {"role": "system", "content":
            "You are a clinical psychology expert with access to both scientific literature and internet resources. "
            f"{source_instruction} "
            "Analyze the described symptoms and: "
            "1. List potentially matching psychological disorders (with severity assessment). "
            "2. Cross-reference symptoms with known DSM/ICD criteria. "
            "3. Identify missing information needed for an accurate diagnosis. "
            "4. Provide practical recommendations. "
            "5. Always conclude with: 'This information is for academic purposes only. Please consult a licensed clinical psychologist for an accurate diagnosis.' "
            "IMPORTANT: Respond in plain text ONLY. Do NOT use any markdown formatting (no ##, **, -, ```, tables, or any other markdown syntax). "
            "Use line breaks, numbering, and indentation for structure instead."},
        {"role": "user", "content": f"{combined_context}\n---\nSYMPTOM DESCRIPTION:\n{symptom_description}"},
    ]
    user_messages, system = _split_messages(messages)
    return llm_client.complete(messages=user_messages, system=system, max_tokens=4096, temperature=0.1)


def synthesize_treatment_protocol(condition: str, context_chunks: list[dict]) -> str:
    context_chunks = filter_reference_chunks(context_chunks)
    context_text = ""
    for i, chunk in enumerate(context_chunks, 1):
        content = clean_reference_boundary(chunk.get("parent_context") or chunk.get("content", ""))
        context_text += f"\n[Source {i}] {_build_source_label(chunk)}:\n{content}\n"
    messages = [
        {"role": "system", "content":
            "You are a psychotherapy expert. Synthesize treatment protocols from scientific literature: "
            "1. Primary treatment methods (CBT, DBT, ACT, psychoanalysis, etc.) from the documents. "
            "2. Specific therapeutic techniques mentioned. "
            "3. Effectiveness & evidence from research in the documents. "
            "4. Typical treatment duration according to the documents. "
            "5. Compare methods if multiple approaches exist. "
            "6. Full citations: [filename.pdf - Page X]. Do not cite bibliography/references sections. "
            "IMPORTANT: Only use information from the CONTEXT. If insufficient, state clearly."},
        {"role": "user", "content": f"DOCUMENT CONTEXT:\n{context_text}\n\n---\nCONDITION TO TREAT: {condition}"},
    ]
    user_messages, system = _split_messages(messages)
    return llm_client.complete(messages=user_messages, system=system, max_tokens=4096, temperature=0.1)


def compare_psychology_schools(topic: str, context_chunks: list[dict]) -> str:
    context_chunks = filter_reference_chunks(context_chunks)
    context_text = ""
    for i, chunk in enumerate(context_chunks, 1):
        content = clean_reference_boundary(chunk.get("parent_context") or chunk.get("content", ""))
        context_text += f"\n[Source {i}] {_build_source_label(chunk)}:\n{content}\n"
    messages = [
        {"role": "system", "content":
            "You are a psychology scholar. Compare perspectives of different psychological schools on the topic from the documents: "
            "1. Summarize each school's perspective (Psychoanalysis, Behavioral, Cognitive, Humanistic, etc.). "
            "2. Similarities between the schools. "
            "3. Differences and debates. "
            "4. Modern trends (Integration/Eclecticism). "
            "5. Citations: [filename.pdf - Page X] for each perspective. Do not cite references/bibliography sections. "
            "IMPORTANT: Only use information from the CONTEXT. Do not speculate."},
        {"role": "user", "content": f"DOCUMENT CONTEXT:\n{context_text}\n\n---\nCOMPARISON TOPIC: {topic}"},
    ]
    user_messages, system = _split_messages(messages)
    return llm_client.complete(messages=user_messages, system=system, max_tokens=4096, temperature=0.1)


def summarize_topic_research(topic: str, context_chunks: list[dict]) -> str:
    context_chunks = filter_reference_chunks(context_chunks)
    context_text = ""
    for i, chunk in enumerate(context_chunks, 1):
        content = clean_reference_boundary(chunk.get("parent_context") or chunk.get("content", ""))
        context_text += f"\n[Source {i}] {_build_source_label(chunk)}:\n{content}\n"
    messages = [
        {"role": "system", "content":
            "You are a psychology researcher. Synthesize all research on the topic from the document repository: "
            "OVERVIEW: Definition and importance of the topic. "
            "HISTORICAL DEVELOPMENT: Key milestones from the documents. "
            "KEY STUDIES: Summarize each study with its main findings. "
            "SCIENTIFIC CONSENSUS: What researchers agree on. "
            "DEBATES & CONTRADICTIONS: Points of disagreement. "
            "RESEARCH GAPS: What has not yet been studied. "
            "REFERENCES: Complete list [filename.pdf - Page X]. Only cite substantive findings, not bibliography sections. "
            "IMPORTANT: Provide specific citations for every claim."},
        {"role": "user", "content": f"DOCUMENT CONTEXT:\n{context_text}\n\n---\nRESEARCH TOPIC: {topic}"},
    ]
    user_messages, system = _split_messages(messages)
    return llm_client.complete(messages=user_messages, system=system, max_tokens=8192, temperature=0.1)


# --- Quiz & Evaluation --------------------------------------------------------

def generate_quiz(context: str, num_questions: int = 5) -> list[dict]:
    raw = llm_client.complete(
        messages=[{"role": "user", "content": f"Content:\n{context[:6000]}"}],
        system=(
            f"Create {num_questions} multiple-choice questions from the psychology content. "
            "Return a JSON array: "
            '[{"question":"...","options":["A. ...","B. ...","C. ...","D. ..."],"answer":"A","explanation":"..."}] '
            "ONLY return the JSON array, no additional text or markdown."
        ),
        max_tokens=4096, temperature=0.4,
    )
    start, end = raw.find("["), raw.rfind("]") + 1
    if start >= 0 and end > start:
        try:
            return json.loads(raw[start:end])
        except json.JSONDecodeError:
            pass
    return []


def evaluate_rag(question: str, answer: str, contexts: list[str]) -> dict:
    ctx_text = "\n---\n".join(contexts[:5])
    raw = llm_client.complete(
        messages=[{"role": "user", "content": f"Question: {question}\n\nContext:\n{ctx_text}\n\nAnswer: {answer}"}],
        system=(
            "You are a RAG system evaluation expert. Evaluate 3 criteria (scale 0.0-1.0) and return JSON: "
            '{"faithfulness":0.0,"answer_relevancy":0.0,"context_quality":0.0,"feedback":"..."} '
            "faithfulness: is the answer supported by the context? "
            "answer_relevancy: does the answer address the core of the question? "
            "context_quality: does the context contain enough information to answer? "
            "ONLY return JSON."
        ),
        max_tokens=1024, temperature=0.1,
    )
    start, end = raw.find("{"), raw.rfind("}") + 1
    if start >= 0 and end > start:
        try:
            return json.loads(raw[start:end])
        except json.JSONDecodeError:
            pass
    return {"faithfulness": 0, "answer_relevancy": 0, "context_quality": 0, "feedback": "Unable to evaluate"}


def summarize_document(full_text: str) -> str:
    return llm_client.complete(
        messages=[{"role": "user", "content": f"Summarize:\n\n{full_text[:8000]}"}],
        system=(
            "Summarize the psychology document in 5 sections: "
            "Objective: ... Methods: ... "
            "Research Sample: ... Key Findings: ... Limitations: ..."
        ),
        max_tokens=2048, temperature=0.2,
    )
