import fs from "node:fs/promises";
import { SpreadsheetFile, Workbook } from "@oai/artifact-tool";

const outputDir = "outputs/acamind_evidence_dossier";
await fs.mkdir(outputDir, { recursive: true });
const inputs = JSON.parse(await fs.readFile("data/operational_test_1000_input.json", "utf8"));

const wb = Workbook.create();
const overview = wb.worksheets.add("Tổng quan");
const live = wb.worksheets.add("Kiểm tra thực tế");
const inputSheet = wb.worksheets.add("1.000 lượt đầu vào");
const gaps = wb.worksheets.add("Dẫn chứng còn thiếu");
for (const sheet of [overview, live, inputSheet, gaps]) sheet.showGridLines = false;

overview.mergeCells("A2:H2");
overview.getRange("A2").values = [["Hồ sơ dẫn chứng thực nghiệm Acamind"]];
overview.mergeCells("A3:H3");
overview.getRange("A3").values = [["Trạng thái tại thời điểm lập hồ sơ: chưa đủ dữ liệu thực nghiệm để hoàn thành bài báo."]];
overview.getRange("A5:B10").values = [
  ["Chỉ tiêu", "Trạng thái"],
  ["Backend FastAPI", "Hoạt động (HTTP 200 tại /docs)"],
  ["Frontend Next.js", "Hoạt động (HTTP 200)"],
  ["Ollama", "Hoạt động (HTTP 200; nomic-embed-text có sẵn)"],
  ["CSDL PostgreSQL/Neo4j", "Container đang hoạt động"],
  ["Một truy vấn thử có ngữ cảnh", "Không đạt: contexts = 0"],
];
overview.getRange("D5:E11").values = [
  ["Dữ liệu đánh giá", "Giá trị"],
  ["Câu hỏi độc lập có đáp án chuẩn", 10],
  ["Lượt kiểm thử vận hành đã chuẩn bị", 1000],
  ["Kết quả 1.000 lượt chạy thật", "Chưa có"],
  ["RAGAS từ log thật", "Chưa có"],
  ["Baseline/ablation cùng tập test", "Chưa có"],
  ["Kết luận", "Chưa đủ để công bố số liệu"]
];
overview.getRange("A13:H18").values = [
  ["Cách đọc", "" , "", "", "", "", "", ""],
  ["1", "Tab 'Kiểm tra thực tế' là bằng chứng đo được trên máy hiện tại.", "", "", "", "", "", ""],
  ["2", "Tab '1.000 lượt đầu vào' là dữ liệu để chạy test, không phải kết quả.", "", "", "", "", "", ""],
  ["3", "Tab 'Dẫn chứng còn thiếu' liệt kê điều kiện để biến bộ chuẩn bị thành bằng chứng thực nghiệm.", "", "", "", "", "", ""],
  ["4", "Không dùng bảng này để thay thế log chạy thật, kết quả RAGAS hoặc đánh giá baseline.", "", "", "", "", "", ""],
  ["Nguồn", "ZIP Overleaf Tuan + Chi, cấu hình dự án hiện tại và truy vấn backend ngày 2026-09-16.", "", "", "", "", "", ""],
];
overview.mergeCells("A13:H13");
for (const row of [14, 15, 16, 17, 18]) overview.mergeCells(`B${row}:H${row}`);

live.getRange("A2:H2").merge();
live.getRange("A2").values = [["Kết quả kiểm tra backend thực tế"]];
live.getRange("A4:H7").values = [
  ["Thời điểm", "Endpoint", "HTTP", "Câu hỏi", "Số context", "Câu trả lời", "Đánh giá", "Ý nghĩa"],
  ["2026-09-16", "POST /api/v1/chat/answer", 200, "Chẩn đoán giai đoạn trầm cảm nhẹ", 0, "Không tìm thấy thông tin liên quan trong tài liệu đã chọn.", "Từ chối an toàn", "UUID/corpus hiện tại chưa cho phép đo RAG"],
  ["2026-09-16", "GET /docs", 200, "N/A", "N/A", "Backend sẵn sàng", "PASS", "Chỉ xác nhận dịch vụ chạy"],
  ["2026-09-16", "GET /api/tags (Ollama)", 200, "N/A", "N/A", "nomic-embed-text có sẵn", "PASS", "Chỉ xác nhận embedding service"],
];
live.tables.add("A4:H7", true, "LiveEvidence");

const headers = ["Mã lượt", "Mã ca nguồn", "Lần lặp", "Loại dữ liệu", "Câu hỏi", "Đáp án chuẩn", "UUID tài liệu", "Trạng thái review", "Kết quả thật" ];
const rows = inputs.map(x => [x.case_id, x.source_case_id, x.replication, x.dataset_type, x.question, x.ground_truth, x.document_ids.join(", "), x.review_status, "Chưa chạy"]);
inputSheet.getRange("A1:I1001").values = [headers, ...rows];
inputSheet.tables.add("A1:I1001", true, "OperationalInputs");
inputSheet.freezePanes.freezeRows(1);

