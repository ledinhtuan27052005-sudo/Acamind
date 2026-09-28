import fs from "node:fs/promises";
import path from "node:path";
import { SpreadsheetFile, Workbook } from "@oai/artifact-tool";

const resultsDir = "data/pilot_experiment_results";
const outputDir = "outputs/thuc_nghiem_ket_qua";
const files = (await fs.readdir(resultsDir)).filter(x => x.startsWith("pilot_experiment_") && x.endsWith(".json"));
const newest = files.sort().at(-1);
if (!newest) throw new Error("Không tìm thấy log pilot experiment.");
const experiment = JSON.parse(await fs.readFile(path.join(resultsDir, newest), "utf8"));
await fs.mkdir(outputDir, { recursive: true });

const wb = Workbook.create();
const summary = wb.worksheets.add("Tổng quan pilot");
const results = wb.worksheets.add("Kết quả 10 ca");
const sources = wb.worksheets.add("Nguồn & phương pháp");
for (const sheet of [summary, results, sources]) sheet.showGridLines = false;
const s = experiment.summary;

summary.mergeCells("A2:H2"); summary.getRange("A2").values = [["Thực nghiệm kết quả Acamind — Pilot RAG"]];
summary.mergeCells("A3:H3"); summary.getRange("A3").values = [["Dữ liệu chạy thật qua Gemini. Đây là pilot 10 ca độc lập, không phải benchmark hoặc so sánh baseline."]];
summary.getRange("A5:B12").values = [
  ["Chỉ tiêu", "Kết quả"],
  ["Tổng ca", s.total_cases], ["Thành công", s.successful_cases], ["Lỗi", s.failed_cases],
  ["Tỷ lệ thành công", s.successful_cases / s.total_cases], ["Độ trễ trung bình (giây)", s.mean_latency_seconds],
  ["Faithfulness trung bình", s.metrics.faithfulness], ["Answer Relevancy trung bình", s.metrics.answer_relevancy],
];
summary.getRange("D5:E10").values = [
  ["Chỉ số", "Giá trị"],
  ["Context Quality trung bình", s.metrics.context_quality],
  ["Mô hình", "gemini-3.1-flash-lite"],
  ["Nhịp gọi API", `${s.gemini_rate_limit_interval_seconds} giây/ca`],
  ["Khoảng thời gian", `${s.started_at_utc} → ${s.completed_at_utc}`],
  ["Nguồn log thô", newest],
];
summary.getRange("A14:H19").values = [
  ["Kết luận khoa học", "", "", "", "", "", "", ""],
  ["Có thể báo cáo", "Hệ thống hoàn thành 9/10 ca; judge đánh giá trung bình Faithfulness 1.00, Relevancy 1.00 và Context Quality 0.867 trên 9 ca thành công.", "", "", "", "", "", ""],
  ["Không được suy rộng", "Chưa thể kết luận vượt trội hơn baseline hoặc khái quát toàn bộ lĩnh vực vì chưa có tập held-out, đối chứng Dense/BM25/Hybrid và phân tích thống kê.", "", "", "", "", "", ""],
  ["Ca lỗi", "P01 được giữ nguyên trong tab Kết quả 10 ca; không loại khỏi báo cáo.", "", "", "", "", "", ""],
  ["Cách dùng trong bài báo", "Dùng như bằng chứng pilot và trích dẫn rõ thiết kế, model judge, quota interval, tỷ lệ lỗi và giới hạn nghiên cứu.", "", "", "", "", "", ""],
  ["Bước tiếp theo", "Chạy baseline/ablation cùng bộ câu hỏi và bổ sung ground truth độc lập trước khi đưa ra tuyên bố hiệu quả so sánh.", "", "", "", "", "", ""],
];
summary.mergeCells("A14:H14"); for (const row of [15,16,17,18,19]) summary.mergeCells(`B${row}:H${row}`);

