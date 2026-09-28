import fs from "node:fs/promises";
import { SpreadsheetFile, Workbook } from "@oai/artifact-tool";

const outputDir = "outputs/acamind_1000_test_results";
await fs.mkdir(outputDir, { recursive: true });

// Deterministic PRNG: the data is repeatable, not a claim of live measurements.
let seed = 20260916;
const rand = () => {
  seed = (seed * 1664525 + 1013904223) >>> 0;
  return seed / 4294967296;
};
const pick = (items) => items[Math.floor(rand() * items.length)];

const modules = [
  ["M1", "Phân tích đa tài liệu"],
  ["M2", "Atlas trực quan 3D"],
  ["M3", "Tải tài liệu động"],
  ["M4", "Quản lý thư viện"],
  ["M5", "Chat hỏi đáp RAG"],
  ["M6", "Tra cứu sức khỏe tâm thần"],
  ["M7", "Chế độ học tập & Quiz"],
];
const digitalScenarios = ["Trầm cảm nhẹ", "Thuốc điều trị hưng cảm", "Tâm lý học hành vi", "Điều kiện hóa Skinner", "Các loại chú ý", "Dấu hiệu căng thẳng học đường", "5 nguyên tắc PFA"];
const scannedScenarios = ["Phân biệt lo âu và sợ hãi", "Điều hòa cảm xúc", "Hiện tượng tâm lý"];
const memoryScenarios = ["Tóm tắt chủ đề đã đọc", "Khôi phục ngữ cảnh phiên chat", "Ôn tập khái niệm chính"];
const testTypes = ["Functional", "Integration", "Performance", "Safety"];
const start = new Date("2026-09-16T08:00:00");
const rows = [];

for (let i = 1; i <= 1000; i++) {
  const r = rand();
  let flow, format, expected, result, scenario, latency, faithfulness, relevancy, precision, citations, outcome;
  if (r < 0.70) {
    flow = "Digital PDF - Full RAG";
    format = "Digital";
    scenario = pick(digitalScenarios);
    expected = "Trả lời có trích dẫn trang";
    latency = +(2.51 + rand() * 0.87).toFixed(2);
    faithfulness = +(0.96 + rand() * 0.04).toFixed(2);
    relevancy = 1;
    precision = +(rand() * 0.65).toFixed(2);
    citations = 1 + Math.floor(rand() * 4);
    outcome = rand() < 0.985 ? "PASS" : "FAIL";
    result = outcome === "PASS" ? "Câu trả lời có trích dẫn trang" : "Thiếu trích dẫn hoặc quá thời gian";
  } else if (r < 0.90) {
    flow = "Scanned PDF - Safe Refusal";
    format = "Scanned";
    scenario = pick(scannedScenarios);
    expected = "Từ chối an toàn khi không có ngữ cảnh";
    latency = +(1.46 + rand() * 0.12).toFixed(2);
    faithfulness = 0;
    relevancy = 0;
    precision = 0;
    citations = 0;
    outcome = rand() < 0.99 ? "PASS" : "FAIL";
    result = outcome === "PASS" ? "__NO_CONTEXT__ được trả về" : "Không kích hoạt từ chối an toàn";
  } else {
    flow = "L1 Compressed Memory";
    format = "Digital";
    scenario = pick(memoryScenarios);
    expected = "Khôi phục ngữ cảnh dưới 0,50 giây";
    latency = +(0.32 + rand() * 0.16).toFixed(2);
    faithfulness = +(0.94 + rand() * 0.06).toFixed(2);
    relevancy = +(0.95 + rand() * 0.05).toFixed(2);
    precision = +(0.55 + rand() * 0.40).toFixed(2);
    citations = 0;
    outcome = rand() < 0.99 ? "PASS" : "FAIL";
    result = outcome === "PASS" ? "Khôi phục ngữ cảnh thành công" : "Độ trễ vượt ngưỡng";
  }
  const [moduleId, moduleName] = modules[(i - 1) % modules.length];
  const executedAt = new Date(start.getTime() + (i - 1) * 60000);
  rows.push([
    `TC-${String(i).padStart(4, "0")}`, executedAt, moduleId, moduleName, pick(testTypes), scenario,
    flow, format, expected, result, outcome, latency, faithfulness, relevancy, precision, citations,
    outcome === "PASS" ? "Không" : "Cần rà soát log và chạy lại", "Mô phỏng từ thiết kế Overleaf"
  ]);
}

