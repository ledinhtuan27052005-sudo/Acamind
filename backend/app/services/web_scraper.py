"""
Robust web scraper with multi-strategy fallback.

Handles cookie-protected, JS-gated, and paywall pages by trying multiple
approaches in sequence until content is successfully extracted.

Strategies (in order):
  0. PubMed NCBI E-utilities API (for pubmed.ncbi.nlm.nih.gov URLs)
  1. Direct scrape with full browser headers + cookie session (requests.Session)
  2. Jina Reader API (r.jina.ai) — renders JS, handles cookies, returns clean text
  3. Google Webcache
  4. Archive.org Wayback Machine
  5. Meta tags / <p> extraction (from direct scrape HTML)
  6. DuckDuckGo snippet as last resort
"""

import re
import logging
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from html.parser import HTMLParser
from typing import Optional

import requests

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Shared browser-like headers
# ---------------------------------------------------------------------------
_BROWSER_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/126.0.0.0 Safari/537.36"
    ),
    "Accept": (
        "text/html,application/xhtml+xml,application/xml;"
        "q=0.9,image/webp,image/apng,*/*;q=0.8"
    ),
    "Accept-Language": "en-US,en;q=0.9,vi;q=0.8",
    "Accept-Encoding": "gzip, deflate, br",
    "DNT": "1",
    "Connection": "keep-alive",
    "Upgrade-Insecure-Requests": "1",
    "Sec-Fetch-Dest": "document",
    "Sec-Fetch-Mode": "navigate",
    "Sec-Fetch-Site": "none",
    "Sec-Fetch-User": "?1",
    "Cache-Control": "max-age=0",
}

# Minimum characters for "real" article content (below this → likely blocked)
_MIN_CONTENT_LENGTH = 80


# ---------------------------------------------------------------------------
# HTML text extractor (improved with article-aware heuristics)
# ---------------------------------------------------------------------------
class _TextExtractor(HTMLParser):
    """Extract visible text from HTML, skipping non-content tags."""
    SKIP_TAGS = {
        "script", "style", "noscript", "nav", "footer", "header",
        "aside", "svg", "form", "button", "iframe",
    }

    def __init__(self):
        super().__init__()
        self._skip = False
        self._skip_depth = 0
        self._tag_stack: list[str] = []
        self.text_parts: list[str] = []

    def handle_starttag(self, tag, attrs):
        self._tag_stack.append(tag)
        if tag in self.SKIP_TAGS:
            self._skip = True
            self._skip_depth += 1

    def handle_endtag(self, tag):
        if self._tag_stack and self._tag_stack[-1] == tag:
            self._tag_stack.pop()
        if tag in self.SKIP_TAGS and self._skip_depth > 0:
            self._skip_depth -= 1
            if self._skip_depth == 0:
                self._skip = False

    def handle_data(self, data):
        if not self._skip:
            stripped = data.strip()
            if stripped:
                self.text_parts.append(stripped)


def _extract_text(html: str) -> str:
    """Extract and clean text from raw HTML."""
    parser = _TextExtractor()
    parser.feed(html)
    content = " ".join(parser.text_parts)
    return re.sub(r"\s{2,}", " ", content).strip()


def _extract_title(html: str, fallback: str = "") -> str:
    """Extract <title> from HTML."""
    m = re.search(r"<title[^>]*>(.*?)</title>", html, re.IGNORECASE | re.DOTALL)
    title = m.group(1).strip() if m else fallback
    # Clean HTML entities
    title = re.sub(r"&amp;", "&", title)
    title = re.sub(r"&lt;", "<", title)
    title = re.sub(r"&gt;", ">", title)
    title = re.sub(r"&#\d+;", "", title)
    return title[:200]


def _extract_meta_content(html: str) -> Optional[str]:
    """
    Extract content from <meta> tags (og:description, description, etc.)
    These are always in the HTML even for JS-rendered pages.
    """
    # Try Open Graph description first (usually richest)
    patterns = [
        r'<meta\s+(?:property|name)=["\']og:description["\']\s+content=["\']([^"\']+)["\']',
        r'<meta\s+content=["\']([^"\']+)["\']\s+(?:property|name)=["\']og:description["\']',
        r'<meta\s+name=["\']description["\']\s+content=["\']([^"\']+)["\']',
        r'<meta\s+content=["\']([^"\']+)["\']\s+name=["\']description["\']',
        r'<meta\s+(?:property|name)=["\']twitter:description["\']\s+content=["\']([^"\']+)["\']',
    ]
    for pattern in patterns:
        match = re.search(pattern, html, re.IGNORECASE)
        if match:
            desc = match.group(1).strip()
            if len(desc) > 30:  # Skip very short meta descriptions
                return desc
    return None