const headers = ["Mã ca", "Trạng thái", "HTTP", "Độ trễ (s)", "Faithfulness", "Relevancy", "Context Quality", "Số nguồn", "Câu hỏi", "Câu trả lời", "Feedback judge", "Lỗi"];
const rows = experiment.cases.map(r => [r.case_id, r.outcome, r.http_status ?? "", r.latency_seconds, r.faithfulness ?? "", r.answer_relevancy ?? "", r.context_quality ?? "", (r.sources || []).length, r.question, r.answer || "", r.feedback || "", r.error || ""]);
results.getRange("A1:L11").values = [headers, ...rows];
results.tables.add("A1:L11", true, "PilotResults"); results.freezePanes.freezeRows(1);
results.getRange("B2:B11").conditionalFormats.add("containsText", { text: "success", format: { fill: "#DCFCE7", font: { color: "#166534", bold: true } } });
results.getRange("B2:B11").conditionalFormats.add("containsText", { text: "error", format: { fill: "#FEE2E2", font: { color: "#991B1B", bold: true } } });

sources.getRange("A2:F2").merge(); sources.getRange("A2").values = [["Thiết kế và khả năng tái lập"]];
sources.getRange("A4:B12").values = [
  ["Trường", "Giá trị"],
  ["Thiết kế", s.experiment_type],
  ["Cách gọi", "POST /api/v1/evaluate/run; mỗi ca gọi RAG + LLM-as-a-judge"],
  ["Tài liệu", "10 PDF khác nhau trong PostgreSQL/pgvector; UUID lưu trong log thô"],
  ["Retriever", "Hybrid vector + FTS/BM25 + RRF + rerank (theo code hiện tại)"],
  ["Chỉ số", "Faithfulness, Answer Relevancy, Context Quality do Gemini judge"],
  ["Raw evidence", `data/pilot_experiment_results/${newest}`],
  ["Lỗi", "Giữ nguyên toàn bộ lỗi HTTP hoặc API; không loại trừ hậu nghiệm"],
  ["Giới hạn", s.limitation],
];

const title = { font: { name: "Arial", size: 15, bold: true, color: "#1F2937" } };
const header = { fill: "#1F4E78", font: { name: "Arial", size: 10, bold: true, color: "#FFFFFF" }, horizontalAlignment: "center", verticalAlignment: "center" };
for (const sheet of [summary, results, sources]) sheet.getUsedRange().format.font = { name: "Arial", size: 10 };
for (const cell of [summary.getRange("A2"), sources.getRange("A2")]) cell.format = title;
summary.getRange("A3").format = { fill: "#FEF3C7", font: { name: "Arial", size: 10, bold: true, color: "#92400E" } };
for (const range of [summary.getRange("A5:B5"), summary.getRange("D5:E5"), summary.getRange("A14:H14"), results.getRange("A1:L1"), sources.getRange("A4:B4")]) range.format = header;
summary.getRange("A5:B12").format.borders = { preset: "all", style: "thin", color: "#D1D5DB" }; summary.getRange("D5:E10").format.borders = { preset: "all", style: "thin", color: "#D1D5DB" }; summary.getRange("A14:H19").format.borders = { preset: "all", style: "thin", color: "#D1D5DB" };
summary.getRange("B9").format.numberFormat = "0.0%"; summary.getRange("B10:B12").format.numberFormat = "0.000"; summary.getRange("E6").format.numberFormat = "0.000";
results.getRange("D2:D11").format.numberFormat = "0.000"; results.getRange("E2:G11").format.numberFormat = "0.000";
summary.getRange("A:A").format.columnWidth = 28; summary.getRange("B:B").format.columnWidth = 32; summary.getRange("D:D").format.columnWidth = 27; summary.getRange("E:E").format.columnWidth = 38;
results.getRange("A:H").format.columnWidth = 15; results.getRange("I:I").format.columnWidth = 44; results.getRange("J:J").format.columnWidth = 62; results.getRange("K:K").format.columnWidth = 45; results.getRange("L:L").format.columnWidth = 42; results.getUsedRange().format.wrapText = true;
sources.getRange("A:A").format.columnWidth = 24; sources.getRange("B:B").format.columnWidth = 90; sources.getUsedRange().format.wrapText = true;

wb.recalculate();
const check = await wb.inspect({ kind: "table", range: "Tổng quan pilot!A2:H19", include: "values,formulas", tableMaxRows: 20, tableMaxCols: 8 }); console.log(check.ndjson);
const preview = await wb.render({ sheetName: "Tổng quan pilot", range: "A1:H19", scale: 1.5, format: "png" }); await fs.writeFile(`${outputDir}/preview.png`, new Uint8Array(await preview.arrayBuffer()));
const output = await SpreadsheetFile.exportXlsx(wb); await output.save(`${outputDir}/Thuc_nghiem_ket_qua.xlsx`);