const wb = Workbook.create();
const summary = wb.worksheets.add("Tổng quan");
const tests = wb.worksheets.add("1.000 kết quả test");
for (const sheet of [summary, tests]) sheet.showGridLines = false;

summary.getRange("A2:H2").merge();
summary.getRange("A2").values = [["Acamind - 1.000 kết quả kiểm thử vận hành (mô phỏng)"]];
summary.getRange("A3:H3").merge();
summary.getRange("A3").values = [["Nguồn thiết kế: overleaf_acamind_paper/main.tex trong Tuan___Chi__Acamind.zip. Dữ liệu mô phỏng, không phải số đo chạy thật."]];
summary.getRange("A5:B12").values = [
  ["Chỉ tiêu", "Giá trị"],
  ["Tổng ca kiểm thử", null],
  ["PASS", null],
  ["FAIL", null],
  ["Tỷ lệ PASS", null],
  ["Độ trễ trung bình (giây)", null],
  ["Faithfulness trung bình", null],
  ["Answer Relevancy trung bình", null],
];
summary.getRange("B6:B12").formulas = [
  ["=COUNTA('1.000 kết quả test'!A2:A1001)"],
  ["=COUNTIF('1.000 kết quả test'!K2:K1001,\"PASS\")"],
  ["=COUNTIF('1.000 kết quả test'!K2:K1001,\"FAIL\")"],
  ["=B7/B6"],
  ["=AVERAGE('1.000 kết quả test'!L2:L1001)"],
  ["=AVERAGE('1.000 kết quả test'!M2:M1001)"],
  ["=AVERAGE('1.000 kết quả test'!N2:N1001)"],
];
summary.getRange("D5:F9").values = [
  ["Luồng xử lý", "Số ca", "PASS"],
  ["Digital PDF - Full RAG", null, null],
  ["Scanned PDF - Safe Refusal", null, null],
  ["L1 Compressed Memory", null, null],
  ["Ngưỡng thiết kế từ paper", "RAGAS/độ trễ", ""],
];
summary.getRange("E6:F8").formulas = [
  ["=COUNTIF('1.000 kết quả test'!G2:G1001,D6)", "=COUNTIFS('1.000 kết quả test'!G2:G1001,D6,'1.000 kết quả test'!K2:K1001,\"PASS\")"],
  ["=COUNTIF('1.000 kết quả test'!G2:G1001,D7)", "=COUNTIFS('1.000 kết quả test'!G2:G1001,D7,'1.000 kết quả test'!K2:K1001,\"PASS\")"],
  ["=COUNTIF('1.000 kết quả test'!G2:G1001,D8)", "=COUNTIFS('1.000 kết quả test'!G2:G1001,D8,'1.000 kết quả test'!K2:K1001,\"PASS\")"],
];
summary.getRange("D11:H16").values = [
  ["Ghi chú vận hành", "" , "", "", ""],
  ["Digital PDF", "Full RAG; mục tiêu tham chiếu: 2,51–3,38 giây", "", "", ""],
  ["Scanned PDF", "Kỳ vọng kích hoạt __NO_CONTEXT__ để từ chối an toàn", "", "", ""],
  ["L1 Memory", "Mục tiêu tham chiếu: dưới 0,50 giây", "", "", ""],
  ["Cách dùng", "Thay dữ liệu mô phỏng bằng log thật khi có corpus và tài khoản test", "", "", ""],
  ["Phạm vi", "7 mô-đun M1–M7, RAGAS, độ trễ và trích dẫn trang", "", "", ""],
];
summary.mergeCells("D11:H11");
summary.mergeCells("E12:H12"); summary.mergeCells("E13:H13"); summary.mergeCells("E14:H14"); summary.mergeCells("E15:H15"); summary.mergeCells("E16:H16");

const headers = ["Mã test", "Thời điểm", "Mô-đun", "Tên mô-đun", "Loại test", "Kịch bản", "Luồng xử lý", "Định dạng", "Kỳ vọng", "Kết quả", "Trạng thái", "Độ trễ (s)", "Faithfulness", "Relevancy", "Context Precision", "Số trích dẫn", "Hành động", "Nguồn dữ liệu"];
tests.getRange("A1:R1001").values = [headers, ...rows];
tests.tables.add("A1:R1001", true, "AcamindTestResults");
tests.freezePanes.freezeRows(1);
tests.freezePanes.freezeColumns(2);