def _extract_p_tags(html: str) -> Optional[str]:
    """
    Extract text from all <p> tags. Works even when the main extractor
    gets confused by complex page layouts.
    """
    p_matches = re.findall(r"<p[^>]*>(.*?)</p>", html, re.IGNORECASE | re.DOTALL)
    if not p_matches:
        return None
    # Strip HTML tags from each <p> content
    texts = []
    for p_html in p_matches:
        clean = re.sub(r"<[^>]+>", " ", p_html)
        clean = re.sub(r"\s+", " ", clean).strip()
        if len(clean) > 15:  # Skip very short paragraphs (menu items, etc.)
            texts.append(clean)
    if texts:
        combined = " ".join(texts)
        if len(combined) >= _MIN_CONTENT_LENGTH:
            return combined
    return None


def _extract_article_body(html: str) -> Optional[str]:
    """
    Try to extract the main article body using common article container
    patterns. This helps get cleaner content for news/blog articles.
    """
    # Try common article containers (ordered by specificity)
    patterns = [
        r'<article[^>]*>(.*?)</article>',
        r'class="[^"]*article[_-]?(?:body|content|text)[^"]*"[^>]*>(.*?)</(?:div|section)>',
        r'class="[^"]*(?:post|entry)[_-]?(?:content|body|text)[^"]*"[^>]*>(.*?)</(?:div|section)>',
        r'class="[^"]*(?:story|news)[_-]?(?:content|body|detail)[^"]*"[^>]*>(.*?)</(?:div|section)>',
        r'id="[^"]*(?:article|content|main)[^"]*"[^>]*>(.*?)</(?:div|section)>',
        r'itemprop="articleBody"[^>]*>(.*?)</(?:div|section)>',
    ]
    for pattern in patterns:
        match = re.search(pattern, html, re.IGNORECASE | re.DOTALL)
        if match:
            article_html = match.group(1)
            text = _extract_text(article_html)
            if len(text) >= _MIN_CONTENT_LENGTH:
                return text
    return None


def _best_content_from_html(html: str) -> str:
    """
    Try multiple extraction methods on the same HTML and return the longest
    meaningful content found.
    """
    candidates = []

    # Method 1: Article body extraction
    article = _extract_article_body(html)
    if article:
        candidates.append(article)

    # Method 2: Full text extraction
    full_text = _extract_text(html)
    if full_text:
        candidates.append(full_text)

    # Method 3: <p> tag extraction
    p_text = _extract_p_tags(html)
    if p_text:
        candidates.append(p_text)

    # Method 4: Meta description (shortest, but always available)
    meta = _extract_meta_content(html)
    if meta:
        candidates.append(meta)

    if not candidates:
        return ""

    # Return the longest candidate (most content)
    return max(candidates, key=len)


# ---------------------------------------------------------------------------
# PubMed detection & NCBI E-utilities API
# ---------------------------------------------------------------------------
def _is_pubmed_url(url: str) -> bool:
    """Check if URL is a PubMed article page."""
    return bool(re.search(r'pubmed\.ncbi\.nlm\.nih\.gov/\d+', url))


def _extract_pmid(url: str) -> Optional[str]:
    """Extract PMID (PubMed ID) from a PubMed URL."""
    match = re.search(r'pubmed\.ncbi\.nlm\.nih\.gov/(\d+)', url)
    return match.group(1) if match else None


