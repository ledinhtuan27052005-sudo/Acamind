"""Conservative source-attribution hints, not verified authorship judgments."""
import re

_OWN = re.compile(
    r"\b(?:we (?:found|find|observed|show|demonstrate|report|recruited|enrolled)|"
    r"our (?:results|findings|study|experiment)|in (?:this|the present) study|"
    r"chúng tôi (?:ghi nhận|phát hiện|nhận thấy|tuyển|khảo sát)|"
    r"kết quả của (?:chúng tôi|nghiên cứu này)|trong nghiên cứu này)\b", re.I)
_OTHER = re.compile(
    r"\b(?:previous (?:studies|research|work)|prior (?:studies|research|work)|"
    r"according to|reported by|nghiên cứu trước|các nghiên cứu trước|"
    r"theo nghiên cứu của|được báo cáo bởi)\b|"
    r"\b[A-ZÀ-Ỹ][\w’'-]+(?:\s+(?:et al\.?|và cộng sự))?\s*"
    r"\((?:19|20)\d{2}[a-z]?\)\s*(?:found|reported|showed|observed|ghi nhận|cho thấy)", re.I)
_CITATION = re.compile(
    r"\[\s*\d+(?:\s*[,;–-]\s*\d+)*\s*\]|"
    r"\([^()]*\b(?:19|20)\d{2}[a-z]?[^()]*\)")


def classify_claim_origins(content):
    """Return exact sentence spans and explicit ambiguous/missing states.

    Headings, statistics, absence of citations and page position never establish
    ownership. Quoted first-person statements remain ambiguous.
    """
    text = str(content or "")
    boundaries = [0]
    for match in re.finditer(r"[.!?]\s+(?=[A-ZÀ-Ỹ])|\n+", text):
        if re.search(r"\b(?:al|Dr|Mr|Ms|Fig|vs)\.$", text[:match.start() + 1], re.I):
            continue
        boundaries.append(match.end())
    boundaries.append(len(text))
    claims = []
    for start, end in zip(boundaries, boundaries[1:]):
        while start < end and text[start].isspace():
            start += 1
        while end > start and text[end - 1].isspace():
            end -= 1
        quote = text[start:end]
        if not quote:
            continue
        own = bool(_OWN.search(quote))
        other = bool(_OTHER.search(quote))
        citation = bool(_CITATION.search(quote))
        quoted_own = own and bool(re.search(r'["“”«»]', quote))
        qualified_own = own and bool(re.search(
            r"\b(?:not our|not in this study|không phải|không thuộc|if our|nếu nghiên cứu này)\b|\?", quote, re.I))
        if own and (other or citation or quoted_own or qualified_own):
            origin, reason = 'unclear', 'mixed_or_quoted_attribution'
        elif own:
            origin, reason = 'current_study_candidate', 'explicit_first_person_or_current_study'
        elif other:
            origin, reason = 'cited_study_candidate', 'explicit_external_attribution'
        else:
            origin, reason = 'unclear', 'citation_without_owner' if citation else 'no_explicit_owner'
        claims.append({'start': start, 'end': end, 'quote': quote, 'origin': origin,
                       'reason': reason, 'status': 'unverified', 'has_citation': citation})
    return claims