const titleStyle = { font: { name: "Arial", size: 15, bold: true, color: "#1F2937" } };
summary.getRange("A2").format = titleStyle;
summary.getRange("A3").format = { font: { name: "Arial", size: 10, italic: true, color: "#4B5563" } };
for (const range of [summary.getRange("A5:B5"), summary.getRange("D5:F5"), summary.getRange("D11:H11"), tests.getRange("A1:R1")]) {
  range.format = { fill: "#1F4E78", font: { name: "Arial", size: 10, bold: true, color: "#FFFFFF" }, horizontalAlignment: "center", verticalAlignment: "center" };
}
summary.getRange("A5:B12").format.borders = { preset: "all", style: "thin", color: "#D1D5DB" };
summary.getRange("D5:F9").format.borders = { preset: "all", style: "thin", color: "#D1D5DB" };
summary.getRange("D11:H16").format.borders = { preset: "all", style: "thin", color: "#D1D5DB" };
summary.getRange("B9").format.numberFormat = "0.0%";
summary.getRange("B10:B12").format.numberFormat = "0.00";
tests.getRange("B2:B1001").format.numberFormat = "yyyy-mm-dd hh:mm";
tests.getRange("L2:L1001").format.numberFormat = "0.00";
tests.getRange("M2:O1001").format.numberFormat = "0.00";
tests.getRange("A1:R1001").format.font = { name: "Arial", size: 10 };
tests.getRange("K2:K1001").conditionalFormats.add("containsText", { text: "PASS", format: { fill: "#DCFCE7", font: { color: "#166534", bold: true } } });
tests.getRange("K2:K1001").conditionalFormats.add("containsText", { text: "FAIL", format: { fill: "#FEE2E2", font: { color: "#B91C1C", bold: true } } });

summary.getRange("A1:H20").format.font = { name: "Arial", size: 10 };
summary.getRange("A:A").format.columnWidth = 25;
summary.getRange("B:B").format.columnWidth = 18;
summary.getRange("D:D").format.columnWidth = 30;
summary.getRange("E:H").format.columnWidth = 18;
tests.getRange("A:A").format.columnWidth = 12;
tests.getRange("B:B").format.columnWidth = 19;
tests.getRange("C:C").format.columnWidth = 10;
tests.getRange("D:D").format.columnWidth = 27;
tests.getRange("E:E").format.columnWidth = 14;
tests.getRange("F:F").format.columnWidth = 29;
tests.getRange("G:G").format.columnWidth = 28;
tests.getRange("H:H").format.columnWidth = 12;
tests.getRange("I:I").format.columnWidth = 35;
tests.getRange("J:J").format.columnWidth = 33;
tests.getRange("K:K").format.columnWidth = 12;
tests.getRange("L:O").format.columnWidth = 16;
tests.getRange("P:P").format.columnWidth = 14;
tests.getRange("Q:Q").format.columnWidth = 30;
tests.getRange("R:R").format.columnWidth = 31;
tests.getRange("A1:R1001").format.verticalAlignment = "center";
tests.getRange("I:J").format.wrapText = true;

wb.recalculate();
const check = await wb.inspect({ kind: "table", range: "Tổng quan!A2:H16", include: "values,formulas", tableMaxRows: 20, tableMaxCols: 8 });
console.log(check.ndjson);
const errors = await wb.inspect({ kind: "match", searchTerm: "#REF!|#DIV/0!|#VALUE!|#NAME\\?|#N/A|#NUM!|#NULL!|#SPILL!|#CALC!", options: { useRegex: true, maxResults: 100 }, summary: "final formula error scan" });
console.log(errors.ndjson);
const preview = await wb.render({ sheetName: "Tổng quan", range: "A1:H16", scale: 1.5, format: "png" });
await fs.writeFile(`${outputDir}/preview.png`, new Uint8Array(await preview.arrayBuffer()));
const testsPreview = await wb.render({ sheetName: "1.000 kết quả test", range: "A1:R16", scale: 1, format: "png" });
await fs.writeFile(`${outputDir}/test-results-preview.png`, new Uint8Array(await testsPreview.arrayBuffer()));
const output = await SpreadsheetFile.exportXlsx(wb);
await output.save(`${outputDir}/acamind_1000_ket_qua_test_van_hanh.xlsx`);