gaps.getRange("A2:F2").merge();
gaps.getRange("A2").values = [["Danh sách dẫn chứng cần bổ sung trước khi nộp bài"]];
gaps.getRange("A4:E10").values = [
  ["Dẫn chứng", "Trạng thái", "Lý do", "Hành động cần thực hiện", "Đầu ra cần lưu"],
  ["Corpus PDF + UUID khớp", "Thiếu", "Truy vấn thật trả contexts = 0", "Nạp lại tài liệu và kiểm tra UUID trong eval_questions.json", "Danh mục corpus + manifest"],
  ["Khóa Gemini hợp lệ", "Thiếu", "GEMINI_API_KEY hiện trống", "Cấu hình khóa trong backend/.env", "Không lưu khóa; chỉ lưu model/version"],
  ["Log 1.000 lượt chạy", "Chưa chạy", "Mới có input dataset", "Chạy run_operational_test.py với --repeat 1", "JSONL + CSV + manifest"],
  ["RAGAS/LLM-as-a-judge", "Chưa chạy", "Cần answer/context thật", "Chạy evaluation.py sau khi log/corpus hợp lệ", "XLSX kết quả RAGAS + prompt/model judge"],
  ["Baseline & ablation", "Thiếu", "Chưa có so sánh định lượng", "Chạy Dense-only, BM25-only, Hybrid, Hybrid+rerank cùng tập", "Bảng metric và kiểm định"],
  ["An toàn PDF scan", "Thiếu", "Chưa có nhãn true/false refusal", "Lập tập scan đã gán nhãn và chạy test", "Confusion matrix từ chối"],
];
gaps.tables.add("A4:E10", true, "EvidenceGaps");

const title = { font: { name: "Arial", size: 15, bold: true, color: "#1F2937" } };
const header = { fill: "#1F4E78", font: { name: "Arial", size: 10, bold: true, color: "#FFFFFF" }, horizontalAlignment: "center", verticalAlignment: "center" };
for (const sheet of [overview, live, inputSheet, gaps]) sheet.getUsedRange().format.font = { name: "Arial", size: 10 };
for (const cell of [overview.getRange("A2"), live.getRange("A2"), gaps.getRange("A2")]) cell.format = title;
overview.getRange("A3").format = { fill: "#FEE2E2", font: { name: "Arial", size: 10, bold: true, color: "#991B1B" } };
for (const range of [overview.getRange("A5:B5"), overview.getRange("D5:E5"), overview.getRange("A13:H13"), live.getRange("A4:H4"), inputSheet.getRange("A1:I1"), gaps.getRange("A4:E4")]) range.format = header;
overview.getRange("A5:B10").format.borders = { preset: "all", style: "thin", color: "#D1D5DB" };
overview.getRange("D5:E11").format.borders = { preset: "all", style: "thin", color: "#D1D5DB" };
overview.getRange("A13:H18").format.borders = { preset: "all", style: "thin", color: "#D1D5DB" };
for (const range of [overview.getRange("A:A"), overview.getRange("D:D"), gaps.getRange("A:A")]) range.format.columnWidth = 30;
overview.getRange("B:B").format.columnWidth = 34; overview.getRange("E:E").format.columnWidth = 30;
live.getRange("A:A").format.columnWidth = 15; live.getRange("B:B").format.columnWidth = 27; live.getRange("C:C").format.columnWidth = 10; live.getRange("D:D").format.columnWidth = 30; live.getRange("E:E").format.columnWidth = 12; live.getRange("F:F").format.columnWidth = 40; live.getRange("G:G").format.columnWidth = 16; live.getRange("H:H").format.columnWidth = 36;
inputSheet.getRange("A:A").format.columnWidth = 12; inputSheet.getRange("B:D").format.columnWidth = 16; inputSheet.getRange("E:E").format.columnWidth = 40; inputSheet.getRange("F:F").format.columnWidth = 48; inputSheet.getRange("G:G").format.columnWidth = 40; inputSheet.getRange("H:I").format.columnWidth = 22;
gaps.getRange("A:A").format.columnWidth = 28; gaps.getRange("B:B").format.columnWidth = 16; gaps.getRange("C:C").format.columnWidth = 35; gaps.getRange("D:D").format.columnWidth = 42; gaps.getRange("E:E").format.columnWidth = 30;
for (const sheet of [live, inputSheet, gaps]) sheet.getUsedRange().format.wrapText = true;
inputSheet.getRange("I2:I1001").conditionalFormats.add("containsText", { text: "Chưa chạy", format: { fill: "#FEF3C7", font: { color: "#92400E", bold: true } } });
gaps.getRange("B5:B10").conditionalFormats.add("containsText", { text: "Thiếu", format: { fill: "#FEE2E2", font: { color: "#991B1B", bold: true } } });

wb.recalculate();
const check = await wb.inspect({ kind: "table", range: "Tổng quan!A2:H18", include: "values,formulas", tableMaxRows: 20, tableMaxCols: 8 });
console.log(check.ndjson);
const preview = await wb.render({ sheetName: "Tổng quan", range: "A1:H18", scale: 1.5, format: "png" });
await fs.writeFile(`${outputDir}/preview.png`, new Uint8Array(await preview.arrayBuffer()));
const output = await SpreadsheetFile.exportXlsx(wb);
await output.save(`${outputDir}/acamind_ho_so_dan_chung.xlsx`);
