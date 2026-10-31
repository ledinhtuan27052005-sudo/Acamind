"""Source-linked study profiles built from original, document-scoped chunks."""
import re
from app.services.claim_origin import classify_claim_origins

FIELDS = {
    'objective': ('Mục tiêu', r'\b(?:aims?|objectives?|purpose|mục tiêu|mục đích)\b'),
    'method': ('Phương pháp', r'\b(?:methods?|design|procedure|randomi[sz]ed|observational|cohort|cross.sectional|phương pháp|thiết kế)\b'),
    'sample': ('Mẫu / quần thể', r'\b(?:participants?|patients?|subjects?|students?|adults?|sample|population|cỡ mẫu|người tham gia|bệnh nhân|sinh viên|người lớn)\b'),
    'data': ('Dữ liệu', r'\b(?:datasets?|corpus|data collection|dữ liệu|thu thập)\b'),
    'measure': ('Thang đo / chỉ số', r'\b(?:metrics?|scales?|instruments?|questionnaires?|GAD-7|PHQ-9|BDI-II|DASS-21|thang đo|chỉ số|công cụ đo)\b'),
    'finding': ('Kết quả', r'\b(?:results?|findings?|outcomes?|we found|kết quả|phát hiện|ghi nhận)\b'),
    'limitation': ('Hạn chế', r'\b(?:limitations?|caveats?|hạn chế|giới hạn)\b'),
    'timepoint': ('Thời điểm đánh giá', r'\b(?:follow.up|weeks?|months?|years?|tuần|tháng|theo dõi)\b'),
    'comparator': ('Can thiệp / đối chứng', r'\b(?:intervention|control|placebo|treatment|CBT|waitlist|can thiệp|đối chứng|giả dược)\b'),
    'direction': ('Quy ước chiều điểm số', r'\b(?:higher|lower|scoring|coding|điểm cao|điểm thấp|mã hóa)\b'),
}


def build_study_profile(document, chunks, truncated=False):
    did = str(document['document_id'])
    pools = {key: [] for key in FIELDS}
    seen = {key: set() for key in FIELDS}
    scanned = 0
    chars = 0
    for chunk in chunks:
        if str(chunk.get('document_id')) != did:
            continue
        page = chunk.get('page_number')
        if type(page) is not int or page < 1:
            continue
        content = str(chunk.get('content') or '')
        if chars + len(content) > 2_000_000:
            truncated = True
            break
        scanned += 1
        chars += len(content)
        for span in classify_claim_origins(content):
            quote = span['quote']
            if len(quote) < 30 or len(quote) > 1200:
                continue
            for key, (_, pattern) in FIELDS.items():
                if not re.search(pattern, quote, re.I):
                    continue
                fingerprint = ' '.join(quote.casefold().split())
                if fingerprint in seen[key]:
                    continue
                seen[key].add(fingerprint)
                pools[key].append({**span, 'document_id': did, 'chunk_id': str(chunk.get('id') or ''),
                                   'page': page})
    priority = {'current_study_candidate': 0, 'unclear': 1, 'cited_study_candidate': 2}
    fields = {}
    for key, (label, _) in FIELDS.items():
        ranked = sorted(pools[key], key=lambda item: priority[item['origin']])
        fields[key] = {'label': label, 'status': 'unverified' if ranked else 'not_found',
                       'candidate_count': len(ranked), 'candidates': ranked[:3]}
    return {**document, 'schema_version': 1, 'status': 'unverified', 'fields': fields,
            'coverage': {'chunks_scanned': scanned, 'truncated': truncated, 'scope': 'indexed_chunks'},
            'message': 'Hồ sơ trích xuất ứng viên, chưa thẩm định. Chưa tìm thấy trong dữ liệu đã quét không có nghĩa bài gốc không đề cập.'}
