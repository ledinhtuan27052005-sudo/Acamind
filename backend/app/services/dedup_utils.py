"""
Dedup utilities — Shared helpers cho loại bỏ trùng lặp toàn diện.

Dùng bởi:
- memory_builder.py: dedup key_facts + entities trong cùng 1 build
- retriever.py: cross-doc dedup trong L1 retrieval
- document.py: detect duplicate file khi upload
"""
from __future__ import annotations

import hashlib
import re
from difflib import SequenceMatcher
from typing import Optional


def _normalize_text(s: str) -> str:
    """Lowercase, strip punctuation, collapse whitespace.

    Dùng để so sánh 2 string có "ngữ nghĩa giống" bất kể format.
    vd: "Freud (1900)" và "  freud 1900 " đều normalize thành "freud 1900".
    """
    if not s:
        return ""
    s = re.sub(r"[^\w\sàáâãèéêìíòóôõùúýăđơưạảấầẩẫậắằẳẵặẹẻẽếềểễệỉịọỏốồổỗộớờởỡợụủứừửữựỳỵỷỹ]", " ", s.lower())
    return re.sub(r"\s+", " ", s).strip()


def _is_fuzzy_dup(a: str, b: str, threshold: float = 0.85) -> bool:
    """True nếu 2 text giống nhau ≥ threshold (theo SequenceMatcher).

    Args:
        a, b: 2 string cần so sánh.
        threshold: 0.0-1.0. Mặc định 0.85 (khá strict, chỉ dedup khi thực sự giống).
                  - 0.95+ : rất giống, gần như identical
                  - 0.85 : gần giống, có thể bỏ trùng
                  - 0.70 : tương tự, cẩn thận false positive

    Special cases (ưu tiên match):
    - Exact match (sau normalize)
    - Substring: 1 string chứa string kia (vd "Freud" trong "Sigmund Freud")
    - SequenceMatcher ratio ≥ threshold
    """
    if not a or not b:
        return False
    norm_a = _normalize_text(a)
    norm_b = _normalize_text(b)
    if not norm_a or not norm_b:
        return False
    # Exact match
    if norm_a == norm_b:
        return True
    # Token-based fuzzy match: split thành từ, so sánh overlap. Đây là cách hiệu quả
    # nhất cho entities vì entities thường là multi-word ("Sigmund Freud" = 2 tokens).
    # Nếu ratio (số token chung) / (max tokens) ≥ 0.5 → match.
    # Ví dụ: {"freud"} vs {"sigmund", "freud"} → 1/2 = 50% → match
    #         {"freud"} vs {"einstein"} → 0/1 = 0% → fail
    #         {"sigmund", "freud"} vs {"freud", "sigmund"} → 2/2 = 100% → match
    tokens_a = set(norm_a.split())
    tokens_b = set(norm_b.split())
    if tokens_a and tokens_b:
        common = tokens_a & tokens_b
        if common:
            token_overlap = len(common) / max(len(tokens_a), len(tokens_b))
            if token_overlap >= 0.5 and len(common) >= 1:
                return True
    # SequenceMatcher ratio (fallback cho typo hoặc word reordering).
    # Chỉ áp dụng khi 1 trong 2 string dài ≥ 8 chars (tránh false positive với
    # single-token typo như "Freud" vs "Freuud" ratio 0.91 nhưng khác nhau).
    if max(len(norm_a), len(norm_b)) >= 8:
        return SequenceMatcher(None, norm_a, norm_b).ratio() >= threshold
    # Single-token ngắn (< 8 chars) + ratio < 0.85 → fail (chấp nhận typo là fact khác)
    return False


def compute_file_hash(file_obj, chunk_size: int = 1024 * 1024) -> str:
    """SHA-256 hash streaming, không load full file vào RAM.

    Args:
        file_obj: File-like object (vd UploadFile.file).
        chunk_size: 1MB default. File 200MB → 200 chunks → ~500ms trên SSD.

    Returns:
        Hex string SHA-256 (64 chars).
    """
    h = hashlib.sha256()
    file_obj.seek(0)
    try:
        while True:
            chunk = file_obj.read(chunk_size)
            if not chunk:
                break
            h.update(chunk)
    finally:
        # Reset pointer để caller có thể đọc lại từ đầu
        try:
            file_obj.seek(0)
        except Exception:
            pass
    return h.hexdigest()


