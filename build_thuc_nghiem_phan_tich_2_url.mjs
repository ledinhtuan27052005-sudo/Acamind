import fs from 'node:fs/promises';
import { Workbook, SpreadsheetFile } from '@oai/artifact-tool';

const root = 'C:/Users/HP/Downloads/Acamind (1)/Acamind';
const inputPath = `${root}/data/two_url_experiment_results/two_url_experiment_20260916_224313.json`;
const outputDir = `${root}/outputs/thuc_nghiem_phan_tich_2_url`;
const outputPath = `${outputDir}/Thuc_nghiem_phan_tich_2_URL.xlsx`;
const report = JSON.parse(await fs.readFile(inputPath, 'utf8'));
const cases = report.cases;
const avgSeconds = cases.reduce((sum, item) => sum + item.elapsed_seconds, 0) / cases.length;

const wb = Workbook.create();
const summary = wb.worksheets.add('Tóm tắt');
const runs = wb.worksheets.add('Lần chạy');
const analyses = wb.worksheets.add('Phân tích gốc');
const sources = wb.worksheets.add('Nguồn và phương pháp');

const navy = '#163A5F';
const blue = '#DCEAF7';
const pale = '#F4F8FC';
const green = '#E2F0D9';
const red = '#FCE4D6';
const grid = '#D9E2F3';
const baseFont = { name: 'Arial', size: 10, color: '#1F2937' };

function title(sheet, text, width = 'A1:H1') {
  sheet.getRange(width).merge();
  sheet.getRange('A1').values = [[text]];
  sheet.getRange('A1').format = { font: { name: 'Arial', size: 15, bold: true, color: navy }, verticalAlignment: 'center' };
  sheet.getRange('A1').format.rowHeight = 26;
}
function header(sheet, range) {
  sheet.getRange(range).format = { fill: navy, font: { name: 'Arial', size: 10, bold: true, color: '#FFFFFF' }, horizontalAlignment: 'center', verticalAlignment: 'center', wrapText: true, borders: { preset: 'all', style: 'thin', color: '#FFFFFF' } };
}
function body(sheet, range) {
  sheet.getRange(range).format = { font: baseFont, verticalAlignment: 'top', wrapText: true, borders: { preset: 'all', style: 'thin', color: grid } };
}
for (const sheet of [summary, runs, analyses, sources]) { sheet.showGridLines = false; sheet.tabColor = navy; }

title(summary, 'Thực nghiệm tính năng phân tích 2 URL web', 'A1:H1');
summary.getRange('A3:H3').merge();
summary.getRange('A3').values = [['Phạm vi: 3 lần gọi thực tế POST /api/v1/debate/analyze. Mỗi lần gồm URL công khai → scraper → Gemini → phản hồi streaming.']];
summary.getRange('A3').format = { font: { name: 'Arial', size: 10, italic: true, color: '#4B5563' }, wrapText: true };
summary.getRange('A5:B10').values = [
  ['Chỉ số', 'Giá trị'],
  ['Số cặp URL kiểm thử', cases.length],
  ['Phản hồi HTTP 200', cases.filter(x => x.analysis_http_status === 200).length],
  ['Tỷ lệ phân tích thành công', cases.filter(x => x.success).length / cases.length],
  ['Thời gian phản hồi trung bình (giây)', avgSeconds],
  ['Ký tự kết quả AI trung bình', cases.reduce((s, x) => s + x.analysis_text.length, 0) / cases.length],
];
header(summary, 'A5:B5'); body(summary, 'A6:B10');
summary.getRange('B8').format.numberFormat = '0.0%';
summary.getRange('B9:B10').format.numberFormat = '#,##0.0';
summary.getRange('D5:H5').merge(); summary.getRange('D5').values = [['Kết luận vận hành']]; header(summary, 'D5:H5');
summary.getRange('D6:H10').merge();
summary.getRange('D6').values = [['Ba cặp nguồn khoa học công khai đã được truy xuất bằng PubMed NCBI API và phân tích thành công qua endpoint mà giao diện sử dụng. Kết quả có đủ sáu phần theo prompt: tóm tắt từng bài, điểm đồng thuận, khác biệt, đánh giá và kết luận. Đây là bằng chứng chức năng ở quy mô nhỏ, không phải đánh giá chất lượng khoa học tổng quát hoặc benchmark với mô hình khác.']];
summary.getRange('D6:H10').format = { fill: pale, font: baseFont, wrapText: true, verticalAlignment: 'top', borders: { preset: 'outside', style: 'thin', color: grid } };
summary.getRange('A12:H12').merge(); summary.getRange('A12').values = [['Kết quả theo cặp URL']]; header(summary, 'A12:H12');
summary.getRange('A13:H16').values = [
  ['Mã', 'Cặp nguồn', 'HTTP', 'Thành công', 'Thời gian (giây)', 'Ký tự phản hồi', 'Phương thức lấy URL 1', 'Phương thức lấy URL 2'],
  ...cases.map(x => [x.case_id, `${x.source_1_label} ↔ ${x.source_2_label}`, x.analysis_http_status, x.success ? 'Có' : 'Không', x.elapsed_seconds, x.analysis_text.length, x.scrape_preview.sources[0].source_method, x.scrape_preview.sources[1].source_method]),
];
header(summary, 'A13:H13'); body(summary, 'A14:H16');
summary.getRange('D14:D16').format.fill = green;
summary.getRange('E14:E16').format.numberFormat = '0.000';
summary.getRange('A1').format.font = { name: 'Arial', size: 15, bold: true, color: navy };
['A','B','C','D','E','F','G','H'].forEach((col, i) => summary.getRange(`${col}:${col}`).format.columnWidth = [12, 44, 10, 12, 15, 16, 20, 20][i]);
summary.getRange('A13:H16').format.rowHeight = 36;