def _scrape_pubmed_api(url: str) -> Optional[tuple[str, str]]:
    """
    Fetch article metadata from NCBI E-utilities (E-fetch) API.

    This is the official, free API from NIH/NLM. It returns structured XML
    with title, abstract, authors, journal, year, DOI, keywords — bypassing
    JavaScript/cookie requirements entirely.

    Rate limit: 3 requests/sec without API key (sufficient for our use case).
    """
    pmid = _extract_pmid(url)
    if not pmid:
        return None

    try:
        api_url = (
            f"https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi"
            f"?db=pubmed&id={pmid}&rettype=xml&retmode=xml"
        )
        resp = requests.get(api_url, timeout=20, headers={
            "User-Agent": _BROWSER_HEADERS["User-Agent"],
        })
        resp.raise_for_status()

        root = ET.fromstring(resp.content)

        # --- Extract article data from XML ---
        article = root.find(".//PubmedArticle/MedlineCitation/Article")
        if article is None:
            logger.debug("PubMed API: No Article element found for PMID %s", pmid)
            return None

        # Title
        title_el = article.find("ArticleTitle")
        title = "".join(title_el.itertext()).strip() if title_el is not None else f"PubMed Article {pmid}"

        # Abstract
        abstract_parts = []
        abstract_el = article.find("Abstract")
        if abstract_el is not None:
            for abs_text in abstract_el.findall("AbstractText"):
                label = abs_text.get("Label", "")
                text = "".join(abs_text.itertext()).strip()
                if label:
                    abstract_parts.append(f"{label}: {text}")
                else:
                    abstract_parts.append(text)
        abstract = "\n\n".join(abstract_parts) if abstract_parts else "(No abstract available)"

        # Authors
        authors = []
        author_list = article.find("AuthorList")
        if author_list is not None:
            for author in author_list.findall("Author"):
                last = author.findtext("LastName", "")
                fore = author.findtext("ForeName", "")
                initials = author.findtext("Initials", "")
                if last:
                    name = f"{last} {fore}" if fore else f"{last} {initials}"
                    authors.append(name.strip())
        authors_str = ", ".join(authors) if authors else "Unknown"

        # Journal
        journal_el = article.find("Journal")
        journal = ""
        if journal_el is not None:
            journal_title = journal_el.findtext("Title", "")
            journal_abbr = journal_el.findtext("ISOAbbreviation", "")
            journal = journal_title or journal_abbr

        # Year
        year = ""
        pub_date = article.find(".//Journal/JournalIssue/PubDate")
        if pub_date is not None:
            year = pub_date.findtext("Year", "")
            if not year:
                medline_date = pub_date.findtext("MedlineDate", "")
                if medline_date:
                    year_match = re.search(r'(\d{4})', medline_date)
                    year = year_match.group(1) if year_match else ""

        # DOI
        doi = ""
        medline_citation = root.find(".//PubmedArticle/MedlineCitation")
        if medline_citation is not None:
            for article_id in root.findall(".//PubmedArticle/PubmedData/ArticleIdList/ArticleId"):
                if article_id.get("IdType") == "doi":
                    doi = article_id.text or ""
                    break

        # Keywords
        keywords = []
        keyword_list = root.find(".//MedlineCitation/KeywordList")
        if keyword_list is not None:
            for kw in keyword_list.findall("Keyword"):
                kw_text = "".join(kw.itertext()).strip()
                if kw_text:
                    keywords.append(kw_text)

        # MeSH terms (additional keywords)
        mesh_list = root.find(".//MedlineCitation/MeshHeadingList")
        if mesh_list is not None:
            for mesh in mesh_list.findall("MeshHeading/DescriptorName"):
                mesh_text = mesh.text
                if mesh_text and mesh_text not in keywords:
                    keywords.append(mesh_text)

        keywords_str = ", ".join(keywords) if keywords else "N/A"

        # --- Format structured content ---
        content_parts = [
            f"Title: {title}",
            f"Authors: {authors_str}",
        ]
        if journal:
            content_parts.append(f"Journal: {journal}")
        if year:
            content_parts.append(f"Year: {year}")
        if doi:
            content_parts.append(f"DOI: {doi}")
        content_parts.append(f"PMID: {pmid}")
        content_parts.append(f"URL: {url}")
        content_parts.append(f"\nAbstract:\n{abstract}")
        if keywords_str != "N/A":
            content_parts.append(f"\nKeywords: {keywords_str}")

        content = "\n".join(content_parts)

        if len(content) >= _MIN_CONTENT_LENGTH:
            logger.info("PubMed API: Successfully fetched PMID %s (%d chars)", pmid, len(content))
            return (title, content)

        return None

    except ET.ParseError as e:
        logger.debug("PubMed API: XML parse error for PMID %s: %s", pmid, e)
        return None
    except Exception as e:
        logger.debug("PubMed API: Failed for PMID %s: %s", pmid, e)
        return None