def compute_bytes_hash(data: bytes) -> str:
    """SHA-256 hash của bytes (cho path-based hashing, vd hash content đã load)."""
    return hashlib.sha256(data).hexdigest()


def dedup_facts(facts: list, threshold: float = 0.85) -> list:
    """Bỏ fact trùng nhau trong cùng 1 list, dùng fuzzy match.

    Khi 2 facts match (similarity ≥ threshold):
    - Giữ fact có confidence cao hơn
    - Nếu bằng → giữ fact có page nhỏ hơn (fact xuất hiện sớm hơn trong doc)

    Args:
        facts: list các dict {"claim": str, "page": int, "confidence": float, ...}
        threshold: SequenceMatcher threshold (default 0.85).

    Returns:
        list đã dedup, giữ nguyên format input.
    """
    out = []
    for f in facts:
        if not isinstance(f, dict):
            continue
        claim = f.get("claim", "")
        if not claim:
            continue
        # Tìm trong out có fact nào match fuzzy không
        matched_idx = -1
        for i, existing in enumerate(out):
            if _is_fuzzy_dup(claim, existing.get("claim", ""), threshold):
                matched_idx = i
                break
        if matched_idx < 0:
            # Mới, copy
            out.append(dict(f))
        else:
            # Match → merge: giữ conf cao hơn hoặc page nhỏ hơn
            existing = out[matched_idx]
            new_conf = float(f.get("confidence", 0.8))
            old_conf = float(existing.get("confidence", 0.8))
            new_page = int(f.get("page", 999))
            old_page = int(existing.get("page", 999))
            if new_conf > old_conf or (new_conf == old_conf and new_page < old_page):
                out[matched_idx] = dict(f)
    return out


def dedup_entities(entities: list, threshold: float = 0.80) -> list:
    """Bỏ entity trùng tên gần đúng, merge pages.

    Logic:
    - So sánh tên entities bằng SequenceMatcher với threshold 0.80 (thấp hơn facts
      vì tên entity thường ngắn, dễ trùng gần đúng).
    - Khi match: giữ tên dài hơn (thường đầy đủ hơn, vd "Sigmund Freud" > "Freud"),
      union pages (entity xuất hiện ở nhiều trang).
    - Ưu tiên type cụ thể hơn ("person"/"theory") hơn "term".

    Lưu ý: input entities có format {"name", "type", "page"} (page đơn).
    Hàm này internally dùng list `pages` để merge, sau đó convert về page đại diện.
    """
    out = []
    for e in entities:
        if not isinstance(e, dict):
            continue
        name = e.get("name", "").strip()
        if not name:
            continue
        # Tìm match
        matched_idx = -1
        for i, existing in enumerate(out):
            if _is_fuzzy_dup(name, existing.get("name", ""), threshold):
                matched_idx = i
                break
        if matched_idx < 0:
            # Mới
            new_e = dict(e)
            new_e["pages"] = [e.get("page", 0)] if e.get("page", 0) else []
            out.append(new_e)
        else:
            # Merge
            existing = out[matched_idx]
            # Giữ tên dài hơn (đầy đủ hơn)
            if len(name) > len(existing.get("name", "")):
                existing["name"] = name
            # Union pages
            if e.get("page", 0):
                existing.setdefault("pages", []).append(e["page"])
            # Ưu tiên type cụ thể hơn
            current_type = existing.get("type", "term")
            new_type = e.get("type", "term")
            if new_type in ("person", "theory") and current_type == "term":
                existing["type"] = new_type
    # Convert pages list → page đại diện (min)
    for e in out:
        if "pages" in e and e["pages"]:
            valid_pages = [p for p in e["pages"] if p and p > 0]
            e["page"] = min(valid_pages) if valid_pages else 0
            # Xóa field tạm
            del e["pages"]
    return out
