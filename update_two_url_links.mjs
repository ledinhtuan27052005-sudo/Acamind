import fs from 'node:fs/promises';
import { FileBlob, SpreadsheetFile } from '@oai/artifact-tool';

const workbookPath = 'C:/Users/HP/Downloads/Acamind (1)/Acamind/outputs/thuc_nghiem_phan_tich_2_url/Thuc_nghiem_phan_tich_2_URL.xlsx';
const input = await FileBlob.load(workbookPath);
const wb = await SpreadsheetFile.importXlsx(input);
const sources = wb.worksheets.getItem('Nguồn và phương pháp');

const urls = [
  'https://pubmed.ncbi.nlm.nih.gov/36357950/',
  'https://pubmed.ncbi.nlm.nih.gov/33291415/',
  'https://pubmed.ncbi.nlm.nih.gov/22707964/',
];
sources.getRange('B4:B6').values = urls.map(url => [url]);
sources.getRange('B4:B6').format.font = { name: 'Arial', size: 10, color: '#0563C1', underline: 'single' };
sources.getRange('A9:E11').values = [['Gọi POST /api/v1/debate/scrape-multi để lưu metadata và khả năng truy xuất. Sau đó gọi POST /api/v1/debate/analyze với đúng hai URL và chủ đề. Ba liên kết PubMed ở cột “URL truy cập” là liên kết bấm được; endpoint giới hạn nội dung trích xuất và yêu cầu Gemini trả về tóm tắt, điểm đồng thuận/khác biệt, đánh giá và kết luận. Các lần chạy được giãn 30 giây để hạn chế tải Gemini.']];
wb.recalculate();
const check = await wb.inspect({ kind: 'table', range: 'Nguồn và phương pháp!A3:E6', include: 'values,formulas', tableMaxRows: 6, tableMaxCols: 5 });
console.log(check.ndjson);
const errors = await wb.inspect({ kind: 'match', searchTerm: '#REF!|#DIV/0!|#VALUE!|#NAME\\?|#N/A|#NUM!|#NULL!|#SPILL!|#CALC!', options: { useRegex: true, maxResults: 100 }, summary: 'formula error scan' });
console.log(errors.ndjson);
const output = await SpreadsheetFile.exportXlsx(wb);
await output.save(workbookPath);
const preview = await wb.render({ sheetName: 'Nguồn và phương pháp', range: 'A1:E17', scale: 1.25, format: 'png' });
await fs.writeFile('C:/Users/HP/Downloads/Acamind (1)/Acamind/outputs/thuc_nghiem_phan_tich_2_url/preview_sources.png', new Uint8Array(await preview.arrayBuffer()));
console.log(workbookPath);