title(runs, 'Chi tiết các lần chạy endpoint', 'A1:L1');
runs.getRange('A3:L6').values = [
  ['Mã', 'Thời điểm UTC', 'URL 1', 'URL 2', 'Chủ đề yêu cầu', 'HTTP scrape', 'HTTP phân tích', 'Thành công', 'Thời gian (giây)', 'Ký tự URL 1', 'Ký tự URL 2', 'Ký tự kết quả'],
  ...cases.map(x => [x.case_id, x.run_at_utc, x.url1, x.url2, x.topic, x.scrape_http_status, x.analysis_http_status, x.success ? 'Có' : 'Không', x.elapsed_seconds, x.scrape_preview.sources[0].char_count, x.scrape_preview.sources[1].char_count, x.analysis_text.length]),
];
header(runs, 'A3:L3'); body(runs, 'A4:L6');
runs.getRange('H4:H6').format.fill = green;
runs.getRange('I4:I6').format.numberFormat = '0.000';
['A','B','C','D','E','F','G','H','I','J','K','L'].forEach((col, i) => runs.getRange(`${col}:${col}`).format.columnWidth = [9,25,42,42,40,14,15,12,16,15,15,16][i]);
runs.getRange('A3:L6').format.rowHeight = 34;
runs.freezePanes.freezeRows(3);

title(analyses, 'Văn bản phản hồi nguyên gốc từ tính năng phân tích 2 URL', 'A1:D1');
analyses.getRange('A3:D3').values = [['Mã', 'Cặp URL', 'Thời gian (giây)', 'Phân tích AI nguyên gốc']];
header(analyses, 'A3:D3');
analyses.getRange('A4:D6').values = cases.map(x => [x.case_id, `${x.url1}\n${x.url2}`, x.elapsed_seconds, x.analysis_text]);
body(analyses, 'A4:D6');
analyses.getRange('C4:C6').format.numberFormat = '0.000';
analyses.getRange('A:A').format.columnWidth = 10;
analyses.getRange('B:B').format.columnWidth = 46;
analyses.getRange('C:C').format.columnWidth = 16;
analyses.getRange('D:D').format.columnWidth = 110;
analyses.getRange('A4:D6').format.rowHeight = 330;
analyses.freezePanes.freezeRows(3);