# ---------------------------------------------------------------------------
# Strategy 1: Direct scrape with requests.Session (handles cookies)
# ---------------------------------------------------------------------------
def _scrape_direct(url: str) -> Optional[tuple[str, str]]:
    """
    Scrape URL using requests.Session which automatically handles:
    - Cookies (set-cookie headers, session cookies)
    - Redirects (301, 302, 303, 307, 308)
    - Compression (gzip, deflate, br)

    Returns (html, content) tuple or None.
    """
    try:
        session = requests.Session()
        session.headers.update(_BROWSER_HEADERS)

        resp = session.get(url, timeout=20, allow_redirects=True)
        resp.raise_for_status()

        # Use apparent_encoding first (chardet-detected), fallback to header
        resp.encoding = resp.apparent_encoding or resp.encoding or "utf-8"
        html = resp.text

        content = _best_content_from_html(html)

        # If content is too short, try a second request with session cookies
        if len(content) < _MIN_CONTENT_LENGTH:
            resp2 = session.get(url, timeout=20, allow_redirects=True)
            resp2.encoding = resp2.apparent_encoding or resp2.encoding or "utf-8"
            html = resp2.text
            content = _best_content_from_html(html)

        session.close()

        if len(content) >= _MIN_CONTENT_LENGTH:
            title = _extract_title(html, fallback=url)
            return (title, content)
        return None

    except Exception as e:
        logger.debug("Direct scrape failed for %s: %s", url, e)
        return None


# ---------------------------------------------------------------------------
# Strategy 2: Jina Reader API (renders JavaScript!)
# ---------------------------------------------------------------------------
def _scrape_jina_reader(url: str) -> Optional[tuple[str, str]]:
    """
    Use Jina Reader API (https://r.jina.ai/) to fetch and render the page.
    This is a FREE service that:
    - Renders JavaScript (handles SPA/React/Vue sites)
    - Handles cookies and redirects
    - Returns clean markdown text
    """
    try:
        jina_url = f"https://r.jina.ai/{url}"
        headers = {
            "Accept": "text/plain",
            "User-Agent": _BROWSER_HEADERS["User-Agent"],
        }
        resp = requests.get(jina_url, timeout=30, headers=headers)

        if resp.status_code != 200:
            return None

        resp.encoding = resp.apparent_encoding or resp.encoding or "utf-8"
        text = resp.text.strip()

        if len(text) < _MIN_CONTENT_LENGTH:
            return None

        # Jina returns markdown. Extract title from first line if it starts with #
        title = url
        lines = text.split("\n", 2)
        if lines and lines[0].startswith("#"):
            title = lines[0].lstrip("#").strip()

        return (title, text)

    except Exception as e:
        logger.debug("Jina Reader failed for %s: %s", url, e)
        return None


# ---------------------------------------------------------------------------
# Strategy 3: Google Webcache
# ---------------------------------------------------------------------------
def _scrape_google_cache(url: str) -> Optional[tuple[str, str]]:
    """Try to fetch content from Google's webcache."""
    try:
        cache_url = f"https://webcache.googleusercontent.com/search?q=cache:{urllib.parse.quote(url, safe='')}"
        session = requests.Session()
        session.headers.update(_BROWSER_HEADERS)
        resp = session.get(cache_url, timeout=15, allow_redirects=True)
        session.close()

        if resp.status_code == 200:
            content = _best_content_from_html(resp.text)
            if len(content) >= _MIN_CONTENT_LENGTH:
                title = _extract_title(resp.text, fallback=url)
                return (title, content)
        return None
    except Exception as e:
        logger.debug("Google cache failed for %s: %s", url, e)
        return None


# ---------------------------------------------------------------------------
# Strategy 4: Archive.org Wayback Machine
# ---------------------------------------------------------------------------
def _scrape_archive_org(url: str) -> Optional[tuple[str, str]]:
    """Try to fetch the latest cached version from Wayback Machine."""
    try:
        api_url = f"https://archive.org/wayback/available?url={urllib.parse.quote(url, safe='')}"
        resp = requests.get(api_url, timeout=10, headers={"User-Agent": _BROWSER_HEADERS["User-Agent"]})
        data = resp.json()

        snapshots = data.get("archived_snapshots", {})
        closest = snapshots.get("closest", {})
        if not closest.get("available"):
            return None

        archive_url = closest["url"]
        session = requests.Session()
        session.headers.update(_BROWSER_HEADERS)
        resp2 = session.get(archive_url, timeout=20, allow_redirects=True)
        session.close()

        if resp2.status_code == 200:
            content = _best_content_from_html(resp2.text)
            if len(content) >= _MIN_CONTENT_LENGTH:
                title = _extract_title(resp2.text, fallback=url)
                return (title, content)
        return None
    except Exception as e:
        logger.debug("Archive.org failed for %s: %s", url, e)
        return None


