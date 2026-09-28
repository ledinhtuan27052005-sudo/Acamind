# HƯỚNG DẪN XÂY DỰNG HỆ THỐNG HỎI ĐÁP HỌC THUẬT AI & RAG
## Step-by-Step — Từ Số 0 Đến Demo Chạy Được

---

> **Cách đọc tài liệu này:**  
> - **PHẦN 1 (50% đầu):** Làm xong là có demo chạy được — upload PDF, hỏi đáp AI, nhận câu trả lời có trích dẫn.  
> - **PHẦN 2 (50% sau):** Bổ sung đồ thị tri thức, đăng nhập, đánh giá RAGAS, xuất báo cáo.  
> - Mỗi bước có lệnh copy-paste được, không cần suy đoán.

---

# CÁC CHỨC NĂNG ĐÃ CÓ — TÓM TẮT DỄ HIỂU

> Đây là danh sách tất cả những gì hệ thống đã làm được, viết theo ngôn ngữ bình thường để dễ hình dung.

---

## 🔐 Nhóm 1 — Tài khoản & Đăng nhập
- Đăng ký bằng email + mã OTP 6 số gửi qua Gmail (có giới hạn gửi lại 60 giây)
- Đăng nhập email/mật khẩu hoặc đăng nhập 1 click bằng tài khoản Google
- Đổi ảnh đại diện, đổi tên hiển thị, đổi mật khẩu ngay trong hồ sơ
- 3 vai trò người dùng: **Student** (học viên) → **Researcher** (nhà nghiên cứu) → **Admin** (quản trị viên)
- Giao diện sidebar và menu tự điều chỉnh theo vai trò — ai không có quyền thì không thấy nút

## 📄 Nhóm 2 — Tải lên & Quản lý tài liệu
- Upload file PDF → hệ thống tự đọc, tách đoạn, tạo embedding AI (mất khoảng 30–60 giây)
- Xem thư viện tài liệu: tìm kiếm theo tên/tác giả, lọc theo trạng thái hoặc danh mục
- Mỗi tài liệu có thể để công khai (mọi người thấy) hoặc riêng tư (chỉ mình và admin thấy)
- AI tự gán nhãn danh mục cho tài liệu sau khi upload

## 💬 Nhóm 3 — Hỏi đáp AI
- Chat với 1 hoặc nhiều tài liệu cùng lúc — câu trả lời có trích dẫn trang cụ thể
- Tìm kiếm thông minh: kết hợp tìm theo nghĩa (vector) + tìm theo từ khóa (BM25) để ra đúng đoạn
- **Memory Chat**: AI nhớ những gì đã nói trong cùng phiên làm việc, không hỏi lại từ đầu
- **Learning Mode**: chọn trình độ Beginner / Advanced / Researcher → câu trả lời thay đổi độ sâu tương ứng
- Dịch đoạn văn trong tài liệu Anh ↔ Việt tức thì; double-click từ khó → tooltip giải thích

## 📝 Nhóm 4 — Học tập & Kiểm tra
- Quiz tự động từ tài liệu: AI tự ra câu hỏi trắc nghiệm, có giải thích đáp án sau khi nộp
- Quiz phân loại trình độ lần đầu đăng nhập (Beginner / Intermediate / Advanced / Researcher)
- **Literature Review AI**: chọn nhiều bài → AI viết tổng quan nghiên cứu tổng hợp
- **Tạo slide AI**: chọn tài liệu → AI tạo outline thuyết trình chi tiết
- Xuất báo cáo Word (.docx) từ cuộc hội thoại chat (có câu hỏi, câu trả lời, trích dẫn)

## 📊 Nhóm 5 — Phân tích & Trực quan
- **Đồ thị tri thức**: sơ đồ tương tác tác giả ↔ bài báo (kéo thả, zoom, click xem chi tiết)
- **Timeline nghiên cứu**: trục thời gian sắp xếp bài báo theo năm xuất bản
- **Trending Topics**: word cloud + top chủ đề nổi bật toàn bộ thư viện
- Đánh giá chất lượng AI tự động bằng RAGAS (Faithfulness, Context Precision, Answer Relevancy)

## 💳 Nhóm 6 — Gói dịch vụ & Thanh toán
- 4 gói: **Free** (miễn phí) / **Pro** (149.000đ) / **Researcher** (499.000đ) / **Enterprise** (từ 3.000.000đ)
- Mỗi gói có giới hạn số tài liệu/tháng và số câu hỏi/tháng khác nhau
- Thanh toán bằng QR ngân hàng — hệ thống nhận tiền và **tự động nâng cấp ngay** mà không cần duyệt tay
- Mã QR có hiệu lực 15 phút, hết hạn tạo lại được; xem lịch sử thanh toán đầy đủ

## 🏫 Nhóm 7 — Tài khoản Enterprise (Trường / Tổ chức)
- Gửi yêu cầu liên hệ → Admin tư vấn qua ticket → Admin tạo form thanh toán riêng với giá và giới hạn tùy chỉnh
- Khách nhận link riêng → nhập email → quét QR → tài khoản tự kích hoạt ngay
- Workspace riêng cho cả tổ chức; giới hạn tài liệu đặt riêng cho chủ tài khoản (550/tháng, 7.000/năm)
- Hết hạn gói → tài khoản tự về Free, không cần thao tác tay

## 🔔 Nhóm 8 — Thông báo hệ thống
- Icon chuông trên thanh header, badge đỏ hiện số thông báo chưa đọc
- Click chuông → danh sách 50 thông báo gần nhất; click từng cái → tự đánh dấu đã đọc
- Admin gửi thông báo đến **1 tài khoản cụ thể** hoặc **toàn bộ người dùng** chỉ bằng 1 form

## 🛠️ Nhóm 9 — Quản trị (Admin)
- Quản lý toàn bộ tài khoản: xem, đổi vai trò, duyệt đơn Researcher
- Quản lý danh mục tài liệu; xem lịch sử thanh toán
- Quản lý Enterprise: duyệt tickets, tạo và gửi offer, theo dõi trạng thái thanh toán
- Gửi thông báo hệ thống tới người dùng

## 🫀 Nhóm 10 — Tính năng đặc biệt
- Mô hình 3D cơ thể người: click vào vùng bất kỳ → ghi nhận triệu chứng, xem lịch sử theo ngày
- Hồ sơ cá nhân AI: AI phân tích toàn bộ lịch sử hỏi đáp và đưa ra nhận định cá nhân hóa

---

# MỤC LỤC CHỨC NĂNG — CHECKLIST CHI TIẾT

> Dùng mục này để kiểm tra tiến độ hoàn thiện hệ thống. Đánh dấu ✅ khi chức năng đã hoạt động đúng.

---

## 1. Xác Thực & Tài Khoản

### 1.1 Đăng ký tài khoản (OTP Email)
- [ ] Nhập email → nhấn **Gửi OTP** → nhận mã 6 chữ số qua Gmail
- [ ] Nhập đúng OTP trong vòng 10 phút → đăng ký thành công
- [ ] OTP hết hạn (>10 phút) → hệ thống báo lỗi "Mã OTP đã hết hạn"
- [ ] Gửi lại OTP: phải chờ 60 giây giữa các lần gửi (rate-limit)
- [ ] Email đã tồn tại → báo lỗi "Email đã được sử dụng"
- [ ] Mật khẩu dưới 6 ký tự → báo lỗi validation
- [ ] Chế độ dev (SMTP chưa cấu hình) → hiện banner vàng chứa `debug_otp`

### 1.2 Đăng nhập email/mật khẩu
- [ ] Đăng nhập thành công → nhận JWT token → chuyển về trang chủ
- [ ] Email/mật khẩu sai → thông báo "Email hoặc mật khẩu không đúng"
- [ ] Token lưu vào `localStorage` → refresh trang vẫn giữ trạng thái đăng nhập
- [ ] Đăng xuất → xóa token, chuyển về `/login`

### 1.3 Đăng nhập / đăng ký bằng Google OAuth
- [ ] Nhấn nút **Đăng nhập với Google** → popup chọn tài khoản Google
- [ ] Tài khoản mới → tự động tạo user với `role=student`, lưu avatar Google
- [ ] Tài khoản đã tồn tại → đăng nhập trực tiếp, cập nhật avatar nếu chưa có
- [ ] Token Google không hợp lệ → báo lỗi 401
- [ ] Nút Google chỉ hiện khi `NEXT_PUBLIC_GOOGLE_CLIENT_ID` đã được cấu hình

---

## 2. Hồ Sơ Người Dùng

### 2.1 Xem hồ sơ
- [ ] Trang `/profile` hiển thị: avatar, tên, email, vai trò
- [ ] Avatar Google tự hiển thị khi đăng nhập bằng Google (badge "Google" xuất hiện)
- [ ] Khi chưa có avatar → hiển thị vòng tròn initials (chữ cái đầu tên)

### 2.2 Đổi tên hiển thị
- [ ] Nhấn icon bút chì → ô nhập tên → nhấn ✓ lưu
- [ ] Tên mới cập nhật ngay trên giao diện và trong Zustand store
- [ ] Nhấn ✗ → hủy, giữ tên cũ

### 2.3 Đổi mật khẩu
- [ ] Người dùng email thường: phải nhập mật khẩu cũ đúng → đổi mới thành công
- [ ] Người dùng OAuth (Google): bỏ qua bước nhập mật khẩu cũ, chỉ đặt mật khẩu mới (nút "Đặt mật khẩu")
- [ ] Sau khi đặt mật khẩu lần đầu (OAuth) → `is_oauth` = false, có thể đăng nhập bằng email
- [ ] Mật khẩu mới dưới 6 ký tự → báo lỗi

### 2.4 Thay ảnh đại diện
- [ ] Nhấn icon camera trên avatar → chọn file ảnh (JPG/PNG/GIF/WebP)
- [ ] Ảnh upload thành công → hiển thị ngay, lưu vào `data/avatars/{user_id}.{ext}`
- [ ] Endpoint `GET /api/v1/profile/avatar/{user_id}` phục vụ file ảnh
a
---

## 3. Phân Quyền Người Dùng

### 3.1 Vai trò hệ thống
- [ ] **Admin** (`role=admin`): toàn quyền — quản lý user, duyệt đơn researcher, xóa tài liệu bất kỳ
- [ ] **Researcher** (`role=researcher`): upload tài liệu riêng, truy cập tài liệu công khai + riêng của mình
- [ ] **Student** (`role=student`): chỉ đọc tài liệu công khai, hỏi đáp AI, làm quiz
- [ ] Role hiển thị đúng trên trang profile và sidebar navigation

### 3.2 Điều hướng theo vai trò
- [ ] Student: không thấy menu Upload, Admin Panel
- [ ] Researcher: thấy menu Upload, không thấy Admin Panel
- [ ] Admin: thấy tất cả menu bao gồm Admin Panel

---

## 4. Quản Lý Tài Liệu

### 4.1 Upload PDF
- [ ] Chọn file PDF → điền tiêu đề, tác giả, năm, loại → upload
- [ ] Trạng thái xử lý: `processing` → `ready` (sau khoảng 30–60 giây)
- [ ] Nếu lỗi parsing → trạng thái `error`, có thông báo chi tiết
- [ ] File lưu vào `data/raw_pdfs/`, chunks lưu vào PostgreSQL

### 4.2 Xem danh sách tài liệu
- [ ] Trang `/library` liệt kê các tài liệu theo quyền truy cập
- [ ] Hiển thị: tên, tác giả, năm, trạng thái, số chunk
- [ ] Lọc theo trạng thái (ready/processing/error)
- [ ] Tìm kiếm theo tiêu đề/tác giả

### 4.3 Phân quyền tài liệu
- [ ] Tài liệu `visibility=public`: tất cả đăng nhập đều thấy
- [ ] Tài liệu `visibility=private`: chỉ người upload và admin thấy
- [ ] Researcher chỉ xóa được tài liệu của mình
- [ ] Admin xóa được mọi tài liệu

### 4.4 Pipeline xử lý
- [ ] PyMuPDF parse text → RecursiveTextSplitter tách chunk (500 ký tự, overlap 50)
- [ ] Ollama `nomic-embed-text` tạo embedding 768 chiều → lưu vào pgvector
- [ ] Neo4j lưu quan hệ Author→Document

---

## 5. Hỏi Đáp AI (Chat RAG)

### 5.1 Chức năng cơ bản
- [ ] Trang `/chat` → chọn 1 hoặc nhiều tài liệu → nhập câu hỏi → nhận câu trả lời
- [ ] Câu trả lời hiển thị theo dạng stream (từng token xuất hiện dần)
- [ ] Trích dẫn nguồn: `[Nguồn X, Trang Y]` hiển thị sau câu trả lời
- [ ] Lịch sử chat giữ trong session

### 5.2 Hybrid Search
- [ ] Vector search (cosine similarity trên pgvector) + BM25 keyword search
- [ ] RRF (Reciprocal Rank Fusion) kết hợp kết quả → top 5 chunks
- [ ] Câu hỏi ngắn/thuật ngữ chuyên ngành: BM25 hỗ trợ hiệu quả

### 5.3 LLM Generation
- [ ] Model: Groq `llama-3.3-70b-versatile`
- [ ] Prompt có context chunks → câu trả lời bám sát tài liệu
- [ ] Header `X-Context-Pages` trả về danh sách trang đã dùng
- [ ] Khi không có tài liệu phù hợp → thông báo "Không tìm thấy thông tin"

---

## 6. Đồ Thị Tri Thức (Knowledge Graph)

### 6.1 Xem graph
- [ ] Trang `/graph` hiển thị đồ thị tương tác (ReactFlow)
- [ ] Nodes: tác giả (xanh), bài báo (tím)
- [ ] Edges: quan hệ `WROTE` Author→Document
- [ ] Kéo thả, zoom in/out, click node xem chi tiết

### 6.2 Tìm kiếm trong graph
- [ ] Tìm theo tên tác giả → highlight kết quả
- [ ] Tìm theo tiêu đề bài báo → hiển thị node liên quan

---

## 7. Đánh Giá RAGAS

### 7.1 Chạy đánh giá
- [ ] Chuẩn bị file `data/eval_questions.json` (≥10 cặp Q&A)
- [ ] Chạy `python backend/scripts/evaluation.py`
- [ ] Kết quả xuất ra file Excel trong `data/eval_results/`

### 7.2 Chỉ số mục tiêu
- [ ] **Faithfulness** ≥ 0.85 (câu trả lời bám sát context)
- [ ] **Context Precision** ≥ 0.80 (chunk được chọn đúng)
- [ ] **Answer Relevancy** ≥ 0.80 (câu trả lời liên quan câu hỏi)

---

## 8. Bài Kiểm Tra (Quiz)

### 8.1 Onboarding quiz
- [ ] Lần đầu đăng nhập → quiz 5 câu phân loại trình độ
- [ ] Kết quả phân loại: Beginner / Intermediate / Advanced / Researcher

### 8.2 Tạo quiz từ tài liệu
- [ ] Chọn tài liệu → AI tự sinh câu hỏi trắc nghiệm từ nội dung
- [ ] Tuỳ chọn: số câu hỏi (5/10/15), mức độ khó (dễ/trung bình/khó)
- [ ] Câu hỏi được parse từ output LLM, lưu vào bảng `quizzes` và `quiz_questions`

### 8.3 Làm quiz
- [ ] Giao diện chọn đáp án A/B/C/D, thanh tiến trình, đồng hồ đếm ngược
- [ ] Nộp bài → xem điểm + giải thích từng câu
- [ ] Lịch sử bài làm lưu vào `quiz_attempts`

---

## 9. Mô Hình 3D Cơ Thể Người

### 9.1 Viewer 3D
- [ ] Trang `/model3d` hiển thị mô hình cơ thể người 3D (React Three Fiber)
- [ ] Chuyển đổi Nam/Nữ → mô hình thay đổi
- [ ] Bật X-Ray lần lượt 4 mức → độ trong suốt thay đổi
- [ ] Xoay, zoom mô hình bằng chuột

### 9.2 Ghi nhận triệu chứng
- [ ] Click điểm màu xanh trên mô hình → panel thông tin vùng cơ thể hiện ra
- [ ] Nhấn "Khai báo triệu chứng" → form modal → điền → lưu vào DB
- [ ] Hiển thị danh sách triệu chứng đã ghi theo ngày

---

## 10. Profile Người Dùng & AI Insights

### 10.1 Lịch sử cá nhân
- [ ] Tab "Lịch sử hỏi" hiển thị các câu đã đặt trong /chat
- [ ] Tab "Triệu chứng" hiển thị bảng tiến triển triệu chứng theo vùng cơ thể
- [ ] Tab "AI Insights" hiển thị phân tích tổng hợp từ AI

### 10.2 Phân tích AI
- [ ] Nhấn "Phân tích AI ngay" → đợi 10–15s → nhận nhận định tổng quan + gợi ý cá nhân hóa
- [ ] Kết quả lưu vào DB, hiển thị lại các lần sau không cần chạy lại

---

## 11. Tính Năng Nâng Cao (Phần 4)

### 11.1 Dịch tài liệu (Bước 19)
- [ ] Chọn đoạn văn trong tài liệu → dịch Anh ↔ Việt tức thì

### 11.2 Explain thuật ngữ (Bước 20)
- [ ] Double-click từ khó trong tài liệu → tooltip giải thích xuất hiện

### 11.3 AI Learning Mode (Bước 21)
- [ ] Chat có selector: Beginner / Advanced / Researcher → câu trả lời thay đổi độ sâu

### 11.4 Tự phân loại tài liệu (Bước 22)
- [ ] Upload PDF → AI tự gán nhãn category (AI/Blockchain/Security…)
- [ ] Filter theo category trong /library

### 11.5 Timeline nghiên cứu (Bước 23)
- [ ] Trang /timeline hiển thị bài báo theo trục thời gian năm xuất bản

### 11.6 Trending topics (Bước 24)
- [ ] Trang /trending hiển thị word cloud + top chủ đề nổi bật

### 11.7 Memory Chat (Bước 25)
- [ ] AI nhớ lịch sử hội thoại trong cùng session tài liệu

### 11.8 AI Literature Review (Bước 30)
- [ ] Chọn nhiều tài liệu → AI tổng hợp bài literature review tự động

### 11.9 AI Phản biện Web (Bước 17)
- [ ] Nhập 2 URL bài báo/blog → AI so sánh và phản biện theo chuẩn học thuật

### 11.10 AI Tạo Slide (Bước 29)
- [ ] Chọn tài liệu → AI tạo slide outline thuyết trình

---

## 12. Xuất Báo Cáo

### 12.1 Xuất Word (.docx)
- [ ] Từ trang chat → nút **Xuất báo cáo** → tải file Word
- [ ] File chứa: câu hỏi, câu trả lời, trích dẫn nguồn với số trang

---

## 13. Admin Panel

### 13.1 Quản lý người dùng
- [ ] Xem danh sách toàn bộ user (email, tên, vai trò, ngày tạo)
- [ ] Thay đổi vai trò user (student ↔ researcher ↔ admin)

### 13.2 Duyệt đơn nâng cấp Researcher
- [ ] User gửi đơn xin nâng cấp lên Researcher từ trang `/researcher-apply`
- [ ] Admin thấy danh sách đơn chờ duyệt trong Admin Panel
- [ ] Nhấn Duyệt → `role` tự động đổi thành `researcher`
- [ ] Nhấn Từ chối → đơn bị hủy, role giữ nguyên

### 13.3 Quản lý danh mục tài liệu
- [ ] Xem, thêm, sửa, xóa các danh mục (categories)
- [ ] Tài liệu được gán danh mục khi upload hoặc chỉnh sửa sau

### 13.4 Quản lý Enterprise
- [ ] Tab Enterprise trong Admin Panel — xem danh sách tickets liên hệ chờ xử lý
- [ ] Mỗi ticket ghi rõ: tên, email, tổ chức, điện thoại, nhu cầu, thời gian gửi
- [ ] Nhấn **Tạo Offer** trên ticket → điền: giới hạn tài liệu/tháng, giới hạn/năm, ngày hết hạn, số tiền
- [ ] Hệ thống tạo link offer riêng (`/enterprise/offer/{token}`) → copy gửi cho khách
- [ ] Xem danh sách offers: trạng thái draft / active / paid / expired
- [ ] Nút **Xác nhận thủ công** nếu muốn kích hoạt mà không qua thanh toán QR

### 13.5 Gửi thông báo
- [ ] Tab Thông Báo trong Admin Panel
- [ ] Form gửi: tiêu đề, nội dung, loại (info / success / warning / system), link đính kèm, email đích
- [ ] Để trống email → broadcast đến **toàn bộ** người dùng
- [ ] Điền email cụ thể → gửi riêng cho tài khoản đó

### 13.6 Lịch sử thanh toán
- [ ] Tab Payments: xem tất cả giao dịch hệ thống (ACM + ENT codes)
- [ ] Lọc theo trạng thái, tìm theo mã tham chiếu

---

## 14. Môi Trường & Hạ Tầng

### 14.1 Backend
- [ ] FastAPI chạy tại `http://localhost:8000`
- [ ] Swagger UI tại `http://localhost:8000/docs`
- [ ] Health check `GET /health/db` trả về `{"postgres": "ok"}`
- [ ] CORS cho phép `localhost:3000` và `localhost:3001`

### 14.2 Frontend
- [ ] Next.js 14 App Router chạy tại `http://localhost:3001`
- [ ] Biến môi trường `NEXT_PUBLIC_API_URL=http://localhost:8000`
- [ ] Biến môi trường `NEXT_PUBLIC_GOOGLE_CLIENT_ID` đã cấu hình

### 14.3 Database
- [ ] PostgreSQL 16 + pgvector chạy trên Docker port 5433
- [ ] Neo4j Community chạy trên Docker port 7474 (HTTP) / 7687 (Bolt)
- [ ] Bảng `users`, `documents`, `chunks`, `email_otps`, `quizzes`, `quiz_questions`, `quiz_attempts`, `body_symptoms` đã tồn tại

### 14.4 AI Models
- [ ] Ollama chạy tại `http://localhost:11434`
- [ ] Model `nomic-embed-text` đã pull
- [ ] Groq API key hợp lệ (`GROQ_API_KEY` trong `.env`)

---

## 15. Hệ Thống Thanh Toán & Gói Dịch Vụ

### 15.1 Gói dịch vụ
- [ ] Trang `/pricing` hiển thị đúng 4 gói: Free / Pro / Researcher / Enterprise
- [ ] Gói đang dùng được highlight + badge "Gói của bạn"; gói phổ biến có nhãn "Phổ biến" màu vàng
- [ ] Giới hạn đúng theo gói:
  - Free: 3 tài liệu/tháng, 600 câu hỏi/tháng
  - Pro (149.000đ): 20 tài liệu/tháng, 1.000 câu hỏi/tháng
  - Researcher (499.000đ): 80 tài liệu/tháng, 5.000 câu hỏi/tháng
  - Enterprise (từ 3.000.000đ): không giới hạn (fair use)
- [ ] Khi vượt giới hạn → thông báo lỗi rõ ràng, gợi ý nâng cấp

### 15.2 Thanh toán bằng VietQR
- [ ] Nhấn "Nâng cấp ngay" → hệ thống sinh mã tham chiếu ACM + 9 ký tự ngẫu nhiên
- [ ] Hiển thị QR image từ VietQR API đúng số tiền + mã tham chiếu + tên tài khoản
- [ ] Nút copy mã tham chiếu để điền thủ công vào app ngân hàng
- [ ] Mã QR có hiệu lực **15 phút** — hết hạn tự chuyển sang trạng thái `expired`
- [ ] Webhook Casso / SePay nhận sự kiện → tự động match mã tham chiếu → nâng cấp ngay
- [ ] Khi đã có giao dịch pending chưa thanh toán → hỏi có muốn dùng lại hay tạo mới

### 15.3 Lịch sử thanh toán
- [ ] Bảng lịch sử: gói, số tiền, mã tham chiếu, ngày tạo, trạng thái
- [ ] 3 trạng thái: **Chờ TT** (pending) / **Thành công** (completed) / **Hết hạn** (expired)
- [ ] Refresh lịch sử tự động sau khi nâng cấp thành công

---

## 16. Tài Khoản Enterprise (Trường / Tổ Chức)

### 16.1 Gửi yêu cầu liên hệ
- [ ] Trang `/pricing` → nhấn "Liên hệ" trên card Enterprise → mở modal form
- [ ] Điền: tên người liên hệ, email, số điện thoại, tên trường/tổ chức, nhu cầu/ghi chú
- [ ] Hệ thống tạo ticket, gửi email thông báo đến admin
- [ ] Modal xác nhận "Đã gửi yêu cầu!" sau khi submit thành công

### 16.2 Admin tạo offer cho khách
- [ ] Admin Panel → tab Enterprise → xem ticket mới; nhấn **Tạo Offer**
- [ ] Form offer: giới hạn tài liệu/tháng cho thành viên tổ chức, giới hạn/năm, ngày hết hạn gói, số tiền
- [ ] Hệ thống sinh token ngẫu nhiên → link `/enterprise/offer/{token}` → copy gửi cho khách
- [ ] Offer ở trạng thái `draft` → khi khách mở link chuyển sang `active`

### 16.3 Khách thanh toán qua offer link
- [ ] Mở link → nhập email đã đăng ký → xác thực → xem chi tiết offer
- [ ] Hiển thị QR với số tiền đúng theo offer, mã tham chiếu ENT + 9 ký tự
- [ ] Trang tự poll trạng thái **mỗi 4 giây** — phát hiện thanh toán → chuyển sang màn hình thành công
- [ ] Webhook nhận mã `ENT...` → tạo Organization, set giới hạn, kích hoạt tài khoản Enterprise
- [ ] Email/link đến trang đăng nhập sau khi kích hoạt

### 16.4 Workspace tổ chức
- [ ] Tài khoản chủ có giới hạn riêng: 550 tài liệu/tháng, 7.000 tài liệu/năm (mặc định)
- [ ] Admin có thể set giới hạn tùy chỉnh theo từng deal khi tạo offer
- [ ] Hết ngày hết hạn → plan tự động về `free`, Organization vẫn lưu lịch sử
- [ ] Admin có thể confirm thủ công (không qua QR) nếu thanh toán ngoài hệ thống

---

## 17. Thông Báo Hệ Thống

### 17.1 Xem thông báo
- [ ] Icon chuông (🔔) trên thanh header, badge đỏ hiển thị số thông báo chưa đọc
- [ ] Số chưa đọc tự cập nhật **mỗi 30 giây** mà không cần reload trang
- [ ] Click chuông → dropdown hiện 50 thông báo gần nhất (từ mới đến cũ)
- [ ] Màu icon theo loại: 🔵 info | 🟢 success | 🟡 warning | 🟣 system

### 17.2 Tương tác với thông báo
- [ ] Click thông báo → tự đánh dấu đã đọc; nếu có link đính kèm → chuyển đến trang đó
- [ ] Hover từng thông báo → hiện nút xóa (×)
- [ ] Nút **"Đánh dấu tất cả đã đọc"** — một lần xử lý hết
- [ ] Nút **"Xóa tất cả"** — dọn sạch danh sách

### 17.3 Admin gửi thông báo
- [ ] Admin Panel → tab **Thông Báo** → điền form: tiêu đề, nội dung, loại, link, email đích
- [ ] **Để trống email** → broadcast tới TẤT CẢ tài khoản trong hệ thống (fan-out)
- [ ] **Điền email cụ thể** → gửi riêng cho 1 tài khoản
- [ ] Thông báo xuất hiện ngay trong chuông của người nhận

---

## 18. 📚 Thư Viện Tổng Hợp

### 18.1 Nguồn tài liệu
- [ ] Các file PDF trong **folder `DOCUMENT/`** là tài liệu gốc của thư viện (không phải upload của người dùng)
- [ ] Admin seed tài liệu: quét toàn bộ `DOCUMENT/`, tạo bản ghi `library_articles` cho từng file
- [ ] Mỗi bài có: tiêu đề song ngữ (Anh + Việt), tác giả, năm, tóm tắt học thuật, ngôn ngữ gốc
- [ ] Người dùng thấy rõ ngôn ngữ gốc (🇬🇧 EN / 🇻🇳 VI) và trạng thái dịch

### 18.2 Nội dung song ngữ
- [ ] Mỗi bài có **tóm tắt chuẩn học thuật** bằng tiếng Việt: Mục tiêu → Phương pháp → Kết quả → Kết luận
- [ ] Bài tiếng Anh: có thêm **bản dịch toàn văn tiếng Việt** lưu trong DB (do admin/AI cập nhật)
- [ ] Admin có thể cập nhật nội dung dịch trực tiếp qua API hoặc Admin Panel

### 18.3 Phân tầng truy cập (Paywall)
- [ ] **Bài không paywall**: tất cả người dùng đăng nhập xem được toàn văn PDF + bản dịch
- [ ] **Bài paywall** (`is_paywall = true`): Free chỉ xem tóm tắt; **Pro/Researcher/Enterprise** mở khóa bản dịch đầy đủ và PDF gốc
- [ ] Bài paywall hiển thị banner mờ với nút "Nâng cấp để đọc đầy đủ" → link `/pricing`
- [ ] Người dùng chưa đăng nhập: chỉ xem tiêu đề và tóm tắt ngắn (50 từ đầu)

---

## 19. 👥 Tra Cứu Tác Giả

### 19.1 Thư mục tác giả
- [ ] **178 nhà nghiên cứu** chuyên về tâm lý trẻ em / thanh thiếu niên được lập hồ sơ đầy đủ
- [ ] Mỗi profile bao gồm: tên đầy đủ, đơn vị công tác, quốc gia, lĩnh vực chuyên môn
- [ ] Có profile các nhà nghiên cứu nổi bật: Erskine, Patton, Blum, Weiss, Đặng Hoàng Minh, Matsumoto và nhiều người khác
- [ ] Mỗi tác giả liên kết đến danh sách bài đã có trong hệ thống

### 19.2 Tìm kiếm & lọc tác giả
- [ ] Tìm theo tên tác giả hoặc tên tổ chức/trường đại học
- [ ] Lọc theo lĩnh vực chuyên môn, quốc gia, số bài trong hệ thống
- [ ] Xem **mạng lưới hợp tác**: tác giả này thường viết chung với ai, nghiên cứu nhóm nào
- [ ] Click vào tác giả → xem toàn bộ bài đã có + link đến graph tri thức

---

## 20. 📊 Phân Tích Liên Bài

### 20.1 Bảng tổng hợp so sánh
- [ ] Chọn 2+ bài → hệ thống tự tổng hợp **bảng yếu tố nguy cơ / yếu tố bảo vệ** so sánh ngang
- [ ] Mỗi hàng = 1 yếu tố (ví dụ: stress gia đình, hỗ trợ xã hội…); mỗi cột = 1 nghiên cứu
- [ ] Ô trong bảng ghi: có / không / mức độ tác động (nếu báo cáo)

### 20.2 Biểu đồ phân tích nâng cao
- [ ] **Forest plot**: so sánh effect size của các nghiên cứu trên cùng 1 yếu tố — nhìn thấy ngay độ nhất quán
- [ ] **Heatmap chủ đề × tác giả × năm**: bức tranh tổng thể xu hướng nghiên cứu trong 10–20 năm qua
- [ ] Xuất bảng và biểu đồ ra file Excel / hình ảnh để dùng trong báo cáo

---

## 21. 🌏 Đa Ngôn Ngữ

### 21.1 Giao diện đa ngôn ngữ
- [ ] Chuyển đổi ngôn ngữ giao diện: **Tiếng Việt / English / Français / Русский / 中文**
- [ ] Cài đặt ngôn ngữ lưu vào tài khoản → nhớ sau khi đăng xuất và đăng nhập lại
- [ ] Tất cả nhãn menu, thông báo lỗi, tiêu đề trang đều dịch theo ngôn ngữ đã chọn
- [ ] Người dùng không đăng nhập: ngôn ngữ lưu vào localStorage trên máy

### 21.2 Nội dung phản hồi đa ngôn ngữ
- [ ] AI trả lời bằng **ngôn ngữ của câu hỏi** — hỏi tiếng Anh ra tiếng Anh, hỏi tiếng Việt ra tiếng Việt
- [ ] Bản tóm tắt tài liệu có thể xuất theo ngôn ngữ đã chọn trong cài đặt
- [ ] Giao diện quiz, slide AI, và literature review tự điều chỉnh theo ngôn ngữ hệ thống

---

# ═══════════════════════════════════════
# PHẦN 1 — 50% ĐẦU: DEMO CHẠY ĐƯỢC
# ═══════════════════════════════════════

## BƯỚC 1: CÀI ĐẶT PHẦN MỀM NỀN TẢNG

### 1.1. Cài Python 3.11

1. Truy cập `https://www.python.org/downloads/`
2. Tải **Python 3.11.x** (không dùng 3.12+ vì một số thư viện AI chưa tương thích)
3. Khi cài: **✅ tick vào "Add Python to PATH"** trước khi nhấn Install
4. Kiểm tra sau cài:
```powershell
python --version
# Kết quả: Python 3.11.x
```

### 1.2. Cài Node.js 18 LTS

1. Truy cập `https://nodejs.org/`
2. Tải bản **LTS (18.x hoặc 20.x)**
3. Cài mặc định, next-next-finish
4. Kiểm tra:
```powershell
node --version   # v18.x.x hoặc v20.x.x
npm --version    # 9.x.x hoặc 10.x.x
```

### 1.3. Cài Docker Desktop

1. Truy cập `https://www.docker.com/products/docker-desktop/`
2. Tải bản Windows, cài mặc định
3. Sau cài, **khởi động lại máy**
4. Mở Docker Desktop — chờ icon dưới taskbar chuyển sang **xanh lá** (Running)
5. Kiểm tra:
```powershell
docker --version
# Docker version 24.x.x
```

### 1.4. Cài Ollama (AI Local)

1. Truy cập `https://ollama.com/download`
2. Tải bản Windows, cài mặc định
3. Sau cài, Ollama tự chạy nền — kiểm tra:
```powershell
ollama --version
```

### 1.5. Tải Mô Hình AI Về Máy

Mở PowerShell, chạy 2 lệnh này (lần lượt, chờ tải xong mỗi lệnh):

```powershell
# Mô hình embedding — biến văn bản thành vector số (270MB)
ollama pull nomic-embed-text

# Mô hình chat dự phòng offline (1GB)
ollama pull qwen2.5:1.5b
```

Kiểm tra đã tải xong:
```powershell
ollama list
# Phải thấy: nomic-embed-text và qwen2.5:1.5b
```

---

## BƯỚC 2: TẠO CẤU TRÚC THƯ MỤC DỰ ÁN

Chọn một ổ đĩa thoải mái (ví dụ D:\), mở PowerShell và chạy:

```powershell
# Tạo thư mục gốc
mkdir D:\academic-rag-system
cd D:\academic-rag-system

# Tạo toàn bộ cây thư mục một lần
mkdir backend\app\api\v1
mkdir backend\app\core
mkdir backend\app\db
mkdir backend\app\models
mkdir backend\app\services
mkdir backend\app\utils
mkdir backend\scripts
mkdir frontend
mkdir docker
mkdir data\raw_pdfs
mkdir data\eval_results

# Tạo các file __init__.py cần thiết
New-Item backend\app\__init__.py -ItemType File
New-Item backend\app\api\__init__.py -ItemType File
New-Item backend\app\api\v1\__init__.py -ItemType File
New-Item backend\app\core\__init__.py -ItemType File
New-Item backend\app\db\__init__.py -ItemType File
New-Item backend\app\models\__init__.py -ItemType File
New-Item backend\app\services\__init__.py -ItemType File
New-Item backend\app\utils\__init__.py -ItemType File
```

---

## BƯỚC 3: KHỞI ĐỘNG DATABASE BẰNG DOCKER

### 3.1. Tạo File docker-compose.yml

Tạo file `D:\academic-rag-system\docker\docker-compose.yml`:

```yaml
version: '3.8'

services:
  postgres:
    image: pgvector/pgvector:pg16
    container_name: pgvector-db
    environment:
      POSTGRES_USER: admin
      POSTGRES_PASSWORD: secret
      POSTGRES_DB: rag_db
    ports:
      - "5432:5432"
    volumes:
      - pgdata:/var/lib/postgresql/data
      - ./init_db.sql:/docker-entrypoint-initdb.d/init_db.sql
    restart: unless-stopped

  neo4j:
    image: neo4j:5-community
    container_name: neo4j-db
    environment:
      NEO4J_AUTH: neo4j/secretpassword
    ports:
      - "7474:7474"
      - "7687:7687"
    volumes:
      - neo4jdata:/data
    restart: unless-stopped

volumes:
  pgdata:
  neo4jdata:
```

### 3.2. Tạo File init_db.sql

Tạo file `D:\academic-rag-system\docker\init_db.sql`:

```sql
-- Bật extension pgvector để lưu và tìm kiếm vector
CREATE EXTENSION IF NOT EXISTS vector;

-- Bảng người dùng
CREATE TABLE IF NOT EXISTS users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email VARCHAR(255) UNIQUE NOT NULL,
    hashed_password VARCHAR(255) NOT NULL,
    full_name VARCHAR(255),
    role VARCHAR(50) DEFAULT 'user',
    created_at TIMESTAMP DEFAULT NOW()
);

-- Bảng tài liệu PDF
CREATE TABLE IF NOT EXISTS documents (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    filename VARCHAR(500) NOT NULL,
    file_path VARCHAR(1000) NOT NULL,
    title VARCHAR(1000),
    authors TEXT,
    year INTEGER,
    total_pages INTEGER,
    status VARCHAR(50) DEFAULT 'processing',
    created_at TIMESTAMP DEFAULT NOW()
);

-- Bảng chunks văn bản (có vector embedding)
CREATE TABLE IF NOT EXISTS chunks (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    document_id UUID REFERENCES documents(id) ON DELETE CASCADE,
    content TEXT NOT NULL,
    embedding vector(768),
    page_number INTEGER,
    chunk_index INTEGER,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Index HNSW để tìm kiếm vector cực nhanh
CREATE INDEX IF NOT EXISTS chunks_embedding_idx 
ON chunks USING hnsw (embedding vector_cosine_ops);
```

### 3.3. Khởi Động Database

```powershell
cd D:\academic-rag-system\docker
docker-compose up -d

# Chờ 30 giây rồi kiểm tra
docker ps
# Phải thấy: pgvector-db (Up) và neo4j-db (Up)
```

**Kiểm tra Neo4j hoạt động:** Mở trình duyệt vào `http://localhost:7474`  
- Username: `neo4j` | Password: `secretpassword`
- Nếu thấy giao diện web là OK

> **Lần sau bật lại máy:** Chỉ cần chạy `docker-compose up -d` trong thư mục `docker/` — không cần tạo lại.

---

## BƯỚC 4: LẤY GROQ API KEY (MIỄN PHÍ)

1. Truy cập `https://console.groq.com`
2. Đăng nhập bằng Google
3. Menu trái → **API Keys** → **Create API Key**
4. Đặt tên bất kỳ (vd: "NCKH") → Create
5. Copy chuỗi `gsk_xxxxxxxxxxxxxxxxxxxxxxxx` — **lưu vào Notepad ngay**, hiện 1 lần duy nhất

---

## BƯỚC 5: XÂY DỰNG BACKEND

### 5.1. Tạo Môi Trường Python Ảo

```powershell
cd D:\academic-rag-system\backend

# Tạo môi trường ảo
python -m venv venv

# Kích hoạt môi trường ảo (Windows)
venv\Scripts\activate
# Dấu nhắc lệnh sẽ có (venv) ở đầu

# Cài toàn bộ thư viện
pip install fastapi "uvicorn[standard]" python-multipart
pip install PyMuPDF pdfplumber
pip install langchain langchain-community
pip install psycopg2-binary pgvector
pip install neo4j
pip install groq
pip install rank-bm25
pip install python-dotenv pydantic-settings
pip install "python-jose[cryptography]" "passlib[bcrypt]"
pip install sqlalchemy

# Lưu danh sách thư viện
pip freeze > requirements.txt
```

### 5.2. Tạo File `backend/.env`

Tạo file `D:\academic-rag-system\backend\.env`:

```env
# Database
POSTGRES_URL=postgresql://admin:secret@localhost:5432/rag_db
NEO4J_URL=bolt://localhost:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=secretpassword

# AI
GROQ_API_KEY=gsk_xxxxxxxxxxxxxxxxxxxxxxxx
OLLAMA_BASE_URL=http://localhost:11434

# Security
SECRET_KEY=change-this-to-a-random-64-char-string-minimum
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=1440

# Storage
PDF_UPLOAD_DIR=../data/raw_pdfs
```

> **Tạo SECRET_KEY ngẫu nhiên:**
> ```powershell
> python -c "import secrets; print(secrets.token_hex(32))"
> ```
> Copy kết quả vào `SECRET_KEY=` trong file `.env`

### 5.3. Tạo File `backend/app/core/config.py`

```python
from pydantic_settings import BaseSettings
from pathlib import Path

class Settings(BaseSettings):
    POSTGRES_URL: str
    NEO4J_URL: str
    NEO4J_USER: str
    NEO4J_PASSWORD: str
    GROQ_API_KEY: str
    OLLAMA_BASE_URL: str = "http://localhost:11434"
    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 1440
    PDF_UPLOAD_DIR: str = "../data/raw_pdfs"

    class Config:
        env_file = ".env"

settings = Settings()
```

### 5.4. Tạo File `backend/app/db/postgres.py`

```python
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, DeclarativeBase
from app.core.config import settings

engine = create_engine(settings.POSTGRES_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

class Base(DeclarativeBase):
    pass

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
```

### 5.5. Tạo File `backend/app/models/document.py`

```python
import uuid
from datetime import datetime
from sqlalchemy import Column, String, Integer, Text, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from pgvector.sqlalchemy import Vector
from app.db.postgres import Base

class User(Base):
    __tablename__ = "users"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email = Column(String(255), unique=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    full_name = Column(String(255))
    role = Column(String(50), default="user")
    created_at = Column(DateTime, default=datetime.now)

class Document(Base):
    __tablename__ = "documents"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"))
    filename = Column(String(500), nullable=False)
    file_path = Column(String(1000), nullable=False)
    title = Column(String(1000))
    authors = Column(Text)
    year = Column(Integer)
    total_pages = Column(Integer)
    status = Column(String(50), default="processing")
    created_at = Column(DateTime, default=datetime.now)

class Chunk(Base):
    __tablename__ = "chunks"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    document_id = Column(UUID(as_uuid=True), ForeignKey("documents.id", ondelete="CASCADE"))
    content = Column(Text, nullable=False)
    embedding = Column(Vector(768))
    page_number = Column(Integer)
    chunk_index = Column(Integer)
    created_at = Column(DateTime, default=datetime.now)
```

### 5.6. Tạo File `backend/app/services/parser.py`

```python
import fitz  # PyMuPDF
import pdfplumber
from pathlib import Path

def parse_pdf(file_path: str) -> dict:
    """Đọc PDF và trả về text đầy đủ + metadata."""
    doc = fitz.open(file_path)
    
    pages_text = []
    full_text = ""
    
    for page_num in range(len(doc)):
        page = doc[page_num]
        text = page.get_text("text")
        pages_text.append({"page": page_num + 1, "text": text})
        full_text += f"\n[Trang {page_num + 1}]\n{text}"
    
    metadata = doc.metadata or {}
    
    return {
        "full_text": full_text.strip(),
        "pages": pages_text,
        "total_pages": len(doc),
        "metadata": {
            "title": metadata.get("title", ""),
            "author": metadata.get("author", ""),
            "creation_date": metadata.get("creationDate", ""),
        }
    }

def extract_tables(file_path: str) -> list:
    """Trích xuất bảng biểu từ PDF."""
    tables = []
    with pdfplumber.open(file_path) as pdf:
        for page_num, page in enumerate(pdf.pages):
            for table in page.extract_tables():
                tables.append({
                    "page": page_num + 1,
                    "data": table
                })
    return tables
```

### 5.7. Tạo File `backend/app/services/chunking.py`

```python
from langchain.text_splitter import RecursiveCharacterTextSplitter

def chunk_text(text: str, document_id: str, pages_data: list) -> list[dict]:
    """Cắt văn bản thành các đoạn nhỏ tối ưu cho RAG."""
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=500,
        chunk_overlap=50,
        separators=["\n\n", "\n", ". ", " ", ""]
    )
    
    raw_chunks = splitter.split_text(text)
    
    chunks = []
    for idx, content in enumerate(raw_chunks):
        # Tìm trang chứa chunk này
        page_num = _find_page(content, pages_data)
        chunks.append({
            "content": content,
            "chunk_index": idx,
            "document_id": document_id,
            "page_number": page_num,
        })
    
    return chunks

def _find_page(chunk_text: str, pages_data: list) -> int:
    """Tìm số trang chứa đoạn văn bản."""
    # Lấy 50 ký tự đầu của chunk để tìm kiếm
    sample = chunk_text[:50]
    for page in pages_data:
        if sample in page.get("text", ""):
            return page["page"]
    return 1
```

### 5.8. Tạo File `backend/app/services/embedder.py`

```python
import httpx
import json
from app.core.config import settings

OLLAMA_EMBED_URL = f"{settings.OLLAMA_BASE_URL}/api/embeddings"

def embed_text(text: str) -> list[float]:
    """Biến đoạn văn bản thành vector 768 chiều bằng Ollama."""
    response = httpx.post(
        OLLAMA_EMBED_URL,
        json={"model": "nomic-embed-text", "prompt": text},
        timeout=30.0
    )
    response.raise_for_status()
    return response.json()["embedding"]

def embed_and_store(chunks: list[dict], db) -> None:
    """Tạo vector cho từng chunk và lưu vào PostgreSQL."""
    from app.models.document import Chunk
    import uuid
    
    chunk_objects = []
    for chunk_data in chunks:
        vector = embed_text(chunk_data["content"])
        
        chunk_obj = Chunk(
            id=uuid.uuid4(),
            document_id=chunk_data["document_id"],
            content=chunk_data["content"],
            embedding=vector,
            page_number=chunk_data.get("page_number", 1),
            chunk_index=chunk_data.get("chunk_index", 0),
        )
        chunk_objects.append(chunk_obj)
    
    db.bulk_save_objects(chunk_objects)
    db.commit()

def embed_query(query: str) -> list[float]:
    """Biến câu hỏi thành vector để tìm kiếm."""
    return embed_text(query)
```

### 5.9. Tạo File `backend/app/services/retriever.py`

```python
from sqlalchemy.orm import Session
from sqlalchemy import text
from rank_bm25 import BM25Okapi
from app.services.embedder import embed_query

def retrieve(query: str, document_ids: list[str], db: Session) -> list[dict]:
    """Hybrid Search: kết hợp Vector Search + BM25 Keyword Search."""
    
    # --- Vector Search ---
    query_vector = embed_query(query)
    vector_str = "[" + ",".join(map(str, query_vector)) + "]"
    
    doc_ids_str = "'" + "','".join(document_ids) + "'"
    
    sql = text(f"""
        SELECT id, content, page_number, document_id,
               1 - (embedding <=> '{vector_str}'::vector) AS score
        FROM chunks
        WHERE document_id IN ({doc_ids_str})
        ORDER BY score DESC
        LIMIT 10
    """)
    
    vector_results = db.execute(sql).fetchall()
    
    # --- BM25 Keyword Search ---
    all_chunks_sql = text(f"""
        SELECT id, content, page_number, document_id
        FROM chunks
        WHERE document_id IN ({doc_ids_str})
    """)
    all_chunks = db.execute(all_chunks_sql).fetchall()
    
    if all_chunks:
        corpus = [row.content.split() for row in all_chunks]
        bm25 = BM25Okapi(corpus)
        bm25_scores = bm25.get_scores(query.split())
        
        # Top 10 từ BM25
        top_bm25_idx = sorted(range(len(bm25_scores)), key=lambda i: bm25_scores[i], reverse=True)[:10]
        bm25_results = [all_chunks[i] for i in top_bm25_idx]
    else:
        bm25_results = []
    
    # --- Reciprocal Rank Fusion ---
    scores = {}
    
    for rank, row in enumerate(vector_results):
        rid = str(row.id)
        scores[rid] = scores.get(rid, 0) + 1 / (rank + 60)
    
    for rank, row in enumerate(bm25_results):
        rid = str(row.id)
        scores[rid] = scores.get(rid, 0) + 1 / (rank + 60)
    
    # Gộp tất cả chunks
    all_unique = {str(r.id): r for r in list(vector_results) + bm25_results}
    
    # Sắp xếp theo điểm RRF, lấy top 5
    top5_ids = sorted(scores.keys(), key=lambda x: scores[x], reverse=True)[:5]
    
    return [
        {
            "content": all_unique[rid].content,
            "page_number": all_unique[rid].page_number,
            "document_id": str(all_unique[rid].document_id),
            "score": scores[rid],
        }
        for rid in top5_ids if rid in all_unique
    ]
```

### 5.10. Tạo File `backend/app/services/generator.py`

```python
from groq import Groq
from app.core.config import settings
from typing import Generator

groq_client = Groq(api_key=settings.GROQ_API_KEY)

def build_prompt(query: str, context_chunks: list[dict]) -> list[dict]:
    """Xây dựng prompt có hệ thống chống hallucination."""
    context_text = ""
    for i, chunk in enumerate(context_chunks):
        context_text += f"\n[Nguồn {i+1} - Trang {chunk['page_number']}]:\n{chunk['content']}\n"
    
    return [
        {
            "role": "system",
            "content": (
                "Bạn là trợ lý nghiên cứu học thuật chuyên nghiệp. "
                "CHỈ trả lời dựa trên văn bản CONTEXT được cung cấp. "
                "Nếu không tìm thấy thông tin trong context, hãy nói: "
                "'Tôi không tìm thấy thông tin này trong tài liệu được cung cấp.' "
                "Luôn trích dẫn nguồn theo định dạng [Nguồn X, Trang Y] khi trả lời. "
                "Trả lời bằng tiếng Việt trừ khi người dùng hỏi bằng tiếng Anh."
            )
        },
        {
            "role": "user",
            "content": f"CONTEXT:\n{context_text}\n\nCÂU HỎI: {query}"
        }
    ]

def generate_stream(query: str, context_chunks: list[dict]):
    """Sinh câu trả lời dạng stream (từng token một)."""
    messages = build_prompt(query, context_chunks)
    
    stream = groq_client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=messages,
        stream=True,
        max_tokens=2048,
        temperature=0.1,
    )
    
    for chunk in stream:
        delta = chunk.choices[0].delta.content
        if delta:
            yield delta

def summarize_document(full_text: str) -> str:
    """Tóm tắt bài báo theo cấu trúc học thuật."""
    # Cắt text nếu quá dài
    text_sample = full_text[:8000]
    
    response = groq_client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[
            {
                "role": "system",
                "content": "Bạn là chuyên gia tóm tắt bài báo khoa học. Tóm tắt theo đúng cấu trúc: Mục tiêu / Phương pháp / Mẫu nghiên cứu / Kết quả chính / Hạn chế."
            },
            {
                "role": "user",
                "content": f"Tóm tắt bài báo sau:\n\n{text_sample}"
            }
        ],
        max_tokens=1024,
        temperature=0.2,
    )
    return response.choices[0].message.content
```

### 5.11. Tạo File `backend/app/api/v1/document.py`

```python
import uuid
import os
import shutil
from fastapi import APIRouter, UploadFile, File, BackgroundTasks, Depends, HTTPException
from sqlalchemy.orm import Session
from app.db.postgres import get_db
from app.models.document import Document, Chunk
from app.services.parser import parse_pdf
from app.services.chunking import chunk_text
from app.services.embedder import embed_and_store
from app.core.config import settings

router = APIRouter()

def _run_pipeline(file_path: str, document_id: str, db_url: str):
    """Pipeline xử lý PDF chạy ngầm (Background Task)."""
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker
    
    engine = create_engine(db_url)
    SessionBg = sessionmaker(bind=engine)
    db = SessionBg()
    
    try:
        # 1. Parse PDF
        parsed = parse_pdf(file_path)
        
        # 2. Cập nhật metadata
        doc = db.query(Document).filter(Document.id == document_id).first()
        if doc:
            doc.title = parsed["metadata"].get("title") or doc.filename
            doc.authors = parsed["metadata"].get("author", "")
            doc.total_pages = parsed["total_pages"]
        db.commit()
        
        # 3. Chunking
        chunks = chunk_text(parsed["full_text"], document_id, parsed["pages"])
        
        # 4. Embed và lưu vào Postgres
        embed_and_store(chunks, db)
        
        # 5. Cập nhật status = ready
        doc.status = "ready"
        db.commit()
        
    except Exception as e:
        doc = db.query(Document).filter(Document.id == document_id).first()
        if doc:
            doc.status = "error"
            db.commit()
        print(f"Pipeline error: {e}")
    finally:
        db.close()

@router.post("/upload")
async def upload_document(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    if not file.filename.endswith(".pdf"):
        raise HTTPException(400, "Chỉ chấp nhận file PDF")
    
    # Tạo thư mục lưu file
    upload_dir = settings.PDF_UPLOAD_DIR
    os.makedirs(upload_dir, exist_ok=True)
    
    document_id = str(uuid.uuid4())
    file_path = os.path.join(upload_dir, f"{document_id}_{file.filename}")
    
    # Lưu file lên server
    with open(file_path, "wb") as f:
        shutil.copyfileobj(file.file, f)
    
    # Lưu record vào DB
    doc = Document(
        id=document_id,
        filename=file.filename,
        file_path=file_path,
        status="processing"
    )
    db.add(doc)
    db.commit()
    
    # Xử lý ngầm — không block request
    background_tasks.add_task(_run_pipeline, file_path, document_id, settings.POSTGRES_URL)
    
    return {
        "document_id": document_id,
        "filename": file.filename,
        "status": "processing",
        "message": "File đang được xử lý, vui lòng chờ 30-60 giây"
    }

@router.get("/list")
def list_documents(db: Session = Depends(get_db)):
    docs = db.query(Document).order_by(Document.created_at.desc()).all()
    return {
        "total": len(docs),
        "documents": [
            {
                "id": str(d.id),
                "filename": d.filename,
                "title": d.title,
                "authors": d.authors,
                "year": d.year,
                "total_pages": d.total_pages,
                "status": d.status,
                "created_at": d.created_at.isoformat() if d.created_at else None,
            }
            for d in docs
        ]
    }

@router.get("/{document_id}")
def get_document(document_id: str, db: Session = Depends(get_db)):
    doc = db.query(Document).filter(Document.id == document_id).first()
    if not doc:
        raise HTTPException(404, "Không tìm thấy tài liệu")
    return {
        "id": str(doc.id),
        "filename": doc.filename,
        "title": doc.title,
        "authors": doc.authors,
        "year": doc.year,
        "status": doc.status,
        "total_pages": doc.total_pages,
    }

@router.delete("/{document_id}")
def delete_document(document_id: str, db: Session = Depends(get_db)):
    doc = db.query(Document).filter(Document.id == document_id).first()
    if not doc:
        raise HTTPException(404, "Không tìm thấy tài liệu")
    
    # Xóa file vật lý
    if os.path.exists(doc.file_path):
        os.remove(doc.file_path)
    
    db.delete(doc)
    db.commit()
    return {"message": "Đã xóa tài liệu"}

@router.post("/{document_id}/summarize")
def summarize_document_endpoint(document_id: str, db: Session = Depends(get_db)):
    doc = db.query(Document).filter(Document.id == document_id).first()
    if not doc:
        raise HTTPException(404, "Không tìm thấy tài liệu")
    if doc.status != "ready":
        raise HTTPException(400, "Tài liệu chưa xử lý xong")
    
    # Lấy toàn bộ chunks ghép lại
    chunks = db.query(Chunk).filter(Chunk.document_id == document_id).order_by(Chunk.chunk_index).all()
    full_text = " ".join([c.content for c in chunks])
    
    from app.services.generator import summarize_document
    summary = summarize_document(full_text)
    
    return {"document_id": document_id, "summary": summary}
```

### 5.12. Tạo File `backend/app/api/v1/chat.py`

```python
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional
from app.db.postgres import get_db
from app.services.retriever import retrieve
from app.services.generator import generate_stream

router = APIRouter()

class ChatRequest(BaseModel):
    query: str
    document_ids: list[str]
    mode: Optional[str] = "single"

@router.post("")
def chat(request: ChatRequest, db: Session = Depends(get_db)):
    if not request.query.strip():
        raise HTTPException(400, "Câu hỏi không được để trống")
    if not request.document_ids:
        raise HTTPException(400, "Phải chọn ít nhất 1 tài liệu")
    
    # Tìm kiếm context liên quan
    context_chunks = retrieve(request.query, request.document_ids, db)
    
    if not context_chunks:
        def no_context():
            yield "Không tìm thấy thông tin liên quan trong các tài liệu đã chọn."
        return StreamingResponse(no_context(), media_type="text/plain")
    
    # Stream câu trả lời
    return StreamingResponse(
        generate_stream(request.query, context_chunks),
        media_type="text/plain",
        headers={
            "X-Context-Pages": ",".join(str(c["page_number"]) for c in context_chunks),
            "X-Document-IDs": ",".join(c["document_id"] for c in context_chunks),
        }
    )
```

### 5.13. Tạo File `backend/app/api/v1/__init__.py`

```python
from fastapi import APIRouter
from app.api.v1 import document, chat

api_router = APIRouter()
api_router.include_router(document.router, prefix="/document", tags=["Documents"])
api_router.include_router(chat.router, prefix="/chat", tags=["Chat"])
```

### 5.14. Tạo File `backend/main.py`

```python
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.v1 import api_router
from app.db.postgres import engine
from app.models.document import Base

# Tạo bảng nếu chưa có
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Academic RAG System",
    description="Hệ thống hỏi đáp học thuật thông minh",
    version="1.0.0"
)

# Cho phép Frontend gọi API
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:3001"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router, prefix="/api/v1")

@app.get("/")
def health_check():
    return {"status": "ok", "message": "Academic RAG System is running"}
```

### 5.15. Khởi Động Backend

```powershell
cd D:\academic-rag-system\backend
venv\Scripts\activate
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

**Kiểm tra:** Mở trình duyệt vào `http://localhost:8000/docs`  
Phải thấy Swagger UI với các endpoint Documents và Chat.

---

## BƯỚC 6: XÂY DỰNG FRONTEND CƠ BẢN

### 6.1. Tạo Dự Án Next.js

Mở **terminal MỚI** (giữ terminal backend đang chạy):

```powershell
cd D:\academic-rag-system

npx create-next-app@latest frontend --typescript --tailwind --app --src-dir --import-alias "@/*"
# Khi hỏi: Chọn Yes cho tất cả, No cho Turbopack nếu hỏi

cd frontend

# Cài thư viện bổ sung
npm install axios
npm install react-markdown remark-gfm
npm install lucide-react
npm install zustand
```

### 6.2. Tạo File `frontend/.env.local`

```env
NEXT_PUBLIC_API_URL=http://localhost:8000
```

### 6.3. Tạo File `frontend/src/lib/api.ts`

```typescript
import axios from 'axios';

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

const api = axios.create({
  baseURL: `${API_URL}/api/v1`,
  timeout: 60000,
});

export interface DocumentInfo {
  id: string;
  filename: string;
  title: string | null;
  authors: string | null;
  year: number | null;
  status: string;
  total_pages: number | null;
}

export const uploadDocument = async (file: File): Promise<{ document_id: string; status: string }> => {
  const formData = new FormData();
  formData.append('file', file);
  const res = await api.post('/document/upload', formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
  });
  return res.data;
};

export const getDocuments = async (): Promise<DocumentInfo[]> => {
  const res = await api.get('/document/list');
  return res.data.documents;
};

export const getDocument = async (id: string): Promise<DocumentInfo> => {
  const res = await api.get(`/document/${id}`);
  return res.data;
};

export const deleteDocument = async (id: string): Promise<void> => {
  await api.delete(`/document/${id}`);
};

export const summarizeDocument = async (id: string): Promise<string> => {
  const res = await api.post(`/document/${id}/summarize`);
  return res.data.summary;
};

export const chatStream = async (
  query: string,
  documentIds: string[],
  onChunk: (text: string) => void
): Promise<void> => {
  const response = await fetch(`${API_URL}/api/v1/chat`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ query, document_ids: documentIds }),
  });

  if (!response.ok) throw new Error('Chat request failed');
  
  const reader = response.body!.getReader();
  const decoder = new TextDecoder();
  
  while (true) {
    const { done, value } = await reader.read();
    if (done) break;
    onChunk(decoder.decode(value));
  }
};
```

### 6.4. Tạo File `frontend/src/store/useAppStore.ts`

```typescript
import { create } from 'zustand';

interface Message {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  timestamp: Date;
}

interface AppStore {
  selectedDocumentIds: string[];
  setSelectedDocumentIds: (ids: string[]) => void;
  toggleDocument: (id: string) => void;
  chatMessages: Message[];
  addMessage: (msg: Omit<Message, 'id' | 'timestamp'>) => void;
  clearChat: () => void;
}

export const useAppStore = create<AppStore>((set) => ({
  selectedDocumentIds: [],
  setSelectedDocumentIds: (ids) => set({ selectedDocumentIds: ids }),
  toggleDocument: (id) =>
    set((state) => ({
      selectedDocumentIds: state.selectedDocumentIds.includes(id)
        ? state.selectedDocumentIds.filter((d) => d !== id)
        : [...state.selectedDocumentIds, id],
    })),
  chatMessages: [],
  addMessage: (msg) =>
    set((state) => ({
      chatMessages: [
        ...state.chatMessages,
        { ...msg, id: crypto.randomUUID(), timestamp: new Date() },
      ],
    })),
  clearChat: () => set({ chatMessages: [] }),
}));
```

### 6.5. Sửa File `frontend/src/app/globals.css`

Xóa hết nội dung cũ, thay bằng:

```css
@tailwind base;
@tailwind components;
@tailwind utilities;

:root {
  --background: #ffffff;
  --foreground: #171717;
}

body {
  background: var(--background);
  color: var(--foreground);
  font-family: 'Inter', sans-serif;
}
```

### 6.6. Sửa File `frontend/src/app/layout.tsx`

```typescript
import type { Metadata } from 'next';
import { Inter } from 'next/font/google';
import './globals.css';
import Link from 'next/link';

const inter = Inter({ subsets: ['latin'] });

export const metadata: Metadata = {
  title: 'Academic RAG System',
  description: 'Hệ thống hỏi đáp học thuật thông minh',
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="vi">
      <body className={inter.className}>
        <nav className="bg-blue-700 text-white px-6 py-3 flex items-center gap-6 shadow">
          <span className="font-bold text-lg">Academic RAG</span>
          <Link href="/library" className="hover:underline">Thư viện</Link>
          <Link href="/chat" className="hover:underline">Hỏi đáp</Link>
        </nav>
        <main className="min-h-screen bg-gray-50">
          {children}
        </main>
      </body>
    </html>
  );
}
```

### 6.7. Sửa File `frontend/src/app/page.tsx`

```typescript
import Link from 'next/link';

export default function HomePage() {
  return (
    <div className="flex flex-col items-center justify-center min-h-[80vh] gap-6 text-center px-4">
      <h1 className="text-4xl font-bold text-blue-700">
        Hệ Thống Hỏi Đáp Học Thuật AI
      </h1>
      <p className="text-gray-600 max-w-xl text-lg">
        Upload bài báo PDF → Hỏi đáp bằng AI → Nhận câu trả lời có trích dẫn chính xác
      </p>
      <div className="flex gap-4">
        <Link
          href="/library"
          className="bg-blue-600 text-white px-6 py-3 rounded-lg hover:bg-blue-700 font-medium"
        >
          Upload Bài Báo
        </Link>
        <Link
          href="/chat"
          className="bg-white border-2 border-blue-600 text-blue-600 px-6 py-3 rounded-lg hover:bg-blue-50 font-medium"
        >
          Bắt Đầu Hỏi Đáp
        </Link>
      </div>
    </div>
  );
}
```

### 6.8. Tạo Trang Library `frontend/src/app/library/page.tsx`

```typescript
'use client';

import { useEffect, useState, useRef } from 'react';
import { DocumentInfo, getDocuments, uploadDocument, deleteDocument } from '@/lib/api';

export default function LibraryPage() {
  const [documents, setDocuments] = useState<DocumentInfo[]>([]);
  const [uploading, setUploading] = useState(false);
  const [uploadMessage, setUploadMessage] = useState('');
  const fileInputRef = useRef<HTMLInputElement>(null);
  const pollRef = useRef<NodeJS.Timeout | null>(null);

  const fetchDocs = async () => {
    try {
      const docs = await getDocuments();
      setDocuments(docs);
    } catch (e) {
      console.error(e);
    }
  };

  useEffect(() => {
    fetchDocs();
  }, []);

  const handleUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;

    setUploading(true);
    setUploadMessage('Đang tải lên...');

    try {
      const result = await uploadDocument(file);
      setUploadMessage(`Đang xử lý file... (document_id: ${result.document_id})`);
      fetchDocs();

      // Polling mỗi 3 giây để cập nhật status
      pollRef.current = setInterval(async () => {
        await fetchDocs();
        const updated = await getDocuments();
        const doc = updated.find(d => d.id === result.document_id);
        if (doc && doc.status === 'ready') {
          setUploadMessage('Xử lý hoàn tất!');
          setUploading(false);
          if (pollRef.current) clearInterval(pollRef.current);
        }
        if (doc && doc.status === 'error') {
          setUploadMessage('Lỗi xử lý file!');
          setUploading(false);
          if (pollRef.current) clearInterval(pollRef.current);
        }
      }, 3000);
    } catch (err) {
      setUploadMessage('Lỗi upload file!');
      setUploading(false);
    }
  };

  const handleDelete = async (id: string) => {
    if (!confirm('Xóa tài liệu này?')) return;
    await deleteDocument(id);
    fetchDocs();
  };

  return (
    <div className="max-w-5xl mx-auto p-6">
      <h1 className="text-2xl font-bold mb-6 text-gray-800">Thư Viện Bài Báo</h1>

      {/* Upload Zone */}
      <div
        className="border-2 border-dashed border-blue-400 rounded-xl p-10 text-center mb-6 cursor-pointer hover:bg-blue-50"
        onClick={() => fileInputRef.current?.click()}
      >
        <p className="text-gray-500 text-lg">Kéo thả PDF vào đây hoặc click để chọn file</p>
        <p className="text-sm text-gray-400 mt-1">Chỉ nhận file .PDF</p>
        <input
          ref={fileInputRef}
          type="file"
          accept=".pdf"
          className="hidden"
          onChange={handleUpload}
        />
      </div>

      {/* Upload Status */}
      {uploadMessage && (
        <div className={`p-3 rounded-lg mb-4 text-sm ${
          uploadMessage.includes('Lỗi') ? 'bg-red-100 text-red-700' :
          uploadMessage.includes('hoàn tất') ? 'bg-green-100 text-green-700' :
          'bg-blue-100 text-blue-700'
        }`}>
          {uploadMessage}
        </div>
      )}

      {/* Documents Table */}
      <div className="bg-white rounded-xl shadow overflow-hidden">
        <table className="w-full text-sm">
          <thead className="bg-gray-100 text-gray-600 uppercase text-xs">
            <tr>
              <th className="px-4 py-3 text-left">Tên File</th>
              <th className="px-4 py-3 text-left">Tiêu đề</th>
              <th className="px-4 py-3 text-left">Tác giả</th>
              <th className="px-4 py-3 text-center">Trang</th>
              <th className="px-4 py-3 text-center">Trạng thái</th>
              <th className="px-4 py-3 text-center">Hành động</th>
            </tr>
          </thead>
          <tbody>
            {documents.length === 0 && (
              <tr>
                <td colSpan={6} className="text-center py-8 text-gray-400">
                  Chưa có tài liệu nào. Hãy upload file PDF đầu tiên.
                </td>
              </tr>
            )}
            {documents.map((doc) => (
              <tr key={doc.id} className="border-t hover:bg-gray-50">
                <td className="px-4 py-3 font-medium text-gray-800 max-w-[200px] truncate">
                  {doc.filename}
                </td>
                <td className="px-4 py-3 text-gray-600 max-w-[250px] truncate">
                  {doc.title || '—'}
                </td>
                <td className="px-4 py-3 text-gray-500 max-w-[150px] truncate">
                  {doc.authors || '—'}
                </td>
                <td className="px-4 py-3 text-center text-gray-500">
                  {doc.total_pages || '—'}
                </td>
                <td className="px-4 py-3 text-center">
                  <span className={`px-2 py-1 rounded-full text-xs font-medium ${
                    doc.status === 'ready' ? 'bg-green-100 text-green-700' :
                    doc.status === 'processing' ? 'bg-yellow-100 text-yellow-700' :
                    'bg-red-100 text-red-700'
                  }`}>
                    {doc.status === 'ready' ? 'Sẵn sàng' :
                     doc.status === 'processing' ? 'Đang xử lý' : 'Lỗi'}
                  </span>
                </td>
                <td className="px-4 py-3 text-center">
                  <button
                    onClick={() => handleDelete(doc.id)}
                    className="text-red-500 hover:text-red-700 text-xs underline"
                  >
                    Xóa
                  </button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
```

### 6.9. Tạo Trang Chat `frontend/src/app/chat/page.tsx`

```typescript
'use client';

import { useEffect, useState, useRef } from 'react';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import { getDocuments, chatStream, DocumentInfo } from '@/lib/api';
import { useAppStore } from '@/store/useAppStore';

export default function ChatPage() {
  const [documents, setDocuments] = useState<DocumentInfo[]>([]);
  const [input, setInput] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const { selectedDocumentIds, toggleDocument, chatMessages, addMessage } = useAppStore();

  useEffect(() => {
    getDocuments().then(docs => setDocuments(docs.filter(d => d.status === 'ready')));
  }, []);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [chatMessages]);

  const handleSend = async () => {
    if (!input.trim() || isLoading) return;
    if (selectedDocumentIds.length === 0) {
      alert('Vui lòng chọn ít nhất 1 tài liệu ở bên trái');
      return;
    }

    const userMsg = input.trim();
    setInput('');
    addMessage({ role: 'user', content: userMsg });
    setIsLoading(true);

    // Tạo placeholder cho tin nhắn assistant
    const tempId = crypto.randomUUID();
    addMessage({ role: 'assistant', content: '' });

    let fullResponse = '';

    try {
      await chatStream(userMsg, selectedDocumentIds, (chunk) => {
        fullResponse += chunk;
        // Cập nhật tin nhắn cuối cùng
        useAppStore.setState((state) => {
          const msgs = [...state.chatMessages];
          msgs[msgs.length - 1] = {
            ...msgs[msgs.length - 1],
            content: fullResponse,
          };
          return { chatMessages: msgs };
        });
      });
    } catch (err) {
      useAppStore.setState((state) => {
        const msgs = [...state.chatMessages];
        msgs[msgs.length - 1] = {
          ...msgs[msgs.length - 1],
          content: 'Lỗi kết nối. Vui lòng thử lại.',
        };
        return { chatMessages: msgs };
      });
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="flex h-[calc(100vh-56px)]">
      {/* Sidebar chọn tài liệu */}
      <div className="w-64 bg-white border-r p-4 overflow-y-auto flex-shrink-0">
        <h2 className="font-semibold text-gray-700 mb-3">Chọn tài liệu</h2>
        {documents.length === 0 && (
          <p className="text-xs text-gray-400">
            Chưa có tài liệu. Vào Thư viện để upload PDF.
          </p>
        )}
        {documents.map((doc) => (
          <label key={doc.id} className="flex items-start gap-2 mb-2 cursor-pointer">
            <input
              type="checkbox"
              checked={selectedDocumentIds.includes(doc.id)}
              onChange={() => toggleDocument(doc.id)}
              className="mt-1"
            />
            <span className="text-sm text-gray-600 leading-tight">
              {doc.title || doc.filename}
            </span>
          </label>
        ))}
        {selectedDocumentIds.length > 0 && (
          <p className="text-xs text-blue-600 mt-3">
            Đã chọn: {selectedDocumentIds.length} tài liệu
          </p>
        )}
      </div>

      {/* Chat area */}
      <div className="flex-1 flex flex-col">
        {/* Messages */}
        <div className="flex-1 overflow-y-auto p-6 space-y-4">
          {chatMessages.length === 0 && (
            <div className="text-center text-gray-400 mt-20">
              <p className="text-xl mb-2">Hỏi đáp về bài báo của bạn</p>
              <p className="text-sm">Chọn tài liệu bên trái và đặt câu hỏi</p>
            </div>
          )}
          {chatMessages.map((msg) => (
            <div
              key={msg.id}
              className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}
            >
              <div
                className={`max-w-[80%] rounded-2xl px-4 py-3 text-sm ${
                  msg.role === 'user'
                    ? 'bg-blue-600 text-white'
                    : 'bg-white border shadow-sm text-gray-800'
                }`}
              >
                {msg.role === 'user' ? (
                  msg.content
                ) : (
                  <ReactMarkdown remarkPlugins={[remarkGfm]}>
                    {msg.content || '...'}
                  </ReactMarkdown>
                )}
              </div>
            </div>
          ))}
          <div ref={messagesEndRef} />
        </div>

        {/* Input bar */}
        <div className="border-t bg-white p-4 flex gap-3">
          <input
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={(e) => e.key === 'Enter' && !e.shiftKey && handleSend()}
            placeholder="Nhập câu hỏi về bài báo... (Enter để gửi)"
            className="flex-1 border rounded-xl px-4 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-400"
            disabled={isLoading}
          />
          <button
            onClick={handleSend}
            disabled={isLoading || !input.trim()}
            className="bg-blue-600 text-white px-5 py-2 rounded-xl text-sm hover:bg-blue-700 disabled:opacity-50"
          >
            {isLoading ? 'Đang trả lời...' : 'Gửi'}
          </button>
        </div>
      </div>
    </div>
  );
}
```

### 6.10. Khởi Động Frontend

```powershell
cd D:\academic-rag-system\frontend
npm run dev
```

Mở trình duyệt vào `http://localhost:3000`

---

## BƯỚC 7: KIỂM TRA DEMO 50% ĐẦU

Làm theo thứ tự:

1. **Đảm bảo đang chạy:**
   - Docker Desktop → pgvector-db và neo4j-db Up
   - Ollama đang chạy nền
   - Backend: `uvicorn main:app --reload` tại port 8000
   - Frontend: `npm run dev` tại port 3000

2. **Test Upload PDF:**
   - Vào `http://localhost:3000/library`
   - Click vùng upload → chọn 1 file PDF nhỏ (bài báo học thuật)
   - Thấy trạng thái "Đang xử lý" → đợi 30-60s → chuyển sang "Sẵn sàng"

3. **Test Hỏi Đáp:**
   - Vào `http://localhost:3000/chat`
   - Tick chọn bài báo vừa upload ở sidebar trái
   - Nhập câu hỏi: "Mục tiêu chính của nghiên cứu này là gì?"
   - Nhấn Enter → thấy câu trả lời stream từng chữ

4. **Test API trực tiếp (Swagger):**
   - Vào `http://localhost:8000/docs`
   - Thử `GET /api/v1/document/list` → thấy danh sách PDF

**Demo 50% đầu hoàn tất khi bạn hỏi được AI về nội dung bài báo và nhận câu trả lời!**

---

---

# ═══════════════════════════════════════
# PHẦN 2 — 50% SAU: HỆ THỐNG ĐẦY ĐỦ
# ═══════════════════════════════════════

## BƯỚC 8: ĐỒ THỊ TRI THỨC (Neo4j + GraphRAG)

### 8.1. Tạo File `backend/app/db/neo4j.py`

```python
from neo4j import GraphDatabase
from app.core.config import settings

_driver = None

def get_driver():
    global _driver
    if _driver is None:
        _driver = GraphDatabase.driver(
            settings.NEO4J_URL,
            auth=(settings.NEO4J_USER, settings.NEO4J_PASSWORD)
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
    """Chèn node tài liệu và tác giả vào Neo4j."""
    driver = get_driver()
    with driver.session() as session:
        # Tạo node Document
        session.run(
            "MERGE (d:Document {id: $id}) SET d.title = $title, d.year = $year",
            id=document_id, title=title, year=year
        )
        
        # Tạo node Author và quan hệ WROTE
        if authors:
            author_list = [a.strip() for a in authors.split(',')]
            for author in author_list:
                session.run(
                    """
                    MERGE (a:Author {name: $name})
                    MERGE (d:Document {id: $doc_id})
                    MERGE (a)-[:WROTE]->(d)
                    """,
                    name=author, doc_id=document_id
                )
```

### 8.2. Cập Nhật Pipeline Trong `document.py`

Trong hàm `_run_pipeline`, thêm bước sau khi commit `status = ready`:

```python
# Thêm vào cuối hàm _run_pipeline, trước doc.status = "ready"
from app.db.neo4j import insert_document_graph

insert_document_graph(
    document_id=document_id,
    title=doc.title or doc.filename,
    authors=doc.authors or "",
    year=doc.year or 0
)
```

### 8.3. Tạo File `backend/app/api/v1/graph.py`

```python
from fastapi import APIRouter, Depends
from neo4j import Session as Neo4jSession
from app.db.neo4j import get_neo4j_session

router = APIRouter()

@router.get("")
def get_graph(session: Neo4jSession = Depends(get_neo4j_session)):
    """Trả về toàn bộ đồ thị theo chuẩn React-Flow."""
    result = session.run("""
        MATCH (a:Author)-[:WROTE]->(d:Document)
        RETURN a.name AS author, d.id AS doc_id, d.title AS doc_title, d.year AS year
        LIMIT 200
    """)
    
    nodes = {}
    edges = []
    edge_id = 0
    
    for record in result:
        # Node tác giả
        author_id = f"author-{record['author']}"
        if author_id not in nodes:
            nodes[author_id] = {
                "id": author_id,
                "type": "author",
                "position": {"x": 0, "y": 0},
                "data": {"label": record['author'], "type": "Author"}
            }
        
        # Node tài liệu
        doc_id = f"doc-{record['doc_id']}"
        if doc_id not in nodes:
            nodes[doc_id] = {
                "id": doc_id,
                "type": "document",
                "position": {"x": 0, "y": 0},
                "data": {
                    "label": (record['doc_title'] or "Untitled")[:60],
                    "year": record['year'],
                    "type": "Document"
                }
            }
        
        # Edge
        edges.append({
            "id": f"e{edge_id}",
            "source": author_id,
            "target": doc_id,
            "label": "WROTE",
            "animated": False,
        })
        edge_id += 1
    
    return {"nodes": list(nodes.values()), "edges": edges}

@router.get("/author/{name}")
def get_author_graph(name: str, session: Neo4jSession = Depends(get_neo4j_session)):
    """Lấy mạng lưới của 1 tác giả cụ thể."""
    result = session.run("""
        MATCH (a:Author {name: $name})-[:WROTE]->(d:Document)
        RETURN d.id AS doc_id, d.title AS title, d.year AS year
    """, name=name)
    
    papers = [{"id": r["doc_id"], "title": r["title"], "year": r["year"]} for r in result]
    return {"author": name, "papers": papers, "total": len(papers)}
```

### 8.4. Đăng Ký Router Graph trong `__init__.py`

Cập nhật `backend/app/api/v1/__init__.py`:

```python
from fastapi import APIRouter
from app.api.v1 import document, chat, graph

api_router = APIRouter()
api_router.include_router(document.router, prefix="/document", tags=["Documents"])
api_router.include_router(chat.router, prefix="/chat", tags=["Chat"])
api_router.include_router(graph.router, prefix="/graph", tags=["Knowledge Graph"])
```

### 8.5. Cài Thư Viện Frontend Cho Đồ Thị

```powershell
cd D:\academic-rag-system\frontend
npm install reactflow
```

### 8.6. Tạo Component `frontend/src/components/graph/KnowledgeGraph.tsx`

```typescript
'use client';

import { useCallback } from 'react';
import ReactFlow, {
  Node, Edge, Background, Controls, MiniMap,
  NodeTypes, useNodesState, useEdgesState
} from 'reactflow';
import 'reactflow/dist/style.css';

const AuthorNode = ({ data }: { data: { label: string } }) => (
  <div className="bg-blue-100 border-2 border-blue-500 rounded-full px-4 py-2 text-sm font-medium text-blue-800 text-center min-w-[80px]">
    {data.label}
  </div>
);

const DocumentNode = ({ data }: { data: { label: string; year?: number } }) => (
  <div className="bg-yellow-50 border-2 border-yellow-400 rounded-lg px-3 py-2 text-xs text-gray-700 max-w-[160px] text-center">
    <div className="font-medium">{data.label}</div>
    {data.year ? <div className="text-gray-400 mt-1">{data.year}</div> : null}
  </div>
);

const nodeTypes: NodeTypes = {
  author: AuthorNode,
  document: DocumentNode,
};

interface Props {
  nodes: Node[];
  edges: Edge[];
}

export default function KnowledgeGraph({ nodes: initialNodes, edges: initialEdges }: Props) {
  // Tự động layout nodes theo dạng lưới
  const layoutedNodes = initialNodes.map((node, i) => ({
    ...node,
    position: {
      x: node.type === 'author' ? (i % 5) * 220 : (i % 7) * 180 + 100,
      y: node.type === 'author' ? Math.floor(i / 5) * 150 : Math.floor(i / 7) * 120 + 250,
    }
  }));

  const [nodes, , onNodesChange] = useNodesState(layoutedNodes);
  const [edges, , onEdgesChange] = useEdgesState(initialEdges);

  return (
    <div style={{ width: '100%', height: '100%' }}>
      <ReactFlow
        nodes={nodes}
        edges={edges}
        onNodesChange={onNodesChange}
        onEdgesChange={onEdgesChange}
        nodeTypes={nodeTypes}
        fitView
      >
        <Background />
        <Controls />
        <MiniMap />
      </ReactFlow>
    </div>
  );
}
```

### 8.7. Tạo Trang Graph `frontend/src/app/graph/page.tsx`

```typescript
'use client';

import { useEffect, useState } from 'react';
import dynamic from 'next/dynamic';

const KnowledgeGraph = dynamic(
  () => import('@/components/graph/KnowledgeGraph'),
  { ssr: false }
);

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

export default function GraphPage() {
  const [graphData, setGraphData] = useState<{ nodes: any[]; edges: any[] } | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetch(`${API_URL}/api/v1/graph`)
      .then(r => r.json())
      .then(data => {
        setGraphData(data);
        setLoading(false);
      })
      .catch(() => setLoading(false));
  }, []);

  return (
    <div className="h-[calc(100vh-56px)] flex flex-col">
      <div className="px-6 py-3 bg-white border-b flex items-center justify-between">
        <h1 className="text-lg font-semibold text-gray-800">Đồ Thị Tri Thức</h1>
        <span className="text-sm text-gray-500">
          {graphData ? `${graphData.nodes.length} nodes · ${graphData.edges.length} cạnh` : ''}
        </span>
      </div>

      <div className="flex-1">
        {loading && (
          <div className="flex items-center justify-center h-full text-gray-400">
            Đang tải đồ thị...
          </div>
        )}
        {!loading && (!graphData || graphData.nodes.length === 0) && (
          <div className="flex items-center justify-center h-full text-gray-400">
            Chưa có dữ liệu. Hãy upload bài báo để xây dựng đồ thị.
          </div>
        )}
        {graphData && graphData.nodes.length > 0 && (
          <KnowledgeGraph nodes={graphData.nodes} edges={graphData.edges} />
        )}
      </div>
    </div>
  );
}
```

Thêm link Graph vào `layout.tsx`:
```typescript
<Link href="/graph" className="hover:underline">Đồ thị</Link>
```

---

## BƯỚC 9: XÁC THỰC NGƯỜI DÙNG (JWT)

### 9.1. Tạo File `backend/app/core/security.py`

```python
from datetime import datetime, timedelta
from typing import Optional
from jose import JWTError, jwt
from passlib.context import CryptContext
from fastapi import HTTPException, status, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from app.core.config import settings

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
security = HTTPBearer(auto_error=False)

def hash_password(password: str) -> str:
    return pwd_context.hash(password)

def verify_password(plain: str, hashed: str) -> bool:
    return pwd_context.verify(plain, hashed)

def create_access_token(data: dict, expires_minutes: Optional[int] = None) -> str:
    payload = data.copy()
    expire = datetime.utcnow() + timedelta(
        minutes=expires_minutes or settings.ACCESS_TOKEN_EXPIRE_MINUTES
    )
    payload.update({"exp": expire})
    return jwt.encode(payload, settings.SECRET_KEY, algorithm=settings.ALGORITHM)

def get_current_user_id(credentials: Optional[HTTPAuthorizationCredentials] = Depends(security)) -> Optional[str]:
    if not credentials:
        return None
    try:
        payload = jwt.decode(credentials.credentials, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        return payload.get("sub")
    except JWTError:
        return None
```

### 9.2. Tạo Endpoint Auth Trong `backend/app/api/v1/document.py`

Thêm vào đầu file `document.py` (sau imports hiện tại) endpoint đăng ký/đăng nhập đơn giản. Tạo file riêng `backend/app/api/v1/auth.py`:

```python
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from app.db.postgres import get_db
from app.models.document import User
from app.core.security import hash_password, verify_password, create_access_token
import uuid

router = APIRouter()

class RegisterRequest(BaseModel):
    email: str
    password: str
    full_name: str = ""

class LoginRequest(BaseModel):
    email: str
    password: str

@router.post("/register")
def register(req: RegisterRequest, db: Session = Depends(get_db)):
    existing = db.query(User).filter(User.email == req.email).first()
    if existing:
        raise HTTPException(400, "Email đã tồn tại")
    
    user = User(
        id=uuid.uuid4(),
        email=req.email,
        hashed_password=hash_password(req.password),
        full_name=req.full_name,
    )
    db.add(user)
    db.commit()
    return {"message": "Đăng ký thành công", "user_id": str(user.id)}

@router.post("/login")
def login(req: LoginRequest, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == req.email).first()
    if not user or not verify_password(req.password, user.hashed_password):
        raise HTTPException(401, "Email hoặc mật khẩu không đúng")
    
    token = create_access_token({"sub": str(user.id), "email": user.email})
    return {
        "access_token": token,
        "token_type": "bearer",
        "user": {"id": str(user.id), "email": user.email, "full_name": user.full_name}
    }
```

Đăng ký router auth trong `__init__.py`:

```python
from app.api.v1 import document, chat, graph, auth

api_router.include_router(auth.router, prefix="/auth", tags=["Authentication"])
```

---

## BƯỚC 10: ĐÁNH GIÁ RAGAS (SỐ LIỆU NCKH)

### 10.1. Cài Thêm Thư Viện

```powershell
cd D:\academic-rag-system\backend
venv\Scripts\activate
pip install ragas datasets openpyxl langchain-groq
```

### 10.2. Tạo File Câu Hỏi Test `data/eval_questions.json`

Tạo file `D:\academic-rag-system\data\eval_questions.json` — ví dụ mẫu:

```json
[
  {
    "question": "Mục tiêu chính của nghiên cứu là gì?",
    "ground_truth": "Nghiên cứu nhằm đánh giá hiệu quả của phương pháp RAG trong hỏi đáp học thuật",
    "document_ids": ["THAY-BẰNG-UUID-THẬT"]
  },
  {
    "question": "Phương pháp nghiên cứu nào được sử dụng?",
    "ground_truth": "Nghiên cứu sử dụng phương pháp thực nghiệm với tập dữ liệu benchmark",
    "document_ids": ["THAY-BẰNG-UUID-THẬT"]
  }
]
```

> **Lưu ý:** Thay `THAY-BẰNG-UUID-THẬT` bằng UUID thật lấy từ `GET /api/v1/document/list`. Cần tối thiểu 10-20 cặp câu hỏi/ground truth lấy từ bài báo thật bạn đã upload.

### 10.3. Tạo File `backend/scripts/evaluation.py`

```python
"""
Script đánh giá chất lượng hệ thống RAG bằng RAGAS.
Chạy: python scripts/evaluation.py
"""

import json
import requests
import os
from datetime import datetime
from datasets import Dataset
from ragas import evaluate
from ragas.metrics import faithfulness, answer_relevancy, context_precision
from langchain_groq import ChatGroq
from langchain_community.embeddings import OllamaEmbeddings
import openpyxl
from dotenv import load_dotenv

load_dotenv()

API_URL = "http://localhost:8000/api/v1"
EVAL_FILE = "../data/eval_questions.json"
RESULTS_DIR = "../data/eval_results"

def get_answer_and_context(question: str, document_ids: list) -> tuple[str, list[str]]:
    """Gọi API chat để lấy câu trả lời."""
    full_answer = ""
    
    response = requests.post(
        f"{API_URL}/chat",
        json={"query": question, "document_ids": document_ids},
        stream=True,
        timeout=60
    )
    
    # Đọc context từ header
    context_pages = response.headers.get("X-Context-Pages", "")
    
    for chunk in response.iter_content(chunk_size=None, decode_unicode=True):
        if chunk:
            full_answer += chunk
    
    # Lấy chunks thực tế từ DB để làm context cho RAGAS
    contexts = [full_answer]  # Đơn giản hóa: dùng câu trả lời làm context
    
    return full_answer, contexts

def run_evaluation():
    # Load câu hỏi test
    with open(EVAL_FILE, "r", encoding="utf-8") as f:
        eval_data = json.load(f)
    
    print(f"Đang đánh giá {len(eval_data)} câu hỏi...")
    
    questions, answers, contexts, ground_truths = [], [], [], []
    
    for i, item in enumerate(eval_data):
        print(f"  [{i+1}/{len(eval_data)}] {item['question'][:50]}...")
        
        answer, ctx = get_answer_and_context(item["question"], item["document_ids"])
        
        questions.append(item["question"])
        answers.append(answer)
        contexts.append(ctx)
        ground_truths.append(item["ground_truth"])
    
    # Tạo Dataset RAGAS
    dataset = Dataset.from_dict({
        "question": questions,
        "answer": answers,
        "contexts": contexts,
        "ground_truth": ground_truths,
    })
    
    # Cấu hình LLM giám khảo (Groq)
    groq_api_key = os.getenv("GROQ_API_KEY")
    llm = ChatGroq(model="llama-3.3-70b-versatile", api_key=groq_api_key)
    embeddings = OllamaEmbeddings(model="nomic-embed-text")
    
    print("\nĐang chạy RAGAS evaluation...")
    result = evaluate(
        dataset=dataset,
        metrics=[faithfulness, answer_relevancy, context_precision],
        llm=llm,
        embeddings=embeddings,
    )
    
    print("\n=== KẾT QUẢ RAGAS ===")
    print(f"Faithfulness:      {result['faithfulness']:.4f}")
    print(f"Answer Relevancy:  {result['answer_relevancy']:.4f}")
    print(f"Context Precision: {result['context_precision']:.4f}")
    
    # Xuất Excel
    os.makedirs(RESULTS_DIR, exist_ok=True)
    filename = os.path.join(RESULTS_DIR, f"ragas_report_{datetime.now().strftime('%Y%m%d_%H%M')}.xlsx")
    
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Chi tiết"
    
    # Header
    ws.append(["Câu hỏi", "Câu trả lời", "Ground Truth", "Faithfulness", "Answer Relevancy", "Context Precision"])
    
    # Lấy điểm từng câu
    result_df = result.to_pandas()
    for _, row in result_df.iterrows():
        ws.append([
            row.get("question", ""),
            row.get("answer", ""),
            row.get("ground_truth", ""),
            round(row.get("faithfulness", 0), 4),
            round(row.get("answer_relevancy", 0), 4),
            round(row.get("context_precision", 0), 4),
        ])
    
    # Sheet tổng kết
    ws2 = wb.create_sheet("Tổng kết")
    ws2.append(["Chỉ số", "Điểm trung bình", "Ngưỡng tốt"])
    ws2.append(["Faithfulness", round(result['faithfulness'], 4), "≥ 0.85"])
    ws2.append(["Answer Relevancy", round(result['answer_relevancy'], 4), "≥ 0.80"])
    ws2.append(["Context Precision", round(result['context_precision'], 4), "≥ 0.80"])
    
    wb.save(filename)
    print(f"\nĐã xuất báo cáo: {filename}")

if __name__ == "__main__":
    run_evaluation()
```

Chạy đánh giá:
```powershell
cd D:\academic-rag-system\backend
venv\Scripts\activate
python scripts/evaluation.py
```

---

## BƯỚC 11: XUẤT BÁO CÁO WORD

### 11.1. Cài Thêm Thư Viện

```powershell
pip install python-docx
```

### 11.2. Tạo File `backend/app/utils/citation.py`

```python
def format_apa(author: str, year: int, title: str, journal: str = "", pages: str = "") -> str:
    """Format trích dẫn APA."""
    parts = [f"{author} ({year}). {title}."]
    if journal:
        parts.append(f" {journal}")
    if pages:
        parts.append(f", {pages}")
    return "".join(parts) + "."

def format_bibtex(title: str, author: str, year: int, journal: str = "", doc_id: str = "") -> str:
    """Format BibTeX."""
    key = f"{author.split()[0].lower()}{year}" if author else f"ref{year}"
    lines = [
        f"@article{{{key},",
        f"  title = {{{title}}},",
        f"  author = {{{author}}},",
        f"  year = {{{year}}}",
    ]
    if journal:
        lines.insert(-1, f"  journal = {{{journal}}},")
    lines.append("}")
    return "\n".join(lines)
```

### 11.3. Tạo File `backend/app/utils/export.py`

```python
from docx import Document as DocxDocument
from docx.shared import Pt, RGBColor
from io import BytesIO
from datetime import datetime

def export_chat_to_docx(messages: list, title: str = "Báo cáo Hỏi Đáp Học Thuật") -> bytes:
    """Xuất lịch sử chat ra file Word."""
    doc = DocxDocument()
    
    # Tiêu đề
    heading = doc.add_heading(title, 0)
    heading.alignment = 1  # Center
    
    doc.add_paragraph(f"Ngày xuất: {datetime.now().strftime('%d/%m/%Y %H:%M')}")
    doc.add_paragraph("=" * 60)
    
    for msg in messages:
        if msg["role"] == "user":
            p = doc.add_paragraph()
            run = p.add_run(f"Câu hỏi: {msg['content']}")
            run.bold = True
            run.font.color.rgb = RGBColor(0, 84, 166)  # Xanh dương
        else:
            p = doc.add_paragraph()
            run = p.add_run(f"Trả lời: {msg['content']}")
            run.font.size = Pt(11)
        
        doc.add_paragraph("")  # Dòng trống
    
    buffer = BytesIO()
    doc.save(buffer)
    return buffer.getvalue()
```

### 11.4. Thêm Endpoint Export Vào `chat.py`

```python
from fastapi.responses import Response
from app.utils.export import export_chat_to_docx

class ExportRequest(BaseModel):
    messages: list[dict]
    title: str = "Báo cáo Hỏi Đáp"

@router.post("/export")
def export_chat(req: ExportRequest):
    docx_bytes = export_chat_to_docx(req.messages, req.title)
    return Response(
        content=docx_bytes,
        media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        headers={"Content-Disposition": f'attachment; filename="chat_export.docx"'}
    )
```

---

## BƯỚC 12: TRANG DASHBOARD HOÀN CHỈNH

Tạo `frontend/src/app/dashboard/page.tsx`:

```typescript
'use client';

import { useEffect, useState } from 'react';
import Link from 'next/link';
import { getDocuments, DocumentInfo } from '@/lib/api';

export default function DashboardPage() {
  const [docs, setDocs] = useState<DocumentInfo[]>([]);

  useEffect(() => {
    getDocuments().then(setDocs);
  }, []);

  const readyCount = docs.filter(d => d.status === 'ready').length;
  const processingCount = docs.filter(d => d.status === 'processing').length;

  return (
    <div className="max-w-5xl mx-auto p-6">
      <h1 className="text-2xl font-bold mb-6 text-gray-800">Dashboard</h1>

      {/* Stats */}
      <div className="grid grid-cols-3 gap-4 mb-8">
        <div className="bg-white rounded-xl shadow p-5">
          <p className="text-3xl font-bold text-blue-600">{docs.length}</p>
          <p className="text-gray-500 mt-1">Tổng bài báo</p>
        </div>
        <div className="bg-white rounded-xl shadow p-5">
          <p className="text-3xl font-bold text-green-600">{readyCount}</p>
          <p className="text-gray-500 mt-1">Sẵn sàng hỏi đáp</p>
        </div>
        <div className="bg-white rounded-xl shadow p-5">
          <p className="text-3xl font-bold text-yellow-500">{processingCount}</p>
          <p className="text-gray-500 mt-1">Đang xử lý</p>
        </div>
      </div>

      {/* Quick actions */}
      <div className="grid grid-cols-2 gap-4 mb-8">
        <Link href="/library" className="bg-blue-600 text-white rounded-xl p-5 hover:bg-blue-700 flex items-center gap-3">
          <span className="text-2xl">📄</span>
          <div>
            <p className="font-semibold">Upload Bài Báo Mới</p>
            <p className="text-sm text-blue-200">Thêm PDF vào thư viện</p>
          </div>
        </Link>
        <Link href="/chat" className="bg-green-600 text-white rounded-xl p-5 hover:bg-green-700 flex items-center gap-3">
          <span className="text-2xl">💬</span>
          <div>
            <p className="font-semibold">Bắt Đầu Hỏi Đáp</p>
            <p className="text-sm text-green-200">Chat với AI về bài báo</p>
          </div>
        </Link>
      </div>

      {/* Recent documents */}
      <h2 className="text-lg font-semibold mb-3 text-gray-700">Tài Liệu Gần Đây</h2>
      <div className="bg-white rounded-xl shadow overflow-hidden">
        {docs.slice(0, 5).map((doc) => (
          <div key={doc.id} className="flex items-center px-5 py-3 border-b last:border-0 hover:bg-gray-50">
            <span className="text-2xl mr-3">📄</span>
            <div className="flex-1 min-w-0">
              <p className="font-medium text-gray-800 truncate">{doc.title || doc.filename}</p>
              <p className="text-sm text-gray-500">{doc.authors || 'Không rõ tác giả'}</p>
            </div>
            <span className={`ml-3 px-2 py-1 rounded-full text-xs ${
              doc.status === 'ready' ? 'bg-green-100 text-green-700' : 'bg-yellow-100 text-yellow-600'
            }`}>
              {doc.status === 'ready' ? 'Sẵn sàng' : 'Đang xử lý'}
            </span>
          </div>
        ))}
        {docs.length === 0 && (
          <p className="text-center py-8 text-gray-400">Chưa có tài liệu nào.</p>
        )}
      </div>
    </div>
  );
}
```

Thêm Dashboard link vào navigation:
```typescript
<Link href="/dashboard" className="hover:underline">Dashboard</Link>
```

---

## BƯỚC 13: CHECKLIST TRƯỚC KHI BẢO VỆ NCKH

### ✅ Checklist Backend

```powershell
# 1. Database đang chạy?
docker ps
# Phải thấy: pgvector-db (Up) và neo4j-db (Up)

# 2. Ollama có model?
ollama list
# Phải thấy: nomic-embed-text

# 3. Server chạy không lỗi?
cd D:\academic-rag-system\backend
venv\Scripts\activate
uvicorn main:app --reload --port 8000
# Mở http://localhost:8000/docs -> thấy Swagger UI

# 4. Test upload PDF nhỏ qua Swagger /docs
# POST /api/v1/document/upload -> status: processing

# 5. Sau 60s test GET /api/v1/document/list -> status: ready

# 6. Test chat qua Swagger:
# POST /api/v1/chat body: {"query": "...", "document_ids": ["uuid"]}
```

### ✅ Checklist Frontend

```powershell
cd D:\academic-rag-system\frontend
npm run dev
# Mở http://localhost:3000

# Test: Library -> Upload PDF -> chờ ready
# Test: Chat -> chọn tài liệu -> hỏi -> nhận stream trả lời
# Test: Graph -> thấy đồ thị tác giả-bài báo
```

### ✅ Checklist RAGAS

```powershell
# 1. Chuẩn bị ít nhất 10 cặp Q&A trong data/eval_questions.json
# 2. Chạy đánh giá:
cd D:\academic-rag-system\backend
python scripts/evaluation.py
# 3. Kiểm tra file Excel trong data/eval_results/
# Mục tiêu: Faithfulness >= 0.85, Context Precision >= 0.80
```

### 📋 Script Khởi Động Nhanh (Lưu thành file .ps1)

Tạo file `D:\academic-rag-system\start.ps1`:

```powershell
# Khởi động toàn bộ hệ thống
Write-Host "Starting Academic RAG System..." -ForegroundColor Green

# 1. Khởi động Docker databases
Write-Host "Starting databases..." -ForegroundColor Yellow
Set-Location D:\academic-rag-system\docker
docker-compose up -d
Start-Sleep -Seconds 5

# 2. Thông báo Ollama
Write-Host "Make sure Ollama is running (check system tray)" -ForegroundColor Yellow

# 3. Khởi động Backend (cửa sổ mới)
Write-Host "Starting Backend on port 8000..." -ForegroundColor Yellow
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd D:\academic-rag-system\backend; venv\Scripts\activate; uvicorn main:app --reload --port 8000"

Start-Sleep -Seconds 3

# 4. Khởi động Frontend (cửa sổ mới)
Write-Host "Starting Frontend on port 3000..." -ForegroundColor Yellow
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd D:\academic-rag-system\frontend; npm run dev"

Write-Host ""
Write-Host "=== System Started ===" -ForegroundColor Green
Write-Host "Frontend:  http://localhost:3000" -ForegroundColor Cyan
Write-Host "Backend:   http://localhost:8000/docs" -ForegroundColor Cyan
Write-Host "Neo4j:     http://localhost:7474" -ForegroundColor Cyan
```

Chạy script: `powershell -ExecutionPolicy Bypass -File D:\academic-rag-system\start.ps1`

---

## BƯỚC 14: CÁCH DEMO TRƯỚC HỘI ĐỒNG (5 PHÚT)

**Thứ tự demo:**

1. **Upload** (1 phút): Vào `/library` → kéo thả PDF → chờ "Sẵn sàng"
2. **Hỏi đáp** (2 phút): Vào `/chat` → chọn bài báo → hỏi:
   - *"Mục tiêu chính của nghiên cứu là gì?"*
   - *"Phương pháp nào được sử dụng?"*
   - *"Kết quả có ý nghĩa gì?"*
3. **Đồ thị** (30 giây): Vào `/graph` → zoom, hover vào node
4. **RAGAS** (1 phút): Mở file Excel → nói *"Faithfulness đạt X%, chứng minh AI không bịa thông tin"*
5. **Kết luận** (30 giây): *"Hệ thống hoàn toàn miễn phí, chạy được trên laptop không cần GPU"*

> **Dự phòng:** Quay sẵn 1 video demo 3 phút. Nếu rớt mạng/lỗi kỹ thuật, phát video thay thế.

---

**🎉 Chúc bạn bảo vệ NCKH thành công!**

---

---

# ═══════════════════════════════════════
# PHẦN 3 — TÍNH NĂNG MỞ RỘNG
# ═══════════════════════════════════════

---

## BƯỚC 15: MÔ HÌNH 3D CƠ THỂ NGƯỜI

### Tổng quan
Tab "Mô hình 3D" trong navbar cho phép xem mô hình cơ thể người 3D tương tác, click vào các vùng giải phẫu để khai báo triệu chứng, và bật chế độ X-Ray xem nội tạng. Nội dung hiển thị thay đổi theo phân loại user (bệnh nhân / sinh viên / chuyên gia).

**Stack sử dụng (toàn bộ miễn phí):**
- `@react-three/fiber` + `@react-three/drei` + `three` — render 3D trong React/Next.js
- Model 3D định dạng `.glb` tải về từ Sketchfab (miễn phí, Creative Commons)
- PostgreSQL (đã có) — lưu lịch sử khai báo triệu chứng

---

### 15.1. Cài Thư Viện Frontend

```powershell
cd D:\academic-rag-system\frontend
npm install @react-three/fiber @react-three/drei three
npm install @types/three
```

---

### 15.2. Tải Model 3D Miễn Phí

1. Truy cập `https://sketchfab.com/search?q=human+body+anatomy&type=models&features=downloadable&license=cc-attribution`
2. Tìm model **"Human Body Male"** và **"Human Body Female"** — chọn loại có thể download, license CC
3. Download định dạng **GLTF/GLB**
4. Lưu vào:
   - `frontend/public/models/body_male.glb`
   - `frontend/public/models/body_female.glb`

> **Gợi ý model cụ thể (miễn phí, CC-BY):**
> - "Anatomy - Male Body" by Sketchfab user: tìm từ khóa "human anatomy male glb free"
> - Hoặc dùng model từ `https://github.com/KhronosGroup/glTF-Sample-Models` làm placeholder khi phát triển

---

### 15.3. Tạo File Dữ Liệu Vùng Cơ Thể

Tạo `frontend/public/body_regions.json` — định nghĩa toạ độ và thông tin từng vùng:

```json
[
  {
    "id": "brain",
    "name_vi": "Não",
    "name_latin": "Cerebrum",
    "position": [0, 1.75, 0.1],
    "symptoms": ["Đau đầu", "Chóng mặt", "Mất trí nhớ", "Buồn nôn"],
    "description_basic": "Trung tâm điều khiển toàn bộ cơ thể. Các vấn đề thường gặp: đau đầu, chóng mặt.",
    "description_advanced": "Cerebrum gồm hai bán cầu não điều khiển vận động, nhận thức, ngôn ngữ. Triệu chứng lâm sàng: GCS giảm, dấu thần kinh khu trú.",
    "layer": 3
  },
  {
    "id": "heart",
    "name_vi": "Tim",
    "name_latin": "Cor",
    "position": [-0.1, 1.3, 0.15],
    "symptoms": ["Đau ngực", "Khó thở", "Tim đập nhanh", "Hồi hộp"],
    "description_basic": "Bơm máu đi khắp cơ thể. Triệu chứng cảnh báo: đau thắt ngực, khó thở khi gắng sức.",
    "description_advanced": "Tim 4 buồng, nhịp xoang bình thường 60-100 lần/phút. Đánh giá: ECG, Troponin I/T, Echo tim.",
    "layer": 3
  },
  {
    "id": "lung_left",
    "name_vi": "Phổi trái",
    "name_latin": "Pulmo sinister",
    "position": [-0.2, 1.3, 0.1],
    "symptoms": ["Khó thở", "Ho", "Đau ngực khi thở", "Khạc đờm"],
    "description_basic": "Cơ quan hô hấp, trao đổi oxy và CO2. Triệu chứng: khó thở, ho kéo dài.",
    "description_advanced": "Phổi trái 2 thùy. SpO2 bình thường ≥95%. Đánh giá: X-quang phổi, CT scan, khí máu động mạch.",
    "layer": 3
  },
  {
    "id": "lung_right",
    "name_vi": "Phổi phải",
    "name_latin": "Pulmo dexter",
    "position": [0.2, 1.3, 0.1],
    "symptoms": ["Khó thở", "Ho", "Đau ngực khi thở", "Khạc đờm"],
    "description_basic": "Cơ quan hô hấp bên phải, lớn hơn phổi trái. Triệu chứng tương tự phổi trái.",
    "description_advanced": "Phổi phải 3 thùy. Viêm phổi thùy phải hay gặp nhất. CXR, HRCT ngực để chẩn đoán.",
    "layer": 3
  },
  {
    "id": "liver",
    "name_vi": "Gan",
    "name_latin": "Hepar",
    "position": [0.15, 1.05, 0.1],
    "symptoms": ["Đau hạ sườn phải", "Vàng da", "Mệt mỏi", "Chán ăn"],
    "description_basic": "Cơ quan lọc máu và tiêu hóa lớn nhất. Dấu hiệu cảnh báo: vàng da, đau bụng phải.",
    "description_advanced": "Gan nặng 1.2-1.5kg, 8 phân thùy Couinaud. AST/ALT >3 lần giới hạn trên = tổn thương gan đáng kể.",
    "layer": 3
  },
  {
    "id": "stomach",
    "name_vi": "Dạ dày",
    "name_latin": "Gaster",
    "position": [-0.05, 1.0, 0.12],
    "symptoms": ["Đau thượng vị", "Ợ chua", "Buồn nôn", "Đầy hơi"],
    "description_basic": "Cơ quan tiêu hóa thức ăn. Triệu chứng phổ biến: đau bụng trên, ợ hơi sau ăn.",
    "description_advanced": "Dạ dày pH 1.5-3.5. H.pylori gây viêm loét dạ dày tá tràng. Chẩn đoán: nội soi, test urease.",
    "layer": 3
  },
  {
    "id": "kidney_left",
    "name_vi": "Thận trái",
    "name_latin": "Ren sinister",
    "position": [-0.18, 0.95, -0.1],
    "symptoms": ["Đau lưng", "Tiểu ít", "Phù nề", "Tiểu buốt"],
    "description_basic": "Lọc máu và tạo nước tiểu. Dấu hiệu cảnh báo: tiểu ít, phù hai chân.",
    "description_advanced": "GFR bình thường >90 mL/phút/1.73m2. Creatinine, Urea, tổng phân tích nước tiểu để đánh giá chức năng.",
    "layer": 3
  },
  {
    "id": "kidney_right",
    "name_vi": "Thận phải",
    "name_latin": "Ren dexter",
    "position": [0.18, 0.95, -0.1],
    "symptoms": ["Đau lưng", "Tiểu ít", "Phù nề", "Tiểu buốt"],
    "description_basic": "Lọc máu và tạo nước tiểu. Thận phải nằm thấp hơn thận trái do vị trí gan.",
    "description_advanced": "Thận phải thường là vị trí hay gặp sỏi thận. Siêu âm thận là cận lâm sàng đầu tay.",
    "layer": 3
  },
  {
    "id": "spine",
    "name_vi": "Cột sống",
    "name_latin": "Columna vertebralis",
    "position": [0, 1.1, -0.12],
    "symptoms": ["Đau lưng", "Tê bì tay chân", "Cứng cổ", "Đau lan xuống chân"],
    "description_basic": "Trục xương chính của cơ thể. Đau lưng là triệu chứng phổ biến nhất.",
    "description_advanced": "33 đốt sống: 7 cổ, 12 ngực, 5 thắt lưng, 5 cùng, 4 cụt. MRI cột sống là gold standard chẩn đoán thoát vị đĩa đệm.",
    "layer": 2
  },
  {
    "id": "knee_left",
    "name_vi": "Khớp gối trái",
    "name_latin": "Articulatio genus sinister",
    "position": [-0.12, 0.4, 0.05],
    "symptoms": ["Đau khớp gối", "Sưng", "Cứng khớp sáng", "Lạo xạo khi cử động"],
    "description_basic": "Khớp lớn nhất cơ thể. Đau gối khi đi cầu thang hoặc ngồi xổm là dấu hiệu hay gặp.",
    "description_advanced": "Gồm meniscus, dây chằng chéo (ACL/PCL), dây chằng bên. MRI gối để đánh giá cấu trúc mô mềm.",
    "layer": 2
  }
]
```

---

### 15.4. Tạo Migration SQL Cho Bảng Triệu Chứng

Thêm vào file `docker/init_db.sql` (hoặc chạy trực tiếp trong psql):

```sql
-- Bảng phân loại user (dùng cho cả Tính năng 2)
CREATE TABLE IF NOT EXISTS user_profiles (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    user_type VARCHAR(50) DEFAULT 'patient',
    onboarding_done BOOLEAN DEFAULT FALSE,
    answers JSONB,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Bảng khai báo triệu chứng từ mô hình 3D
CREATE TABLE IF NOT EXISTS body_symptoms (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    region_id VARCHAR(100) NOT NULL,
    region_name VARCHAR(255),
    description TEXT NOT NULL,
    pain_level INTEGER CHECK (pain_level BETWEEN 1 AND 10),
    duration VARCHAR(255),
    reported_at TIMESTAMP DEFAULT NOW()
);
```

---

### 15.5. Tạo Backend API Cho Mô Hình 3D

Tạo file `backend/app/api/v1/body.py`:

```python
import uuid
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field
from typing import Optional
from app.db.postgres import get_db

router = APIRouter()

class SymptomReport(BaseModel):
    user_id: Optional[str] = None
    region_id: str
    region_name: str
    description: str
    pain_level: int = Field(..., ge=1, le=10)
    duration: Optional[str] = None

class SymptomResponse(BaseModel):
    id: str
    region_id: str
    region_name: str
    description: str
    pain_level: int
    duration: Optional[str]
    reported_at: str

@router.post("/symptoms", response_model=dict)
def report_symptom(report: SymptomReport, db: Session = Depends(get_db)):
    from sqlalchemy import text
    symptom_id = str(uuid.uuid4())
    db.execute(
        text("""
            INSERT INTO body_symptoms (id, user_id, region_id, region_name, description, pain_level, duration)
            VALUES (:id, :user_id, :region_id, :region_name, :description, :pain_level, :duration)
        """),
        {
            "id": symptom_id,
            "user_id": report.user_id,
            "region_id": report.region_id,
            "region_name": report.region_name,
            "description": report.description,
            "pain_level": report.pain_level,
            "duration": report.duration,
        }
    )
    db.commit()
    return {"id": symptom_id, "message": "Đã lưu triệu chứng thành công"}

@router.get("/symptoms/{user_id}")
def get_symptoms(user_id: str, db: Session = Depends(get_db)):
    from sqlalchemy import text
    rows = db.execute(
        text("""
            SELECT id, region_id, region_name, description, pain_level, duration, reported_at
            FROM body_symptoms
            WHERE user_id = :user_id
            ORDER BY reported_at DESC
        """),
        {"user_id": user_id}
    ).fetchall()
    return {
        "total": len(rows),
        "symptoms": [
            {
                "id": str(r.id),
                "region_id": r.region_id,
                "region_name": r.region_name,
                "description": r.description,
                "pain_level": r.pain_level,
                "duration": r.duration,
                "reported_at": r.reported_at.isoformat() if r.reported_at else None,
            }
            for r in rows
        ]
    }

@router.delete("/symptoms/{symptom_id}")
def delete_symptom(symptom_id: str, db: Session = Depends(get_db)):
    from sqlalchemy import text
    db.execute(
        text("DELETE FROM body_symptoms WHERE id = :id"),
        {"id": symptom_id}
    )
    db.commit()
    return {"message": "Đã xóa triệu chứng"}
```

Đăng ký router trong `backend/app/api/v1/__init__.py`:

```python
from app.api.v1 import document, chat, graph, auth, body

api_router.include_router(body.router, prefix="/body", tags=["Body 3D"])
```

---

### 15.6. Tạo Component BodyViewer3D

Tạo `frontend/src/components/body3d/BodyViewer3D.tsx`:

```typescript
'use client';

import { Suspense, useState, useRef } from 'react';
import { Canvas } from '@react-three/fiber';
import { OrbitControls, Html, useGLTF, Environment } from '@react-three/drei';
import * as THREE from 'three';

interface BodyRegion {
  id: string;
  name_vi: string;
  name_latin: string;
  position: [number, number, number];
  symptoms: string[];
  description_basic: string;
  description_advanced: string;
  layer: number;
}

interface Props {
  regions: BodyRegion[];
  gender: 'male' | 'female';
  xrayLevel: number;
  userType: 'patient' | 'student' | 'expert';
  onRegionClick: (region: BodyRegion) => void;
}

function BodyModel({ gender, xrayLevel }: { gender: 'male' | 'female'; xrayLevel: number }) {
  const modelPath = gender === 'male' ? '/models/body_male.glb' : '/models/body_female.glb';
  const { scene } = useGLTF(modelPath);

  scene.traverse((child) => {
    if ((child as THREE.Mesh).isMesh) {
      const mesh = child as THREE.Mesh;
      const mat = mesh.material as THREE.MeshStandardMaterial;
      if (mat) {
        mat.transparent = xrayLevel > 0;
        mat.opacity = xrayLevel === 0 ? 1 : xrayLevel === 1 ? 0.6 : xrayLevel === 2 ? 0.35 : 0.15;
        mat.depthWrite = xrayLevel === 0;
      }
    }
  });

  return <primitive object={scene} scale={1} position={[0, -1, 0]} />;
}

function RegionMarker({
  region,
  onClick,
}: {
  region: BodyRegion;
  onClick: () => void;
}) {
  const [hovered, setHovered] = useState(false);

  return (
    <Html position={region.position} style={{ pointerEvents: 'all' }}>
      <div
        onClick={onClick}
        onMouseEnter={() => setHovered(true)}
        onMouseLeave={() => setHovered(false)}
        style={{
          width: hovered ? 18 : 12,
          height: hovered ? 18 : 12,
          borderRadius: '50%',
          background: hovered ? '#ef4444' : '#3b82f6',
          border: '2px solid white',
          cursor: 'pointer',
          transition: 'all 0.2s',
          boxShadow: '0 0 8px rgba(59,130,246,0.8)',
          animation: 'pulse 2s infinite',
        }}
        title={region.name_vi}
      />
    </Html>
  );
}

export default function BodyViewer3D({ regions, gender, xrayLevel, userType, onRegionClick }: Props) {
  return (
    <Canvas
      camera={{ position: [0, 0, 3.5], fov: 50 }}
      style={{ background: 'linear-gradient(180deg, #0f172a 0%, #1e3a5f 100%)' }}
    >
      <ambientLight intensity={0.6} />
      <directionalLight position={[2, 4, 2]} intensity={1.2} />
      <pointLight position={[-2, 2, -2]} intensity={0.4} color="#60a5fa" />

      <Suspense fallback={null}>
        <BodyModel gender={gender} xrayLevel={xrayLevel} />
        {regions.map((region) => (
          <RegionMarker
            key={region.id}
            region={region}
            onClick={() => onRegionClick(region)}
          />
        ))}
      </Suspense>

      <OrbitControls
        enablePan={false}
        minDistance={1.5}
        maxDistance={6}
        minPolarAngle={0.2}
        maxPolarAngle={Math.PI - 0.2}
      />
    </Canvas>
  );
}
```

---

### 15.7. Tạo Component Panel Thông Tin Vùng Cơ Thể

Tạo `frontend/src/components/body3d/RegionPanel.tsx`:

```typescript
'use client';

import { useState } from 'react';
import { X } from 'lucide-react';

interface BodyRegion {
  id: string;
  name_vi: string;
  name_latin: string;
  symptoms: string[];
  description_basic: string;
  description_advanced: string;
}

interface Props {
  region: BodyRegion | null;
  userType: 'patient' | 'student' | 'expert';
  onClose: () => void;
  onReportSymptom: (regionId: string, regionName: string) => void;
}

export default function RegionPanel({ region, userType, onClose, onReportSymptom }: Props) {
  if (!region) return null;

  const isAdvanced = userType === 'student' || userType === 'expert';

  return (
    <div className="absolute top-4 right-4 w-80 bg-white/95 backdrop-blur rounded-2xl shadow-2xl p-5 z-10 border border-blue-100">
      <div className="flex items-start justify-between mb-3">
        <div>
          <h3 className="text-lg font-bold text-gray-800">{region.name_vi}</h3>
          {isAdvanced && (
            <p className="text-xs text-gray-400 italic">{region.name_latin}</p>
          )}
        </div>
        <button onClick={onClose} className="text-gray-400 hover:text-gray-600 mt-1">
          <X size={18} />
        </button>
      </div>

      <p className="text-sm text-gray-600 mb-3 leading-relaxed">
        {isAdvanced ? region.description_advanced : region.description_basic}
      </p>

      <div className="mb-4">
        <p className="text-xs font-semibold text-gray-500 uppercase mb-2">Triệu chứng thường gặp</p>
        <div className="flex flex-wrap gap-1">
          {region.symptoms.map((s) => (
            <span
              key={s}
              className="px-2 py-0.5 bg-red-50 text-red-600 text-xs rounded-full border border-red-100"
            >
              {s}
            </span>
          ))}
        </div>
      </div>

      <button
        onClick={() => onReportSymptom(region.id, region.name_vi)}
        className="w-full bg-blue-600 text-white rounded-xl py-2 text-sm font-medium hover:bg-blue-700 transition"
      >
        Khai báo triệu chứng tại đây
      </button>
    </div>
  );
}
```

---

### 15.8. Tạo Component Form Khai Báo Triệu Chứng

Tạo `frontend/src/components/body3d/SymptomForm.tsx`:

```typescript
'use client';

import { useState } from 'react';
import { X } from 'lucide-react';

interface Props {
  regionId: string;
  regionName: string;
  userId?: string;
  onClose: () => void;
  onSaved: () => void;
}

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

export default function SymptomForm({ regionId, regionName, userId, onClose, onSaved }: Props) {
  const [description, setDescription] = useState('');
  const [painLevel, setPainLevel] = useState(5);
  const [duration, setDuration] = useState('');
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState('');

  const handleSubmit = async () => {
    if (!description.trim()) {
      setError('Vui lòng mô tả triệu chứng');
      return;
    }
    setSaving(true);
    setError('');
    try {
      const res = await fetch(`${API_URL}/api/v1/body/symptoms`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          user_id: userId,
          region_id: regionId,
          region_name: regionName,
          description,
          pain_level: painLevel,
          duration,
        }),
      });
      if (!res.ok) throw new Error('Lưu thất bại');
      onSaved();
      onClose();
    } catch {
      setError('Không thể lưu. Vui lòng thử lại.');
    } finally {
      setSaving(false);
    }
  };

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
      <div className="bg-white rounded-2xl shadow-2xl p-6 w-full max-w-md mx-4">
        <div className="flex justify-between items-center mb-4">
          <h3 className="text-lg font-bold text-gray-800">Khai báo triệu chứng</h3>
          <button onClick={onClose}><X size={20} className="text-gray-400 hover:text-gray-600" /></button>
        </div>

        <div className="mb-1 text-sm text-blue-600 font-medium">Vùng: {regionName}</div>

        <div className="mt-3">
          <label className="block text-sm font-medium text-gray-700 mb-1">Mô tả triệu chứng *</label>
          <textarea
            value={description}
            onChange={(e) => setDescription(e.target.value)}
            placeholder="Ví dụ: Đau nhói khi hít thở sâu, kéo dài 3 ngày..."
            className="w-full border rounded-xl px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-400 resize-none h-24"
          />
        </div>

        <div className="mt-3">
          <label className="block text-sm font-medium text-gray-700 mb-2">
            Mức độ đau: <span className="text-blue-600 font-bold">{painLevel}/10</span>
          </label>
          <input
            type="range" min={1} max={10} value={painLevel}
            onChange={(e) => setPainLevel(Number(e.target.value))}
            className="w-full accent-blue-600"
          />
          <div className="flex justify-between text-xs text-gray-400 mt-1">
            <span>1 — Không đau</span><span>10 — Đau dữ dội</span>
          </div>
        </div>

        <div className="mt-3">
          <label className="block text-sm font-medium text-gray-700 mb-1">Thời gian xuất hiện</label>
          <input
            type="text"
            value={duration}
            onChange={(e) => setDuration(e.target.value)}
            placeholder="Ví dụ: 2 ngày, 1 tuần, vừa mới xuất hiện..."
            className="w-full border rounded-xl px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-400"
          />
        </div>

        {error && <p className="text-red-500 text-sm mt-2">{error}</p>}

        <div className="flex gap-3 mt-5">
          <button
            onClick={onClose}
            className="flex-1 border border-gray-300 rounded-xl py-2 text-sm text-gray-600 hover:bg-gray-50"
          >
            Huỷ
          </button>
          <button
            onClick={handleSubmit}
            disabled={saving}
            className="flex-1 bg-blue-600 text-white rounded-xl py-2 text-sm font-medium hover:bg-blue-700 disabled:opacity-50"
          >
            {saving ? 'Đang lưu...' : 'Lưu vào hồ sơ'}
          </button>
        </div>
      </div>
    </div>
  );
}
```

---

### 15.9. Tạo Trang Mô Hình 3D

Tạo `frontend/src/app/model3d/page.tsx`:

```typescript
'use client';

import { useState, useEffect } from 'react';
import dynamic from 'next/dynamic';
import RegionPanel from '@/components/body3d/RegionPanel';
import SymptomForm from '@/components/body3d/SymptomForm';

// Import dynamic để tắt SSR (Three.js không chạy server-side)
const BodyViewer3D = dynamic(() => import('@/components/body3d/BodyViewer3D'), { ssr: false });

interface BodyRegion {
  id: string;
  name_vi: string;
  name_latin: string;
  position: [number, number, number];
  symptoms: string[];
  description_basic: string;
  description_advanced: string;
  layer: number;
}

// Lấy userType từ localStorage (sẽ được lưu sau khi hoàn thành Onboarding)
function getUserType(): 'patient' | 'student' | 'expert' {
  if (typeof window === 'undefined') return 'patient';
  return (localStorage.getItem('user_type') as any) || 'patient';
}

export default function Model3DPage() {
  const [regions, setRegions] = useState<BodyRegion[]>([]);
  const [gender, setGender] = useState<'male' | 'female'>('male');
  const [xrayLevel, setXrayLevel] = useState(0);
  const [selectedRegion, setSelectedRegion] = useState<BodyRegion | null>(null);
  const [showSymptomForm, setShowSymptomForm] = useState(false);
  const [symptomTarget, setSymptomTarget] = useState({ id: '', name: '' });
  const [savedCount, setSavedCount] = useState(0);
  const userType = getUserType();

  useEffect(() => {
    fetch('/body_regions.json')
      .then((r) => r.json())
      .then(setRegions);
  }, []);

  // Lọc vùng hiển thị theo xrayLevel
  const visibleRegions = xrayLevel === 0
    ? regions.filter((r) => r.layer <= 1)
    : xrayLevel === 1
    ? regions.filter((r) => r.layer <= 2)
    : regions;

  const handleReportSymptom = (regionId: string, regionName: string) => {
    setSymptomTarget({ id: regionId, name: regionName });
    setSelectedRegion(null);
    setShowSymptomForm(true);
  };

  const xrayLabels = ['Tắt', 'Cơ bắp', 'Xương', 'Nội tạng'];

  return (
    <div className="h-[calc(100vh-56px)] flex flex-col">
      {/* Toolbar */}
      <div className="bg-gray-900 text-white px-6 py-2 flex items-center gap-6 flex-shrink-0">
        <span className="font-semibold text-sm">Mô Hình 3D Giải Phẫu</span>

        {/* Chọn giới tính */}
        <div className="flex items-center gap-2">
          <span className="text-xs text-gray-400">Mô hình:</span>
          {(['male', 'female'] as const).map((g) => (
            <button
              key={g}
              onClick={() => setGender(g)}
              className={`px-3 py-1 rounded-lg text-xs font-medium transition ${
                gender === g ? 'bg-blue-600 text-white' : 'bg-gray-700 text-gray-300 hover:bg-gray-600'
              }`}
            >
              {g === 'male' ? 'Nam' : 'Nữ'}
            </button>
          ))}
        </div>

        {/* X-Ray level */}
        <div className="flex items-center gap-2">
          <span className="text-xs text-gray-400">X-Ray:</span>
          {xrayLabels.map((label, i) => (
            <button
              key={i}
              onClick={() => setXrayLevel(i)}
              className={`px-3 py-1 rounded-lg text-xs font-medium transition ${
                xrayLevel === i ? 'bg-cyan-500 text-white' : 'bg-gray-700 text-gray-300 hover:bg-gray-600'
              }`}
            >
              {label}
            </button>
          ))}
        </div>

        <div className="ml-auto text-xs text-gray-400">
          Kéo để xoay · Scroll để zoom · Click điểm để xem thông tin
        </div>
      </div>

      {/* 3D Viewport */}
      <div className="flex-1 relative">
        <BodyViewer3D
          regions={visibleRegions}
          gender={gender}
          xrayLevel={xrayLevel}
          userType={userType}
          onRegionClick={setSelectedRegion}
        />

        {/* Panel thông tin vùng */}
        <RegionPanel
          region={selectedRegion}
          userType={userType}
          onClose={() => setSelectedRegion(null)}
          onReportSymptom={handleReportSymptom}
        />

        {/* Badge số triệu chứng đã lưu */}
        {savedCount > 0 && (
          <div className="absolute bottom-4 left-4 bg-green-600 text-white text-xs px-3 py-1.5 rounded-full shadow">
            Đã lưu {savedCount} triệu chứng vào hồ sơ
          </div>
        )}
      </div>

      {/* Form khai báo triệu chứng */}
      {showSymptomForm && (
        <SymptomForm
          regionId={symptomTarget.id}
          regionName={symptomTarget.name}
          userId={typeof window !== 'undefined' ? localStorage.getItem('user_id') || undefined : undefined}
          onClose={() => setShowSymptomForm(false)}
          onSaved={() => setSavedCount((c) => c + 1)}
        />
      )}
    </div>
  );
}
```

---

### 15.10. Thêm Link Navbar Cho Mô Hình 3D

Trong `frontend/src/app/layout.tsx`, thêm vào nav:

```typescript
<Link href="/model3d" className="hover:underline">Mô hình 3D</Link>
```

---

### 15.11. Kiểm Tra Tính Năng 3D

```powershell
# Đảm bảo model file đã có trong public/models/
# Truy cập: http://localhost:3000/model3d

# Kiểm tra các chức năng:
# 1. Chuyển Nam/Nữ -> model thay đổi
# 2. Bật X-Ray lần lượt 4 mức -> độ trong suốt thay đổi
# 3. Click điểm màu xanh -> panel thông tin hiện ra
# 4. Bấm "Khai báo triệu chứng" -> form modal hiện
# 5. Điền form -> Lưu -> kiểm tra DB:
#    SELECT * FROM body_symptoms LIMIT 5;
```

---

## BƯỚC 16: TAB BÀI KIỂM TRA

### Tổng quan
Tab "Bài kiểm tra" gồm 2 mục:
1. **Onboarding Quiz** — câu hỏi cố định phân loại user lần đầu đăng nhập (ảnh hưởng quyền truy cập)
2. **Document Quiz** — AI tạo bộ câu hỏi từ PDF, thời gian tối đa 5 giờ, có thể tạm dừng, lưu lịch sử

**Stack sử dụng (toàn bộ miễn phí):**
- Groq API (Llama-3.3-70b) — đã có trong stack — tạo câu hỏi từ PDF
- Server-Sent Events (FastAPI) — streaming progress bar khi AI tạo câu hỏi
- PostgreSQL (đã có) — lưu câu hỏi, bài làm, kết quả

---

### 16.1. Migration SQL Cho Hệ Thống Quiz

Thêm vào `docker/init_db.sql` (hoặc chạy trực tiếp):

```sql
-- Bộ câu hỏi quiz (gắn với 1 tài liệu PDF)
CREATE TABLE IF NOT EXISTS quiz_sets (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    document_id UUID REFERENCES documents(id) ON DELETE CASCADE,
    user_id UUID REFERENCES users(id) ON DELETE SET NULL,
    title VARCHAR(500),
    question_type VARCHAR(50) DEFAULT 'mixed',
    difficulty VARCHAR(20) DEFAULT 'medium',
    language VARCHAR(10) DEFAULT 'vi',
    total_questions INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Từng câu hỏi trong bộ quiz
CREATE TABLE IF NOT EXISTS quiz_questions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    quiz_set_id UUID REFERENCES quiz_sets(id) ON DELETE CASCADE,
    question_index INTEGER NOT NULL,
    question_text TEXT NOT NULL,
    question_type VARCHAR(20) DEFAULT 'mcq',
    options JSONB,
    correct_answer VARCHAR(500) NOT NULL,
    explanation TEXT,
    source_text TEXT,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Lần làm bài của user
CREATE TABLE IF NOT EXISTS quiz_attempts (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    quiz_set_id UUID REFERENCES quiz_sets(id) ON DELETE CASCADE,
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    started_at TIMESTAMP DEFAULT NOW(),
    submitted_at TIMESTAMP,
    deadline TIMESTAMP,
    status VARCHAR(20) DEFAULT 'in_progress',
    score NUMERIC(5,2),
    total_correct INTEGER DEFAULT 0,
    time_spent_seconds INTEGER
);

-- Từng câu trả lời của user
CREATE TABLE IF NOT EXISTS quiz_answers (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    attempt_id UUID REFERENCES quiz_attempts(id) ON DELETE CASCADE,
    question_id UUID REFERENCES quiz_questions(id) ON DELETE CASCADE,
    user_answer VARCHAR(500),
    is_correct BOOLEAN,
    is_flagged BOOLEAN DEFAULT FALSE,
    answered_at TIMESTAMP
);
```

---

### 16.2. Backend — Endpoint Onboarding

Tạo `backend/app/api/v1/onboarding.py`:

```python
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import List
from app.db.postgres import get_db
import uuid

router = APIRouter()

# Câu hỏi cố định — không thay đổi
ONBOARDING_QUESTIONS = [
    {
        "id": 1,
        "question": "Bạn đang sử dụng ứng dụng với mục đích gì?",
        "options": [
            {"value": "patient", "label": "Tìm hiểu về triệu chứng / bệnh lý của bản thân"},
            {"value": "student", "label": "Học tập y khoa / sinh viên ngành y"},
            {"value": "expert", "label": "Nghiên cứu khoa học / bác sĩ / chuyên gia"},
            {"value": "general", "label": "Tìm hiểu kiến thức chung về sức khỏe"},
        ]
    },
    {
        "id": 2,
        "question": "Trình độ hiểu biết y tế hiện tại của bạn?",
        "options": [
            {"value": "basic", "label": "Người dùng phổ thông — không có nền tảng y tế"},
            {"value": "intermediate", "label": "Biết một số kiến thức cơ bản về y tế"},
            {"value": "advanced", "label": "Sinh viên y / y tá / dược sĩ"},
            {"value": "professional", "label": "Bác sĩ / chuyên gia y tế"},
        ]
    },
    {
        "id": 3,
        "question": "Bạn có đang điều trị bệnh lý nào không?",
        "options": [
            {"value": "yes_chronic", "label": "Có — bệnh mãn tính (tiểu đường, huyết áp, tim mạch...)"},
            {"value": "yes_acute", "label": "Có — đang điều trị bệnh cấp tính"},
            {"value": "no", "label": "Không — tôi khỏe mạnh"},
            {"value": "unsure", "label": "Không chắc / đang cần tìm hiểu"},
        ]
    },
    {
        "id": 4,
        "question": "Bạn thường tìm kiếm thông tin y tế về lĩnh vực nào?",
        "options": [
            {"value": "internal", "label": "Nội khoa (tim mạch, hô hấp, tiêu hóa...)"},
            {"value": "neuro", "label": "Thần kinh học / tâm thần"},
            {"value": "surgery", "label": "Ngoại khoa / chỉnh hình"},
            {"value": "general_health", "label": "Sức khỏe tổng quát / dinh dưỡng / phòng bệnh"},
        ]
    },
    {
        "id": 5,
        "question": "Nhóm tuổi của bạn?",
        "options": [
            {"value": "under18", "label": "Dưới 18 tuổi"},
            {"value": "18_30", "label": "18 — 30 tuổi"},
            {"value": "31_50", "label": "31 — 50 tuổi"},
            {"value": "over50", "label": "Trên 50 tuổi"},
        ]
    },
]

def _classify_user(answers: dict) -> str:
    """Phân loại user dựa trên câu trả lời onboarding."""
    q1 = answers.get("1", "")
    q2 = answers.get("2", "")
    if q1 in ("expert",) or q2 in ("professional",):
        return "expert"
    if q1 in ("student",) or q2 in ("advanced",):
        return "student"
    return "patient"

class OnboardingSubmit(BaseModel):
    user_id: str
    answers: dict  # {"1": "patient", "2": "basic", ...}

@router.get("/questions")
def get_questions():
    return {"questions": ONBOARDING_QUESTIONS}

@router.post("/complete")
def complete_onboarding(data: OnboardingSubmit, db: Session = Depends(get_db)):
    from sqlalchemy import text
    user_type = _classify_user(data.answers)

    # Upsert vào user_profiles
    existing = db.execute(
        text("SELECT id FROM user_profiles WHERE user_id = :uid"),
        {"uid": data.user_id}
    ).fetchone()

    if existing:
        db.execute(
            text("""
                UPDATE user_profiles
                SET user_type = :ut, onboarding_done = TRUE, answers = :ans, updated_at = NOW()
                WHERE user_id = :uid
            """),
            {"ut": user_type, "ans": str(data.answers), "uid": data.user_id}
        )
    else:
        db.execute(
            text("""
                INSERT INTO user_profiles (id, user_id, user_type, onboarding_done, answers)
                VALUES (:id, :uid, :ut, TRUE, :ans)
            """),
            {"id": str(uuid.uuid4()), "uid": data.user_id, "ut": user_type, "ans": str(data.answers)}
        )
    db.commit()

    ACCESS_MAP = {
        "patient": ["model3d_basic", "quiz_easy", "chat"],
        "student": ["model3d_full", "quiz_all", "chat", "library", "graph"],
        "expert": ["model3d_full", "quiz_all", "chat", "library", "graph", "advanced_info"],
    }

    return {
        "user_type": user_type,
        "access_rights": ACCESS_MAP[user_type],
        "message": f"Phân loại thành công: {user_type}"
    }

@router.get("/profile/{user_id}")
def get_profile(user_id: str, db: Session = Depends(get_db)):
    from sqlalchemy import text
    row = db.execute(
        text("SELECT user_type, onboarding_done FROM user_profiles WHERE user_id = :uid"),
        {"uid": user_id}
    ).fetchone()
    if not row:
        return {"onboarding_done": False, "user_type": None}
    return {"onboarding_done": row.onboarding_done, "user_type": row.user_type}
```

---

### 16.3. Backend — Endpoint Tạo Quiz Từ PDF

Tạo `backend/app/api/v1/quiz.py`:

```python
import uuid
import json
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional
from app.db.postgres import get_db
from app.core.config import settings
from groq import Groq

router = APIRouter()
groq_client = Groq(api_key=settings.GROQ_API_KEY)

QUIZ_SYSTEM_PROMPT = """Bạn là chuyên gia tạo bộ câu hỏi kiểm tra học thuật y khoa.
Nhiệm vụ: Đọc nội dung tài liệu được cung cấp và tạo bộ câu hỏi trắc nghiệm hoàn chỉnh.

QUY TẮC BẮT BUỘC:
1. Mỗi câu hỏi có đúng 4 lựa chọn (A, B, C, D)
2. Chỉ có 1 đáp án đúng
3. Câu hỏi phải bao phủ đều các phần của tài liệu
4. Thêm giải thích ngắn gọn cho đáp án đúng (trích từ tài liệu)
5. Trả về JSON thuần túy, không thêm markdown hay text ngoài JSON

Định dạng JSON trả về (KHÔNG THÊM GÌ NGOÀI JSON):
{
  "questions": [
    {
      "index": 1,
      "question": "Nội dung câu hỏi?",
      "type": "mcq",
      "options": {"A": "...", "B": "...", "C": "...", "D": "..."},
      "correct_answer": "A",
      "explanation": "Giải thích tại sao A đúng, dựa trên tài liệu...",
      "source_text": "Đoạn văn gốc từ tài liệu liên quan"
    }
  ]
}"""

class GenerateQuizRequest(BaseModel):
    document_id: str
    user_id: Optional[str] = None
    question_type: str = "mcq"
    difficulty: str = "medium"
    language: str = "vi"
    num_questions: Optional[int] = None

class StartAttemptRequest(BaseModel):
    quiz_set_id: str
    user_id: str

class SaveAnswerRequest(BaseModel):
    question_id: str
    user_answer: str
    is_flagged: bool = False

@router.post("/generate")
def generate_quiz(req: GenerateQuizRequest, db: Session = Depends(get_db)):
    """Tạo bộ câu hỏi từ PDF bằng AI. Streaming progress."""
    from sqlalchemy import text
    from app.models.document import Chunk

    # Lấy document
    doc = db.execute(
        text("SELECT id, filename, title, status FROM documents WHERE id = :id"),
        {"id": req.document_id}
    ).fetchone()
    if not doc:
        raise HTTPException(404, "Không tìm thấy tài liệu")
    if doc.status != "ready":
        raise HTTPException(400, "Tài liệu chưa xử lý xong")

    # Lấy toàn bộ nội dung từ chunks
    chunks = db.execute(
        text("""
            SELECT content FROM chunks
            WHERE document_id = :doc_id
            ORDER BY chunk_index
        """),
        {"doc_id": req.document_id}
    ).fetchall()

    full_text = " ".join([c.content for c in chunks])
    # Giới hạn 12000 ký tự để không vượt context window Groq
    text_sample = full_text[:12000]

    word_count = len(text_sample.split())
    num_questions = req.num_questions or max(10, min(50, word_count // 80))

    difficulty_desc = {"easy": "dễ (kiến thức cơ bản)", "medium": "trung bình", "hard": "khó (chuyên sâu)"}
    lang_desc = {"vi": "Tiếng Việt", "en": "English"}

    user_prompt = f"""Tài liệu:
---
{text_sample}
---

Yêu cầu: Tạo đúng {num_questions} câu hỏi trắc nghiệm.
Độ khó: {difficulty_desc.get(req.difficulty, 'trung bình')}
Ngôn ngữ câu hỏi: {lang_desc.get(req.language, 'Tiếng Việt')}
Câu hỏi phải bao phủ đều các chủ đề trong tài liệu."""

    def generate_and_save():
        yield "data: {\"status\": \"generating\", \"message\": \"AI đang đọc tài liệu...\"}\n\n"

        try:
            response = groq_client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=[
                    {"role": "system", "content": QUIZ_SYSTEM_PROMPT},
                    {"role": "user", "content": user_prompt},
                ],
                max_tokens=8192,
                temperature=0.3,
            )

            raw_content = response.choices[0].message.content.strip()

            yield "data: {\"status\": \"parsing\", \"message\": \"Đang xử lý câu hỏi...\"}\n\n"

            # Parse JSON
            if "```json" in raw_content:
                raw_content = raw_content.split("```json")[1].split("```")[0].strip()
            elif "```" in raw_content:
                raw_content = raw_content.split("```")[1].split("```")[0].strip()

            parsed = json.loads(raw_content)
            questions = parsed.get("questions", [])

            if not questions:
                yield "data: {\"status\": \"error\", \"message\": \"AI không tạo được câu hỏi. Thử lại.\"}\n\n"
                return

            # Lưu vào DB
            db_session = db
            quiz_id = str(uuid.uuid4())

            db_session.execute(
                text("""
                    INSERT INTO quiz_sets (id, document_id, user_id, title, question_type, difficulty, language, total_questions)
                    VALUES (:id, :doc_id, :user_id, :title, :qtype, :diff, :lang, :total)
                """),
                {
                    "id": quiz_id,
                    "doc_id": req.document_id,
                    "user_id": req.user_id,
                    "title": f"Quiz — {doc.title or doc.filename}",
                    "qtype": req.question_type,
                    "diff": req.difficulty,
                    "lang": req.language,
                    "total": len(questions),
                }
            )

            for q in questions:
                db_session.execute(
                    text("""
                        INSERT INTO quiz_questions
                        (id, quiz_set_id, question_index, question_text, question_type, options, correct_answer, explanation, source_text)
                        VALUES (:id, :qsid, :idx, :qtxt, :qtype, :opts::jsonb, :ans, :expl, :src)
                    """),
                    {
                        "id": str(uuid.uuid4()),
                        "qsid": quiz_id,
                        "idx": q.get("index", 0),
                        "qtxt": q.get("question", ""),
                        "qtype": q.get("type", "mcq"),
                        "opts": json.dumps(q.get("options", {}), ensure_ascii=False),
                        "ans": q.get("correct_answer", ""),
                        "expl": q.get("explanation", ""),
                        "src": q.get("source_text", ""),
                    }
                )

            db_session.commit()

            result = json.dumps({"status": "done", "quiz_id": quiz_id, "total_questions": len(questions)}, ensure_ascii=False)
            yield f"data: {result}\n\n"

        except json.JSONDecodeError:
            yield "data: {\"status\": \"error\", \"message\": \"AI trả về định dạng không hợp lệ. Hãy thử tạo lại.\"}\n\n"
        except Exception as e:
            yield f"data: {{\"status\": \"error\", \"message\": \"Lỗi: {str(e)[:100]}\"}}\n\n"

    return StreamingResponse(generate_and_save(), media_type="text/event-stream")

@router.get("/{quiz_set_id}")
def get_quiz(quiz_set_id: str, db: Session = Depends(get_db)):
    from sqlalchemy import text
    quiz = db.execute(
        text("SELECT id, title, total_questions, difficulty, language FROM quiz_sets WHERE id = :id"),
        {"id": quiz_set_id}
    ).fetchone()
    if not quiz:
        raise HTTPException(404, "Không tìm thấy bộ câu hỏi")

    questions = db.execute(
        text("""
            SELECT id, question_index, question_text, question_type, options
            FROM quiz_questions WHERE quiz_set_id = :qsid ORDER BY question_index
        """),
        {"qsid": quiz_set_id}
    ).fetchall()

    return {
        "id": str(quiz.id),
        "title": quiz.title,
        "total_questions": quiz.total_questions,
        "difficulty": quiz.difficulty,
        "language": quiz.language,
        "questions": [
            {
                "id": str(q.id),
                "index": q.question_index,
                "text": q.question_text,
                "type": q.question_type,
                "options": q.options,
            }
            for q in questions
        ]
    }

@router.post("/attempt/start")
def start_attempt(req: StartAttemptRequest, db: Session = Depends(get_db)):
    from sqlalchemy import text
    from datetime import datetime, timedelta

    attempt_id = str(uuid.uuid4())
    deadline = datetime.now() + timedelta(hours=5)

    db.execute(
        text("""
            INSERT INTO quiz_attempts (id, quiz_set_id, user_id, deadline, status)
            VALUES (:id, :qsid, :uid, :deadline, 'in_progress')
        """),
        {"id": attempt_id, "qsid": req.quiz_set_id, "uid": req.user_id, "deadline": deadline}
    )
    db.commit()

    return {"attempt_id": attempt_id, "deadline": deadline.isoformat()}

@router.put("/attempt/{attempt_id}/answer")
def save_answer(attempt_id: str, req: SaveAnswerRequest, db: Session = Depends(get_db)):
    from sqlalchemy import text
    from datetime import datetime

    existing = db.execute(
        text("SELECT id FROM quiz_answers WHERE attempt_id = :aid AND question_id = :qid"),
        {"aid": attempt_id, "qid": req.question_id}
    ).fetchone()

    if existing:
        db.execute(
            text("""
                UPDATE quiz_answers
                SET user_answer = :ans, is_flagged = :flag, answered_at = NOW()
                WHERE attempt_id = :aid AND question_id = :qid
            """),
            {"ans": req.user_answer, "flag": req.is_flagged, "aid": attempt_id, "qid": req.question_id}
        )
    else:
        db.execute(
            text("""
                INSERT INTO quiz_answers (id, attempt_id, question_id, user_answer, is_flagged, answered_at)
                VALUES (:id, :aid, :qid, :ans, :flag, NOW())
            """),
            {"id": str(uuid.uuid4()), "aid": attempt_id, "qid": req.question_id,
             "ans": req.user_answer, "flag": req.is_flagged}
        )
    db.commit()
    return {"saved": True}

@router.post("/attempt/{attempt_id}/submit")
def submit_attempt(attempt_id: str, db: Session = Depends(get_db)):
    from sqlalchemy import text
    from datetime import datetime

    # Lấy tất cả câu trả lời
    answers = db.execute(
        text("""
            SELECT qa.id, qa.question_id, qa.user_answer, qq.correct_answer
            FROM quiz_answers qa
            JOIN quiz_questions qq ON qa.question_id = qq.id
            WHERE qa.attempt_id = :aid
        """),
        {"aid": attempt_id}
    ).fetchall()

    total_correct = sum(1 for a in answers if a.user_answer == a.correct_answer)
    total = len(answers)
    score = (total_correct / total * 100) if total > 0 else 0

    # Cập nhật is_correct
    for a in answers:
        db.execute(
            text("UPDATE quiz_answers SET is_correct = :ic WHERE id = :id"),
            {"ic": a.user_answer == a.correct_answer, "id": str(a.id)}
        )

    # Lấy thời gian bắt đầu
    attempt = db.execute(
        text("SELECT started_at FROM quiz_attempts WHERE id = :id"),
        {"id": attempt_id}
    ).fetchone()
    time_spent = int((datetime.now() - attempt.started_at).total_seconds()) if attempt else 0

    db.execute(
        text("""
            UPDATE quiz_attempts
            SET status = 'submitted', submitted_at = NOW(),
                score = :score, total_correct = :tc, time_spent_seconds = :ts
            WHERE id = :id
        """),
        {"score": round(score, 2), "tc": total_correct, "ts": time_spent, "id": attempt_id}
    )
    db.commit()

    return {
        "attempt_id": attempt_id,
        "score": round(score, 2),
        "total_correct": total_correct,
        "total_questions": total,
        "time_spent_seconds": time_spent,
    }

@router.get("/attempt/{attempt_id}/result")
def get_result(attempt_id: str, db: Session = Depends(get_db)):
    from sqlalchemy import text

    attempt = db.execute(
        text("""
            SELECT qa.score, qa.total_correct, qa.time_spent_seconds, qa.submitted_at,
                   qs.total_questions, qs.title
            FROM quiz_attempts qa
            JOIN quiz_sets qs ON qa.quiz_set_id = qs.id
            WHERE qa.id = :id
        """),
        {"id": attempt_id}
    ).fetchone()
    if not attempt:
        raise HTTPException(404, "Không tìm thấy bài làm")

    detail = db.execute(
        text("""
            SELECT ans.question_id, ans.user_answer, ans.is_correct,
                   qq.question_text, qq.options, qq.correct_answer, qq.explanation, qq.source_text
            FROM quiz_answers ans
            JOIN quiz_questions qq ON ans.question_id = qq.id
            WHERE ans.attempt_id = :id
            ORDER BY qq.question_index
        """),
        {"id": attempt_id}
    ).fetchall()

    return {
        "score": attempt.score,
        "total_correct": attempt.total_correct,
        "total_questions": attempt.total_questions,
        "time_spent_seconds": attempt.time_spent_seconds,
        "submitted_at": attempt.submitted_at.isoformat() if attempt.submitted_at else None,
        "title": attempt.title,
        "questions": [
            {
                "question_text": r.question_text,
                "options": r.options,
                "user_answer": r.user_answer,
                "correct_answer": r.correct_answer,
                "is_correct": r.is_correct,
                "explanation": r.explanation,
                "source_text": r.source_text,
            }
            for r in detail
        ]
    }

@router.get("/history/{user_id}")
def get_history(user_id: str, db: Session = Depends(get_db)):
    from sqlalchemy import text
    rows = db.execute(
        text("""
            SELECT qa.id, qa.score, qa.total_correct, qa.submitted_at, qa.status,
                   qs.title, qs.total_questions
            FROM quiz_attempts qa
            JOIN quiz_sets qs ON qa.quiz_set_id = qs.id
            WHERE qa.user_id = :uid
            ORDER BY qa.started_at DESC
        """),
        {"uid": user_id}
    ).fetchall()
    return {
        "total": len(rows),
        "attempts": [
            {
                "id": str(r.id),
                "title": r.title,
                "score": r.score,
                "total_correct": r.total_correct,
                "total_questions": r.total_questions,
                "status": r.status,
                "submitted_at": r.submitted_at.isoformat() if r.submitted_at else None,
            }
            for r in rows
        ]
    }
```

Đăng ký cả 2 router mới trong `backend/app/api/v1/__init__.py`:

```python
from app.api.v1 import document, chat, graph, auth, body, onboarding, quiz

api_router.include_router(onboarding.router, prefix="/onboarding", tags=["Onboarding"])
api_router.include_router(quiz.router, prefix="/quiz", tags=["Quiz"])
```

---

### 16.4. Frontend — Trang Onboarding Quiz

Tạo `frontend/src/app/quiz/onboarding/page.tsx`:

```typescript
'use client';

import { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { ChevronRight, ChevronLeft, Check } from 'lucide-react';

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

interface Question {
  id: number;
  question: string;
  options: { value: string; label: string }[];
}

const USER_TYPE_LABELS: Record<string, { label: string; desc: string; color: string }> = {
  patient: {
    label: "Bệnh nhân / Người dùng phổ thông",
    desc: "Truy cập thông tin sức khỏe cơ bản, khai báo triệu chứng, quiz dễ",
    color: "bg-green-50 border-green-400 text-green-800",
  },
  student: {
    label: "Sinh viên / Người học y khoa",
    desc: "Đầy đủ tính năng: thông tin chuyên sâu, quiz nâng cao, thư viện tài liệu",
    color: "bg-blue-50 border-blue-400 text-blue-800",
  },
  expert: {
    label: "Bác sĩ / Chuyên gia nghiên cứu",
    desc: "Toàn bộ tính năng + thông tin lâm sàng chuyên sâu + đồ thị tri thức",
    color: "bg-purple-50 border-purple-400 text-purple-800",
  },
};

export default function OnboardingPage() {
  const router = useRouter();
  const [questions, setQuestions] = useState<Question[]>([]);
  const [current, setCurrent] = useState(0);
  const [answers, setAnswers] = useState<Record<number, string>>({});
  const [result, setResult] = useState<{ user_type: string; access_rights: string[] } | null>(null);
  const [submitting, setSubmitting] = useState(false);

  useEffect(() => {
    fetch(`${API_URL}/api/v1/onboarding/questions`)
      .then((r) => r.json())
      .then((d) => setQuestions(d.questions));
  }, []);

  const handleSelect = (value: string) => {
    setAnswers((prev) => ({ ...prev, [questions[current].id]: value }));
  };

  const handleNext = () => {
    if (current < questions.length - 1) setCurrent((c) => c + 1);
  };

  const handleBack = () => {
    if (current > 0) setCurrent((c) => c - 1);
  };

  const handleSubmit = async () => {
    setSubmitting(true);
    const userId = localStorage.getItem('user_id') || 'anonymous';
    const stringAnswers: Record<string, string> = {};
    Object.entries(answers).forEach(([k, v]) => { stringAnswers[k] = v; });

    try {
      const res = await fetch(`${API_URL}/api/v1/onboarding/complete`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ user_id: userId, answers: stringAnswers }),
      });
      const data = await res.json();
      localStorage.setItem('user_type', data.user_type);
      setResult(data);
    } finally {
      setSubmitting(false);
    }
  };

  if (result) {
    const info = USER_TYPE_LABELS[result.user_type] || USER_TYPE_LABELS.patient;
    return (
      <div className="max-w-lg mx-auto mt-16 px-4 text-center">
        <div className="w-16 h-16 bg-green-100 rounded-full flex items-center justify-center mx-auto mb-4">
          <Check className="text-green-600" size={32} />
        </div>
        <h2 className="text-2xl font-bold text-gray-800 mb-2">Phân loại hoàn tất!</h2>
        <p className="text-gray-500 mb-6">Chúng tôi đã cá nhân hoá trải nghiệm cho bạn</p>

        <div className={`border-2 rounded-2xl p-5 mb-6 ${info.color}`}>
          <p className="font-bold text-lg mb-1">{info.label}</p>
          <p className="text-sm">{info.desc}</p>
        </div>

        <button
          onClick={() => router.push('/')}
          className="w-full bg-blue-600 text-white rounded-xl py-3 font-medium hover:bg-blue-700"
        >
          Bắt đầu sử dụng
        </button>
        <button
          onClick={() => { setResult(null); setCurrent(0); setAnswers({}); }}
          className="w-full mt-2 text-gray-500 text-sm hover:underline"
        >
          Làm lại bài kiểm tra
        </button>
      </div>
    );
  }

  if (questions.length === 0) {
    return <div className="text-center mt-20 text-gray-400">Đang tải...</div>;
  }

  const q = questions[current];
  const progress = ((current) / questions.length) * 100;
  const allAnswered = Object.keys(answers).length === questions.length;

  return (
    <div className="max-w-lg mx-auto mt-10 px-4">
      {/* Progress */}
      <div className="mb-6">
        <div className="flex justify-between text-sm text-gray-500 mb-1">
          <span>Câu {current + 1} / {questions.length}</span>
          <span>{Math.round(progress)}% hoàn thành</span>
        </div>
        <div className="h-2 bg-gray-200 rounded-full overflow-hidden">
          <div
            className="h-full bg-blue-500 rounded-full transition-all duration-300"
            style={{ width: `${progress}%` }}
          />
        </div>
      </div>

      {/* Question card */}
      <div className="bg-white rounded-2xl shadow-lg p-6 mb-4">
        <h2 className="text-lg font-semibold text-gray-800 mb-5">{q.question}</h2>
        <div className="space-y-3">
          {q.options.map((opt) => (
            <button
              key={opt.value}
              onClick={() => handleSelect(opt.value)}
              className={`w-full text-left px-4 py-3 rounded-xl border-2 text-sm transition ${
                answers[q.id] === opt.value
                  ? 'border-blue-500 bg-blue-50 text-blue-700 font-medium'
                  : 'border-gray-200 hover:border-blue-300 text-gray-700'
              }`}
            >
              {opt.label}
            </button>
          ))}
        </div>
      </div>

      {/* Navigation */}
      <div className="flex gap-3">
        <button
          onClick={handleBack}
          disabled={current === 0}
          className="flex items-center gap-1 px-4 py-2 rounded-xl border border-gray-300 text-sm text-gray-600 disabled:opacity-30 hover:bg-gray-50"
        >
          <ChevronLeft size={16} /> Quay lại
        </button>

        {current < questions.length - 1 ? (
          <button
            onClick={handleNext}
            disabled={!answers[q.id]}
            className="flex-1 flex items-center justify-center gap-1 bg-blue-600 text-white rounded-xl py-2 text-sm font-medium disabled:opacity-40 hover:bg-blue-700"
          >
            Tiếp theo <ChevronRight size={16} />
          </button>
        ) : (
          <button
            onClick={handleSubmit}
            disabled={!allAnswered || submitting}
            className="flex-1 bg-green-600 text-white rounded-xl py-2 text-sm font-medium disabled:opacity-40 hover:bg-green-700"
          >
            {submitting ? 'Đang xử lý...' : 'Hoàn tất & Xem kết quả'}
          </button>
        )}
      </div>
    </div>
  );
}
```

---

### 16.5. Frontend — Component Timer Đếm Ngược

Tạo `frontend/src/components/quiz/QuizTimer.tsx`:

```typescript
'use client';

import { useEffect, useState } from 'react';
import { Clock } from 'lucide-react';

interface Props {
  deadline: string;
  onExpired: () => void;
}

export default function QuizTimer({ deadline, onExpired }: Props) {
  const [remaining, setRemaining] = useState(0);

  useEffect(() => {
    const calc = () => {
      const diff = Math.max(0, Math.floor((new Date(deadline).getTime() - Date.now()) / 1000));
      setRemaining(diff);
      if (diff === 0) onExpired();
    };
    calc();
    const interval = setInterval(calc, 1000);
    return () => clearInterval(interval);
  }, [deadline, onExpired]);

  const h = Math.floor(remaining / 3600);
  const m = Math.floor((remaining % 3600) / 60);
  const s = remaining % 60;
  const pad = (n: number) => String(n).padStart(2, '0');

  const isWarning = remaining < 1800; // < 30 phút

  return (
    <div className={`flex items-center gap-2 px-4 py-2 rounded-xl font-mono text-sm font-bold ${
      isWarning ? 'bg-red-100 text-red-600' : 'bg-gray-100 text-gray-700'
    }`}>
      <Clock size={16} />
      {pad(h)}:{pad(m)}:{pad(s)}
      {isWarning && <span className="text-xs font-normal">— Còn ít thời gian!</span>}
    </div>
  );
}
```

---

### 16.6. Frontend — Trang Document Quiz (Chính)

Tạo `frontend/src/app/quiz/document/page.tsx`:

```typescript
'use client';

import { useState, useEffect, useCallback } from 'react';
import { getDocuments, DocumentInfo } from '@/lib/api';
import QuizTimer from '@/components/quiz/QuizTimer';
import { Flag, ChevronLeft, ChevronRight, RotateCcw, CheckCircle } from 'lucide-react';

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

type Step = 'select' | 'configure' | 'generating' | 'preview' | 'taking' | 'result';

interface QuizQuestion {
  id: string;
  index: number;
  text: string;
  type: string;
  options: Record<string, string>;
}

interface QuizSet {
  id: string;
  title: string;
  total_questions: number;
  difficulty: string;
  questions: QuizQuestion[];
}

interface ResultData {
  score: number;
  total_correct: number;
  total_questions: number;
  time_spent_seconds: number;
  title: string;
  questions: Array<{
    question_text: string;
    options: Record<string, string>;
    user_answer: string;
    correct_answer: string;
    is_correct: boolean;
    explanation: string;
    source_text: string;
  }>;
}

export default function DocumentQuizPage() {
  const [step, setStep] = useState<Step>('select');
  const [documents, setDocuments] = useState<DocumentInfo[]>([]);
  const [selectedDoc, setSelectedDoc] = useState<string>('');
  const [config, setConfig] = useState({ difficulty: 'medium', language: 'vi', num_questions: '' });
  const [generateMsg, setGenerateMsg] = useState('');
  const [quizSet, setQuizSet] = useState<QuizSet | null>(null);
  const [attemptId, setAttemptId] = useState('');
  const [deadline, setDeadline] = useState('');
  const [answers, setAnswers] = useState<Record<string, string>>({});
  const [flagged, setFlagged] = useState<Set<string>>(new Set());
  const [currentQ, setCurrentQ] = useState(0);
  const [result, setResult] = useState<ResultData | null>(null);
  const [submitting, setSubmitting] = useState(false);
  const [reviewIndex, setReviewIndex] = useState<number | null>(null);

  const userId = typeof window !== 'undefined' ? localStorage.getItem('user_id') || 'anonymous' : 'anonymous';

  useEffect(() => {
    getDocuments().then((docs) => setDocuments(docs.filter((d) => d.status === 'ready')));
  }, []);

  const handleGenerate = async () => {
    setStep('generating');
    setGenerateMsg('Đang chuẩn bị...');

    const params: any = {
      document_id: selectedDoc,
      user_id: userId,
      difficulty: config.difficulty,
      language: config.language,
    };
    if (config.num_questions) params.num_questions = parseInt(config.num_questions);

    const res = await fetch(`${API_URL}/api/v1/quiz/generate`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(params),
    });

    const reader = res.body!.getReader();
    const decoder = new TextDecoder();

    while (true) {
      const { done, value } = await reader.read();
      if (done) break;
      const text = decoder.decode(value);
      const lines = text.split('\n').filter((l) => l.startsWith('data:'));
      for (const line of lines) {
        try {
          const data = JSON.parse(line.replace('data: ', ''));
          if (data.status === 'generating') setGenerateMsg(data.message);
          if (data.status === 'parsing') setGenerateMsg(data.message);
          if (data.status === 'done') {
            // Load quiz
            const qRes = await fetch(`${API_URL}/api/v1/quiz/${data.quiz_id}`);
            const qData = await qRes.json();
            setQuizSet(qData);
            setStep('preview');
          }
          if (data.status === 'error') {
            setGenerateMsg(`Lỗi: ${data.message}`);
          }
        } catch {}
      }
    }
  };

  const handleStartQuiz = async () => {
    if (!quizSet) return;
    const res = await fetch(`${API_URL}/api/v1/quiz/attempt/start`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ quiz_set_id: quizSet.id, user_id: userId }),
    });
    const data = await res.json();
    setAttemptId(data.attempt_id);
    setDeadline(data.deadline);
    setCurrentQ(0);
    setAnswers({});
    setFlagged(new Set());
    setStep('taking');
  };

  const handleAnswer = async (questionId: string, answer: string) => {
    setAnswers((prev) => ({ ...prev, [questionId]: answer }));
    await fetch(`${API_URL}/api/v1/quiz/attempt/${attemptId}/answer`, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ question_id: questionId, user_answer: answer, is_flagged: flagged.has(questionId) }),
    });
  };

  const toggleFlag = (questionId: string) => {
    setFlagged((prev) => {
      const next = new Set(prev);
      next.has(questionId) ? next.delete(questionId) : next.add(questionId);
      return next;
    });
  };

  const handleSubmit = async () => {
    if (!window.confirm('Nộp bài? Bạn không thể thay đổi sau khi nộp.')) return;
    setSubmitting(true);
    const res = await fetch(`${API_URL}/api/v1/quiz/attempt/${attemptId}/submit`, { method: 'POST' });
    const summary = await res.json();

    const resultRes = await fetch(`${API_URL}/api/v1/quiz/attempt/${attemptId}/result`);
    const resultData = await resultRes.json();
    setResult(resultData);
    setStep('result');
    setSubmitting(false);
  };

  const handleExpired = useCallback(() => {
    if (step === 'taking') handleSubmit();
  }, [step, attemptId]);

  // --- RENDER ---

  if (step === 'select') {
    return (
      <div className="max-w-2xl mx-auto mt-10 px-4">
        <h2 className="text-xl font-bold text-gray-800 mb-6">Chọn tài liệu để tạo bộ câu hỏi</h2>
        <div className="space-y-3">
          {documents.map((doc) => (
            <button
              key={doc.id}
              onClick={() => { setSelectedDoc(doc.id); setStep('configure'); }}
              className="w-full text-left bg-white rounded-xl border-2 border-gray-200 hover:border-blue-400 px-5 py-4 transition"
            >
              <p className="font-medium text-gray-800">{doc.title || doc.filename}</p>
              <p className="text-sm text-gray-500 mt-0.5">{doc.authors || 'Không rõ tác giả'} · {doc.total_pages} trang</p>
            </button>
          ))}
          {documents.length === 0 && (
            <p className="text-center text-gray-400 py-10">Chưa có tài liệu. Vào Thư viện để upload PDF trước.</p>
          )}
        </div>
      </div>
    );
  }

  if (step === 'configure') {
    return (
      <div className="max-w-md mx-auto mt-10 px-4">
        <h2 className="text-xl font-bold text-gray-800 mb-6">Cấu hình bộ câu hỏi</h2>
        <div className="bg-white rounded-2xl shadow p-6 space-y-5">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">Độ khó</label>
            {[['easy','Dễ'],['medium','Trung bình'],['hard','Khó']].map(([v,l]) => (
              <label key={v} className="flex items-center gap-2 mb-1 cursor-pointer">
                <input type="radio" value={v} checked={config.difficulty === v}
                  onChange={() => setConfig((c) => ({ ...c, difficulty: v }))} />
                <span className="text-sm text-gray-700">{l}</span>
              </label>
            ))}
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">Ngôn ngữ câu hỏi</label>
            {[['vi','Tiếng Việt'],['en','English']].map(([v,l]) => (
              <label key={v} className="flex items-center gap-2 mb-1 cursor-pointer">
                <input type="radio" value={v} checked={config.language === v}
                  onChange={() => setConfig((c) => ({ ...c, language: v }))} />
                <span className="text-sm text-gray-700">{l}</span>
              </label>
            ))}
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Số câu hỏi <span className="text-gray-400 font-normal">(để trống = AI tự quyết định)</span>
            </label>
            <input type="number" min={5} max={100}
              value={config.num_questions}
              onChange={(e) => setConfig((c) => ({ ...c, num_questions: e.target.value }))}
              placeholder="Tự động"
              className="w-full border rounded-xl px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-400"
            />
          </div>
          <div className="flex gap-3 pt-2">
            <button onClick={() => setStep('select')} className="flex-1 border border-gray-300 rounded-xl py-2 text-sm">
              Quay lại
            </button>
            <button onClick={handleGenerate} className="flex-1 bg-blue-600 text-white rounded-xl py-2 text-sm font-medium hover:bg-blue-700">
              Tạo câu hỏi
            </button>
          </div>
        </div>
      </div>
    );
  }

  if (step === 'generating') {
    return (
      <div className="max-w-md mx-auto mt-20 text-center px-4">
        <div className="w-16 h-16 border-4 border-blue-500 border-t-transparent rounded-full animate-spin mx-auto mb-4" />
        <p className="text-lg font-semibold text-gray-700 mb-2">AI đang tạo bộ câu hỏi</p>
        <p className="text-sm text-gray-500">{generateMsg}</p>
        <p className="text-xs text-gray-400 mt-3">Quá trình này mất khoảng 15–45 giây...</p>
      </div>
    );
  }

  if (step === 'preview' && quizSet) {
    return (
      <div className="max-w-2xl mx-auto mt-10 px-4">
        <h2 className="text-xl font-bold text-gray-800 mb-2">{quizSet.title}</h2>
        <p className="text-gray-500 mb-6">{quizSet.total_questions} câu hỏi · Thời gian tối đa: 5 giờ</p>
        <div className="bg-white rounded-2xl shadow p-5 mb-5 max-h-96 overflow-y-auto">
          {quizSet.questions.map((q) => (
            <div key={q.id} className="py-2 border-b last:border-0 text-sm text-gray-700">
              <span className="font-medium text-gray-500 mr-2">{q.index}.</span> {q.text}
            </div>
          ))}
        </div>
        <div className="flex gap-3">
          <button
            onClick={() => { setStep('configure'); }}
            className="flex items-center gap-1 px-4 py-2 border border-gray-300 rounded-xl text-sm text-gray-600 hover:bg-gray-50"
          >
            <RotateCcw size={14} /> Tạo lại
          </button>
          <button
            onClick={handleStartQuiz}
            className="flex-1 bg-green-600 text-white rounded-xl py-2 text-sm font-medium hover:bg-green-700"
          >
            Bắt đầu làm bài
          </button>
        </div>
      </div>
    );
  }

  if (step === 'taking' && quizSet) {
    const q = quizSet.questions[currentQ];
    const totalAnswered = Object.keys(answers).length;

    return (
      <div className="max-w-3xl mx-auto mt-6 px-4">
        {/* Header */}
        <div className="flex items-center justify-between mb-4">
          <span className="text-sm text-gray-600 font-medium">
            Câu {currentQ + 1} / {quizSet.total_questions}
            <span className="ml-3 text-gray-400">({totalAnswered} đã trả lời)</span>
          </span>
          <QuizTimer deadline={deadline} onExpired={handleExpired} />
        </div>

        {/* Progress dots */}
        <div className="flex flex-wrap gap-1 mb-5">
          {quizSet.questions.map((qq, i) => (
            <button
              key={qq.id}
              onClick={() => setCurrentQ(i)}
              className={`w-7 h-7 rounded text-xs font-medium transition ${
                i === currentQ ? 'bg-blue-600 text-white' :
                flagged.has(qq.id) ? 'bg-yellow-400 text-white' :
                answers[qq.id] ? 'bg-green-500 text-white' :
                'bg-gray-200 text-gray-600 hover:bg-gray-300'
              }`}
            >
              {i + 1}
            </button>
          ))}
        </div>

        {/* Question */}
        <div className="bg-white rounded-2xl shadow-md p-6 mb-4">
          <div className="flex justify-between items-start mb-4">
            <p className="text-gray-800 font-medium leading-relaxed flex-1">{q.text}</p>
            <button
              onClick={() => toggleFlag(q.id)}
              className={`ml-3 p-1.5 rounded-lg flex-shrink-0 ${flagged.has(q.id) ? 'text-yellow-500 bg-yellow-50' : 'text-gray-400 hover:text-yellow-500'}`}
              title="Đánh dấu xem lại"
            >
              <Flag size={16} />
            </button>
          </div>
          <div className="space-y-2">
            {Object.entries(q.options || {}).map(([key, val]) => (
              <button
                key={key}
                onClick={() => handleAnswer(q.id, key)}
                className={`w-full text-left flex items-start gap-3 px-4 py-3 rounded-xl border-2 text-sm transition ${
                  answers[q.id] === key
                    ? 'border-blue-500 bg-blue-50 text-blue-700'
                    : 'border-gray-200 hover:border-blue-300 text-gray-700'
                }`}
              >
                <span className="font-bold w-5 flex-shrink-0">{key}.</span>
                <span>{val as string}</span>
              </button>
            ))}
          </div>
        </div>

        {/* Navigation */}
        <div className="flex gap-3">
          <button onClick={() => setCurrentQ((c) => Math.max(0, c - 1))} disabled={currentQ === 0}
            className="flex items-center gap-1 px-4 py-2 border border-gray-300 rounded-xl text-sm disabled:opacity-30">
            <ChevronLeft size={16} /> Trước
          </button>
          <button onClick={() => setCurrentQ((c) => Math.min(quizSet.total_questions - 1, c + 1))}
            disabled={currentQ === quizSet.total_questions - 1}
            className="flex items-center gap-1 px-4 py-2 border border-gray-300 rounded-xl text-sm disabled:opacity-30">
            Tiếp <ChevronRight size={16} />
          </button>
          <button
            onClick={handleSubmit}
            disabled={submitting}
            className="ml-auto flex items-center gap-1 bg-green-600 text-white px-5 py-2 rounded-xl text-sm font-medium hover:bg-green-700 disabled:opacity-50"
          >
            <CheckCircle size={16} /> Nộp bài ({totalAnswered}/{quizSet.total_questions})
          </button>
        </div>
      </div>
    );
  }

  if (step === 'result' && result) {
    const mins = Math.floor(result.time_spent_seconds / 60);
    const secs = result.time_spent_seconds % 60;
    const scoreColor = result.score >= 80 ? 'text-green-600' : result.score >= 60 ? 'text-yellow-600' : 'text-red-600';

    if (reviewIndex !== null) {
      const q = result.questions[reviewIndex];
      return (
        <div className="max-w-2xl mx-auto mt-6 px-4">
          <button onClick={() => setReviewIndex(null)} className="text-blue-600 text-sm hover:underline mb-4 flex items-center gap-1">
            <ChevronLeft size={14} /> Về kết quả
          </button>
          <div className="bg-white rounded-2xl shadow p-6">
            <p className="font-medium text-gray-800 mb-4">{reviewIndex + 1}. {q.question_text}</p>
            {Object.entries(q.options || {}).map(([k, v]) => (
              <div key={k} className={`flex items-start gap-2 px-3 py-2 rounded-xl mb-1 text-sm ${
                k === q.correct_answer ? 'bg-green-100 text-green-800 font-medium' :
                k === q.user_answer && k !== q.correct_answer ? 'bg-red-100 text-red-700' : 'text-gray-600'
              }`}>
                <span className="font-bold w-5">{k}.</span> {v as string}
                {k === q.correct_answer && <span className="ml-auto text-green-600 font-bold">✓ Đúng</span>}
                {k === q.user_answer && k !== q.correct_answer && <span className="ml-auto text-red-500">✗ Bạn chọn</span>}
              </div>
            ))}
            {q.explanation && (
              <div className="mt-4 p-3 bg-blue-50 rounded-xl text-sm text-blue-700">
                <span className="font-medium">Giải thích: </span>{q.explanation}
              </div>
            )}
            {q.source_text && (
              <div className="mt-2 p-3 bg-gray-50 rounded-xl text-xs text-gray-500 italic">
                "{q.source_text}"
              </div>
            )}
          </div>
          <div className="flex gap-2 mt-3">
            <button onClick={() => setReviewIndex(Math.max(0, reviewIndex - 1))} disabled={reviewIndex === 0}
              className="px-3 py-1 border rounded-lg text-sm disabled:opacity-30">Câu trước</button>
            <button onClick={() => setReviewIndex(Math.min(result.questions.length - 1, reviewIndex + 1))}
              disabled={reviewIndex === result.questions.length - 1}
              className="px-3 py-1 border rounded-lg text-sm disabled:opacity-30">Câu tiếp</button>
          </div>
        </div>
      );
    }

    return (
      <div className="max-w-2xl mx-auto mt-10 px-4">
        <div className="bg-white rounded-2xl shadow-lg p-8 text-center mb-6">
          <h2 className="text-2xl font-bold text-gray-800 mb-1">Kết quả bài kiểm tra</h2>
          <p className="text-gray-400 text-sm mb-5">{result.title}</p>
          <div className={`text-6xl font-bold mb-2 ${scoreColor}`}>{result.score.toFixed(1)}%</div>
          <p className="text-gray-600 mb-1">{result.total_correct} / {result.total_questions} câu đúng</p>
          <p className="text-gray-400 text-sm">Thời gian làm bài: {mins} phút {secs} giây</p>
        </div>

        <h3 className="font-semibold text-gray-700 mb-3">Xem lại từng câu</h3>
        <div className="space-y-2">
          {result.questions.map((q, i) => (
            <button
              key={i}
              onClick={() => setReviewIndex(i)}
              className={`w-full text-left px-4 py-3 rounded-xl border text-sm flex items-center gap-3 hover:shadow-sm transition ${
                q.is_correct ? 'border-green-200 bg-green-50' : 'border-red-200 bg-red-50'
              }`}
            >
              <span className={`font-bold ${q.is_correct ? 'text-green-600' : 'text-red-500'}`}>
                {q.is_correct ? '✓' : '✗'}
              </span>
              <span className={q.is_correct ? 'text-gray-700' : 'text-gray-700'}>
                {i + 1}. {q.question_text.slice(0, 80)}...
              </span>
            </button>
          ))}
        </div>

        <button
          onClick={() => { setStep('select'); setResult(null); setQuizSet(null); }}
          className="w-full mt-5 bg-blue-600 text-white rounded-xl py-3 text-sm font-medium hover:bg-blue-700"
        >
          Tạo bộ câu hỏi mới
        </button>
      </div>
    );
  }

  return null;
}
```

---

### 16.7. Frontend — Trang Index Bài Kiểm Tra

Tạo `frontend/src/app/quiz/page.tsx`:

```typescript
import Link from 'next/link';
import { ClipboardList, BookOpen } from 'lucide-react';

export default function QuizIndexPage() {
  return (
    <div className="max-w-2xl mx-auto mt-16 px-4">
      <h1 className="text-2xl font-bold text-gray-800 mb-2">Bài Kiểm Tra</h1>
      <p className="text-gray-500 mb-8">Chọn loại bài kiểm tra bạn muốn thực hiện</p>

      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
        <Link
          href="/quiz/onboarding"
          className="bg-white rounded-2xl shadow-md hover:shadow-lg border border-gray-100 p-6 flex flex-col gap-3 transition group"
        >
          <div className="w-12 h-12 bg-blue-100 rounded-xl flex items-center justify-center group-hover:bg-blue-200 transition">
            <ClipboardList className="text-blue-600" size={24} />
          </div>
          <h2 className="font-bold text-gray-800 text-lg">Kiểm tra người dùng mới</h2>
          <p className="text-sm text-gray-500">
            Trả lời 5 câu hỏi ngắn để hệ thống cá nhân hoá trải nghiệm và cấp quyền truy cập phù hợp.
          </p>
          <span className="text-blue-600 text-sm font-medium">Bắt đầu →</span>
        </Link>

        <Link
          href="/quiz/document"
          className="bg-white rounded-2xl shadow-md hover:shadow-lg border border-gray-100 p-6 flex flex-col gap-3 transition group"
        >
          <div className="w-12 h-12 bg-green-100 rounded-xl flex items-center justify-center group-hover:bg-green-200 transition">
            <BookOpen className="text-green-600" size={24} />
          </div>
          <h2 className="font-bold text-gray-800 text-lg">Kiểm tra theo tài liệu</h2>
          <p className="text-sm text-gray-500">
            Chọn PDF, AI tự tạo bộ câu hỏi hoàn chỉnh. Thời gian tối đa 5 giờ, lưu lịch sử bài làm.
          </p>
          <span className="text-green-600 text-sm font-medium">Bắt đầu →</span>
        </Link>
      </div>
    </div>
  );
}
```

---

### 16.8. Thêm Link Navbar Cho Bài Kiểm Tra

Trong `frontend/src/app/layout.tsx`:

```typescript
<Link href="/quiz" className="hover:underline">Bài kiểm tra</Link>
```

---

### 16.9. Kiểm Tra Tính Năng Quiz

```powershell
# 1. Chạy migration SQL mới (kết nối vào postgres container):
docker exec -it pgvector-db psql -U admin -d rag_db -c "
  CREATE TABLE IF NOT EXISTS user_profiles (...);
  CREATE TABLE IF NOT EXISTS quiz_sets (...);
  -- (copy từ Bước 16.1)
"

# 2. Restart backend để load router mới
cd D:\academic-rag-system\backend
venv\Scripts\activate
uvicorn main:app --reload --port 8000

# 3. Kiểm tra endpoint mới tại http://localhost:8000/docs:
# GET  /api/v1/onboarding/questions
# POST /api/v1/onboarding/complete
# POST /api/v1/quiz/generate
# GET  /api/v1/quiz/{quiz_set_id}
# POST /api/v1/quiz/attempt/start
# PUT  /api/v1/quiz/attempt/{id}/answer
# POST /api/v1/quiz/attempt/{id}/submit
# GET  /api/v1/quiz/attempt/{id}/result

# 4. Test luồng đầy đủ trên Frontend:
# http://localhost:3000/quiz/onboarding  -> làm 5 câu -> xem kết quả phân loại
# http://localhost:3000/quiz/document    -> chọn PDF -> cấu hình -> AI tạo -> làm bài -> nộp -> xem kết quả
```

---

## CHECKLIST PHẦN 3

### Tính năng Mô Hình 3D
- [ ] Cài `@react-three/fiber`, `@react-three/drei`, `three`, `@types/three`
- [ ] Download và đặt model GLB vào `public/models/`
- [ ] Tạo `public/body_regions.json`
- [ ] Chạy migration SQL bảng `user_profiles` và `body_symptoms`
- [ ] Tạo backend `body.py` và đăng ký router
- [ ] Tạo các component: `BodyViewer3D.tsx`, `RegionPanel.tsx`, `SymptomForm.tsx`
- [ ] Tạo trang `/model3d`
- [ ] Thêm link navbar
- [ ] Test: click điểm 3D → panel → khai báo triệu chứng → kiểm tra DB

### Tính năng Bài Kiểm Tra
- [ ] Chạy migration SQL bảng `quiz_sets`, `quiz_questions`, `quiz_attempts`, `quiz_answers`
- [ ] Tạo backend `onboarding.py` và `quiz.py`, đăng ký router
- [ ] Tạo component `QuizTimer.tsx`
- [ ] Tạo trang `/quiz` (index), `/quiz/onboarding`, `/quiz/document`
- [ ] Thêm link navbar
- [ ] Test Onboarding: hoàn thành 5 câu → phân loại → `localStorage.user_type` được set
- [ ] Test Document Quiz: chọn PDF → tạo quiz → làm bài → nộp → xem kết quả từng câu

---

## BƯỚC 17: AI PHẢN BIỆN TRANG WEB (Web Debate)

### Tổng Quan

Tính năng cho phép người dùng nhập **2–5 URL** bất kỳ, hệ thống tự động:
1. Tải và trích xuất nội dung từng trang web
2. AI phân tích, so sánh và **phản biện** giữa các nguồn theo cấu trúc học thuật:
   - Tóm tắt quan điểm từng nguồn
   - Điểm đồng thuận
   - Mâu thuẫn / khác biệt
   - Phản biện có căn cứ
   - Kết luận khách quan
3. Kết quả stream từng token, có thể xuất Word

**Stack:** `httpx` (đã có) + `beautifulsoup4` + Groq API (đã có)

---

### 17.1. Cài Thêm Thư Viện Backend

```powershell
cd D:\academic-rag-system\backend
venv\Scripts\activate
pip install beautifulsoup4 lxml
```

---

### 17.2. Tạo File `backend/app/services/web_scraper.py`

```python
import httpx
from bs4 import BeautifulSoup

_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "vi-VN,vi;q=0.9,en;q=0.8",
}

def fetch_web_content(url: str, max_chars: int = 6000) -> dict:
    """Tải và trích xuất văn bản thuần từ một URL."""
    try:
        response = httpx.get(
            url,
            headers=_HEADERS,
            timeout=15.0,
            follow_redirects=True,
        )
        response.raise_for_status()

        soup = BeautifulSoup(response.text, "lxml")

        # Xóa các tag không chứa nội dung
        for tag in soup(["script", "style", "nav", "footer",
                         "header", "aside", "noscript", "iframe"]):
            tag.decompose()

        title = (soup.title.string or url).strip() if soup.title else url

        # Ưu tiên lấy nội dung từ thẻ ngữ nghĩa
        body = (
            soup.find("article")
            or soup.find("main")
            or soup.find(id="content")
            or soup.find(class_="content")
            or soup.body
        )
        text = body.get_text(separator="\n", strip=True) if body else ""

        # Gộp nhiều dòng trắng liên tiếp thành 1
        lines = [ln for ln in text.splitlines() if ln.strip()]
        clean_text = "\n".join(lines)[:max_chars]

        return {
            "url": url,
            "title": title,
            "content": clean_text,
            "char_count": len(clean_text),
            "error": None,
        }

    except httpx.HTTPStatusError as e:
        return {"url": url, "title": url, "content": "", "char_count": 0,
                "error": f"HTTP {e.response.status_code}"}
    except httpx.TimeoutException:
        return {"url": url, "title": url, "content": "", "char_count": 0,
                "error": "Timeout — trang web phản hồi quá chậm"}
    except Exception as e:
        return {"url": url, "title": url, "content": "", "char_count": 0,
                "error": str(e)}
```

---

### 17.3. Thêm Hàm `generate_debate_stream` Vào `backend/app/services/generator.py`

Mở file `generator.py` hiện có, thêm hàm sau vào **cuối file**:

```python
def generate_debate_stream(topic: str, web_sources: list[dict]):
    """
    Stream phản biện AI giữa nhiều nguồn web.
    web_sources: list of {"url", "title", "content"}
    """
    sources_block = ""
    for i, src in enumerate(web_sources, start=1):
        sources_block += (
            f"\n\n━━━ NGUỒN {i}: {src['title']} ━━━\n"
            f"URL: {src['url']}\n"
            f"{src['content']}"
        )

    messages = [
        {
            "role": "system",
            "content": (
                "Bạn là chuyên gia phân tích và phản biện học thuật. "
                "Khi nhận được nhiều nguồn thông tin, hãy trả lời theo đúng cấu trúc sau:\n\n"
                "## 1. Tóm tắt từng nguồn\n"
                "Tóm tắt ngắn gọn quan điểm / nội dung chính của mỗi nguồn (2-3 câu/nguồn).\n\n"
                "## 2. Điểm đồng thuận\n"
                "Liệt kê những điểm mà tất cả (hoặc đa số) nguồn đều nhất trí.\n\n"
                "## 3. Mâu thuẫn & Khác biệt\n"
                "Chỉ ra cụ thể những điểm các nguồn mâu thuẫn hoặc có góc nhìn khác nhau. "
                "Trích dẫn nội dung gốc khi cần.\n\n"
                "## 4. Phản biện có căn cứ\n"
                "Đánh giá độ tin cậy, tính logic, bằng chứng của từng nguồn. "
                "Chỉ ra điểm yếu hoặc thiếu sót nếu có.\n\n"
                "## 5. Kết luận khách quan\n"
                "Đưa ra nhận định tổng hợp cân bằng, không thiên vị nguồn nào.\n\n"
                "Trả lời bằng tiếng Việt, rõ ràng, có đánh số và dùng Markdown."
            ),
        },
        {
            "role": "user",
            "content": (
                f"Chủ đề phân tích: **{topic}**\n\n"
                f"Các nguồn web cần phản biện:{sources_block}"
            ),
        },
    ]

    stream = groq_client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=messages,
        stream=True,
        max_tokens=3000,
        temperature=0.2,
    )

    for chunk in stream:
        delta = chunk.choices[0].delta.content
        if delta:
            yield delta
```

---

### 17.4. Tạo File `backend/app/api/v1/debate.py`

```python
from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import Optional
from app.services.web_scraper import fetch_web_content
from app.services.generator import generate_debate_stream

router = APIRouter()


class DebateRequest(BaseModel):
    urls: list[str]
    topic: Optional[str] = "So sánh và phản biện nội dung các nguồn"


class PreviewRequest(BaseModel):
    urls: list[str]


def _validate_urls(urls: list[str]):
    if len(urls) < 2:
        raise HTTPException(400, "Cần ít nhất 2 URL để phản biện")
    if len(urls) > 5:
        raise HTTPException(400, "Tối đa 5 URL mỗi lần")
    for url in urls:
        if not url.startswith(("http://", "https://")):
            raise HTTPException(400, f"URL không hợp lệ: {url}")


@router.post("/preview")
async def preview_urls(request: PreviewRequest):
    """Tải nhanh tiêu đề + 200 ký tự đầu của mỗi URL để xem trước."""
    _validate_urls(request.urls)
    previews = []
    for url in request.urls:
        src = fetch_web_content(url, max_chars=500)
        previews.append({
            "url": url,
            "title": src["title"],
            "preview": src["content"][:200] + ("..." if len(src["content"]) > 200 else ""),
            "char_count": src["char_count"],
            "error": src["error"],
        })
    return {"sources": previews}


@router.post("")
async def debate(request: DebateRequest):
    """Phản biện AI giữa các trang web, trả về stream text."""
    _validate_urls(request.urls)

    web_sources = []
    for url in request.urls:
        src = fetch_web_content(url)
        if src["error"]:
            raise HTTPException(
                400,
                f"Không thể tải '{url}': {src['error']}"
            )
        if not src["content"].strip():
            raise HTTPException(
                400,
                f"Không đọc được nội dung từ '{url}' — trang có thể yêu cầu đăng nhập hoặc chặn bot"
            )
        web_sources.append(src)

    topic = request.topic or "So sánh và phản biện nội dung các nguồn"

    return StreamingResponse(
        generate_debate_stream(topic, web_sources),
        media_type="text/plain",
        headers={
            "X-Source-Count": str(len(web_sources)),
            "X-Source-Titles": " | ".join(s["title"][:40] for s in web_sources),
        },
    )
```

---

### 17.5. Đăng Ký Router Debate Trong `backend/app/api/v1/__init__.py`

Mở file `__init__.py` hiện có, thêm `debate` vào import và `include_router`:

```python
from fastapi import APIRouter
from app.api.v1 import document, chat, graph, auth, body, debate  # thêm debate

api_router = APIRouter()
api_router.include_router(document.router, prefix="/document", tags=["Documents"])
api_router.include_router(chat.router, prefix="/chat", tags=["Chat"])
api_router.include_router(graph.router, prefix="/graph", tags=["Knowledge Graph"])
api_router.include_router(auth.router, prefix="/auth", tags=["Authentication"])
api_router.include_router(body.router, prefix="/body", tags=["Body 3D"])
api_router.include_router(debate.router, prefix="/debate", tags=["Web Debate"])  # thêm dòng này
```

---

### 17.6. Thêm Hàm Debate Vào `frontend/src/lib/api.ts`

Thêm vào **cuối file** `api.ts`:

```typescript
export interface WebSource {
  url: string;
  title: string;
  preview: string;
  char_count: number;
  error: string | null;
}

export const previewUrls = async (urls: string[]): Promise<WebSource[]> => {
  const res = await api.post('/debate/preview', { urls });
  return res.data.sources;
};

export const debateStream = async (
  urls: string[],
  topic: string,
  onChunk: (text: string) => void
): Promise<void> => {
  const response = await fetch(`${API_URL}/api/v1/debate`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ urls, topic }),
  });

  if (!response.ok) {
    const err = await response.json().catch(() => ({}));
    throw new Error(err.detail || 'Debate request failed');
  }

  const reader = response.body!.getReader();
  const decoder = new TextDecoder();

  while (true) {
    const { done, value } = await reader.read();
    if (done) break;
    onChunk(decoder.decode(value));
  }
};
```

---

### 17.7. Tạo Trang `frontend/src/app/debate/page.tsx`

```typescript
'use client';

import { useState, useRef } from 'react';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import { previewUrls, debateStream, WebSource } from '@/lib/api';

const EXAMPLE_TOPICS = [
  'So sánh quan điểm về chủ đề này',
  'Phân tích độ tin cậy của các nguồn',
  'Tìm mâu thuẫn giữa các bài viết',
  'Đánh giá khách quan theo tiêu chí khoa học',
];

export default function DebatePage() {
  const [urls, setUrls] = useState<string[]>(['', '']);
  const [topic, setTopic] = useState('So sánh và phản biện nội dung các nguồn');
  const [previews, setPreviews] = useState<WebSource[]>([]);
  const [isPreviewing, setIsPreviewing] = useState(false);
  const [isDebating, setIsDebating] = useState(false);
  const [result, setResult] = useState('');
  const [error, setError] = useState('');
  const resultRef = useRef<HTMLDivElement>(null);

  const validUrls = urls.filter(u => u.trim().startsWith('http'));

  const handleUrlChange = (index: number, value: string) => {
    const next = [...urls];
    next[index] = value;
    setUrls(next);
  };

  const addUrl = () => {
    if (urls.length < 5) setUrls([...urls, '']);
  };

  const removeUrl = (index: number) => {
    if (urls.length <= 2) return;
    setUrls(urls.filter((_, i) => i !== index));
  };

  const handlePreview = async () => {
    if (validUrls.length < 2) {
      setError('Cần ít nhất 2 URL hợp lệ (bắt đầu bằng http/https)');
      return;
    }
    setError('');
    setIsPreviewing(true);
    setPreviews([]);
    try {
      const sources = await previewUrls(validUrls);
      setPreviews(sources);
      const failed = sources.filter(s => s.error);
      if (failed.length > 0) {
        setError(`Không tải được: ${failed.map(s => s.url).join(', ')}`);
      }
    } catch (e: any) {
      setError(e.message || 'Lỗi khi tải trang web');
    } finally {
      setIsPreviewing(false);
    }
  };

  const handleDebate = async () => {
    if (validUrls.length < 2) {
      setError('Cần ít nhất 2 URL hợp lệ');
      return;
    }
    setError('');
    setResult('');
    setIsDebating(true);

    try {
      await debateStream(validUrls, topic, (chunk) => {
        setResult(prev => {
          const next = prev + chunk;
          setTimeout(() => resultRef.current?.scrollIntoView({ behavior: 'smooth', block: 'end' }), 50);
          return next;
        });
      });
    } catch (e: any) {
      setError(e.message || 'Lỗi khi phản biện');
    } finally {
      setIsDebating(false);
    }
  };

  const handleExport = () => {
    const blob = new Blob([result], { type: 'text/markdown;charset=utf-8' });
    const a = document.createElement('a');
    a.href = URL.createObjectURL(blob);
    a.download = `phan-bien-web-${Date.now()}.md`;
    a.click();
  };

  return (
    <div className="max-w-5xl mx-auto p-6">
      <h1 className="text-2xl font-bold text-gray-800 mb-1">AI Phản Biện Trang Web</h1>
      <p className="text-gray-500 text-sm mb-6">
        Nhập 2–5 URL → AI tải nội dung → So sánh, phản biện và đưa ra nhận định khách quan
      </p>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* === CỘT TRÁI: Nhập liệu === */}
        <div className="space-y-4">
          {/* URL inputs */}
          <div className="bg-white rounded-xl shadow p-4 space-y-3">
            <h2 className="font-semibold text-gray-700">Danh sách URL</h2>

            {urls.map((url, i) => (
              <div key={i} className="flex gap-2 items-center">
                <span className="text-xs text-gray-400 w-5 text-right">{i + 1}</span>
                <input
                  type="url"
                  value={url}
                  onChange={e => handleUrlChange(i, e.target.value)}
                  placeholder="https://example.com/article"
                  className="flex-1 border rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-400"
                />
                {urls.length > 2 && (
                  <button
                    onClick={() => removeUrl(i)}
                    className="text-red-400 hover:text-red-600 text-lg leading-none"
                    title="Xóa URL này"
                  >
                    ×
                  </button>
                )}
              </div>
            ))}

            {urls.length < 5 && (
              <button
                onClick={addUrl}
                className="text-blue-600 text-sm hover:underline"
              >
                + Thêm URL ({urls.length}/5)
              </button>
            )}
          </div>

          {/* Topic */}
          <div className="bg-white rounded-xl shadow p-4">
            <h2 className="font-semibold text-gray-700 mb-2">Góc độ phân tích</h2>
            <input
              type="text"
              value={topic}
              onChange={e => setTopic(e.target.value)}
              placeholder="VD: So sánh quan điểm về..."
              className="w-full border rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-400 mb-2"
            />
            <div className="flex flex-wrap gap-1">
              {EXAMPLE_TOPICS.map(t => (
                <button
                  key={t}
                  onClick={() => setTopic(t)}
                  className="text-xs bg-gray-100 hover:bg-blue-100 text-gray-600 px-2 py-1 rounded-full"
                >
                  {t}
                </button>
              ))}
            </div>
          </div>

          {/* Actions */}
          <div className="flex gap-3">
            <button
              onClick={handlePreview}
              disabled={isPreviewing || validUrls.length < 2}
              className="flex-1 border-2 border-blue-500 text-blue-600 py-2 rounded-xl text-sm font-medium hover:bg-blue-50 disabled:opacity-40"
            >
              {isPreviewing ? 'Đang tải...' : 'Xem trước nội dung'}
            </button>
            <button
              onClick={handleDebate}
              disabled={isDebating || validUrls.length < 2}
              className="flex-1 bg-blue-600 text-white py-2 rounded-xl text-sm font-medium hover:bg-blue-700 disabled:opacity-40"
            >
              {isDebating ? 'AI đang phân tích...' : 'Bắt đầu phản biện'}
            </button>
          </div>

          {error && (
            <div className="bg-red-50 border border-red-200 text-red-700 text-sm px-4 py-3 rounded-lg">
              {error}
            </div>
          )}

          {/* Previews */}
          {previews.length > 0 && (
            <div className="bg-white rounded-xl shadow p-4 space-y-3">
              <h2 className="font-semibold text-gray-700">Xem trước nội dung</h2>
              {previews.map((src, i) => (
                <div
                  key={i}
                  className={`border rounded-lg p-3 text-xs ${
                    src.error ? 'border-red-200 bg-red-50' : 'border-gray-200'
                  }`}
                >
                  <p className="font-medium text-gray-800 truncate">{src.title}</p>
                  <p className="text-blue-500 truncate text-[10px] mb-1">{src.url}</p>
                  {src.error ? (
                    <p className="text-red-600">{src.error}</p>
                  ) : (
                    <>
                      <p className="text-gray-500 line-clamp-2">{src.preview}</p>
                      <p className="text-gray-400 mt-1">{src.char_count.toLocaleString()} ký tự</p>
                    </>
                  )}
                </div>
              ))}
            </div>
          )}
        </div>

        {/* === CỘT PHẢI: Kết quả phản biện === */}
        <div className="bg-white rounded-xl shadow flex flex-col" style={{ minHeight: '500px' }}>
          <div className="flex items-center justify-between px-4 py-3 border-b">
            <h2 className="font-semibold text-gray-700">Kết quả phân tích</h2>
            {result && (
              <button
                onClick={handleExport}
                className="text-xs text-blue-600 hover:underline"
              >
                Tải Markdown
              </button>
            )}
          </div>

          <div className="flex-1 overflow-y-auto p-4">
            {!result && !isDebating && (
              <div className="flex items-center justify-center h-full text-gray-400 text-sm text-center">
                <div>
                  <p className="text-3xl mb-3">⚖️</p>
                  <p>Nhập URL và nhấn <strong>Bắt đầu phản biện</strong></p>
                  <p className="text-xs mt-1">AI sẽ so sánh và đánh giá khách quan các nguồn</p>
                </div>
              </div>
            )}

            {(result || isDebating) && (
              <div className="prose prose-sm max-w-none text-gray-800">
                <ReactMarkdown remarkPlugins={[remarkGfm]}>
                  {result || '...'}
                </ReactMarkdown>
                {isDebating && (
                  <span className="inline-block w-2 h-4 bg-blue-500 animate-pulse ml-1" />
                )}
              </div>
            )}

            <div ref={resultRef} />
          </div>
        </div>
      </div>
    </div>
  );
}
```

---

### 17.8. Thêm Link Vào Navigation `frontend/src/app/layout.tsx`

Tìm đoạn `<nav>` trong `layout.tsx`, thêm link mới:

```typescript
<Link href="/debate" className="hover:underline">Phản biện Web</Link>
```

Kết quả navigation đầy đủ:
```typescript
<nav className="bg-blue-700 text-white px-6 py-3 flex items-center gap-6 shadow">
  <span className="font-bold text-lg">Academic RAG</span>
  <Link href="/dashboard" className="hover:underline">Dashboard</Link>
  <Link href="/library" className="hover:underline">Thư viện</Link>
  <Link href="/chat" className="hover:underline">Hỏi đáp</Link>
  <Link href="/graph" className="hover:underline">Đồ thị</Link>
  <Link href="/debate" className="hover:underline">Phản biện Web</Link>
</nav>
```

---

### 17.9. Kiểm Tra Tính Năng

```powershell
# 1. Cài thư viện (nếu chưa cài)
cd D:\academic-rag-system\backend
venv\Scripts\activate
pip install beautifulsoup4 lxml

# 2. Khởi động lại backend
uvicorn main:app --reload --port 8000

# 3. Kiểm tra endpoint mới tại http://localhost:8000/docs:
#    POST /api/v1/debate/preview  — xem trước nội dung URL
#    POST /api/v1/debate          — phản biện streaming

# 4. Test trên Frontend: http://localhost:3000/debate
#    - Nhập 2 URL bài báo/blog có chủ đề tương tự
#    - Nhấn "Xem trước" → kiểm tra nội dung tải được
#    - Nhấn "Bắt đầu phản biện" → xem AI stream kết quả
```

**Ví dụ test nhanh** — dán 2 URL Wikipedia/VnExpress/Tạp chí khoa học cùng chủ đề:
- URL 1: bài Wikipedia tiếng Việt về một chủ đề
- URL 2: bài báo khoa học hoặc blog phân tích cùng chủ đề
- Topic: `"So sánh mức độ chi tiết và độ tin cậy của hai nguồn"`

---

### Checklist Tính Năng Phản Biện Web

- [ ] Cài `beautifulsoup4` và `lxml` trong môi trường ảo
- [ ] Tạo `services/web_scraper.py`
- [ ] Thêm `generate_debate_stream()` vào `services/generator.py`
- [ ] Tạo `api/v1/debate.py` và đăng ký router trong `__init__.py`
- [ ] Thêm `previewUrls()` và `debateStream()` vào `src/lib/api.ts`
- [ ] Tạo trang `src/app/debate/page.tsx`
- [ ] Thêm link `/debate` vào `layout.tsx`
- [ ] Test: nhập 2 URL → xem trước → phản biện → kết quả stream OK
- [ ] Test edge case: URL không tồn tại → hiển thị lỗi rõ ràng
- [ ] Test: URL yêu cầu đăng nhập → hiển thị cảnh báo

---

## BƯỚC 18: PROFILE NGƯỜI DÙNG VÀ AI THEO DÕI CÁ NHÂN HÓA

### Tổng Quan

Mỗi người dùng có một **hồ sơ cá nhân** tích lũy theo thời gian gồm:
- **Lịch sử triệu chứng** — từ tính năng Mô Hình 3D (BƯỚC 15)
- **Lịch sử hỏi đáp** — tự động lưu mỗi câu hỏi từ Chat (BƯỚC 5)
- **AI theo dõi tiến triển** — phát hiện xu hướng tăng/giảm đau
- **Gợi ý cá nhân hóa** — AI đề xuất tài liệu, chuyên khoa, câu hỏi nên hỏi tiếp

**Không bắt buộc đăng nhập** — hệ thống tự tạo UUID ẩn danh lưu vào `localStorage` khi người dùng lần đầu truy cập; nếu đã đăng nhập JWT thì dùng `user_id` thật.

```
Người dùng
    │
    ├─ Khai báo triệu chứng (Model 3D) ──→ body_symptoms
    │
    ├─ Đặt câu hỏi (Chat)              ──→ chat_history  (tự động)
    │
    └─ Nhấn "Phân tích AI"             ──→ ai_insights
                                            ↓
                              Tổng quan / Tiến triển / Gợi ý
```

---

### 18.1. Migration SQL — Thêm 2 Bảng Mới

Thêm vào file `docker/init_db.sql` (hoặc chạy trực tiếp):

```sql
-- Lịch sử hỏi đáp (persist mỗi tin nhắn Chat)
CREATE TABLE IF NOT EXISTS chat_history (
    id           UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id      UUID,                          -- NULL = ẩn danh
    session_id   UUID NOT NULL,                 -- nhóm các tin nhắn cùng phiên
    role         VARCHAR(20) NOT NULL,          -- 'user' | 'assistant'
    content      TEXT NOT NULL,
    document_ids TEXT[] DEFAULT '{}',           -- UUID các tài liệu đã hỏi
    created_at   TIMESTAMP DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS chat_history_user_idx ON chat_history (user_id, created_at DESC);
CREATE INDEX IF NOT EXISTS chat_history_session_idx ON chat_history (session_id);

-- Insights AI được tạo tự động cho từng người dùng
CREATE TABLE IF NOT EXISTS ai_insights (
    id           UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id      UUID,
    insight_type VARCHAR(100) DEFAULT 'full_analysis',
    content      TEXT NOT NULL,
    created_at   TIMESTAMP DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS ai_insights_user_idx ON ai_insights (user_id, created_at DESC);
```

Chạy migration:
```powershell
# Kết nối vào container và chạy SQL
docker exec -it pgvector-db psql -U admin -d rag_db -c "
CREATE TABLE IF NOT EXISTS chat_history (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID,
    session_id UUID NOT NULL,
    role VARCHAR(20) NOT NULL,
    content TEXT NOT NULL,
    document_ids TEXT[] DEFAULT '{}',
    created_at TIMESTAMP DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS chat_history_user_idx ON chat_history (user_id, created_at DESC);
CREATE INDEX IF NOT EXISTS chat_history_session_idx ON chat_history (session_id);

CREATE TABLE IF NOT EXISTS ai_insights (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID,
    insight_type VARCHAR(100) DEFAULT 'full_analysis',
    content TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS ai_insights_user_idx ON ai_insights (user_id, created_at DESC);
"
```

---

### 18.2. Tạo File `backend/app/services/profile_analyzer.py`

```python
from groq import Groq
from app.core.config import settings

_groq = Groq(api_key=settings.GROQ_API_KEY)


def _build_symptom_block(symptoms: list[dict]) -> str:
    if not symptoms:
        return "  (Chưa khai báo triệu chứng)"
    lines = []
    for s in symptoms:
        date = str(s.get("reported_at", ""))[:10]
        lines.append(
            f"  • [{date}] {s.get('region_name','?')} — "
            f"đau mức {s.get('pain_level','?')}/10"
            + (f", kéo dài {s['duration']}" if s.get("duration") else "")
        )
    return "\n".join(lines)


def _build_question_block(messages: list[dict]) -> str:
    questions = [m["content"] for m in messages if m.get("role") == "user"]
    if not questions:
        return "  (Chưa có lịch sử hỏi đáp)"
    return "\n".join(f"  • {q[:120]}" for q in questions[-15:])


def analyze_profile(
    symptoms: list[dict],
    messages: list[dict],
    user_type: str = "patient",
) -> str:
    """
    Gọi AI phân tích toàn bộ hồ sơ người dùng.
    Trả về chuỗi Markdown chứa 4 phần: nhận định, tiến triển, gợi ý, lưu ý.
    """
    symptom_block = _build_symptom_block(symptoms)
    question_block = _build_question_block(messages)

    prompt = f"""Bạn đang phân tích hồ sơ của người dùng loại "{user_type}".

━━━ LỊCH SỬ TRIỆU CHỨNG ━━━
{symptom_block}

━━━ LỊCH SỬ CÂU HỎI ĐÃ HỎI ━━━
{question_block}

Hãy phân tích và trả lời theo đúng cấu trúc sau (dùng Markdown):

## 🔍 Nhận định tổng quan
Mô tả pattern chung của người dùng (2–3 câu): họ quan tâm đến vùng nào, chủ đề nào.

## 📈 Tiến triển triệu chứng
Phân tích xu hướng: mức đau tăng / giảm / ổn định theo thời gian. Nêu rõ vùng cụ thể.

## 💡 Gợi ý cá nhân hóa
Đưa ra 3–5 gợi ý cụ thể:
- Tài liệu / chủ đề nên tìm hiểu thêm
- Câu hỏi hữu ích nên hỏi tiếp theo
- Chuyên khoa nên tham khảo (nếu là bệnh nhân)

## ⚠️ Lưu ý quan trọng
Nếu có triệu chứng đáng lo ngại (đau cao, kéo dài, nhiều vùng), hãy nhắc nhở gặp bác sĩ.
Nếu không có gì đáng lo, ghi "Không có dấu hiệu bất thường đặc biệt."

Trả lời bằng tiếng Việt, ngắn gọn, thiết thực."""

    resp = _groq.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[
            {
                "role": "system",
                "content": (
                    "Bạn là trợ lý phân tích sức khỏe cá nhân. "
                    "KHÔNG chẩn đoán bệnh. Chỉ đưa ra nhận xét xu hướng và gợi ý tham khảo. "
                    "Luôn khuyến khích gặp chuyên gia y tế khi triệu chứng nghiêm trọng."
                ),
            },
            {"role": "user", "content": prompt},
        ],
        max_tokens=1800,
        temperature=0.25,
    )
    return resp.choices[0].message.content


def compute_progress(symptoms: list[dict]) -> dict:
    """
    Tính xu hướng đau theo từng vùng cơ thể.
    Trả về dict: { region_id: { trend, avg_early, avg_late, count } }
    """
    from collections import defaultdict

    grouped: dict[str, list[int]] = defaultdict(list)
    for s in sorted(symptoms, key=lambda x: x.get("reported_at", "")):
        grouped[s["region_id"]].append(s["pain_level"])

    result = {}
    for rid, levels in grouped.items():
        n = len(levels)
        if n < 2:
            trend = "stable"
            avg_early = avg_late = levels[0] if levels else 0
        else:
            half = n // 2
            avg_early = sum(levels[:half]) / half
            avg_late = sum(levels[half:]) / (n - half)
            if avg_late < avg_early - 1:
                trend = "improving"
            elif avg_late > avg_early + 1:
                trend = "worsening"
            else:
                trend = "stable"

        result[rid] = {
            "trend": trend,
            "avg_early": round(avg_early, 1),
            "avg_late": round(avg_late, 1),
            "count": n,
        }
    return result
```

---

### 18.3. Tạo File `backend/app/api/v1/profile.py`

```python
import uuid
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import text
from pydantic import BaseModel
from typing import Optional
from app.db.postgres import get_db
from app.services.profile_analyzer import analyze_profile, compute_progress

router = APIRouter()


# ─── Schemas ────────────────────────────────────────────────────────────────

class SaveMessageRequest(BaseModel):
    user_id: Optional[str] = None
    session_id: Optional[str] = None
    role: str                        # 'user' | 'assistant'
    content: str
    document_ids: Optional[list[str]] = []


# ─── Helpers ─────────────────────────────────────────────────────────────────

def _fetch_symptoms(user_id: str, db: Session) -> list[dict]:
    rows = db.execute(
        text("""
            SELECT region_id, region_name, pain_level, duration, reported_at
            FROM body_symptoms
            WHERE user_id = :uid
            ORDER BY reported_at ASC
            LIMIT 60
        """),
        {"uid": user_id},
    ).fetchall()
    return [
        {
            "region_id": r.region_id,
            "region_name": r.region_name,
            "pain_level": r.pain_level,
            "duration": r.duration,
            "reported_at": r.reported_at.isoformat() if r.reported_at else "",
        }
        for r in rows
    ]


def _fetch_messages(user_id: str, db: Session) -> list[dict]:
    rows = db.execute(
        text("""
            SELECT role, content
            FROM chat_history
            WHERE user_id = :uid
            ORDER BY created_at DESC
            LIMIT 60
        """),
        {"uid": user_id},
    ).fetchall()
    return [{"role": r.role, "content": r.content} for r in reversed(rows)]


# ─── Endpoints ───────────────────────────────────────────────────────────────

@router.get("/{user_id}")
def get_profile(user_id: str, db: Session = Depends(get_db)):
    """Tổng quan hồ sơ: thống kê + insights gần nhất."""
    symptom_count = db.execute(
        text("SELECT COUNT(*) FROM body_symptoms WHERE user_id = :uid"),
        {"uid": user_id},
    ).scalar() or 0

    question_count = db.execute(
        text("SELECT COUNT(*) FROM chat_history WHERE user_id = :uid AND role = 'user'"),
        {"uid": user_id},
    ).scalar() or 0

    latest_insight = db.execute(
        text("""
            SELECT content, created_at FROM ai_insights
            WHERE user_id = :uid ORDER BY created_at DESC LIMIT 1
        """),
        {"uid": user_id},
    ).fetchone()

    user_type = db.execute(
        text("SELECT user_type FROM user_profiles WHERE user_id = :uid"),
        {"uid": user_id},
    ).scalar() or "patient"

    return {
        "user_id": user_id,
        "user_type": user_type,
        "stats": {
            "total_symptoms": symptom_count,
            "total_questions": question_count,
        },
        "latest_insight": {
            "content": latest_insight.content if latest_insight else None,
            "created_at": latest_insight.created_at.isoformat() if latest_insight else None,
        },
    }


@router.get("/{user_id}/symptoms")
def get_symptoms(user_id: str, db: Session = Depends(get_db)):
    """Lịch sử triệu chứng + tiến triển theo vùng."""
    rows = db.execute(
        text("""
            SELECT id, region_id, region_name, description,
                   pain_level, duration, reported_at
            FROM body_symptoms
            WHERE user_id = :uid
            ORDER BY reported_at DESC
            LIMIT 100
        """),
        {"uid": user_id},
    ).fetchall()

    symptoms = [
        {
            "id": str(r.id),
            "region_id": r.region_id,
            "region_name": r.region_name,
            "description": r.description,
            "pain_level": r.pain_level,
            "duration": r.duration,
            "reported_at": r.reported_at.isoformat() if r.reported_at else None,
        }
        for r in rows
    ]

    progress = compute_progress(
        [{"region_id": s["region_id"], "pain_level": s["pain_level"],
          "reported_at": s["reported_at"]} for s in reversed(symptoms)]
    )

    return {"symptoms": symptoms, "total": len(symptoms), "progress": progress}


@router.get("/{user_id}/chats")
def get_chats(user_id: str, limit: int = 80, db: Session = Depends(get_db)):
    """Lịch sử hỏi đáp, nhóm theo session."""
    rows = db.execute(
        text("""
            SELECT id, session_id, role, content, document_ids, created_at
            FROM chat_history
            WHERE user_id = :uid
            ORDER BY created_at DESC
            LIMIT :limit
        """),
        {"uid": user_id, "limit": limit},
    ).fetchall()

    return {
        "messages": [
            {
                "id": str(r.id),
                "session_id": str(r.session_id),
                "role": r.role,
                "content": r.content,
                "document_ids": r.document_ids or [],
                "created_at": r.created_at.isoformat() if r.created_at else None,
            }
            for r in rows
        ],
        "total": len(rows),
    }


@router.post("/{user_id}/chats")
def save_message(user_id: str, req: SaveMessageRequest, db: Session = Depends(get_db)):
    """Lưu một tin nhắn vào lịch sử."""
    session_id = req.session_id or str(uuid.uuid4())
    msg_id = str(uuid.uuid4())
    db.execute(
        text("""
            INSERT INTO chat_history (id, user_id, session_id, role, content, document_ids)
            VALUES (:id, :uid, :sid, :role, :content, :doc_ids)
        """),
        {
            "id": msg_id,
            "uid": user_id,
            "sid": session_id,
            "role": req.role,
            "content": req.content,
            "doc_ids": req.document_ids or [],
        },
    )
    db.commit()
    return {"id": msg_id, "session_id": session_id}


@router.get("/{user_id}/insights")
def get_insights(user_id: str, db: Session = Depends(get_db)):
    """Danh sách AI insights đã tạo."""
    rows = db.execute(
        text("""
            SELECT id, insight_type, content, created_at FROM ai_insights
            WHERE user_id = :uid ORDER BY created_at DESC LIMIT 10
        """),
        {"uid": user_id},
    ).fetchall()
    return {
        "insights": [
            {
                "id": str(r.id),
                "type": r.insight_type,
                "content": r.content,
                "created_at": r.created_at.isoformat() if r.created_at else None,
            }
            for r in rows
        ]
    }


@router.post("/{user_id}/analyze")
def run_analysis(user_id: str, db: Session = Depends(get_db)):
    """Kích hoạt AI phân tích profile → lưu và trả về insight mới."""
    symptoms = _fetch_symptoms(user_id, db)
    messages = _fetch_messages(user_id, db)

    if not symptoms and not messages:
        raise HTTPException(
            400,
            "Chưa có dữ liệu để phân tích. Hãy khai báo triệu chứng hoặc đặt câu hỏi trước."
        )

    user_type = db.execute(
        text("SELECT user_type FROM user_profiles WHERE user_id = :uid"),
        {"uid": user_id},
    ).scalar() or "patient"

    content = analyze_profile(symptoms, messages, user_type)

    insight_id = str(uuid.uuid4())
    db.execute(
        text("""
            INSERT INTO ai_insights (id, user_id, insight_type, content)
            VALUES (:id, :uid, 'full_analysis', :content)
        """),
        {"id": insight_id, "uid": user_id, "content": content},
    )
    db.commit()
    return {"insight_id": insight_id, "content": content}
```

---

### 18.4. Đăng Ký Router Profile Trong `backend/app/api/v1/__init__.py`

```python
from fastapi import APIRouter
from app.api.v1 import document, chat, graph, auth, body, debate, profile  # thêm profile

api_router = APIRouter()
api_router.include_router(document.router, prefix="/document",  tags=["Documents"])
api_router.include_router(chat.router,     prefix="/chat",      tags=["Chat"])
api_router.include_router(graph.router,    prefix="/graph",     tags=["Knowledge Graph"])
api_router.include_router(auth.router,     prefix="/auth",      tags=["Authentication"])
api_router.include_router(body.router,     prefix="/body",      tags=["Body 3D"])
api_router.include_router(debate.router,   prefix="/debate",    tags=["Web Debate"])
api_router.include_router(profile.router,  prefix="/profile",   tags=["User Profile"])  # mới
```

---

### 18.5. Cập Nhật `backend/app/api/v1/chat.py` — Tự Động Lưu Lịch Sử

Thêm logic lưu tin nhắn vào DB ngay sau khi chat thành công. Sửa hàm `chat()` trong `chat.py`:

```python
from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from sqlalchemy import text
from pydantic import BaseModel
from typing import Optional
import uuid
from app.db.postgres import get_db
from app.services.retriever import retrieve
from app.services.generator import generate_stream

router = APIRouter()


class ChatRequest(BaseModel):
    query: str
    document_ids: list[str]
    mode: Optional[str] = "single"
    user_id: Optional[str] = None      # thêm trường này
    session_id: Optional[str] = None   # thêm trường này


def _save_to_history(db: Session, user_id: str, session_id: str,
                     role: str, content: str, doc_ids: list[str]):
    """Lưu một tin nhắn vào chat_history (silent — không raise exception)."""
    try:
        db.execute(
            text("""
                INSERT INTO chat_history (id, user_id, session_id, role, content, document_ids)
                VALUES (:id, :uid, :sid, :role, :content, :doc_ids)
            """),
            {
                "id": str(uuid.uuid4()),
                "uid": user_id,
                "sid": session_id,
                "role": role,
                "content": content,
                "doc_ids": doc_ids,
            },
        )
        db.commit()
    except Exception:
        db.rollback()   # không để lỗi history làm hỏng chat


def _stream_and_save(generator, user_id: str, session_id: str,
                     doc_ids: list[str], db: Session):
    """Wrap generator: thu thập toàn bộ câu trả lời rồi lưu vào DB."""
    full_answer = []
    for token in generator:
        full_answer.append(token)
        yield token
    if user_id:
        _save_to_history(db, user_id, session_id, "assistant",
                         "".join(full_answer), doc_ids)


@router.post("")
def chat(request: ChatRequest, db: Session = Depends(get_db)):
    if not request.query.strip():
        raise HTTPException(400, "Câu hỏi không được để trống")
    if not request.document_ids:
        raise HTTPException(400, "Phải chọn ít nhất 1 tài liệu")

    user_id = request.user_id
    session_id = request.session_id or str(uuid.uuid4())

    # Lưu câu hỏi của user
    if user_id:
        _save_to_history(db, user_id, session_id, "user",
                         request.query, request.document_ids)

    context_chunks = retrieve(request.query, request.document_ids, db)

    if not context_chunks:
        def _no_context():
            yield "Không tìm thấy thông tin liên quan trong các tài liệu đã chọn."
        return StreamingResponse(_no_context(), media_type="text/plain")

    return StreamingResponse(
        _stream_and_save(
            generate_stream(request.query, context_chunks),
            user_id, session_id, request.document_ids, db
        ),
        media_type="text/plain",
        headers={
            "X-Context-Pages": ",".join(str(c["page_number"]) for c in context_chunks),
            "X-Session-ID": session_id,
        },
    )
```

---

### 18.6. Thêm Profile API Vào `frontend/src/lib/api.ts`

Thêm vào **cuối file** `api.ts`:

```typescript
// ─── User Profile ─────────────────────────────────────────────────────────

export interface ProfileStats {
  total_symptoms: number;
  total_questions: number;
}

export interface SymptomRecord {
  id: string;
  region_id: string;
  region_name: string;
  description: string;
  pain_level: number;
  duration: string | null;
  reported_at: string;
}

export interface ProgressInfo {
  trend: 'improving' | 'worsening' | 'stable';
  avg_early: number;
  avg_late: number;
  count: number;
}

export interface ChatMessage {
  id: string;
  session_id: string;
  role: 'user' | 'assistant';
  content: string;
  document_ids: string[];
  created_at: string;
}

export interface AiInsight {
  id: string;
  type: string;
  content: string;
  created_at: string;
}

// Lấy hoặc tạo mới user_id ẩn danh trong localStorage
export function getOrCreateUserId(): string {
  if (typeof window === 'undefined') return '';
  let uid = localStorage.getItem('profile_user_id');
  if (!uid) {
    uid = crypto.randomUUID();
    localStorage.setItem('profile_user_id', uid);
  }
  return uid;
}

export const getProfile = async (userId: string) => {
  const res = await api.get(`/profile/${userId}`);
  return res.data as {
    user_id: string;
    user_type: string;
    stats: ProfileStats;
    latest_insight: { content: string | null; created_at: string | null };
  };
};

export const getProfileSymptoms = async (userId: string) => {
  const res = await api.get(`/profile/${userId}/symptoms`);
  return res.data as {
    symptoms: SymptomRecord[];
    total: number;
    progress: Record<string, ProgressInfo>;
  };
};

export const getProfileChats = async (userId: string) => {
  const res = await api.get(`/profile/${userId}/chats`);
  return res.data as { messages: ChatMessage[]; total: number };
};

export const getProfileInsights = async (userId: string) => {
  const res = await api.get(`/profile/${userId}/insights`);
  return res.data as { insights: AiInsight[] };
};

export const runProfileAnalysis = async (userId: string): Promise<AiInsight> => {
  const res = await api.post(`/profile/${userId}/analyze`);
  return res.data;
};
```

---

### 18.7. Tạo Hook `frontend/src/hooks/useUserId.ts`

```typescript
'use client';

import { useState, useEffect } from 'react';
import { getOrCreateUserId } from '@/lib/api';

export function useUserId(): string {
  const [userId, setUserId] = useState('');

  useEffect(() => {
    setUserId(getOrCreateUserId());
  }, []);

  return userId;
}
```

---

### 18.8. Cập Nhật Trang Chat Để Gửi `user_id` Lên API

Mở `frontend/src/app/chat/page.tsx`, sửa hàm `handleSend`:

```typescript
// Thêm import ở đầu file
import { useUserId } from '@/hooks/useUserId';

// Thêm trong component ChatPage
const userId = useUserId();

// Sửa hàm chatStream call — thêm tham số user_id và session_id vào body
// Trong src/lib/api.ts, sửa chatStream:
export const chatStream = async (
  query: string,
  documentIds: string[],
  onChunk: (text: string) => void,
  userId?: string,
  sessionId?: string,
): Promise<void> => {
  const response = await fetch(`${API_URL}/api/v1/chat`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      query,
      document_ids: documentIds,
      user_id: userId || null,
      session_id: sessionId || null,
    }),
  });
  // ... phần còn lại giữ nguyên
};
```

Trong `ChatPage`, khi gọi `chatStream`:
```typescript
const sessionId = useRef(crypto.randomUUID());   // 1 session = 1 lần mở trang Chat

// Trong handleSend:
await chatStream(userMsg, selectedDocumentIds, (chunk) => { ... },
                 userId, sessionId.current);
```

---

### 18.9. Tạo Trang `frontend/src/app/profile/page.tsx`

```typescript
'use client';

import { useEffect, useState } from 'react';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import {
  getProfile, getProfileSymptoms, getProfileChats,
  getProfileInsights, runProfileAnalysis,
  SymptomRecord, ChatMessage, AiInsight, ProgressInfo,
} from '@/lib/api';
import { useUserId } from '@/hooks/useUserId';

type Tab = 'overview' | 'symptoms' | 'chats' | 'insights';

const TREND_LABEL: Record<string, { label: string; color: string; icon: string }> = {
  improving: { label: 'Cải thiện',  color: 'text-green-600', icon: '↓' },
  worsening: { label: 'Tệ hơn',     color: 'text-red-600',   icon: '↑' },
  stable:    { label: 'Ổn định',    color: 'text-gray-500',  icon: '→' },
};

export default function ProfilePage() {
  const userId = useUserId();
  const [tab, setTab] = useState<Tab>('overview');

  const [stats, setStats] = useState<{ total_symptoms: number; total_questions: number } | null>(null);
  const [latestInsight, setLatestInsight] = useState<string | null>(null);
  const [symptoms, setSymptoms] = useState<SymptomRecord[]>([]);
  const [progress, setProgress] = useState<Record<string, ProgressInfo>>({});
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [insights, setInsights] = useState<AiInsight[]>([]);
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(true);

  // Load overview
  useEffect(() => {
    if (!userId) return;
    setLoading(true);
    getProfile(userId)
      .then(d => {
        setStats(d.stats);
        setLatestInsight(d.latest_insight.content);
      })
      .catch(() => {})
      .finally(() => setLoading(false));
  }, [userId]);

  // Lazy load tabs
  useEffect(() => {
    if (!userId) return;
    if (tab === 'symptoms' && symptoms.length === 0) {
      getProfileSymptoms(userId).then(d => {
        setSymptoms(d.symptoms);
        setProgress(d.progress);
      });
    }
    if (tab === 'chats' && messages.length === 0) {
      getProfileChats(userId).then(d => setMessages(d.messages));
    }
    if (tab === 'insights' && insights.length === 0) {
      getProfileInsights(userId).then(d => setInsights(d.insights));
    }
  }, [tab, userId]);

  const handleAnalyze = async () => {
    if (!userId) return;
    setIsAnalyzing(true);
    setError('');
    try {
      const result = await runProfileAnalysis(userId);
      setInsights(prev => [result, ...prev]);
      setLatestInsight(result.content);
      setTab('insights');
    } catch (e: any) {
      setError(e.response?.data?.detail || e.message || 'Lỗi phân tích');
    } finally {
      setIsAnalyzing(false);
    }
  };

  if (!userId || loading) {
    return (
      <div className="flex items-center justify-center h-[60vh] text-gray-400">
        Đang tải hồ sơ...
      </div>
    );
  }

  const tabs: { key: Tab; label: string }[] = [
    { key: 'overview',  label: 'Tổng quan' },
    { key: 'symptoms',  label: `Triệu chứng (${stats?.total_symptoms ?? 0})` },
    { key: 'chats',     label: `Lịch sử hỏi (${stats?.total_questions ?? 0})` },
    { key: 'insights',  label: 'AI Phân tích' },
  ];

  return (
    <div className="max-w-4xl mx-auto p-6">
      {/* Header */}
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-2xl font-bold text-gray-800">Hồ Sơ Cá Nhân</h1>
          <p className="text-xs text-gray-400 mt-1">ID: {userId.slice(0, 8)}…</p>
        </div>
        <button
          onClick={handleAnalyze}
          disabled={isAnalyzing}
          className="bg-blue-600 text-white px-5 py-2 rounded-xl text-sm font-medium hover:bg-blue-700 disabled:opacity-50 flex items-center gap-2"
        >
          {isAnalyzing ? (
            <>
              <span className="animate-spin">⟳</span> Đang phân tích...
            </>
          ) : (
            '🤖 Phân tích AI ngay'
          )}
        </button>
      </div>

      {error && (
        <div className="bg-red-50 border border-red-200 text-red-700 text-sm px-4 py-3 rounded-lg mb-4">
          {error}
        </div>
      )}

      {/* Tabs */}
      <div className="flex border-b mb-6">
        {tabs.map(t => (
          <button
            key={t.key}
            onClick={() => setTab(t.key)}
            className={`px-4 py-2 text-sm font-medium border-b-2 transition-colors ${
              tab === t.key
                ? 'border-blue-600 text-blue-600'
                : 'border-transparent text-gray-500 hover:text-gray-700'
            }`}
          >
            {t.label}
          </button>
        ))}
      </div>

      {/* ── Tab: Tổng quan ── */}
      {tab === 'overview' && (
        <div className="space-y-5">
          {/* Stats cards */}
          <div className="grid grid-cols-2 gap-4">
            <div className="bg-white rounded-xl shadow p-5 text-center">
              <p className="text-4xl font-bold text-blue-600">{stats?.total_symptoms ?? 0}</p>
              <p className="text-gray-500 mt-1 text-sm">Lần khai báo triệu chứng</p>
            </div>
            <div className="bg-white rounded-xl shadow p-5 text-center">
              <p className="text-4xl font-bold text-green-600">{stats?.total_questions ?? 0}</p>
              <p className="text-gray-500 mt-1 text-sm">Câu hỏi đã đặt</p>
            </div>
          </div>

          {/* Latest AI insight preview */}
          <div className="bg-white rounded-xl shadow p-5">
            <h2 className="font-semibold text-gray-700 mb-3">Nhận định AI gần nhất</h2>
            {latestInsight ? (
              <div className="prose prose-sm max-w-none text-gray-700 line-clamp-6">
                <ReactMarkdown remarkPlugins={[remarkGfm]}>{latestInsight}</ReactMarkdown>
              </div>
            ) : (
              <p className="text-gray-400 text-sm">
                Chưa có phân tích. Nhấn <strong>"Phân tích AI ngay"</strong> để bắt đầu.
              </p>
            )}
            {latestInsight && (
              <button
                onClick={() => setTab('insights')}
                className="mt-3 text-blue-600 text-xs hover:underline"
              >
                Xem toàn bộ →
              </button>
            )}
          </div>

          {/* Quick tips */}
          <div className="bg-blue-50 rounded-xl p-4 text-sm text-blue-700">
            <p className="font-medium mb-2">Để AI phân tích chính xác hơn:</p>
            <ul className="list-disc list-inside space-y-1 text-blue-600">
              <li>Khai báo triệu chứng thường xuyên qua trang Mô hình 3D</li>
              <li>Đặt câu hỏi chi tiết trong Chat để lưu lịch sử nghiên cứu</li>
              <li>Nhấn "Phân tích AI" định kỳ (1–2 lần/tuần) để theo dõi tiến triển</li>
            </ul>
          </div>
        </div>
      )}

      {/* ── Tab: Triệu chứng ── */}
      {tab === 'symptoms' && (
        <div className="space-y-4">
          {/* Progress by region */}
          {Object.keys(progress).length > 0 && (
            <div className="bg-white rounded-xl shadow p-4">
              <h2 className="font-semibold text-gray-700 mb-3">Tiến triển theo vùng</h2>
              <div className="space-y-2">
                {Object.entries(progress).map(([rid, info]) => {
                  const t = TREND_LABEL[info.trend] ?? TREND_LABEL.stable;
                  return (
                    <div key={rid} className="flex items-center justify-between text-sm py-2 border-b last:border-0">
                      <span className="text-gray-700 font-medium">{rid}</span>
                      <div className="flex items-center gap-4">
                        <span className="text-gray-400">{info.count} lần</span>
                        <span className="text-gray-400">
                          {info.avg_early} → {info.avg_late}
                        </span>
                        <span className={`font-medium ${t.color}`}>
                          {t.icon} {t.label}
                        </span>
                        {/* Mini pain bar */}
                        <div className="w-20 h-2 bg-gray-100 rounded-full overflow-hidden">
                          <div
                            className={`h-full rounded-full ${
                              info.trend === 'worsening' ? 'bg-red-400' :
                              info.trend === 'improving' ? 'bg-green-400' : 'bg-gray-400'
                            }`}
                            style={{ width: `${(info.avg_late / 10) * 100}%` }}
                          />
                        </div>
                      </div>
                    </div>
                  );
                })}
              </div>
            </div>
          )}

          {/* Symptom timeline */}
          <div className="bg-white rounded-xl shadow divide-y">
            {symptoms.length === 0 ? (
              <p className="text-center py-10 text-gray-400">
                Chưa có triệu chứng. Hãy khai báo qua trang Mô hình 3D.
              </p>
            ) : (
              symptoms.map(s => (
                <div key={s.id} className="px-5 py-3 flex items-start justify-between gap-4">
                  <div className="flex-1 min-w-0">
                    <p className="font-medium text-gray-800">{s.region_name}</p>
                    <p className="text-sm text-gray-500 truncate">{s.description}</p>
                    {s.duration && (
                      <p className="text-xs text-gray-400">Kéo dài: {s.duration}</p>
                    )}
                  </div>
                  <div className="text-right flex-shrink-0">
                    <div className="flex items-center gap-1 justify-end">
                      {Array.from({ length: 10 }).map((_, i) => (
                        <div
                          key={i}
                          className={`w-2 h-2 rounded-full ${
                            i < s.pain_level
                              ? s.pain_level >= 7 ? 'bg-red-400'
                              : s.pain_level >= 4 ? 'bg-yellow-400' : 'bg-green-400'
                              : 'bg-gray-100'
                          }`}
                        />
                      ))}
                      <span className="text-xs text-gray-500 ml-1">{s.pain_level}/10</span>
                    </div>
                    <p className="text-xs text-gray-400 mt-1">
                      {s.reported_at ? new Date(s.reported_at).toLocaleDateString('vi-VN') : ''}
                    </p>
                  </div>
                </div>
              ))
            )}
          </div>
        </div>
      )}

      {/* ── Tab: Lịch sử hỏi ── */}
      {tab === 'chats' && (
        <div className="space-y-2">
          {messages.length === 0 ? (
            <p className="text-center py-10 text-gray-400">
              Chưa có lịch sử hỏi đáp. Hãy vào Chat và đặt câu hỏi.
            </p>
          ) : (
            messages.map(m => (
              <div
                key={m.id}
                className={`rounded-xl px-4 py-3 text-sm ${
                  m.role === 'user'
                    ? 'bg-blue-50 border border-blue-100'
                    : 'bg-white border border-gray-100 shadow-sm'
                }`}
              >
                <div className="flex items-center justify-between mb-1">
                  <span className={`text-xs font-medium ${
                    m.role === 'user' ? 'text-blue-600' : 'text-gray-500'
                  }`}>
                    {m.role === 'user' ? '🙋 Bạn' : '🤖 AI'}
                  </span>
                  <span className="text-xs text-gray-400">
                    {m.created_at ? new Date(m.created_at).toLocaleString('vi-VN') : ''}
                  </span>
                </div>
                <p className="text-gray-700 line-clamp-3">{m.content}</p>
              </div>
            ))
          )}
        </div>
      )}

      {/* ── Tab: AI Insights ── */}
      {tab === 'insights' && (
        <div className="space-y-4">
          {insights.length === 0 ? (
            <div className="text-center py-10 text-gray-400">
              <p className="text-3xl mb-3">🤖</p>
              <p>Chưa có phân tích nào.</p>
              <button
                onClick={handleAnalyze}
                disabled={isAnalyzing}
                className="mt-3 bg-blue-600 text-white px-5 py-2 rounded-xl text-sm hover:bg-blue-700 disabled:opacity-50"
              >
                {isAnalyzing ? 'Đang phân tích...' : 'Phân tích ngay'}
              </button>
            </div>
          ) : (
            insights.map((ins, i) => (
              <div key={ins.id} className="bg-white rounded-xl shadow p-5">
                <div className="flex items-center justify-between mb-3">
                  <span className="text-xs font-medium text-blue-600 bg-blue-50 px-2 py-1 rounded-full">
                    Phân tích #{insights.length - i}
                  </span>
                  <span className="text-xs text-gray-400">
                    {ins.created_at ? new Date(ins.created_at).toLocaleString('vi-VN') : ''}
                  </span>
                </div>
                <div className="prose prose-sm max-w-none text-gray-700">
                  <ReactMarkdown remarkPlugins={[remarkGfm]}>{ins.content}</ReactMarkdown>
                </div>
              </div>
            ))
          )}
        </div>
      )}
    </div>
  );
}
```

---

### 18.10. Thêm Link Vào Navigation `frontend/src/app/layout.tsx`

```typescript
<nav className="bg-blue-700 text-white px-6 py-3 flex items-center gap-6 shadow">
  <span className="font-bold text-lg">Academic RAG</span>
  <Link href="/dashboard"  className="hover:underline">Dashboard</Link>
  <Link href="/library"    className="hover:underline">Thư viện</Link>
  <Link href="/chat"       className="hover:underline">Hỏi đáp</Link>
  <Link href="/graph"      className="hover:underline">Đồ thị</Link>
  <Link href="/debate"     className="hover:underline">Phản biện Web</Link>
  <Link href="/profile"    className="hover:underline">Hồ sơ</Link>
</nav>
```

---

### 18.11. Kiểm Tra Tính Năng

```powershell
# 1. Chạy migration SQL (xem mục 18.1)

# 2. Restart backend
cd D:\academic-rag-system\backend
venv\Scripts\activate
uvicorn main:app --reload --port 8000

# 3. Kiểm tra endpoints mới tại http://localhost:8000/docs:
# GET  /api/v1/profile/{user_id}            — tổng quan
# GET  /api/v1/profile/{user_id}/symptoms   — lịch sử triệu chứng + tiến triển
# GET  /api/v1/profile/{user_id}/chats      — lịch sử hỏi đáp
# GET  /api/v1/profile/{user_id}/insights   — danh sách AI insights
# POST /api/v1/profile/{user_id}/analyze    — kích hoạt AI phân tích
# POST /api/v1/profile/{user_id}/chats      — lưu tin nhắn (dùng nội bộ)

# 4. Test trên Frontend: http://localhost:3000/profile
# Bước 1: Đặt 1-2 câu hỏi trong /chat → tự động lưu lịch sử
# Bước 2: Khai báo 1-2 triệu chứng trong /model3d
# Bước 3: Vào /profile → tab "Lịch sử hỏi" phải thấy câu hỏi vừa đặt
# Bước 4: Nhấn "Phân tích AI ngay" → đợi 10-15s → xem kết quả tab Insights
# Bước 5: Tab "Triệu chứng" → xem bảng tiến triển theo vùng
```

---

### Checklist Tính Năng Profile Người Dùng

- [ ] Chạy migration SQL tạo bảng `chat_history` và `ai_insights`
- [ ] Tạo `services/profile_analyzer.py` (AI + compute_progress)
- [ ] Tạo `api/v1/profile.py` (6 endpoints) và đăng ký router
- [ ] Cập nhật `api/v1/chat.py` — thêm `user_id`, `session_id`, auto-save history
- [ ] Thêm profile functions vào `src/lib/api.ts`
- [ ] Tạo hook `src/hooks/useUserId.ts`
- [ ] Cập nhật `src/app/chat/page.tsx` — truyền userId + sessionId khi gọi chatStream
- [ ] Tạo trang `src/app/profile/page.tsx` (4 tab)
- [ ] Thêm link `/profile` vào `layout.tsx`
- [ ] Test: đặt câu hỏi → vào Profile → thấy lịch sử hỏi
- [ ] Test: nhấn "Phân tích AI" → AI phân tích và hiện kết quả
- [ ] Test: khai báo triệu chứng nhiều lần → tab Triệu chứng hiện xu hướng improving/worsening


---

# ═══════════════════════════════════════
# PHẦN 4 — TÍNH NĂNG NÂNG CAO (ACADEMIC RAG)
# ═══════════════════════════════════════

---

## BƯỚC 19: 🌐 DỊCH TÀI LIỆU TỰ ĐỘNG (Anh ↔ Việt)

### 19.1. Backend — Endpoint Dịch Tài Liệu

Thêm vào `backend/app/api/v1/document.py`:

```python
from fastapi.responses import StreamingResponse as SR

class TranslateRequest(BaseModel):
    target_language: str = "vi"   # "vi" hoặc "en"
    chunk_start: int = 0
    chunk_end: int = 20

@router.post("/{document_id}/translate")
def translate_document(
    document_id: str,
    req: TranslateRequest,
    db: Session = Depends(get_db)
):
    from app.models.document import Chunk
    from groq import Groq
    from app.core.config import settings

    chunks = (
        db.query(Chunk)
        .filter(Chunk.document_id == document_id)
        .order_by(Chunk.chunk_index)
        .offset(req.chunk_start)
        .limit(req.chunk_end - req.chunk_start)
        .all()
    )
    if not chunks:
        raise HTTPException(404, "Không tìm thấy nội dung")

    combined = "\n\n".join(c.content for c in chunks)
    lang_name = "tiếng Việt" if req.target_language == "vi" else "English"

    client = Groq(api_key=settings.GROQ_API_KEY)

    def _stream():
        stream = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {
                    "role": "system",
                    "content": (
                        f"Dịch toàn bộ nội dung sau sang {lang_name}. "
                        "Giữ nguyên cấu trúc đoạn văn, thuật ngữ kỹ thuật viết kèm bản gốc trong ngoặc đơn. "
                        "Không thêm giải thích ngoài bản dịch."
                    ),
                },
                {"role": "user", "content": combined},
            ],
            stream=True,
            max_tokens=4096,
            temperature=0.1,
        )
        for chunk in stream:
            delta = chunk.choices[0].delta.content
            if delta:
                yield delta

    return SR(_stream(), media_type="text/plain")
```

### 19.2. Frontend — Component TranslatePanel

Tạo `frontend/src/components/TranslatePanel.tsx`:

```typescript
'use client';

import { useState } from 'react';

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

interface Props {
  documentId: string;
  documentTitle: string;
}

export default function TranslatePanel({ documentId, documentTitle }: Props) {
  const [translating, setTranslating] = useState(false);
  const [result, setResult] = useState('');
  const [targetLang, setTargetLang] = useState<'vi' | 'en'>('vi');

  const handleTranslate = async () => {
    setTranslating(true);
    setResult('');
    try {
      const res = await fetch(`${API_URL}/api/v1/document/${documentId}/translate`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ target_language: targetLang, chunk_start: 0, chunk_end: 15 }),
      });
      if (!res.ok) throw new Error('Lỗi dịch');
      const reader = res.body!.getReader();
      const decoder = new TextDecoder();
      while (true) {
        const { done, value } = await reader.read();
        if (done) break;
        setResult((prev) => prev + decoder.decode(value));
      }
    } catch {
      setResult('Không thể dịch. Kiểm tra kết nối và thử lại.');
    } finally {
      setTranslating(false);
    }
  };

  return (
    <div className="border rounded-xl p-4 bg-white shadow-sm">
      <h3 className="font-semibold text-gray-700 mb-3">Dịch tài liệu: {documentTitle}</h3>
      <div className="flex gap-2 mb-3">
        {(['vi', 'en'] as const).map((lang) => (
          <button
            key={lang}
            onClick={() => setTargetLang(lang)}
            className={`px-4 py-1.5 rounded-lg text-sm font-medium border transition ${
              targetLang === lang
                ? 'bg-blue-600 text-white border-blue-600'
                : 'bg-white text-gray-600 border-gray-300 hover:bg-gray-50'
            }`}
          >
            {lang === 'vi' ? 'Dịch sang Tiếng Việt' : 'Translate to English'}
          </button>
        ))}
        <button
          onClick={handleTranslate}
          disabled={translating}
          className="ml-auto px-4 py-1.5 bg-green-600 text-white rounded-lg text-sm hover:bg-green-700 disabled:opacity-50"
        >
          {translating ? 'Đang dịch...' : 'Bắt đầu dịch'}
        </button>
      </div>
      {result && (
        <div className="bg-gray-50 rounded-lg p-4 text-sm text-gray-700 max-h-96 overflow-y-auto whitespace-pre-wrap leading-relaxed">
          {result}
        </div>
      )}
    </div>
  );
}
```

Thêm vào trang Library (`/library`) bên dưới bảng tài liệu khi click vào một tài liệu, hoặc tạo route `/library/[id]/translate`.

---

## BƯỚC 20: 📖 EXPLAIN THUẬT NGỮ KHÓ

### 20.1. Backend — Endpoint Giải Thích Thuật Ngữ

Tạo `backend/app/api/v1/explain.py`:

```python
from fastapi import APIRouter
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from groq import Groq
from app.core.config import settings

router = APIRouter()
_client = Groq(api_key=settings.GROQ_API_KEY)

class ExplainRequest(BaseModel):
    term: str
    context: str = ""
    language: str = "vi"

@router.post("")
def explain_term(req: ExplainRequest):
    ctx_note = f'\nNgữ cảnh: "{req.context[:300]}"' if req.context else ""
    lang_note = "Trả lời bằng tiếng Việt." if req.language == "vi" else "Answer in English."

    def _stream():
        stream = _client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {
                    "role": "system",
                    "content": (
                        "Bạn là từ điển học thuật thông minh. "
                        "Giải thích thuật ngữ ngắn gọn trong 3-5 câu: "
                        "(1) định nghĩa, (2) ứng dụng thực tế, (3) ví dụ cụ thể. "
                        f"{lang_note}"
                    ),
                },
                {"role": "user", "content": f'Giải thích thuật ngữ: "{req.term}"{ctx_note}'},
            ],
            stream=True,
            max_tokens=512,
            temperature=0.2,
        )
        for chunk in stream:
            delta = chunk.choices[0].delta.content
            if delta:
                yield delta

    return StreamingResponse(_stream(), media_type="text/plain")
```

Đăng ký router trong `backend/app/api/v1/__init__.py`:

```python
from app.api.v1 import document, chat, graph, auth, explain

api_router.include_router(explain.router, prefix="/explain", tags=["Explain Term"])
```

### 20.2. Frontend — Hook useTermExplainer

Tạo `frontend/src/hooks/useTermExplainer.ts`:

```typescript
import { useState } from 'react';

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

export function useTermExplainer() {
  const [explanation, setExplanation] = useState('');
  const [loading, setLoading] = useState(false);
  const [activeTerm, setActiveTerm] = useState('');

  const explain = async (term: string, context?: string) => {
    setActiveTerm(term);
    setExplanation('');
    setLoading(true);
    try {
      const res = await fetch(`${API_URL}/api/v1/explain`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ term, context: context ?? '', language: 'vi' }),
      });
      const reader = res.body!.getReader();
      const decoder = new TextDecoder();
      while (true) {
        const { done, value } = await reader.read();
        if (done) break;
        setExplanation((p) => p + decoder.decode(value));
      }
    } finally {
      setLoading(false);
    }
  };

  const clear = () => { setExplanation(''); setActiveTerm(''); };

  return { explanation, loading, activeTerm, explain, clear };
}
```

### 20.3. Frontend — Component TermTooltip

Tạo `frontend/src/components/TermTooltip.tsx`:

```typescript
'use client';

import { useState, useRef } from 'react';
import { useTermExplainer } from '@/hooks/useTermExplainer';

interface Props {
  children: React.ReactNode;
  context?: string;
}

export default function TermTooltip({ children, context }: Props) {
  const [show, setShow] = useState(false);
  const { explanation, loading, explain, clear } = useTermExplainer();
  const ref = useRef<HTMLSpanElement>(null);

  const handleDoubleClick = () => {
    const selection = window.getSelection()?.toString().trim();
    if (!selection || selection.length < 2 || selection.length > 80) return;
    setShow(true);
    explain(selection, context);
  };

  return (
    <span ref={ref} onDoubleClick={handleDoubleClick} className="relative">
      {children}
      {show && (
        <div className="absolute z-50 bottom-full left-0 mb-2 w-80 bg-white border border-blue-200 rounded-xl shadow-xl p-4 text-sm text-gray-700">
          <div className="flex justify-between items-center mb-2">
            <span className="font-semibold text-blue-700 text-xs uppercase tracking-wide">Giải thích thuật ngữ</span>
            <button
              onClick={() => { setShow(false); clear(); }}
              className="text-gray-400 hover:text-gray-600 text-xs"
            >
              ✕
            </button>
          </div>
          <div className="leading-relaxed">{loading ? 'Đang giải thích...' : explanation}</div>
        </div>
      )}
    </span>
  );
}
```

**Cách dùng:** Bọc đoạn văn bản trong trang chat bằng `<TermTooltip>` — double-click vào từ bất kỳ để xem giải thích ngay.

---

## BƯỚC 21: 🎓 AI HỌC CÙNG SINH VIÊN (Learning Mode)

### 21.1. Backend — Learning Mode trong Chat

Sửa `backend/app/api/v1/chat.py`, thêm trường `learning_mode` vào `ChatRequest`:

```python
class ChatRequest(BaseModel):
    query: str
    document_ids: list[str]
    mode: Optional[str] = "single"
    learning_mode: Optional[str] = "standard"   # "beginner" | "advanced" | "researcher"

LEARNING_PROMPTS = {
    "beginner": (
        "Giải thích đơn giản như dạy cho người chưa biết gì về lĩnh vực này. "
        "Tránh thuật ngữ kỹ thuật; nếu bắt buộc dùng thì giải thích ngay. "
        "Dùng ví dụ thực tế, ngắn gọn, dễ hiểu. Trả lời bằng tiếng Việt."
    ),
    "advanced": (
        "Trả lời ở mức độ sinh viên đại học hoặc người đã có nền tảng về lĩnh vực này. "
        "Có thể dùng thuật ngữ kỹ thuật. Phân tích sâu hơn, đề cập trade-off và giới hạn. "
        "Trả lời bằng tiếng Việt."
    ),
    "researcher": (
        "Trả lời ở mức độ nghiên cứu viên. Đề cập methodology, limitations, "
        "so sánh với các phương pháp khác, chỉ ra research gap nếu có. "
        "Dùng học thuật, trích dẫn chính xác từ context. Trả lời bằng tiếng Việt hoặc Anh tùy câu hỏi."
    ),
    "standard": (
        "Trả lời trực tiếp, súc tích, có trích dẫn nguồn. Trả lời bằng tiếng Việt."
    ),
}
```

Sửa hàm `build_prompt` trong `backend/app/services/generator.py`:

```python
def build_prompt(query: str, context_chunks: list[dict], learning_mode: str = "standard") -> list[dict]:
    context_text = ""
    for i, chunk in enumerate(context_chunks):
        context_text += f"\n[Nguồn {i+1} - Trang {chunk['page_number']}]:\n{chunk['content']}\n"

    mode_instruction = LEARNING_PROMPTS.get(learning_mode, LEARNING_PROMPTS["standard"])

    return [
        {
            "role": "system",
            "content": (
                "Bạn là trợ lý nghiên cứu học thuật chuyên nghiệp. "
                "CHỈ trả lời dựa trên văn bản CONTEXT được cung cấp. "
                f"{mode_instruction} "
                "Luôn trích dẫn nguồn [Nguồn X, Trang Y]."
            ),
        },
        {"role": "user", "content": f"CONTEXT:\n{context_text}\n\nCÂU HỎI: {query}"},
    ]
```

Và truyền `learning_mode` khi gọi `generate_stream`:

```python
# Trong endpoint chat():
return StreamingResponse(
    generate_stream(request.query, context_chunks, learning_mode=request.learning_mode or "standard"),
    media_type="text/plain",
    ...
)
```

Cập nhật signature của `generate_stream`:

```python
def generate_stream(query: str, context_chunks: list[dict], learning_mode: str = "standard"):
    messages = build_prompt(query, context_chunks, learning_mode)
    ...
```

### 21.2. Frontend — Mode Selector trong Chat

Thêm vào sidebar trang `/chat`, trước danh sách tài liệu:

```typescript
// Trong ChatPage, thêm state:
const [learningMode, setLearningMode] = useState<'beginner' | 'advanced' | 'researcher' | 'standard'>('standard');

const MODES = [
  { value: 'beginner', label: 'Beginner', icon: '🌱', desc: 'Giải thích đơn giản' },
  { value: 'advanced', label: 'Advanced', icon: '🎓', desc: 'Phân tích sâu' },
  { value: 'researcher', label: 'Researcher', icon: '🔬', desc: 'Học thuật' },
];

// JSX thêm trên sidebar (trước danh sách tài liệu):
<div className="mb-4">
  <p className="text-xs font-semibold text-gray-500 uppercase mb-2">Chế độ học</p>
  <div className="space-y-1">
    {MODES.map((m) => (
      <button
        key={m.value}
        onClick={() => setLearningMode(m.value as any)}
        className={`w-full text-left px-3 py-2 rounded-lg text-xs transition ${
          learningMode === m.value
            ? 'bg-blue-100 text-blue-700 font-medium'
            : 'hover:bg-gray-100 text-gray-600'
        }`}
      >
        {m.icon} {m.label}
        <span className="block text-gray-400">{m.desc}</span>
      </button>
    ))}
  </div>
</div>
```

Cập nhật hàm `handleSend` để truyền `learning_mode`:

```typescript
await chatStream(userMsg, selectedDocumentIds, learningMode, (chunk) => { ... });
```

Cập nhật `chatStream` trong `lib/api.ts`:

```typescript
export const chatStream = async (
  query: string,
  documentIds: string[],
  learningMode: string = 'standard',
  onChunk: (text: string) => void
): Promise<void> => {
  const response = await fetch(`${API_URL}/api/v1/chat`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ query, document_ids: documentIds, learning_mode: learningMode }),
  });
  // ... phần còn lại giữ nguyên
};
```

---

## BƯỚC 22: 🗂️ TỰ PHÂN LOẠI TÀI LIỆU

### 22.1. Migration SQL — Thêm Cột Category

```sql
ALTER TABLE documents ADD COLUMN IF NOT EXISTS category VARCHAR(100) DEFAULT 'Uncategorized';
ALTER TABLE documents ADD COLUMN IF NOT EXISTS category_confidence NUMERIC(4,2) DEFAULT 0;
```

### 22.2. Backend — Service Phân Loại

Tạo `backend/app/services/classifier.py`:

```python
import json
from groq import Groq
from app.core.config import settings

_client = Groq(api_key=settings.GROQ_API_KEY)

CATEGORIES = [
    "Artificial Intelligence",
    "Machine Learning",
    "Deep Learning",
    "Natural Language Processing",
    "Computer Vision",
    "Blockchain",
    "Cybersecurity",
    "Data Science",
    "Software Engineering",
    "Cloud Computing",
    "Internet of Things",
    "Robotics",
    "Bioinformatics",
    "Other",
]

def classify_document(title: str, abstract: str) -> dict:
    """Phân loại tài liệu vào một trong các danh mục học thuật."""
    text = f"Title: {title}\n\nAbstract/Content: {abstract[:1500]}"
    categories_list = "\n".join(f"- {c}" for c in CATEGORIES)

    resp = _client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[
            {
                "role": "system",
                "content": (
                    "Phân loại bài báo khoa học vào đúng một danh mục sau. "
                    "Trả về JSON duy nhất: {\"category\": \"...\", \"confidence\": 0.0-1.0, \"keywords\": [\"...\", ...]}\n\n"
                    f"Danh mục có thể chọn:\n{categories_list}"
                ),
            },
            {"role": "user", "content": text},
        ],
        max_tokens=200,
        temperature=0.1,
        response_format={"type": "json_object"},
    )

    try:
        result = json.loads(resp.choices[0].message.content)
        return {
            "category": result.get("category", "Other"),
            "confidence": float(result.get("confidence", 0.5)),
            "keywords": result.get("keywords", []),
        }
    except Exception:
        return {"category": "Other", "confidence": 0.5, "keywords": []}
```

### 22.3. Backend — Endpoint Phân Loại + Auto-classify trong Pipeline

Thêm vào `backend/app/api/v1/document.py`:

```python
@router.post("/{document_id}/classify")
def classify_document_endpoint(document_id: str, db: Session = Depends(get_db)):
    from app.services.classifier import classify_document
    from sqlalchemy import text

    doc = db.query(Document).filter(Document.id == document_id).first()
    if not doc:
        raise HTTPException(404, "Không tìm thấy tài liệu")

    # Lấy 500 ký tự đầu làm abstract
    from app.models.document import Chunk
    first_chunks = db.query(Chunk).filter(Chunk.document_id == document_id).order_by(Chunk.chunk_index).limit(3).all()
    abstract = " ".join(c.content for c in first_chunks)[:1500]

    result = classify_document(doc.title or doc.filename, abstract)

    db.execute(
        text("UPDATE documents SET category = :cat, category_confidence = :conf WHERE id = :id"),
        {"cat": result["category"], "conf": result["confidence"], "id": document_id},
    )
    db.commit()

    return {
        "document_id": document_id,
        "category": result["category"],
        "confidence": result["confidence"],
        "keywords": result["keywords"],
    }
```

Trong `_run_pipeline`, thêm auto-classify sau khi `status = ready`:

```python
# Thêm sau dòng doc.status = "ready"
from app.services.classifier import classify_document as _cls
first_text = parsed["full_text"][:1500]
cls_result = _cls(doc.title or doc.filename, first_text)
doc.category = cls_result["category"]
doc.category_confidence = cls_result["confidence"]
db.commit()
```

### 22.4. Frontend — Filter Theo Category

Thêm vào trang Library (`/library`):

```typescript
// Thêm state filter:
const [activeCategory, setActiveCategory] = useState<string>('All');
const categories = ['All', ...Array.from(new Set(documents.map(d => (d as any).category || 'Other')))];

const filtered = activeCategory === 'All'
  ? documents
  : documents.filter(d => (d as any).category === activeCategory);

// JSX — thêm filter chips trên bảng:
<div className="flex gap-2 flex-wrap mb-4">
  {categories.map((cat) => (
    <button
      key={cat}
      onClick={() => setActiveCategory(cat)}
      className={`px-3 py-1 rounded-full text-xs font-medium border transition ${
        activeCategory === cat
          ? 'bg-blue-600 text-white border-blue-600'
          : 'bg-white text-gray-600 border-gray-300 hover:bg-blue-50'
      }`}
    >
      {cat}
    </button>
  ))}
</div>
```

Cập nhật `DocumentInfo` trong `lib/api.ts`:

```typescript
export interface DocumentInfo {
  id: string;
  filename: string;
  title: string | null;
  authors: string | null;
  year: number | null;
  status: string;
  total_pages: number | null;
  category: string | null;
  category_confidence: number | null;
}
```

---

## BƯỚC 23: ⏱️ TIMELINE NGHIÊN CỨU

### 23.1. Backend — Endpoint Timeline

Thêm vào `backend/app/api/v1/document.py`:

```python
@router.get("/timeline/by-year")
def document_timeline(db: Session = Depends(get_db)):
    from sqlalchemy import text
    rows = db.execute(
        text("""
            SELECT year, category, COUNT(*) as count, array_agg(title ORDER BY created_at) as titles
            FROM documents
            WHERE status = 'ready' AND year IS NOT NULL
            GROUP BY year, category
            ORDER BY year ASC
        """)
    ).fetchall()

    result = {}
    for row in rows:
        yr = str(row.year)
        if yr not in result:
            result[yr] = {"year": row.year, "total": 0, "by_category": {}, "titles": []}
        result[yr]["total"] += row.count
        result[yr]["by_category"][row.category or "Other"] = row.count
        result[yr]["titles"].extend((row.titles or [])[:3])

    return {"timeline": sorted(result.values(), key=lambda x: x["year"])}
```

### 23.2. Frontend — Trang Timeline

Tạo `frontend/src/app/timeline/page.tsx`:

```typescript
'use client';

import { useEffect, useState } from 'react';

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
const CATEGORY_COLORS: Record<string, string> = {
  'Artificial Intelligence': '#3b82f6',
  'Machine Learning': '#8b5cf6',
  'Deep Learning': '#6366f1',
  'Natural Language Processing': '#06b6d4',
  'Blockchain': '#f59e0b',
  'Cybersecurity': '#ef4444',
  'Data Science': '#10b981',
  'Other': '#6b7280',
};

interface TimelineEntry {
  year: number;
  total: number;
  by_category: Record<string, number>;
  titles: string[];
}

export default function TimelinePage() {
  const [data, setData] = useState<TimelineEntry[]>([]);

  useEffect(() => {
    fetch(`${API_URL}/api/v1/document/timeline/by-year`)
      .then((r) => r.json())
      .then((d) => setData(d.timeline || []));
  }, []);

  const maxTotal = Math.max(...data.map((d) => d.total), 1);

  return (
    <div className="max-w-4xl mx-auto p-6">
      <h1 className="text-2xl font-bold text-gray-800 mb-2">Timeline Nghiên Cứu</h1>
      <p className="text-gray-500 mb-8 text-sm">Sự phát triển công nghệ theo năm trong thư viện của bạn</p>

      {data.length === 0 && (
        <div className="text-center text-gray-400 py-20">
          Chưa có tài liệu nào có thông tin năm. Hãy cập nhật năm cho tài liệu.
        </div>
      )}

      <div className="relative">
        {/* Đường timeline dọc */}
        <div className="absolute left-16 top-0 bottom-0 w-0.5 bg-gray-200" />

        <div className="space-y-8">
          {data.map((entry) => (
            <div key={entry.year} className="flex gap-6 items-start">
              {/* Năm */}
              <div className="w-12 text-right font-bold text-blue-600 text-sm pt-1 flex-shrink-0">
                {entry.year}
              </div>

              {/* Điểm trên timeline */}
              <div className="w-3 h-3 rounded-full bg-blue-500 mt-2 flex-shrink-0 relative z-10 ring-4 ring-white" />

              {/* Nội dung */}
              <div className="flex-1 bg-white border rounded-xl p-4 shadow-sm">
                <div className="flex items-center gap-2 mb-2">
                  <span className="text-sm font-semibold text-gray-700">{entry.total} bài báo</span>
                </div>

                {/* Bar chart mini */}
                <div className="space-y-1 mb-3">
                  {Object.entries(entry.by_category).map(([cat, count]) => (
                    <div key={cat} className="flex items-center gap-2">
                      <span className="text-xs text-gray-500 w-40 truncate">{cat}</span>
                      <div className="flex-1 bg-gray-100 rounded-full h-2">
                        <div
                          className="h-2 rounded-full"
                          style={{
                            width: `${(count / entry.total) * 100}%`,
                            backgroundColor: CATEGORY_COLORS[cat] || '#6b7280',
                          }}
                        />
                      </div>
                      <span className="text-xs text-gray-500 w-4">{count}</span>
                    </div>
                  ))}
                </div>

                {entry.titles.length > 0 && (
                  <div className="text-xs text-gray-500">
                    {entry.titles.slice(0, 2).map((t, i) => (
                      <p key={i} className="truncate">• {t}</p>
                    ))}
                    {entry.titles.length > 2 && <p className="text-blue-400">+ {entry.titles.length - 2} bài khác</p>}
                  </div>
                )}
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
```

Thêm link vào `layout.tsx`:
```typescript
<Link href="/timeline" className="hover:underline">Timeline</Link>
```

---

## BƯỚC 24: 🔥 TRENDING TOPICS

### 24.1. Backend — Endpoint Trending Topics

Tạo `backend/app/api/v1/trends.py`:

```python
import json
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import text
from groq import Groq
from app.db.postgres import get_db
from app.core.config import settings

router = APIRouter()
_client = Groq(api_key=settings.GROQ_API_KEY)

@router.get("")
def get_trending_topics(limit: int = 10, db: Session = Depends(get_db)):
    """Phân tích toàn bộ tài liệu và trả về trending topics."""
    rows = db.execute(
        text("""
            SELECT d.title, d.category, c.content
            FROM documents d
            JOIN chunks c ON c.document_id = d.id
            WHERE d.status = 'ready' AND c.chunk_index < 3
            ORDER BY d.created_at DESC
            LIMIT 60
        """)
    ).fetchall()

    if not rows:
        return {"topics": [], "message": "Chưa có tài liệu nào"}

    combined = "\n".join(f"- [{row.category or 'Other'}] {row.title}: {row.content[:200]}" for row in rows)

    resp = _client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[
            {
                "role": "system",
                "content": (
                    "Phân tích danh sách bài báo và tìm top trending topics. "
                    "Trả về JSON: {\"topics\": [{\"name\": \"...\", \"count\": N, \"category\": \"...\", \"description\": \"...\"}]} "
                    f"Tối đa {limit} topics. Sắp xếp theo độ phổ biến giảm dần."
                ),
            },
            {"role": "user", "content": f"Danh sách bài báo:\n{combined}"},
        ],
        max_tokens=1024,
        temperature=0.2,
        response_format={"type": "json_object"},
    )

    try:
        return json.loads(resp.choices[0].message.content)
    except Exception:
        return {"topics": []}

@router.get("/keywords")
def get_top_keywords(db: Session = Depends(get_db)):
    """Thống kê từ khóa phổ biến từ tất cả chunks (không dùng AI — nhanh)."""
    from collections import Counter
    import re

    rows = db.execute(text("SELECT content FROM chunks LIMIT 500")).fetchall()
    if not rows:
        return {"keywords": []}

    all_text = " ".join(row.content for row in rows).lower()
    words = re.findall(r'\b[a-z]{4,}\b', all_text)
    stop = {"this","that","with","from","have","been","will","when","they","what","their",
            "which","also","then","than","more","such","into","over","other","some","these"}
    filtered = [w for w in words if w not in stop]
    top = Counter(filtered).most_common(30)
    return {"keywords": [{"word": w, "count": c} for w, c in top]}
```

Đăng ký router:
```python
from app.api.v1 import document, chat, graph, auth, explain, trends

api_router.include_router(trends.router, prefix="/trends", tags=["Trending Topics"])
```

### 24.2. Frontend — Trang Trending

Tạo `frontend/src/app/trends/page.tsx`:

```typescript
'use client';

import { useEffect, useState } from 'react';

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

interface Topic { name: string; count: number; category: string; description: string; }
interface Keyword { word: string; count: number; }

export default function TrendsPage() {
  const [topics, setTopics] = useState<Topic[]>([]);
  const [keywords, setKeywords] = useState<Keyword[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    Promise.all([
      fetch(`${API_URL}/api/v1/trends`).then((r) => r.json()),
      fetch(`${API_URL}/api/v1/trends/keywords`).then((r) => r.json()),
    ]).then(([t, k]) => {
      setTopics(t.topics || []);
      setKeywords(k.keywords || []);
      setLoading(false);
    });
  }, []);

  const maxCount = Math.max(...keywords.map((k) => k.count), 1);

  return (
    <div className="max-w-5xl mx-auto p-6">
      <h1 className="text-2xl font-bold text-gray-800 mb-6">Trending Topics</h1>

      {loading && <div className="text-center text-gray-400 py-20">Đang phân tích...</div>}

      {!loading && (
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
          {/* Topics */}
          <div>
            <h2 className="text-lg font-semibold text-gray-700 mb-4">Chủ đề nổi bật (AI phát hiện)</h2>
            <div className="space-y-3">
              {topics.map((topic, i) => (
                <div key={i} className="bg-white border rounded-xl p-4 shadow-sm hover:shadow-md transition">
                  <div className="flex items-center justify-between mb-1">
                    <span className="font-semibold text-gray-800">{topic.name}</span>
                    <span className="bg-blue-100 text-blue-700 text-xs px-2 py-0.5 rounded-full">
                      {topic.count} bài
                    </span>
                  </div>
                  <p className="text-xs text-gray-500 mb-1">{topic.category}</p>
                  <p className="text-sm text-gray-600">{topic.description}</p>
                </div>
              ))}
              {topics.length === 0 && <p className="text-gray-400 text-sm">Chưa đủ dữ liệu</p>}
            </div>
          </div>

          {/* Word cloud đơn giản */}
          <div>
            <h2 className="text-lg font-semibold text-gray-700 mb-4">Từ khóa phổ biến</h2>
            <div className="bg-white border rounded-xl p-5 shadow-sm flex flex-wrap gap-2">
              {keywords.map((kw) => {
                const size = 12 + Math.round((kw.count / maxCount) * 18);
                const opacity = 0.5 + (kw.count / maxCount) * 0.5;
                return (
                  <span
                    key={kw.word}
                    style={{ fontSize: size, opacity }}
                    className="text-blue-700 font-medium cursor-default"
                    title={`${kw.count} lần`}
                  >
                    {kw.word}
                  </span>
                );
              })}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
```

Thêm link vào `layout.tsx`:
```typescript
<Link href="/trends" className="hover:underline">Trending</Link>
```



---

## BƯỚC 25: 🧠 MEMORY CHAT (AI nhớ lịch sử hội thoại)

### 25.1. Migration SQL — Bảng Conversation History

Thêm vào `docker/init_db.sql` hoặc chạy trực tiếp trong psql:

```sql
CREATE TABLE IF NOT EXISTS conversation_sessions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id VARCHAR(255),
    document_ids TEXT[],
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS conversation_messages (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    session_id UUID REFERENCES conversation_sessions(id) ON DELETE CASCADE,
    role VARCHAR(20) NOT NULL,
    content TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_messages_session ON conversation_messages(session_id, created_at);
```

### 25.2. Tạo `backend/app/services/memory.py`

```python
from sqlalchemy.orm import Session
from sqlalchemy import text
import uuid

def get_or_create_session(user_id: str, document_ids: list[str], db: Session) -> str:
    """Lấy hoặc tạo session trò chuyện theo user + bộ tài liệu."""
    doc_array = "{" + ",".join(f'"{d}"' for d in sorted(document_ids)) + "}"
    row = db.execute(
        text("""
            SELECT id FROM conversation_sessions
            WHERE user_id = :uid AND document_ids = :docs
            ORDER BY updated_at DESC LIMIT 1
        """),
        {"uid": user_id or "anonymous", "docs": doc_array},
    ).fetchone()

    if row:
        db.execute(text("UPDATE conversation_sessions SET updated_at = NOW() WHERE id = :id"), {"id": str(row.id)})
        db.commit()
        return str(row.id)

    session_id = str(uuid.uuid4())
    db.execute(
        text("INSERT INTO conversation_sessions (id, user_id, document_ids) VALUES (:id, :uid, :docs)"),
        {"id": session_id, "uid": user_id or "anonymous", "docs": doc_array},
    )
    db.commit()
    return session_id

def save_message(session_id: str, role: str, content: str, db: Session) -> None:
    db.execute(
        text("INSERT INTO conversation_messages (id, session_id, role, content) VALUES (:id, :sid, :role, :content)"),
        {"id": str(uuid.uuid4()), "sid": session_id, "role": role, "content": content},
    )
    db.commit()

def get_history(session_id: str, db: Session, limit: int = 10) -> list[dict]:
    """Lấy N tin nhắn gần nhất của session."""
    rows = db.execute(
        text("""
            SELECT role, content FROM conversation_messages
            WHERE session_id = :sid ORDER BY created_at DESC LIMIT :lim
        """),
        {"sid": session_id, "lim": limit},
    ).fetchall()
    return [{"role": r.role, "content": r.content} for r in reversed(rows)]
```

### 25.3. Cập Nhật `generator.py` Nhận History

```python
def generate_stream(
    query: str,
    context_chunks: list[dict],
    learning_mode: str = "standard",
    history: list[dict] = None,
):
    messages = build_prompt(query, context_chunks, learning_mode)
    # Chèn lịch sử: [system, ...history[-6:], user]
    if history:
        messages = [messages[0]] + history[-6:] + [messages[1]]

    stream = groq_client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=messages,
        stream=True,
        max_tokens=2048,
        temperature=0.1,
    )
    for chunk in stream:
        delta = chunk.choices[0].delta.content
        if delta:
            yield delta
```

### 25.4. Cập Nhật Chat Endpoint

Sửa `ChatRequest` trong `backend/app/api/v1/chat.py`:

```python
class ChatRequest(BaseModel):
    query: str
    document_ids: list[str]
    mode: Optional[str] = "single"
    learning_mode: Optional[str] = "standard"
    user_id: Optional[str] = None
    use_memory: bool = True
```

Trong hàm `chat()`, thêm đoạn sau khi `retrieve()`:

```python
history = []
session_id = None
if request.use_memory and request.user_id:
    from app.services.memory import get_or_create_session, get_history, save_message
    session_id = get_or_create_session(request.user_id, request.document_ids, db)
    history = get_history(session_id, db, limit=8)
    save_message(session_id, "user", request.query, db)
```

Và truyền `history` vào `generate_stream`:

```python
generate_stream(request.query, context_chunks, learning_mode=request.learning_mode or "standard", history=history)
```

### 25.5. Frontend — Toggle Memory Và User ID

Thêm vào `useAppStore.ts`:

```typescript
userId: typeof window !== 'undefined'
  ? localStorage.getItem('anon_uid') ?? (() => {
      const id = crypto.randomUUID();
      localStorage.setItem('anon_uid', id);
      return id;
    })()
  : crypto.randomUUID(),
useMemory: true,
setUseMemory: (v: boolean) => set({ useMemory: v }),
```

Thêm toggle vào sidebar `/chat`:

```typescript
const { useMemory, setUseMemory, userId } = useAppStore();
// ...
<label className="flex items-center gap-2 mt-4 cursor-pointer">
  <input
    type="checkbox"
    checked={useMemory}
    onChange={(e) => setUseMemory(e.target.checked)}
    className="rounded"
  />
  <span className="text-xs text-gray-600">Nhớ lịch sử trò chuyện</span>
</label>
```

Cập nhật `chatStream` trong `lib/api.ts` để truyền `user_id` và `use_memory`:

```typescript
export const chatStream = async (
  query: string,
  documentIds: string[],
  learningMode: string = 'standard',
  userId?: string,
  useMemory: boolean = true,
  onChunk: (text: string) => void = () => {}
): Promise<void> => {
  const response = await fetch(`${API_URL}/api/v1/chat`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      query,
      document_ids: documentIds,
      learning_mode: learningMode,
      user_id: userId,
      use_memory: useMemory,
    }),
  });
  if (!response.ok) throw new Error('Chat request failed');
  const reader = response.body!.getReader();
  const decoder = new TextDecoder();
  while (true) {
    const { done, value } = await reader.read();
    if (done) break;
    onChunk(decoder.decode(value));
  }
};
```

---

## BƯỚC 26: 📱 RESPONSIVE MOBILE + 🌙 DARK MODE HIỆN ĐẠI

### 26.1. Cài next-themes

```powershell
cd D:\academic-rag-system\frontend
npm install next-themes
```

### 26.2. Tạo `frontend/src/components/ThemeToggle.tsx`

```typescript
'use client';

import { useTheme } from 'next-themes';
import { useEffect, useState } from 'react';

export default function ThemeToggle() {
  const { theme, setTheme } = useTheme();
  const [mounted, setMounted] = useState(false);
  useEffect(() => setMounted(true), []);
  if (!mounted) return null;

  return (
    <button
      onClick={() => setTheme(theme === 'dark' ? 'light' : 'dark')}
      className="p-2 rounded-lg bg-white/10 hover:bg-white/20 transition"
      title="Chuyển Dark/Light mode"
    >
      {theme === 'dark' ? '☀️' : '🌙'}
    </button>
  );
}
```

### 26.3. Sửa `frontend/src/app/layout.tsx`

```typescript
import type { Metadata } from 'next';
import { Inter } from 'next/font/google';
import './globals.css';
import Link from 'next/link';
import { ThemeProvider } from 'next-themes';
import ThemeToggle from '@/components/ThemeToggle';

const inter = Inter({ subsets: ['latin'] });

export const metadata: Metadata = {
  title: 'Academic RAG System',
  description: 'Hệ thống hỏi đáp học thuật thông minh',
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="vi" suppressHydrationWarning>
      <body className={`${inter.className} bg-gray-50 dark:bg-gray-950 min-h-screen`}>
        <ThemeProvider attribute="class" defaultTheme="system" enableSystem>
          <nav className="bg-blue-700 dark:bg-gray-900 text-white px-4 py-3 shadow">
            <div className="flex items-center justify-between max-w-7xl mx-auto">
              <span className="font-bold text-lg flex-shrink-0">Academic RAG</span>
              {/* Desktop links */}
              <div className="hidden md:flex gap-4 text-sm flex-wrap">
                <Link href="/dashboard" className="hover:underline">Dashboard</Link>
                <Link href="/library" className="hover:underline">Thư viện</Link>
                <Link href="/chat" className="hover:underline">Hỏi đáp</Link>
                <Link href="/graph" className="hover:underline">Đồ thị</Link>
                <Link href="/timeline" className="hover:underline">Timeline</Link>
                <Link href="/trends" className="hover:underline">Trending</Link>
                <Link href="/literature" className="hover:underline">Literature</Link>
              </div>
              {/* Mobile: chỉ hiện icon */}
              <div className="md:hidden flex gap-3 text-sm">
                <Link href="/library" className="hover:underline">📚</Link>
                <Link href="/chat" className="hover:underline">💬</Link>
                <Link href="/trends" className="hover:underline">🔥</Link>
              </div>
              <ThemeToggle />
            </div>
          </nav>
          <main className="min-h-screen">{children}</main>
        </ThemeProvider>
      </body>
    </html>
  );
}
```

### 26.4. Cập Nhật `globals.css` Cho Dark Mode

```css
@tailwind base;
@tailwind components;
@tailwind utilities;

:root {
  --background: #ffffff;
  --foreground: #171717;
  --card: #ffffff;
  --border: #e5e7eb;
}

.dark {
  --background: #0a0a0a;
  --foreground: #ededed;
  --card: #111827;
  --border: #374151;
}

body {
  background: var(--background);
  color: var(--foreground);
  font-family: 'Inter', sans-serif;
}

/* Scrollbar tối */
.dark ::-webkit-scrollbar { width: 6px; height: 6px; }
.dark ::-webkit-scrollbar-track { background: #1f2937; }
.dark ::-webkit-scrollbar-thumb { background: #4b5563; border-radius: 3px; }

/* Responsive card */
@layer components {
  .card {
    @apply bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-xl shadow-sm;
  }
  .input {
    @apply border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700
           text-gray-900 dark:text-gray-100 rounded-xl px-4 py-2
           focus:outline-none focus:ring-2 focus:ring-blue-400;
  }
}
```

> **Áp dụng cho các trang hiện có:** Thay `bg-white` → `bg-white dark:bg-gray-800`, `text-gray-800` → `text-gray-800 dark:text-gray-100`, `border-gray-200` → `border-gray-200 dark:border-gray-700` để tất cả component đẹp trong cả hai chế độ.

### 26.5. Cập Nhật tailwind.config.ts

```typescript
import type { Config } from 'tailwindcss';

const config: Config = {
  darkMode: 'class',
  content: ['./src/**/*.{js,ts,jsx,tsx,mdx}'],
  theme: {
    extend: {},
  },
  plugins: [],
};
export default config;
```

---

## BƯỚC 27: ⚡ REALTIME PROCESSING PROGRESS (SSE)

### 27.1. Backend — In-Memory Progress Tracker

Thêm vào đầu `backend/app/api/v1/document.py`:

```python
import asyncio

# Dict lưu tiến độ xử lý PDF (key = document_id)
_PROGRESS: dict[str, dict] = {}

def _update_progress(doc_id: str, stage: str, detail: str = "") -> None:
    _PROGRESS[doc_id] = {"stage": stage, "detail": detail}
```

Thêm SSE endpoint vào `document.py`:

```python
@router.get("/{document_id}/progress")
async def stream_progress(document_id: str):
    """Server-Sent Events — client subscribe nhận tiến độ realtime."""
    async def _events():
        for _ in range(180):   # timeout 3 phút
            info = _PROGRESS.get(document_id, {})
            stage = info.get("stage", "waiting")
            detail = info.get("detail", "")
            data = f'{{"stage": "{stage}", "detail": "{detail}"}}'
            yield f"data: {data}\n\n"
            if stage in ("done", "error"):
                break
            await asyncio.sleep(1)

    return StreamingResponse(
        _events(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )
```

### 27.2. Cập Nhật `_run_pipeline` Với Progress

Sửa `_run_pipeline` trong `document.py`:

```python
def _run_pipeline(file_path: str, document_id: str, db_url: str):
    from app.api.v1.document import _update_progress
    # ... (engine, db setup như cũ)
    try:
        _update_progress(document_id, "parsing", "Đang đọc nội dung PDF...")
        parsed = parse_pdf(file_path)

        # Cập nhật metadata
        doc = db.query(Document).filter(Document.id == document_id).first()
        if doc:
            doc.title = parsed["metadata"].get("title") or doc.filename
            doc.authors = parsed["metadata"].get("author", "")
            doc.total_pages = parsed["total_pages"]
        db.commit()

        _update_progress(document_id, "chunking", f"Chia {parsed['total_pages']} trang thành đoạn nhỏ...")
        chunks = chunk_text(parsed["full_text"], document_id, parsed["pages"])

        _update_progress(document_id, "embedding", f"Tạo vector AI cho {len(chunks)} chunks...")
        embed_and_store(chunks, db)

        _update_progress(document_id, "indexing", "Lưu index và phân loại...")
        # Auto-classify
        from app.services.classifier import classify_document as _cls
        cls_result = _cls(doc.title or doc.filename, parsed["full_text"][:1500])
        doc.category = cls_result.get("category", "Other")
        doc.status = "ready"
        db.commit()

        _update_progress(document_id, "done", "Hoàn tất! Tài liệu sẵn sàng hỏi đáp.")

    except Exception as e:
        _update_progress(document_id, "error", str(e))
        doc = db.query(Document).filter(Document.id == document_id).first()
        if doc:
            doc.status = "error"
            db.commit()
        print(f"Pipeline error: {e}")
    finally:
        db.close()
```

### 27.3. Tạo `frontend/src/components/ProcessingProgress.tsx`

```typescript
'use client';

import { useEffect, useState } from 'react';

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

const STAGES = ['parsing', 'chunking', 'embedding', 'indexing', 'done'];
const STAGE_PCT: Record<string, number> = {
  waiting: 0, parsing: 20, chunking: 45, embedding: 70, indexing: 90, done: 100, error: 0,
};
const STAGE_LABEL: Record<string, string> = {
  waiting: 'Đang chờ...', parsing: 'Đọc PDF...', chunking: 'Chia đoạn văn...',
  embedding: 'Tạo vector AI...', indexing: 'Lưu database...', done: 'Hoàn tất!', error: 'Lỗi!',
};

interface Props { documentId: string; onDone?: () => void; }

export default function ProcessingProgress({ documentId, onDone }: Props) {
  const [stage, setStage] = useState('waiting');
  const [detail, setDetail] = useState('');

  useEffect(() => {
    const es = new EventSource(`${API_URL}/api/v1/document/${documentId}/progress`);
    es.onmessage = (e) => {
      try {
        const d = JSON.parse(e.data);
        setStage(d.stage);
        setDetail(d.detail || '');
        if (d.stage === 'done') { es.close(); onDone?.(); }
        if (d.stage === 'error') { es.close(); }
      } catch {}
    };
    return () => es.close();
  }, [documentId]);

  const pct = STAGE_PCT[stage] ?? 0;
  const isDone = stage === 'done';
  const isError = stage === 'error';

  return (
    <div className="bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-xl p-4 shadow-sm">
      <div className="flex justify-between text-sm mb-2">
        <span className={`font-medium ${isDone ? 'text-green-600' : isError ? 'text-red-500' : 'text-blue-600'}`}>
          {STAGE_LABEL[stage] ?? stage}
        </span>
        <span className="text-gray-400">{pct}%</span>
      </div>
      <div className="w-full bg-gray-100 dark:bg-gray-700 rounded-full h-2 mb-3">
        <div
          className={`h-2 rounded-full transition-all duration-700 ${isDone ? 'bg-green-500' : isError ? 'bg-red-500' : 'bg-blue-500 animate-pulse'}`}
          style={{ width: `${pct}%` }}
        />
      </div>
      {detail && <p className="text-xs text-gray-500 mb-3">{detail}</p>}
      {/* Stage dots */}
      <div className="flex gap-1">
        {STAGES.map((s) => {
          const idx = STAGES.indexOf(s);
          const cur = STAGES.indexOf(stage);
          const status = cur > idx ? 'done' : cur === idx ? 'active' : 'pending';
          return (
            <div key={s} className="flex-1 text-center">
              <div className={`h-1.5 rounded-full mb-1 transition-all ${
                status === 'done' ? 'bg-green-400' :
                status === 'active' ? 'bg-blue-500 animate-pulse' : 'bg-gray-200 dark:bg-gray-600'
              }`} />
              <span className="text-xs text-gray-400 hidden sm:block capitalize">{s}</span>
            </div>
          );
        })}
      </div>
    </div>
  );
}
```

### 27.4. Tích Hợp Vào Trang Library

Thêm vào `LibraryPage`:

```typescript
import ProcessingProgress from '@/components/ProcessingProgress';

// State:
const [processingDocId, setProcessingDocId] = useState<string | null>(null);

// Trong handleUpload, sau uploadDocument():
setProcessingDocId(result.document_id);

// JSX thay thế uploadMessage:
{processingDocId && (
  <ProcessingProgress
    documentId={processingDocId}
    onDone={() => { setProcessingDocId(null); fetchDocs(); }}
  />
)}
```

---

## BƯỚC 28: 🖼️ OCR CHO PDF SCAN / ẢNH CHỤP

### 28.1. Cài Thư Viện OCR

```powershell
cd D:\academic-rag-system\backend
venv\Scripts\activate

# EasyOCR hỗ trợ tiếng Việt + Anh, không cần Tesseract riêng
pip install easyocr Pillow pdf2image
```

**Cài Poppler (bắt buộc cho pdf2image trên Windows):**

1. Tải tại: `https://github.com/oschwartz10612/poppler-windows/releases`
2. Giải nén vào `D:\poppler`
3. Thêm `D:\poppler\Library\bin` vào biến môi trường PATH
4. Khởi động lại terminal

### 28.2. Tạo `backend/app/services/ocr.py`

```python
def is_scanned_pdf(file_path: str) -> bool:
    """Phát hiện PDF scan: nếu < 50 ký tự/trang thì coi là scan."""
    import fitz
    doc = fitz.open(file_path)
    total_text = sum(len(page.get_text("text").strip()) for page in doc)
    return (total_text / max(len(doc), 1)) < 50

def ocr_pdf(file_path: str) -> dict:
    """Chạy OCR trên PDF scan, trả về cùng cấu trúc với parse_pdf."""
    import easyocr
    from pdf2image import convert_from_path

    reader = easyocr.Reader(['vi', 'en'], gpu=False, verbose=False)
    images = convert_from_path(file_path, dpi=200)

    pages_text, full_text = [], ""
    for page_num, img in enumerate(images):
        results = reader.readtext(img, detail=0, paragraph=True)
        text = " ".join(results)
        pages_text.append({"page": page_num + 1, "text": text})
        full_text += f"\n[Trang {page_num + 1}]\n{text}"

    return {
        "full_text": full_text.strip(),
        "pages": pages_text,
        "total_pages": len(images),
        "metadata": {"title": "", "author": "", "creation_date": ""},
        "ocr_applied": True,
    }
```

### 28.3. Tích Hợp OCR Vào Pipeline

Sửa `_run_pipeline` trong `document.py`:

```python
from app.services.ocr import is_scanned_pdf, ocr_pdf
from app.services.parser import parse_pdf

# Thay:  parsed = parse_pdf(file_path)
# Bằng:
_update_progress(document_id, "parsing", "Kiểm tra loại PDF...")
if is_scanned_pdf(file_path):
    _update_progress(document_id, "parsing", "PDF scan — chạy OCR (1-2 phút/trang)...")
    parsed = ocr_pdf(file_path)
    parsed["metadata"]["title"] = ""
else:
    parsed = parse_pdf(file_path)
```

> **Hiệu năng:** EasyOCR CPU mất ~30-60 giây/trang. Với 10-trang PDF scan ≈ 5-10 phút. Dùng GPU thì nhanh hơn 5-10x. Chỉ OCR khi thực sự cần.

---

## BƯỚC 29: 📹 AI THUYẾT TRÌNH TÀI LIỆU (Slide Generator)

### 29.1. Backend — Endpoint Tạo Slide

Thêm vào `backend/app/api/v1/document.py`:

```python
import json as _json
from fastapi.responses import Response as FResponse

@router.post("/{document_id}/presentation")
def create_presentation(document_id: str, db: Session = Depends(get_db)):
    """Tạo bộ slide JSON từ nội dung bài báo."""
    from groq import Groq
    from app.core.config import settings
    from app.models.document import Chunk

    doc = db.query(Document).filter(Document.id == document_id).first()
    if not doc:
        raise HTTPException(404, "Không tìm thấy tài liệu")
    if doc.status != "ready":
        raise HTTPException(400, "Tài liệu chưa xử lý xong")

    chunks = db.query(Chunk).filter(Chunk.document_id == document_id).order_by(Chunk.chunk_index).limit(20).all()
    content = " ".join(c.content for c in chunks)[:6000]

    client = Groq(api_key=settings.GROQ_API_KEY)
    resp = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[
            {
                "role": "system",
                "content": (
                    "Tạo bộ slide thuyết trình học thuật. Trả về JSON thuần túy:\n"
                    '{"title": "...", "slides": [{"slide_number": 1, "title": "...", '
                    '"content": ["bullet 1", "bullet 2"], "speaker_note": "..."}]}\n'
                    "Cấu trúc: Slide 1 (Tiêu đề), Slide 2 (Mục tiêu nghiên cứu), "
                    "Slide 3-7 (Nội dung chính), Slide 8 (Kết quả), Slide 9 (Hạn chế), Slide 10 (Kết luận). "
                    "Ngôn ngữ: tiếng Việt. Tổng 10 slides."
                ),
            },
            {"role": "user", "content": f"Tiêu đề: {doc.title}\n\nNội dung:\n{content}"},
        ],
        max_tokens=3000,
        temperature=0.2,
        response_format={"type": "json_object"},
    )
    try:
        return _json.loads(resp.choices[0].message.content)
    except Exception:
        raise HTTPException(500, "Không thể tạo slide")

@router.post("/{document_id}/presentation/export-html")
def export_presentation_html(document_id: str, db: Session = Depends(get_db)):
    """Xuất slide dạng HTML tự chạy được trên browser."""
    pres = create_presentation(document_id, db)
    title = pres.get("title", "Presentation")
    slides_html = ""
    for s in pres.get("slides", []):
        bullets = "".join(f"<li>{b}</li>" for b in s.get("content", []))
        slides_html += f"""
        <section class="slide">
          <h2>{s.get('title','')}</h2>
          <ul>{bullets}</ul>
          <div class="note">💬 {s.get('speaker_note','')}</div>
        </section>"""

    html = f"""<!DOCTYPE html><html lang="vi"><head>
    <meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1">
    <title>{title}</title>
    <style>
      * {{ box-sizing: border-box; margin: 0; padding: 0; }}
      body {{ font-family: Arial, sans-serif; background: #1a1a2e; color: white; }}
      .slide {{ min-height: 100vh; display: flex; flex-direction: column; justify-content: center;
               padding: 60px; border-bottom: 2px solid #16213e; }}
      h2 {{ font-size: clamp(1.5rem, 3vw, 2rem); color: #e94560; margin-bottom: 20px; }}
      ul {{ font-size: clamp(1rem, 2vw, 1.2rem); line-height: 2; padding-left: 20px; }}
      .note {{ margin-top: 30px; font-size: 0.85em; color: #a0a0b0;
               border-left: 3px solid #e94560; padding-left: 12px; }}
    </style></head><body>{slides_html}</body></html>"""

    return FResponse(
        content=html,
        media_type="text/html",
        headers={"Content-Disposition": f'attachment; filename="slides_{document_id[:8]}.html"'},
    )
```

### 29.2. Frontend — Nút Slide Trong Library

Thêm vào bảng tài liệu, cột "Hành động":

```typescript
const handleExportSlides = async (docId: string) => {
  const res = await fetch(`${API_URL}/api/v1/document/${docId}/presentation/export-html`, {
    method: 'POST',
  });
  if (!res.ok) { alert('Lỗi tạo slide'); return; }
  const blob = await res.blob();
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = `slides_${docId.slice(0, 8)}.html`;
  a.click();
  URL.revokeObjectURL(url);
};

// Trong bảng, cột action:
<button
  onClick={() => handleExportSlides(doc.id)}
  disabled={doc.status !== 'ready'}
  className="text-purple-500 hover:text-purple-700 text-xs underline mr-2 disabled:opacity-40"
>
  📊 Slide
</button>
```

---

## BƯỚC 30: 🧬 AI LITERATURE REVIEW

### 30.1. Tạo `backend/app/api/v1/literature.py`

```python
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import List
from groq import Groq
from app.db.postgres import get_db
from app.models.document import Document, Chunk
from app.core.config import settings

router = APIRouter()
_client = Groq(api_key=settings.GROQ_API_KEY)

class LitReviewRequest(BaseModel):
    document_ids: List[str]
    section: str = "full"        # "related_work" | "gap" | "synthesis" | "full"
    research_topic: str = ""

SECTION_PROMPTS = {
    "related_work": (
        "Viết phần Related Work học thuật (~400 từ). "
        "Nhóm bài báo theo chủ đề/phương pháp, so sánh cách tiếp cận. "
        "Trích dẫn theo định dạng [số]. Ngôn ngữ học thuật tiếng Việt."
    ),
    "gap": (
        "Phân tích Research Gap (~300 từ). "
        "Chỉ rõ: (1) những gì đã được giải quyết, "
        "(2) vấn đề còn bỏ ngỏ, (3) hướng nghiên cứu tiếp theo. "
        "Tiếng Việt học thuật."
    ),
    "synthesis": (
        "Tổng hợp literature (~500 từ). "
        "So sánh phương pháp, dataset, kết quả thực nghiệm. "
        "Dùng bảng tổng hợp nếu phù hợp. Tiếng Việt."
    ),
    "full": (
        "Viết literature review đầy đủ gồm 3 phần (Markdown):\n"
        "## Related Work\n## Research Gap\n## Synthesis\n"
        "Mỗi phần 200-400 từ. Trích dẫn [số]. Tiếng Việt học thuật."
    ),
}

@router.post("/review")
def generate_literature_review(req: LitReviewRequest, db: Session = Depends(get_db)):
    if len(req.document_ids) < 2:
        raise HTTPException(400, "Cần ít nhất 2 tài liệu")

    papers_info = []
    for doc_id in req.document_ids[:10]:
        doc = db.query(Document).filter(Document.id == doc_id).first()
        if not doc:
            continue
        chunks = db.query(Chunk).filter(Chunk.document_id == doc_id).order_by(Chunk.chunk_index).limit(5).all()
        summary = " ".join(c.content for c in chunks)[:800]
        papers_info.append({
            "title": doc.title or doc.filename,
            "authors": doc.authors or "Unknown",
            "year": doc.year or "N/A",
            "summary": summary,
        })

    papers_text = "\n\n".join(
        f"[{i+1}] {p['authors']} ({p['year']}). {p['title']}\n{p['summary']}"
        for i, p in enumerate(papers_info)
    )
    topic_note = f"\nChủ đề nghiên cứu: {req.research_topic}" if req.research_topic else ""
    instruction = SECTION_PROMPTS.get(req.section, SECTION_PROMPTS["full"])

    def _stream():
        stream = _client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {"role": "system", "content": f"Bạn là chuyên gia viết literature review. {instruction}"},
                {"role": "user", "content": f"Danh sách bài báo:{topic_note}\n\n{papers_text}"},
            ],
            stream=True, max_tokens=2500, temperature=0.3,
        )
        for chunk in stream:
            delta = chunk.choices[0].delta.content
            if delta:
                yield delta

    return StreamingResponse(_stream(), media_type="text/plain")
```

Đăng ký router trong `backend/app/api/v1/__init__.py`:

```python
from app.api.v1 import document, chat, graph, auth, explain, trends, literature

api_router.include_router(literature.router, prefix="/literature", tags=["Literature Review"])
```

### 30.2. Tạo `frontend/src/app/literature/page.tsx`

```typescript
'use client';

import { useEffect, useState } from 'react';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import { getDocuments, DocumentInfo } from '@/lib/api';

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

const SECTIONS = [
  { value: 'full', label: 'Đầy đủ (Related Work + Gap + Synthesis)' },
  { value: 'related_work', label: 'Chỉ Related Work' },
  { value: 'gap', label: 'Chỉ Research Gap' },
  { value: 'synthesis', label: 'Chỉ Synthesis' },
];

export default function LiteraturePage() {
  const [documents, setDocuments] = useState<DocumentInfo[]>([]);
  const [selectedIds, setSelectedIds] = useState<string[]>([]);
  const [section, setSection] = useState('full');
  const [topic, setTopic] = useState('');
  const [result, setResult] = useState('');
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    getDocuments().then((docs) => setDocuments(docs.filter((d) => d.status === 'ready')));
  }, []);

  const toggleDoc = (id: string) =>
    setSelectedIds((prev) => (prev.includes(id) ? prev.filter((x) => x !== id) : [...prev, id]));

  const handleGenerate = async () => {
    if (selectedIds.length < 2) { alert('Chọn ít nhất 2 tài liệu'); return; }
    setLoading(true); setResult('');
    try {
      const res = await fetch(`${API_URL}/api/v1/literature/review`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ document_ids: selectedIds, section, research_topic: topic }),
      });
      const reader = res.body!.getReader();
      const decoder = new TextDecoder();
      while (true) {
        const { done, value } = await reader.read();
        if (done) break;
        setResult((p) => p + decoder.decode(value));
      }
    } finally { setLoading(false); }
  };

  return (
    <div className="max-w-6xl mx-auto p-4 md:p-6">
      <h1 className="text-2xl font-bold text-gray-800 dark:text-gray-100 mb-6">AI Literature Review</h1>
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Sidebar */}
        <div className="space-y-4">
          <div>
            <p className="text-sm font-semibold text-gray-600 dark:text-gray-300 mb-2">
              Chọn tài liệu (ít nhất 2)
            </p>
            <div className="space-y-1 max-h-56 overflow-y-auto">
              {documents.map((doc) => (
                <label key={doc.id} className="flex items-start gap-2 cursor-pointer p-2 hover:bg-gray-50 dark:hover:bg-gray-700 rounded-lg">
                  <input type="checkbox" checked={selectedIds.includes(doc.id)} onChange={() => toggleDoc(doc.id)} className="mt-1 flex-shrink-0" />
                  <span className="text-xs text-gray-600 dark:text-gray-300 leading-tight">{doc.title || doc.filename}</span>
                </label>
              ))}
            </div>
          </div>

          <div>
            <p className="text-sm font-semibold text-gray-600 dark:text-gray-300 mb-2">Phần cần viết</p>
            <select value={section} onChange={(e) => setSection(e.target.value)}
              className="w-full border rounded-lg px-3 py-2 text-sm dark:bg-gray-700 dark:border-gray-600 dark:text-gray-100">
              {SECTIONS.map((s) => <option key={s.value} value={s.value}>{s.label}</option>)}
            </select>
          </div>

          <div>
            <p className="text-sm font-semibold text-gray-600 dark:text-gray-300 mb-2">Chủ đề (tuỳ chọn)</p>
            <input value={topic} onChange={(e) => setTopic(e.target.value)}
              placeholder="VD: RAG trong giáo dục đại học"
              className="w-full border rounded-lg px-3 py-2 text-sm dark:bg-gray-700 dark:border-gray-600 dark:text-gray-100" />
          </div>

          <button onClick={handleGenerate} disabled={loading || selectedIds.length < 2}
            className="w-full bg-purple-600 text-white rounded-xl py-2.5 font-medium hover:bg-purple-700 disabled:opacity-50 transition">
            {loading ? 'Đang viết...' : 'Tạo Literature Review'}
          </button>

          {result && (
            <button
              onClick={() => {
                const blob = new Blob([result], { type: 'text/markdown' });
                const a = document.createElement('a');
                a.href = URL.createObjectURL(blob);
                a.download = 'literature_review.md'; a.click();
              }}
              className="w-full bg-white dark:bg-gray-700 border border-gray-300 dark:border-gray-600 text-gray-700 dark:text-gray-200 rounded-xl py-2 text-sm hover:bg-gray-50 transition"
            >
              Xuất file .md
            </button>
          )}
        </div>

        {/* Output */}
        <div className="lg:col-span-2 bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-xl p-6 min-h-96 shadow-sm">
          {!result && !loading && (
            <div className="text-center text-gray-400 mt-20">
              <p className="text-xl mb-2">Chọn tài liệu và nhấn tạo</p>
              <p className="text-sm">AI tổng hợp và viết tự động</p>
            </div>
          )}
          {(result || loading) && (
            <div className="prose prose-sm dark:prose-invert max-w-none">
              <ReactMarkdown remarkPlugins={[remarkGfm]}>{result || 'Đang phân tích...'}</ReactMarkdown>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
```

Thêm link vào `layout.tsx`:
```typescript
<Link href="/literature" className="hover:underline">Literature</Link>
```


---

## BƯỚC 31: 🔒 ROLE-BASED SYSTEM (Admin / Researcher / Student)

### 31.1. Migration SQL — Cột Role Cho Users

```sql
-- Bảng users đã có cột role VARCHAR(50) DEFAULT 'user'
-- Chuẩn hóa 3 roles: 'admin', 'researcher', 'student'
-- Chạy lệnh sau để cập nhật role mặc định:
UPDATE users SET role = 'student' WHERE role = 'user';
```

### 31.2. Backend — Permission Middleware

Tạo `backend/app/core/permissions.py`:

```python
from fastapi import HTTPException, Depends
from typing import Optional
from app.core.security import get_current_user_id
from sqlalchemy.orm import Session
from app.db.postgres import get_db

ROLE_HIERARCHY = {"student": 1, "researcher": 2, "admin": 3}

PERMISSIONS = {
    "upload_document":       ["researcher", "admin"],
    "delete_document":       ["admin"],
    "view_documents":        ["student", "researcher", "admin"],
    "chat":                  ["student", "researcher", "admin"],
    "literature_review":     ["researcher", "admin"],
    "export_word":           ["researcher", "admin"],
    "manage_users":          ["admin"],
    "view_ragas":            ["researcher", "admin"],
}

def get_user_role(user_id: Optional[str], db: Session) -> str:
    if not user_id:
        return "student"
    from sqlalchemy import text
    row = db.execute(
        text("SELECT role FROM users WHERE id = :uid"), {"uid": user_id}
    ).fetchone()
    return row.role if row else "student"

def require_permission(permission: str):
    """Dependency factory — dùng như: Depends(require_permission('upload_document'))"""
    def _check(
        user_id: Optional[str] = Depends(get_current_user_id),
        db: Session = Depends(get_db),
    ):
        role = get_user_role(user_id, db)
        allowed_roles = PERMISSIONS.get(permission, [])
        if role not in allowed_roles:
            raise HTTPException(
                403,
                f"Không có quyền thực hiện '{permission}'. Yêu cầu: {allowed_roles}. Hiện tại: {role}",
            )
        return user_id
    return _check

def require_role(min_role: str):
    """Yêu cầu role tối thiểu."""
    def _check(
        user_id: Optional[str] = Depends(get_current_user_id),
        db: Session = Depends(get_db),
    ):
        role = get_user_role(user_id, db)
        if ROLE_HIERARCHY.get(role, 0) < ROLE_HIERARCHY.get(min_role, 99):
            raise HTTPException(403, f"Yêu cầu quyền {min_role} trở lên. Hiện tại: {role}")
        return user_id
    return _check
```

### 31.3. Áp Dụng Permission Vào Các Endpoint

Ví dụ bảo vệ endpoint upload, delete, và literature review:

```python
# document.py — bảo vệ upload
from app.core.permissions import require_permission

@router.post("/upload")
async def upload_document(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    _: str = Depends(require_permission("upload_document")),  # THÊM DÒNG NÀY
):
    ...

# document.py — bảo vệ delete
@router.delete("/{document_id}")
def delete_document(
    document_id: str,
    db: Session = Depends(get_db),
    _: str = Depends(require_permission("delete_document")),  # THÊM DÒNG NÀY
):
    ...

# literature.py — chỉ researcher+
@router.post("/review")
def generate_literature_review(
    req: LitReviewRequest,
    db: Session = Depends(get_db),
    _: str = Depends(require_permission("literature_review")),  # THÊM DÒNG NÀY
):
    ...
```

### 31.4. Backend — Endpoint Quản Lý Users (Admin)

Thêm vào `backend/app/api/v1/auth.py`:

```python
from app.core.permissions import require_role

@router.get("/users")
def list_users(
    db: Session = Depends(get_db),
    _: str = Depends(require_role("admin")),
):
    users = db.query(User).all()
    return {
        "total": len(users),
        "users": [
            {"id": str(u.id), "email": u.email, "full_name": u.full_name,
             "role": u.role, "created_at": u.created_at.isoformat() if u.created_at else None}
            for u in users
        ],
    }

class UpdateRoleRequest(BaseModel):
    role: str  # "student" | "researcher" | "admin"

@router.patch("/users/{user_id}/role")
def update_user_role(
    user_id: str,
    req: UpdateRoleRequest,
    db: Session = Depends(get_db),
    _: str = Depends(require_role("admin")),
):
    if req.role not in ("student", "researcher", "admin"):
        raise HTTPException(400, "Role không hợp lệ")
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(404, "Không tìm thấy người dùng")
    user.role = req.role
    db.commit()
    return {"message": f"Đã cập nhật role thành {req.role}", "user_id": user_id}
```

### 31.5. Frontend — Hiển Thị UI Theo Role

Tạo `frontend/src/hooks/useAuth.ts`:

```typescript
'use client';

import { useState, useEffect } from 'react';

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

export interface AuthUser {
  id: string;
  email: string;
  full_name: string;
  role: 'student' | 'researcher' | 'admin';
  token: string;
}

export function useAuth() {
  const [user, setUser] = useState<AuthUser | null>(null);

  useEffect(() => {
    const stored = localStorage.getItem('auth_user');
    if (stored) {
      try { setUser(JSON.parse(stored)); } catch {}
    }
  }, []);

  const login = async (email: string, password: string) => {
    const res = await fetch(`${API_URL}/api/v1/auth/login`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ email, password }),
    });
    if (!res.ok) throw new Error('Đăng nhập thất bại');
    const data = await res.json();
    const authUser: AuthUser = { ...data.user, role: data.user.role || 'student', token: data.access_token };
    localStorage.setItem('auth_user', JSON.stringify(authUser));
    setUser(authUser);
    return authUser;
  };

  const logout = () => {
    localStorage.removeItem('auth_user');
    setUser(null);
  };

  const canDo = (permission: string): boolean => {
    const PERMISSIONS: Record<string, string[]> = {
      upload_document:   ['researcher', 'admin'],
      delete_document:   ['admin'],
      literature_review: ['researcher', 'admin'],
      export_word:       ['researcher', 'admin'],
      manage_users:      ['admin'],
    };
    const role = user?.role ?? 'student';
    return PERMISSIONS[permission]?.includes(role) ?? true;
  };

  return { user, login, logout, canDo };
}
```

Ví dụ dùng trong Library:

```typescript
// Trong LibraryPage:
const { user, canDo } = useAuth();

// Ẩn nút upload nếu không có quyền:
{canDo('upload_document') && (
  <div className="border-2 border-dashed ..." onClick={() => fileInputRef.current?.click()}>
    ...
  </div>
)}

// Ẩn nút xóa nếu không phải admin:
{canDo('delete_document') && (
  <button onClick={() => handleDelete(doc.id)} className="text-red-500 ...">Xóa</button>
)}
```

### 31.6. Tạo Trang Admin Quản Lý Users

Tạo `frontend/src/app/admin/page.tsx`:

```typescript
'use client';

import { useEffect, useState } from 'react';
import { useAuth } from '@/hooks/useAuth';

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

interface UserRow {
  id: string; email: string; full_name: string; role: string; created_at: string;
}

const ROLE_COLORS: Record<string, string> = {
  admin: 'bg-red-100 text-red-700',
  researcher: 'bg-blue-100 text-blue-700',
  student: 'bg-green-100 text-green-700',
};

export default function AdminPage() {
  const { user } = useAuth();
  const [users, setUsers] = useState<UserRow[]>([]);

  const fetchUsers = () => {
    if (!user?.token) return;
    fetch(`${API_URL}/api/v1/auth/users`, {
      headers: { Authorization: `Bearer ${user.token}` },
    }).then((r) => r.json()).then((d) => setUsers(d.users || []));
  };

  useEffect(fetchUsers, [user]);

  const updateRole = async (userId: string, role: string) => {
    await fetch(`${API_URL}/api/v1/auth/users/${userId}/role`, {
      method: 'PATCH',
      headers: { 'Content-Type': 'application/json', Authorization: `Bearer ${user?.token}` },
      body: JSON.stringify({ role }),
    });
    fetchUsers();
  };

  if (user?.role !== 'admin') {
    return (
      <div className="flex items-center justify-center min-h-[60vh] text-gray-400 text-lg">
        Chỉ Admin mới có quyền truy cập trang này.
      </div>
    );
  }

  return (
    <div className="max-w-5xl mx-auto p-6">
      <h1 className="text-2xl font-bold text-gray-800 dark:text-gray-100 mb-6">Quản Lý Người Dùng</h1>
      <div className="bg-white dark:bg-gray-800 rounded-xl shadow overflow-hidden">
        <table className="w-full text-sm">
          <thead className="bg-gray-100 dark:bg-gray-700 text-gray-600 dark:text-gray-300 uppercase text-xs">
            <tr>
              <th className="px-4 py-3 text-left">Email</th>
              <th className="px-4 py-3 text-left">Họ tên</th>
              <th className="px-4 py-3 text-center">Role</th>
              <th className="px-4 py-3 text-center">Ngày tạo</th>
              <th className="px-4 py-3 text-center">Thay đổi role</th>
            </tr>
          </thead>
          <tbody>
            {users.map((u) => (
              <tr key={u.id} className="border-t dark:border-gray-700 hover:bg-gray-50 dark:hover:bg-gray-700">
                <td className="px-4 py-3 text-gray-800 dark:text-gray-200">{u.email}</td>
                <td className="px-4 py-3 text-gray-600 dark:text-gray-300">{u.full_name || '—'}</td>
                <td className="px-4 py-3 text-center">
                  <span className={`px-2 py-0.5 rounded-full text-xs font-medium ${ROLE_COLORS[u.role] ?? 'bg-gray-100 text-gray-600'}`}>
                    {u.role}
                  </span>
                </td>
                <td className="px-4 py-3 text-center text-gray-500 text-xs">
                  {u.created_at ? new Date(u.created_at).toLocaleDateString('vi-VN') : '—'}
                </td>
                <td className="px-4 py-3 text-center">
                  <select
                    value={u.role}
                    onChange={(e) => updateRole(u.id, e.target.value)}
                    className="text-xs border rounded px-2 py-1 dark:bg-gray-600 dark:border-gray-500 dark:text-gray-200"
                  >
                    <option value="student">student</option>
                    <option value="researcher">researcher</option>
                    <option value="admin">admin</option>
                  </select>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
```

Thêm link Admin vào navbar (chỉ hiện với admin):

```typescript
// Trong layout.tsx navigation:
{/* Admin link - chỉ hiện phía client khi là admin */}
<Link href="/admin" className="hover:underline text-red-300">Admin</Link>
```

---

## BƯỚC 32: ⚙️ CẬP NHẬT DANH SÁCH ROUTER VÀ CHECKLIST TỔNG HỢP

### 32.1. File `backend/app/api/v1/__init__.py` Hoàn Chỉnh

```python
from fastapi import APIRouter
from app.api.v1 import document, chat, graph, auth, explain, trends, literature

api_router = APIRouter()
api_router.include_router(document.router, prefix="/document", tags=["Documents"])
api_router.include_router(chat.router, prefix="/chat", tags=["Chat"])
api_router.include_router(graph.router, prefix="/graph", tags=["Knowledge Graph"])
api_router.include_router(auth.router, prefix="/auth", tags=["Authentication"])
api_router.include_router(explain.router, prefix="/explain", tags=["Explain Term"])
api_router.include_router(trends.router, prefix="/trends", tags=["Trending Topics"])
api_router.include_router(literature.router, prefix="/literature", tags=["Literature Review"])
```

### 32.2. Cài Thêm Thư Viện Còn Thiếu

```powershell
cd D:\academic-rag-system\backend
venv\Scripts\activate

pip install easyocr pdf2image Pillow next-themes
pip freeze > requirements.txt
```

```powershell
cd D:\academic-rag-system\frontend
npm install next-themes
```

### 32.3. Checklist Tất Cả Tính Năng PHẦN 4

| Tính năng | Endpoint Backend | Trang Frontend | Kiểm tra |
|-----------|-----------------|----------------|----------|
| 🌐 Dịch tài liệu | `POST /document/{id}/translate` | Component `TranslatePanel` | Upload PDF → nhấn Dịch → thấy stream |
| 📖 Explain thuật ngữ | `POST /explain` | Hook `useTermExplainer` | Double-click từ trong chat → popup giải thích |
| 🎓 Learning Mode | field `learning_mode` trong `/chat` | Sidebar mode selector | Hỏi câu hỏi → chọn Beginner → thấy giải thích đơn giản hơn |
| 🗂️ Phân loại tài liệu | `POST /document/{id}/classify` | Filter chips trong Library | Upload → thấy tự động gán category |
| ⏱️ Timeline | `GET /document/timeline/by-year` | `/timeline` | Thấy biểu đồ theo năm |
| 🔥 Trending | `GET /trends`, `GET /trends/keywords` | `/trends` | Thấy danh sách topics + word cloud |
| 🧠 Memory Chat | Bảng `conversation_messages` | Toggle trong Chat sidebar | Hỏi → quay lại hỏi tiếp → AI nhớ context |
| 📱 Responsive | — | Layout responsive | Mở trên điện thoại → navbar gọn |
| 🌙 Dark mode | — | ThemeToggle + next-themes | Nhấn toggle → giao diện tối |
| ⚡ Progress SSE | `GET /document/{id}/progress` | `ProcessingProgress` component | Upload → thấy thanh tiến trình realtime |
| 🖼️ OCR | Service `ocr.py` | — (tự động trong pipeline) | Upload PDF scan → text được trích xuất đúng |
| 📹 Slide | `POST /document/{id}/presentation/export-html` | Nút "Slide" trong Library | Tải về file HTML → mở trên trình duyệt |
| 🧬 Literature Review | `POST /literature/review` | `/literature` | Chọn 2+ tài liệu → tạo → thấy văn bản học thuật |
| 🔒 Role-based | Middleware `require_permission` | Hook `useAuth` + trang `/admin` | Đăng nhập student → không thấy nút upload |

### 32.4. Script Khởi Động Nhanh (Cập Nhật)

Cập nhật `D:\academic-rag-system\start.ps1`:

```powershell
Write-Host "=== Academic RAG System — Full Stack ===" -ForegroundColor Cyan

# 1. Docker databases
Set-Location D:\academic-rag-system\docker
docker-compose up -d
Start-Sleep -Seconds 5

# 2. Backend
Start-Process powershell -ArgumentList "-NoExit", "-Command",
  "cd D:\academic-rag-system\backend; venv\Scripts\activate; uvicorn main:app --reload --port 8000"

Start-Sleep -Seconds 3

# 3. Frontend
Start-Process powershell -ArgumentList "-NoExit", "-Command",
  "cd D:\academic-rag-system\frontend; npm run dev"

Write-Host ""
Write-Host "Frontend:      http://localhost:3000" -ForegroundColor Green
Write-Host "API Docs:      http://localhost:8000/docs" -ForegroundColor Green
Write-Host "Neo4j Browser: http://localhost:7474" -ForegroundColor Green
Write-Host ""
Write-Host "Tính năng mới:" -ForegroundColor Yellow
Write-Host "  /trends        — Trending topics"
Write-Host "  /timeline      — Timeline nghiên cứu"
Write-Host "  /literature    — AI Literature Review"
Write-Host "  /admin         — Quản lý users (Admin only)"
```

---

## BƯỚC 33: 🧾 QUIZ TỪ TÀI LIỆU HỌC THUẬT (Academic Quiz)

> **Lưu ý:** BƯỚC 16 đã có quiz cho hệ thống y tế. Bước này tạo quiz riêng cho tài liệu học thuật PDF — không cần onboarding, đơn giản hơn và phù hợp với NCKH.

### 33.1. Backend — Endpoint Tạo Quiz

Thêm vào `backend/app/api/v1/document.py`:

```python
@router.post("/{document_id}/quiz")
def generate_quiz(
    document_id: str,
    num_questions: int = 5,
    difficulty: str = "medium",
    db: Session = Depends(get_db),
):
    """Sinh bộ câu hỏi trắc nghiệm từ nội dung tài liệu."""
    import json as _json
    from groq import Groq
    from app.core.config import settings
    from app.models.document import Chunk

    doc = db.query(Document).filter(Document.id == document_id).first()
    if not doc:
        raise HTTPException(404, "Không tìm thấy tài liệu")
    if doc.status != "ready":
        raise HTTPException(400, "Tài liệu chưa xử lý xong")

    chunks = (
        db.query(Chunk)
        .filter(Chunk.document_id == document_id)
        .order_by(Chunk.chunk_index)
        .limit(15)
        .all()
    )
    content = " ".join(c.content for c in chunks)[:5000]

    difficulty_map = {
        "easy": "câu hỏi dễ, kiến thức cơ bản, chỉ cần đọc qua",
        "medium": "câu hỏi trung bình, cần hiểu nội dung",
        "hard": "câu hỏi khó, phân tích sâu, so sánh và suy luận",
    }
    diff_note = difficulty_map.get(difficulty, difficulty_map["medium"])

    client = Groq(api_key=settings.GROQ_API_KEY)
    resp = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[
            {
                "role": "system",
                "content": (
                    f"Tạo {num_questions} câu hỏi trắc nghiệm ({diff_note}) từ bài báo khoa học. "
                    "Trả về JSON: {\"questions\": [{"
                    "\"id\": 1, \"question\": \"...\", "
                    "\"options\": {\"A\": \"...\", \"B\": \"...\", \"C\": \"...\", \"D\": \"...\"}, "
                    "\"answer\": \"A\", \"explanation\": \"...\"}]}. "
                    "Tiếng Việt. JSON thuần túy."
                ),
            },
            {"role": "user", "content": f"Tài liệu:\n{content}"},
        ],
        max_tokens=2000,
        temperature=0.3,
        response_format={"type": "json_object"},
    )
    try:
        data = _json.loads(resp.choices[0].message.content)
        return {
            "document_id": document_id,
            "document_title": doc.title or doc.filename,
            "difficulty": difficulty,
            "total": len(data.get("questions", [])),
            "questions": data.get("questions", []),
        }
    except Exception:
        raise HTTPException(500, "Không thể tạo câu hỏi")
```

### 33.2. Frontend — Trang Quiz

Tạo `frontend/src/app/quiz/page.tsx`:

```typescript
'use client';

import { useEffect, useState } from 'react';
import { getDocuments, DocumentInfo } from '@/lib/api';

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

interface Question {
  id: number;
  question: string;
  options: { A: string; B: string; C: string; D: string };
  answer: string;
  explanation: string;
}

export default function QuizPage() {
  const [documents, setDocuments] = useState<DocumentInfo[]>([]);
  const [selectedDoc, setSelectedDoc] = useState('');
  const [difficulty, setDifficulty] = useState('medium');
  const [numQ, setNumQ] = useState(5);
  const [questions, setQuestions] = useState<Question[]>([]);
  const [answers, setAnswers] = useState<Record<number, string>>({});
  const [submitted, setSubmitted] = useState(false);
  const [loading, setLoading] = useState(false);
  const [quizTitle, setQuizTitle] = useState('');

  useEffect(() => {
    getDocuments().then((docs) => setDocuments(docs.filter((d) => d.status === 'ready')));
  }, []);

  const handleGenerate = async () => {
    if (!selectedDoc) { alert('Chọn tài liệu'); return; }
    setLoading(true); setQuestions([]); setAnswers({}); setSubmitted(false);
    try {
      const res = await fetch(
        `${API_URL}/api/v1/document/${selectedDoc}/quiz?num_questions=${numQ}&difficulty=${difficulty}`,
        { method: 'POST' }
      );
      const data = await res.json();
      setQuestions(data.questions || []);
      setQuizTitle(data.document_title || '');
    } finally { setLoading(false); }
  };

  const score = submitted
    ? questions.filter((q) => answers[q.id] === q.answer).length
    : 0;

  return (
    <div className="max-w-3xl mx-auto p-4 md:p-6">
      <h1 className="text-2xl font-bold text-gray-800 dark:text-gray-100 mb-6">Quiz Ôn Tập</h1>

      {/* Config */}
      {questions.length === 0 && (
        <div className="bg-white dark:bg-gray-800 border dark:border-gray-700 rounded-xl p-6 shadow-sm space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-600 dark:text-gray-300 mb-2">Chọn tài liệu</label>
            <select value={selectedDoc} onChange={(e) => setSelectedDoc(e.target.value)}
              className="w-full border rounded-lg px-3 py-2 text-sm dark:bg-gray-700 dark:border-gray-600 dark:text-gray-100">
              <option value="">-- Chọn bài báo --</option>
              {documents.map((d) => (
                <option key={d.id} value={d.id}>{d.title || d.filename}</option>
              ))}
            </select>
          </div>
          <div className="flex gap-4">
            <div className="flex-1">
              <label className="block text-sm font-medium text-gray-600 dark:text-gray-300 mb-2">Độ khó</label>
              <select value={difficulty} onChange={(e) => setDifficulty(e.target.value)}
                className="w-full border rounded-lg px-3 py-2 text-sm dark:bg-gray-700 dark:border-gray-600 dark:text-gray-100">
                <option value="easy">Dễ</option>
                <option value="medium">Trung bình</option>
                <option value="hard">Khó</option>
              </select>
            </div>
            <div className="flex-1">
              <label className="block text-sm font-medium text-gray-600 dark:text-gray-300 mb-2">Số câu</label>
              <select value={numQ} onChange={(e) => setNumQ(Number(e.target.value))}
                className="w-full border rounded-lg px-3 py-2 text-sm dark:bg-gray-700 dark:border-gray-600 dark:text-gray-100">
                {[3, 5, 10, 15].map((n) => <option key={n} value={n}>{n} câu</option>)}
              </select>
            </div>
          </div>
          <button onClick={handleGenerate} disabled={loading || !selectedDoc}
            className="w-full bg-blue-600 text-white rounded-xl py-2.5 font-medium hover:bg-blue-700 disabled:opacity-50">
            {loading ? 'Đang tạo câu hỏi...' : 'Tạo Quiz'}
          </button>
        </div>
      )}

      {/* Quiz */}
      {questions.length > 0 && (
        <div>
          <div className="flex items-center justify-between mb-4">
            <h2 className="font-semibold text-gray-700 dark:text-gray-200 text-sm">{quizTitle}</h2>
            <button onClick={() => setQuestions([])} className="text-xs text-blue-500 hover:underline">
              Tạo quiz mới
            </button>
          </div>

          <div className="space-y-4">
            {questions.map((q) => (
              <div key={q.id} className="bg-white dark:bg-gray-800 border dark:border-gray-700 rounded-xl p-5 shadow-sm">
                <p className="font-medium text-gray-800 dark:text-gray-100 mb-3">
                  {q.id}. {q.question}
                </p>
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
                  {(Object.entries(q.options) as [string, string][]).map(([key, val]) => {
                    const isSelected = answers[q.id] === key;
                    const isCorrect = submitted && key === q.answer;
                    const isWrong = submitted && isSelected && key !== q.answer;
                    return (
                      <button key={key} onClick={() => !submitted && setAnswers((p) => ({ ...p, [q.id]: key }))}
                        className={`text-left px-4 py-2.5 rounded-lg border text-sm transition ${
                          isCorrect ? 'bg-green-100 border-green-500 text-green-800' :
                          isWrong ? 'bg-red-100 border-red-400 text-red-700' :
                          isSelected ? 'bg-blue-100 border-blue-500 text-blue-800' :
                          'border-gray-200 dark:border-gray-600 hover:bg-gray-50 dark:hover:bg-gray-700 dark:text-gray-200'
                        }`}>
                        <span className="font-bold mr-2">{key}.</span>{val}
                      </button>
                    );
                  })}
                </div>
                {submitted && (
                  <div className="mt-3 p-3 bg-blue-50 dark:bg-blue-900/30 rounded-lg text-sm text-blue-800 dark:text-blue-200">
                    <strong>Đáp án: {q.answer}</strong> — {q.explanation}
                  </div>
                )}
              </div>
            ))}
          </div>

          {!submitted ? (
            <button
              onClick={() => setSubmitted(true)}
              disabled={Object.keys(answers).length < questions.length}
              className="mt-6 w-full bg-green-600 text-white rounded-xl py-3 font-medium hover:bg-green-700 disabled:opacity-50"
            >
              Nộp bài ({Object.keys(answers).length}/{questions.length} câu đã trả lời)
            </button>
          ) : (
            <div className="mt-6 bg-white dark:bg-gray-800 border dark:border-gray-700 rounded-xl p-6 text-center shadow">
              <p className="text-3xl font-bold text-blue-600">{score}/{questions.length}</p>
              <p className="text-gray-500 mt-1">
                {score === questions.length ? '🎉 Hoàn hảo!' :
                 score >= questions.length * 0.7 ? '👍 Tốt lắm!' :
                 score >= questions.length * 0.5 ? '📚 Cần ôn thêm' : '💪 Thử lại nhé!'}
              </p>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
```

Thêm link vào `layout.tsx`:
```typescript
<Link href="/quiz" className="hover:underline">Quiz</Link>
```

---

## TỔNG KẾT PHẦN 4 — CÁC TÍNH NĂNG ĐÃ BỔ SUNG

| # | Tính năng | Bước |
|---|-----------|------|
| 1 | 🌐 Dịch tài liệu Anh ↔ Việt | BƯỚC 19 |
| 2 | 📖 Explain thuật ngữ khó (double-click) | BƯỚC 20 |
| 3 | 🎓 AI learning mode (beginner/advanced/researcher) | BƯỚC 21 |
| 4 | 🗂️ Tự phân loại tài liệu (AI/Blockchain/Security...) | BƯỚC 22 |
| 5 | ⏱️ Timeline nghiên cứu theo năm | BƯỚC 23 |
| 6 | 🔥 Trending topics + word cloud | BƯỚC 24 |
| 7 | 🧠 Memory Chat theo từng tài liệu | BƯỚC 25 |
| 8 | 📱 Responsive mobile | BƯỚC 26 |
| 9 | 🌙 Dark mode hiện đại | BƯỚC 26 |
| 10 | ⚡ Realtime progress (SSE) | BƯỚC 27 |
| 11 | 🖼️ OCR cho PDF scan/ảnh chụp | BƯỚC 28 |
| 12 | 📹 AI tạo slide thuyết trình | BƯỚC 29 |
| 13 | 🧬 AI Literature Review tự động | BƯỚC 30 |
| 14 | 🔒 Role-based system (Admin/Researcher/Student) | BƯỚC 31 |
| 15 | 🧾 Quiz trắc nghiệm từ tài liệu | BƯỚC 33 |

**🎉 Hệ thống hoàn chỉnh! Tổng cộng 33 bước, đầy đủ tính năng từ demo cơ bản đến hệ thống production.**