title(sources, 'Nguồn, phương pháp và giới hạn diễn giải', 'A1:E1');
sources.getRange('A3:E6').values = [
  ['Nguồn', 'URL truy cập', 'Tác giả / năm', 'Cách hệ thống lấy nội dung', 'Dẫn chứng có thể kiểm tra'],
  ['Bài A', 'https://pubmed.ncbi.nlm.nih.gov/36357950/', 'Gibbons, 2022', 'pubmed_api (NCBI E-utilities)', 'PMID 36357950; trích xuất 1.735 ký tự trong test'],
  ['Bài B', 'https://pubmed.ncbi.nlm.nih.gov/33291415/', 'Trigueros et al., 2020', 'pubmed_api (NCBI E-utilities)', 'PMID 33291415; trích xuất 1.871 ký tự trong test'],
  ['Bài C', 'https://pubmed.ncbi.nlm.nih.gov/22707964/', 'Park et al., 2012', 'pubmed_api (NCBI E-utilities)', 'PMID 22707964; trích xuất 2.075 ký tự trong test'],
];
header(sources, 'A3:E3'); body(sources, 'A4:E6');
sources.getRange('A8:E8').merge(); sources.getRange('A8').values = [['Phương pháp']]; header(sources, 'A8:E8');
sources.getRange('A9:E11').merge(); sources.getRange('A9').values = [['Gọi POST /api/v1/debate/scrape-multi để lưu metadata và khả năng truy xuất. Sau đó gọi POST /api/v1/debate/analyze với đúng hai URL và chủ đề. Endpoint giới hạn nội dung trích xuất và yêu cầu Gemini trả về tóm tắt, điểm đồng thuận/khác biệt, đánh giá và kết luận. Các lần chạy được giãn 30 giây để hạn chế tải Gemini.']];
sources.getRange('A9:E11').format = { fill: pale, font: baseFont, wrapText: true, verticalAlignment: 'top', borders: { preset: 'outside', style: 'thin', color: grid } };
sources.getRange('A13:E13').merge(); sources.getRange('A13').values = [['Giới hạn cần nêu trong báo cáo']]; header(sources, 'A13:E13');
sources.getRange('A14:E17').merge(); sources.getRange('A14').values = [['N=3 cặp URL, cùng chủ đề giáo dục/tâm lý học; đây là kiểm thử vận hành, không phải đánh giá suy luận nhân quả hay độ đúng tuyệt đối. Nội dung được gửi cho AI bị giới hạn theo endpoint (tối đa 4.000 ký tự/bài). Có một vòng thử trước đó ghi nhận Gemini trả HTTP 503 tạm thời ở 2/3 lần; vòng đã báo cáo ở đây dùng nguồn PubMed API và 3/3 thành công. Báo cáo khoa học cần bổ sung tập dữ liệu giữ lại, rubric chấm độc lập, đánh giá mù và baseline trước khi đưa ra tuyên bố hiệu năng tổng quát.']];
sources.getRange('A14:E17').format = { fill: red, font: baseFont, wrapText: true, verticalAlignment: 'top', borders: { preset: 'outside', style: 'thin', color: '#E6B8AF' } };
['A','B','C','D','E'].forEach((col, i) => sources.getRange(`${col}:${col}`).format.columnWidth = [12,48,23,31,46][i]);
sources.getRange('A3:E6').format.rowHeight = 36;

wb.recalculate();
const check = await wb.inspect({ kind: 'table', range: 'Tóm tắt!A1:H16', include: 'values,formulas', tableMaxRows: 20, tableMaxCols: 10 });
console.log(check.ndjson);
const errors = await wb.inspect({ kind: 'match', searchTerm: '#REF!|#DIV/0!|#VALUE!|#NAME\\?|#N/A|#NUM!|#NULL!|#SPILL!|#CALC!', options: { useRegex: true, maxResults: 100 }, summary: 'formula error scan' });
console.log(errors.ndjson);
await fs.mkdir(outputDir, { recursive: true });
const preview = await wb.render({ sheetName: 'Tóm tắt', range: 'A1:H16', scale: 1.5, format: 'png' });
await fs.writeFile(`${outputDir}/preview_summary.png`, new Uint8Array(await preview.arrayBuffer()));
const output = await SpreadsheetFile.exportXlsx(wb);
await output.save(outputPath);
console.log(outputPath);