# ---------------------------------------------------------------------------
# Strategy 5: DuckDuckGo snippet (last resort — limited content)
# ---------------------------------------------------------------------------
def _get_ddg_snippet(url: str) -> Optional[tuple[str, str]]:
    """Search DuckDuckGo for the URL and return title + snippet."""
    try:
        from ddgs import DDGS
        with DDGS() as ddgs:
            results = list(ddgs.text(f"site:{url}", max_results=3))
        if results:
            best = results[0]
            content = best.get("body", "")
            title = best.get("title", url)
            if content:
                return (title, content)
        return None
    except Exception as e:
        logger.debug("DuckDuckGo snippet failed for %s: %s", url, e)
        return None


# ---------------------------------------------------------------------------
# Main entry point: scrape_url with multi-strategy fallback
# ---------------------------------------------------------------------------
def scrape_url(url: str, max_chars: int = 8000) -> dict:
    """
    Scrape text content from a URL with multiple fallback strategies.

    Tries in order:
      0. PubMed NCBI API (for pubmed.ncbi.nlm.nih.gov URLs)
      1. Direct scrape with cookie-aware session
      2. Jina Reader API (renders JavaScript)
      3. Google Webcache
      4. Archive.org Wayback Machine
      5. DuckDuckGo snippet (last resort)

    Returns dict with: url, title, content, char_count, source_method
    """
    # --- Priority: PubMed NCBI E-utilities API ---
    if _is_pubmed_url(url):
        result = _scrape_pubmed_api(url)
        if result:
            title, content = result
            logger.info("Scraped %s via pubmed_api (%d chars)", url, len(content))
            return {
                "url": url,
                "title": title[:200],
                "content": content[:max_chars],
                "char_count": len(content),
                "source_method": "pubmed_api",
            }
        logger.warning("PubMed API failed for %s, falling back to generic strategies", url)

    # --- Generic strategies ---
    strategies = [
        ("direct", _scrape_direct),
        ("jina_reader", _scrape_jina_reader),
        ("google_cache", _scrape_google_cache),
        ("archive_org", _scrape_archive_org),
        ("ddg_snippet", _get_ddg_snippet),
    ]

    for method_name, strategy_fn in strategies:
        result = strategy_fn(url)
        if result:
            title, content = result
            logger.info("Scraped %s via %s (%d chars)", url, method_name, len(content))
            return {
                "url": url,
                "title": title[:200],
                "content": content[:max_chars],
                "char_count": len(content),
                "source_method": method_name,
            }

    # All strategies failed
    raise RuntimeError(
        f"Unable to access URL content: {url}. "
        "All methods failed (direct, Jina Reader, Google Cache, Archive.org, DuckDuckGo). "
        "The site may require login or have strict anti-bot protection."
    )


# ---------------------------------------------------------------------------
# DuckDuckGo search (unchanged)
# ---------------------------------------------------------------------------
def duckduckgo_search(query: str, max_results: int = 5) -> list[dict]:
    """Search DuckDuckGo and return results with title, url, body."""
    try:
        from ddgs import DDGS
        with DDGS() as ddgs:
            results = list(ddgs.text(query, max_results=max_results, region="vn-vi"))
        return results  # Each item: {"title": ..., "href": ..., "body": ...}
    except ImportError:
        return _fallback_search(query, max_results)
    except Exception:
        return _fallback_search(query, max_results)


def _fallback_search(query: str, max_results: int) -> list[dict]:
    """Fallback when ddgs is unavailable — use DuckDuckGo HTML."""
    try:
        encoded = urllib.parse.quote_plus(query)
        search_url = f"https://html.duckduckgo.com/html/?q={encoded}"
        headers = {"User-Agent": _BROWSER_HEADERS["User-Agent"]}
        req = urllib.request.Request(search_url, headers=headers)
        with urllib.request.urlopen(req, timeout=10) as resp:
            html = resp.read().decode("utf-8", errors="replace")
        results = []
        title_matches = re.findall(r'class="result__title"[^>]*>(.*?)</a>', html, re.DOTALL)
        snippet_matches = re.findall(r'class="result__snippet"[^>]*>(.*?)</span>', html, re.DOTALL)
        url_matches = re.findall(r'class="result__url"[^>]*>(.*?)</span>', html, re.DOTALL)
        for i in range(min(max_results, len(title_matches))):
            title = re.sub(r'<[^>]+>', '', title_matches[i]).strip()
            body = re.sub(r'<[^>]+>', '', snippet_matches[i]).strip() if i < len(snippet_matches) else ""
            href = url_matches[i].strip() if i < len(url_matches) else ""
            if title:
                results.append({"title": title, "href": href, "body": body})
        return results
    except Exception:
        return []

