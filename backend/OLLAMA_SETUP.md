# Chạy Acamind với Ollama

Acamind dùng Ollama cho chat, sinh câu trả lời và tạo bộ nhớ tài liệu. OCR trang PDF scan và ảnh dùng nhà cung cấp riêng; cấu hình mặc định là Gemini. Embedding vẫn dùng `intfloat/multilingual-e5-base` local để tương thích với các vector đã lưu trong PostgreSQL.

## Khởi động

1. Mở Ollama và giữ dịch vụ chạy ở `http://localhost:11434`.
2. Mở CMD hoặc PowerShell mới, tải model mặc định:

   ```cmd
   ollama pull qwen2.5:7b
   ```

3. Trong `backend/.env`, kiểm tra các dòng:

   ```dotenv
   LLM_PROVIDER=ollama
   LLM_MODEL=qwen2.5:7b
   OLLAMA_BASE_URL=http://localhost:11434
   OCR_PROVIDER=gemini
   OCR_MODEL=gemini-3.1-flash-lite
   GEMINI_API_KEY=your-gemini-api-key
   ```

   Có thể thay `LLM_MODEL` bằng một model Ollama khác đã tải. Model này cần đủ khả năng làm theo chỉ dẫn và trả lời tiếng Việt.

   Trên máy có GPU 4 GB, có thể dùng model nhỏ hơn cho riêng bước kiểm chứng bằng chứng:

   ```cmd
ollama pull qwen2.5:3b-instruct
ollama pull qwen3:4b-instruct
   ```

   ```dotenv
   EVIDENCE_LOCAL_MODEL=qwen2.5:3b-instruct
   EVIDENCE_COMPARISON_MODEL=qwen3:4b-instruct
   ```

   Mô hình 4B chỉ xử lý kiểm chứng câu hỏi so sánh nhiều tài liệu; mô hình 3B xử lý
   kiểm chứng câu đơn. Giữ `LLM_MODEL` riêng cho phần viết câu trả lời; kiểm tra chất lượng tiếng Việt và
   khả năng nhận diện bằng chứng thiếu trước khi đổi model đó. Backend cần khởi động lại
   để đọc giá trị mới trong `.env`.

4. Khởi động lại backend để nạp cấu hình mới. Frontend không cần đổi endpoint.

Ollama cung cấp endpoint chat tương thích OpenAI tại `/v1/chat/completions`, được client Acamind gọi trực tiếp. Chạy `ollama launch codex` chỉ kết nối Codex CLI; cấu hình ở trên mới chuyển Acamind sang Ollama.

## OCR ảnh và PDF scan

OCR mặc định gọi Gemini bằng `OCR_PROVIDER=gemini`, `OCR_MODEL` và `GEMINI_API_KEY`. Khóa Gemini chỉ được dùng trong các yêu cầu gửi ảnh cho OCR; chat và sinh câu trả lời vẫn dùng Ollama. Nếu muốn OCR hoàn toàn local, đặt `OCR_PROVIDER=ollama` và chọn model vision trong `OCR_MODEL`.

## Embedding

Không đổi embedding model khi tiếp tục truy vấn kho hiện tại. Các vector hiện có được tạo bằng multilingual-E5 768 chiều. Nếu chuyển sang embedding model Ollama khác, cần lập chỉ mục lại toàn bộ tài liệu với cùng model đó trước khi dùng truy xuất vector.

## Chuyển lại Gemini (tùy chọn)

Để dùng Gemini, đặt `LLM_PROVIDER=gemini`, cấu hình `GEMINI_API_KEY`, `GEMINI_BASE_URL` và `LLM_MODEL` trong `backend/.env`, rồi khởi động lại backend.
