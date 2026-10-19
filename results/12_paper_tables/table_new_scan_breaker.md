### Bảng Mới 2 (Giai đoạn 9): Đánh giá Cắt bỏ Scan Circuit Breaker (G0–G4) trên 300 Tài liệu PDF (1,200 Trang, 6 Biến thể Suy giảm V0–V5)

| Guard Configuration | Doc Precision (300 Docs) | Doc Recall (250 Corrupt Docs) | Doc F1 | Page Precision (1,200 Pages) | Page Recall (900 Corrupt Pages) | Page F1 | Pages Routed to OCR (%) | Guard Overhead (ms/page) | Downstream Corrupt Context Exposure (60 Query-PDF Pairs, 95% CI) |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| G0_no_guard | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 0/1200 (0.0%) | 0.0003 | 100.0% [0.9404, 1.0] |
| G1_empty_filter_only | 1.0000 | 0.6000 | 0.7500 | 1.0000 | 0.7778 | 0.8750 | 0/1200 (0.0%) | 0.0327 | Silent data loss on scanned pages; 100% exposure on font corruption |
| G2_ocr_only_no_breaker | 0.0000 | 0.0000 | 0.0000 | 1.0000 | 0.7778 | 0.8750 | 700/1200 (58.3%) | 0.0290 | 100% exposure on font corruption & blank-page LLM OCR text |
| G3_doc_level_eq1_eq2 | 1.0000 | 0.6000 | 0.7500 | 1.0000 | 0.6667 | 0.8000 | 600/1200 (50.0%) | 0.0292 | 66.7% [0.5331, 0.7831] |
| G4_page_level_and_font_guard | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 900/1200 (75.0%) | 0.2337 | 0.0% [0.0, 0.0596] |

> **Ghi chú:** Chứng minh thực nghiệm: Cổng cấp tài liệu G3 (Eq. 1 & 2 trong bài báo) bỏ lọt 100% tài liệu scan một phần (V2_partial_scan, vì mật độ trung bình toàn bài vẫn > 50 ký tự/trang) và bỏ lọt 100% lỗi bảng mã font (V4_font_corruption). Cổng cấp trang kết hợp kiểm tra ký tự thay thế G4 đạt F1 = 1.0000.
