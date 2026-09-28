from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from app.services.web_scraper import scrape_url
from app.services.llm_client import get_default_client
import logging

logger = logging.getLogger(__name__)

router = APIRouter()
llm_client = get_default_client()


class ScrapeRequest(BaseModel):
    url: str


class DebateRequest(BaseModel):
    url1: str
    url2: str
    topic: str = ""


@router.post("/scrape")
def scrape(req: ScrapeRequest):
    try:
        result = scrape_url(req.url)
        return result
    except RuntimeError as e:
        raise HTTPException(400, str(e))


@router.post("/analyze")
def analyze_debate(req: DebateRequest):
    # Scrape each URL separately to identify exactly which one fails.
    scrape_errors: list[str] = []
    try:
        data1 = scrape_url(req.url1, max_chars=4000)
    except RuntimeError as e:
        scrape_errors.append(f"URL 1 ({req.url1}): {e}")
        data1 = None
    try:
        data2 = scrape_url(req.url2, max_chars=4000)
    except RuntimeError as e:
        scrape_errors.append(f"URL 2 ({req.url2}): {e}")
        data2 = None

    if data1 is None and data2 is None:
        # Both URLs failed — cannot analyze anything.
        raise HTTPException(400, "Failed to scrape both URLs. " + " | ".join(scrape_errors))
    if data1 is None or data2 is None:
        # One URL failed — continue with placeholder for the missing one.
        missing_idx = 1 if data1 is None else 2
        missing_url = req.url1 if data1 is None else req.url2
        missing_err = next((e for e in scrape_errors if f"URL {missing_idx}" in e), "unknown error")
        placeholder = {
            "title": f"(Could not scrape URL {missing_idx})",
            "content": f"[Content unavailable: {missing_err}. AI will analyze the available source only.]",
        }
        if data1 is None:
            data1 = placeholder
        else:
            data2 = placeholder

    topic_line = f"Debate topic: {req.topic}\n\n" if req.topic else ""

    prompt = f"""{topic_line}Analyze and compare the content of the two web articles below.

MANDATORY RULES:
- The analysis must be based on the ACTUAL CONTENT scraped from the URLs below. DO NOT speculate beyond the article scope.
- Each analysis point must reference the corresponding URL (ARTICLE 1 = {req.url1}, ARTICLE 2 = {req.url2}).
- If a title is missing or vague, infer the SPECIFIC TOPIC from the extracted content, then provide an in-depth analysis.
- If one URL failed to scrape, clearly state "This URL could not be accessed" and only analyze the available source.
- IMPORTANT: Respond in plain text ONLY. Do NOT use any markdown formatting (no ##, **, -, ```, tables, or any other markdown syntax). Use line breaks, numbering, and indentation for structure instead.

=== ARTICLE 1 ===
Scraped title: {data1['title']}
URL: {req.url1}
Content:
\"\"\"
{data1['content'][:4000]}
\"\"\"

=== ARTICLE 2 ===
Scraped title: {data2['title']}
URL: {req.url2}
Content:
\"\"\"
{data2['content'][:4000]}
\"\"\"

Analyze according to this structure (EVERY section must be grounded in specific content from the scraped articles, not generic statements):

1. Summary of ARTICLE 1 ({data1['title']}):
   - Main topic: ...
   - 3 core arguments: ...
   - Key evidence/citations: ...

2. Summary of ARTICLE 2 ({data2['title']}):
   - Main topic: ...
   - 3 core arguments: ...
   - Key evidence/citations: ...

3. Points of agreement between the two articles:
   (arguments both articles support, with specific evidence)

4. Points of contradiction / differences:
   (where the two articles disagree, and analysis of why)

5. Objective evaluation:
   (which article has stronger evidence, which source is more credible, which argument has gaps)

6. Conclusion:
   (a 2-3 sentence synthesis, with a personal assessment if sufficient evidence from both articles supports it)"""

    def stream_debate():
        try:
            yield from llm_client.stream(
                messages=[{"role": "user", "content": prompt}],
                system=(
                    "You are an expert in information analysis and academic critique. "
                    "Analyze objectively, based on evidence from the article content. "
                    "Always respond in English. Do NOT use any markdown formatting."
                ),
                max_tokens=4096,
                temperature=0.2,
            )
        except Exception as e:
            # If LLM fails mid-stream, send an error line so the frontend knows.
            logger.exception("Debate LLM stream failed")
            yield f"\n\nWarning: AI error encountered: {e}"

    return StreamingResponse(
        stream_debate(),
        media_type="text/plain; charset=utf-8",
    )


@router.post("/scrape-multi")
def scrape_multi(req: DebateRequest):
    """Scrape both URLs and return metadata (used for preview before debate)."""
    results = []
    for url in [req.url1, req.url2]:
        try:
            results.append(scrape_url(url, max_chars=500))
        except RuntimeError as e:
            results.append({"url": url, "title": "Error", "content": str(e), "char_count": 0})
    return {"sources": results}
