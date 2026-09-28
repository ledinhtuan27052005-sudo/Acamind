import json
from app.services.llm_client import get_default_client

llm_client = get_default_client()

def _build_citation(chunk):
    "[filename - Page X]"
    f = chunk.get("doc_filename","") or chunk.get("doc_title","") or "document"
    p = chunk.get("page_number","?")
    return f"[{f} - Page {p}]"

def _build_source_label(chunk):
    "Label context: File name: X | Page Y"
    f = chunk.get("doc_filename","") or chunk.get("doc_title","") or "document"
    p = chunk.get("page_number","?")
    return f"File name: {f} | Page {p}"


PSYCHOLOGY_SYSTEM_PROMPT = '''You are a leading clinical psychologist and psychology researcher.
You are equipped with a specialized scientific database of psychology literature (DSM, ICD, clinical studies, textbooks).

MANDATORY RULES:
1. ONLY answer based on the provided document CONTEXT. DO NOT use external knowledge.
2. DO NOT speculate. DO NOT add information not present in the documents.
3. If the CONTEXT does not contain information to answer the question (even if chunks exist but content is irrelevant), reply with exactly one first line: __NO_CONTEXT__ followed by a brief explanation.
4. MANDATORY CITATION: place [filename.pdf - Page X] immediately after EVERY claim, fact, or definition.
   DO NOT include author names in the citation. Example: [ClinicalPsychology.pdf - Page 7]
   DO NOT combine citations at the end of a paragraph. DO NOT infer page numbers outside the CONTEXT.
5. When there are multiple sources, cite all: [file_a.pdf - Page X; file_b.pdf - Page Y].
6. Always respond in English. Use precise psychological terminology with explanations.
7. For clinical issues, always add a disclaimer: "This is academic information, not a substitute for professional advice."
8. Multidimensional analysis: present perspectives from multiple psychological schools if present in the documents.
9. When synthesizing from multiple pages, clearly state the sources.
10. If there are conflicting statements in the context, highlight the difference and cite both.

PRESENTATION (MANDATORY):
- Use **markdown** to format the answer - this is a mandatory requirement.
- Every answer must have clear main sections separated by `## Heading`.
- Every main section must contain cohesive bullet points starting with `-` on separate lines.
- Comparison tables: use markdown tables `| Column 1 | Column 2 |` when comparing.
- Bold terms: use `**term**` for important concepts.
- DO NOT write long continuous paragraphs - every point must be a separate bullet point starting with `-`.
- Add line breaks between main sections for readability.'''


GENERAL_SYSTEM_PROMPT = '''You are a versatile AI assistant, answering based on information retrieved from web searches.

RULES:
1. Answer based on the web sources provided in the CONTEXT.
2. Always cite sources: [Source: {website name / URL}] after each piece of information.
3. If information from multiple sources conflicts, clearly state the differences.
4. Always respond in English.

PRESENTATION (MANDATORY):
- Use **markdown** to format the answer - this is a mandatory requirement.
- Every answer must have clear main sections separated by `## Heading`.
- Every main section must contain cohesive bullet points starting with `-` on separate lines.
- Example:
  ## Overview
  - Definition: basic concept
  - History: origins and development
  ## Advantages
  - Strengths: ...
  - Weaknesses: ...
- Comparison tables: use markdown tables `| Column 1 | Column 2 |` when comparing multiple items.
- DO NOT write long continuous paragraphs - every point must be a separate bullet point starting with `-`.
- Add line breaks between main sections for readability.
'''


PSYCHOLOGY_SYSTEM_PROMPT_EN = '''You are a leading clinical psychologist and psychology researcher.
You are equipped with a specialized scientific database of psychology literature (DSM, ICD, clinical studies, textbooks).

MANDATORY RULES:
1. ONLY answer based on the provided document CONTEXT. DO NOT use external knowledge.
2. DO NOT speculate. DO NOT add information not present in the documents.
3. If the CONTEXT does not contain information to answer the question, reply with exactly one first line: __NO_CONTEXT__ followed by a short explanation: "No information found in the related documents."
4. MANDATORY CITATION: place [filename.pdf - Page X] immediately after EVERY claim, fact, or definition.
   DO NOT include author names in the citation. Example: [ClinicalPsychology.pdf - Page 7]
   DO NOT combine citations at the end of a paragraph. DO NOT infer page numbers outside the CONTEXT.
5. When there are multiple sources, cite all: [file_a.pdf - Page X; file_b.pdf - Page Y].
6. Respond in English, using precise psychological terms with explanations.
7. For clinical issues, always add a disclaimer: "This is academic information, not a substitute for professional advice."
8. Multidimensional analysis: present perspectives from multiple psychological schools if present in the documents.
9. When synthesizing from multiple pages, clearly state the sources.
10. If there are conflicting statements in the context, highlight the difference and cite both.

PRESENTATION (MANDATORY):
- Use **markdown** to format the answer - this is a mandatory requirement.
- Every answer must have clear main sections separated by `## Heading`.
- Every main section must contain cohesive bullet points starting with `-` on separate lines.
- Comparison tables: use markdown tables `| Column 1 | Column 2 |` when comparing symptoms, therapy methods, etc.
- Bold terms: use `**term**` for important concepts.
- DO NOT write long continuous paragraphs - every point must be a separate bullet point starting with `-`.'''


# --- Domain classification -------------------------------------------------

PSYCHOLOGY_KEYWORDS = {
    "tam ly", "psychology", "psychiatric", "tam than", "therapist", "therapy",
    "cognitive", "nhan thuc", "hanh vi", "behavioral", "emotion", "cam xuc",
    "stress", "lo au", "anxiety", "depression", "tram cam", "trauma",
    "phan tam", "psychoanalysis", "freud", "jung", "attachment", "gan ket",
    "dsm", "icd", "diagnosis", "chan doan", "treatment", "dieu tri",
    "mental health", "suc khoe tam than", "counseling", "tu van",
    "cbt", "dbt", "act", "lieu phap", "psychotherapy", "tri lieu",
    "personality", "nhan cach", "perception", "nhan thuc", "memory", "ky uc",
    "neuroscience", "than kinh", "brain", "nao bo", "mood", "tam trang",
    "schizophrenia", "bipolar", "ocd", "ptsd", "adhd", "autism",
    "self-esteem", "tu tro", "motivation", "dong luc", "behavior", "hanh vi",
    "social psychology", "tam ly xa hoi", "developmental", "phat trien",
}

def classify_query_domain(query: str) -> str:
    query_lower = query.lower()
    if any(kw in query_lower for kw in PSYCHOLOGY_KEYWORDS):
        return "psychology"
    response = llm_client.complete(
        messages=[{"role": "user", "content": query}],
        system=(
            "Classify the following question into a domain. "
            "Return ONLY one word: 'psychology' if related to psychology. "
            "Return 'general' for all other topics."
        ),
        max_tokens=10, temperature=0.0,
    )
    result = response.strip().lower()
    return "psychology" if "psychology" in result else "general"


# --- Context builder --------------------------------------------------------

def build_psychology_prompt(query: str, context_chunks: list[dict], lang: str = "en") -> list[dict]:
    context_text = ""
    for i, chunk in enumerate(context_chunks, 1):
        filename = chunk.get("doc_filename") or chunk.get("doc_title") or "document"
        page = chunk.get("page_number", "?")
        source_label = f"File name: {filename} | Page {page}"
        context_text += f"\n[Source {i}] {source_label}:\n"
        context_text += f"{chunk['content']}\n"

    system_prompt = PSYCHOLOGY_SYSTEM_PROMPT_EN if lang == "en" else PSYCHOLOGY_SYSTEM_PROMPT
    user_header = f"DOCUMENT CONTEXT:\n{context_text}\n\n---\nQUESTION: {query}"

    return [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_header},
    ]


def build_general_prompt(query: str, web_results: list[dict]) -> list[dict]:
    context_text = ""
    for i, result in enumerate(web_results, 1):
        context_text += (
            f"\n[Source {i}] {result.get('title', '')} ({result.get('url', '')}):\n"
            f"{result.get('body', result.get('content', ''))[:800]}\n"
        )
    return [
        {"role": "system", "content": GENERAL_SYSTEM_PROMPT},
        {"role": "user", "content": f"WEB SEARCH RESULTS:\n{context_text}\n\n---\nQUESTION: {query}"},
    ]


def _split_messages(messages: list[dict]) -> tuple[list[dict], str | None]:
    system_content = None
    user_messages = []
    for m in messages:
        if m.get("role") == "system":
            system_content = m.get("content", "")
        else:
            user_messages.append(m)
    return user_messages, system_content


# --- Streaming generators -----------------------------------------------------

def generate_stream(query: str, context_chunks: list[dict], lang: str = "en"):
    messages, system = _split_messages(messages=build_psychology_prompt(query, context_chunks, lang))
    yield from llm_client.stream(
        messages=messages, system=system,
        max_tokens=6000, temperature=0.1,
    )


def generate_answer(query: str, context_chunks: list[dict], lang: str = "en") -> str:
    messages, system = _split_messages(messages=build_psychology_prompt(query, context_chunks, lang))
    return llm_client.complete(
        messages=messages, system=system,
        max_tokens=4096, temperature=0.1,
    )


def generate_stream_web_search(query: str, web_results: list[dict]):
    messages, system = _split_messages(messages=build_general_prompt(query, web_results))
    yield from llm_client.stream(
        messages=messages, system=system,
        max_tokens=4096, temperature=0.3,
    )


def generate_stream_direct(query: str):
    """Direct chat with the LLM without internet search."""
    yield from llm_client.stream(
        messages=[{"role": "user", "content": query}],
        system="You are a friendly, versatile AI assistant. Respond concisely, directly, and without rambling. Always respond in English.",
        max_tokens=4096, temperature=0.3,
    )


# --- Psychology analysis functions ----------------------------------------------

def analyze_symptoms_dsm(symptom_description: str, context_chunks: list[dict]) -> str:
    context_text = ""
    for i, chunk in enumerate(context_chunks, 1):
        context_text += f"\n[Source {i}] {_build_source_label(chunk)}:\n{chunk['content']}\n"
    messages = [
        {"role": "system", "content":
            "You are a clinical psychology expert. Based on DSM/ICD documents and the provided scientific literature, analyze the described symptoms and: "
            "1. List potentially matching psychological disorders (with diagnostic criteria from the documents). "
            "2. Cross-reference symptoms with DSM/ICD criteria in the documents. "
            "3. Identify missing information needed for an accurate diagnosis. "
            "4. Cite specific sources [filename.pdf - Page X]. "
            "5. Always conclude with: 'This information is for academic purposes only. Please consult a licensed clinical psychologist for an accurate diagnosis.' "
            "IMPORTANT: Respond in plain text ONLY. Do NOT use any markdown formatting (no ##, **, -, ```, tables, or any other markdown syntax). "
            "Use line breaks, numbering, and indentation for structure instead."},
        {"role": "user", "content": f"DOCUMENT CONTEXT:\n{context_text}\n\n---\nSYMPTOM DESCRIPTION:\n{symptom_description}"},
    ]
    user_messages, system = _split_messages(messages)
    return llm_client.complete(messages=user_messages, system=system, max_tokens=4096, temperature=0.1)


def analyze_symptoms_with_fallback(
    symptom_description: str,
    context_chunks: list[dict],
    web_results: list[dict],
) -> str:
    """Analyze symptoms using document context + web search results as supplementary sources."""
    # Build document context
    doc_context = ""
    for i, chunk in enumerate(context_chunks, 1):
        doc_context += f"\n[Document Source {i}] {_build_source_label(chunk)}:\n{chunk['content']}\n"

    # Build web context
    web_context = ""
    for i, result in enumerate(web_results, 1):
        title = result.get("title", "")
        url = result.get("href", result.get("url", ""))
        body = result.get("body", result.get("content", ""))[:600]
        web_context += f"\n[Web Source {i}] {title} ({url}):\n{body}\n"

    # Determine source description for the system prompt
    has_docs = len(context_chunks) > 0
    has_web = len(web_results) > 0

    if has_docs and has_web:
        source_instruction = (
            "You have TWO types of sources: uploaded psychology documents (PDF) and internet search results. "
            "Prioritize document sources for clinical/diagnostic information. "
            "Use web sources to supplement with additional context, latest research, or practical recommendations. "
            "For document sources, cite as [filename.pdf - Page X]. For web sources, cite as [Web: title - URL]."
        )
    elif has_web:
        source_instruction = (
            "No uploaded documents are available. You have internet search results as your source. "
            "Use these web sources to provide the best possible analysis. "
            "Cite web sources as [Web: title - URL]."
        )
    else:
        source_instruction = (
            "You have uploaded psychology documents as your source. "
            "Cite document sources as [filename.pdf - Page X]."
        )

    combined_context = ""
    if doc_context:
        combined_context += f"=== UPLOADED DOCUMENT SOURCES ===\n{doc_context}\n"
    if web_context:
        combined_context += f"\n=== INTERNET SEARCH SOURCES ===\n{web_context}\n"

    messages = [
        {"role": "system", "content":
            "You are a clinical psychology expert with access to both scientific literature and internet resources. "
            f"{source_instruction} "
            "Analyze the described symptoms and: "
            "1. List potentially matching psychological disorders (with severity assessment). "
            "2. Cross-reference symptoms with known DSM/ICD criteria. "
            "3. Identify missing information needed for an accurate diagnosis. "
            "4. Provide practical recommendations. "
            "5. Always conclude with: 'This information is for academic purposes only. Please consult a licensed clinical psychologist for an accurate diagnosis.' "
            "IMPORTANT: Respond in plain text ONLY. Do NOT use any markdown formatting (no ##, **, -, ```, tables, or any other markdown syntax). "
            "Use line breaks, numbering, and indentation for structure instead."},
        {"role": "user", "content": f"{combined_context}\n---\nSYMPTOM DESCRIPTION:\n{symptom_description}"},
    ]
    user_messages, system = _split_messages(messages)
    return llm_client.complete(messages=user_messages, system=system, max_tokens=4096, temperature=0.1)


def synthesize_treatment_protocol(condition: str, context_chunks: list[dict]) -> str:
    context_text = ""
    for i, chunk in enumerate(context_chunks, 1):
        context_text += f"\n[Source {i}] {_build_source_label(chunk)}:\n{chunk['content']}\n"
    messages = [
        {"role": "system", "content":
            "You are a psychotherapy expert. Synthesize treatment protocols from scientific literature: "
            "1. Primary treatment methods (CBT, DBT, ACT, psychoanalysis, etc.) from the documents. "
            "2. Specific therapeutic techniques mentioned. "
            "3. Effectiveness & evidence from research in the documents. "
            "4. Typical treatment duration according to the documents. "
            "5. Compare methods if multiple approaches exist. "
            "6. Full citations: [filename.pdf - Page X]. "
            "IMPORTANT: Only use information from the CONTEXT. If insufficient, state clearly."},
        {"role": "user", "content": f"DOCUMENT CONTEXT:\n{context_text}\n\n---\nCONDITION TO TREAT: {condition}"},
    ]
    user_messages, system = _split_messages(messages)
    return llm_client.complete(messages=user_messages, system=system, max_tokens=4096, temperature=0.1)


def compare_psychology_schools(topic: str, context_chunks: list[dict]) -> str:
    context_text = ""
    for i, chunk in enumerate(context_chunks, 1):
        context_text += f"\n[Source {i}] {_build_source_label(chunk)}:\n{chunk['content']}\n"
    messages = [
        {"role": "system", "content":
            "You are a psychology scholar. Compare perspectives of different psychological schools on the topic from the documents: "
            "1. Summarize each school's perspective (Psychoanalysis, Behavioral, Cognitive, Humanistic, etc.). "
            "2. Similarities between the schools. "
            "3. Differences and debates. "
            "4. Modern trends (Integration/Eclecticism). "
            "5. Citations: [filename.pdf - Page X] for each perspective. "
            "IMPORTANT: Only use information from the CONTEXT. Do not speculate."},
        {"role": "user", "content": f"DOCUMENT CONTEXT:\n{context_text}\n\n---\nCOMPARISON TOPIC: {topic}"},
    ]
    user_messages, system = _split_messages(messages)
    return llm_client.complete(messages=user_messages, system=system, max_tokens=4096, temperature=0.1)


def summarize_topic_research(topic: str, context_chunks: list[dict]) -> str:
    context_text = ""
    for i, chunk in enumerate(context_chunks, 1):
        context_text += f"\n[Source {i}] {_build_source_label(chunk)}:\n{chunk['content']}\n"
    messages = [
        {"role": "system", "content":
            "You are a psychology researcher. Synthesize all research on the topic from the document repository: "
            "OVERVIEW: Definition and importance of the topic. "
            "HISTORICAL DEVELOPMENT: Key milestones from the documents. "
            "KEY STUDIES: Summarize each study with its main findings. "
            "SCIENTIFIC CONSENSUS: What researchers agree on. "
            "DEBATES & CONTRADICTIONS: Points of disagreement. "
            "RESEARCH GAPS: What has not yet been studied. "
            "REFERENCES: Complete list [filename.pdf - Page X]. "
            "IMPORTANT: Provide specific citations for every claim."},
        {"role": "user", "content": f"DOCUMENT CONTEXT:\n{context_text}\n\n---\nRESEARCH TOPIC: {topic}"},
    ]
    user_messages, system = _split_messages(messages)
    return llm_client.complete(messages=user_messages, system=system, max_tokens=8192, temperature=0.1)


# --- Quiz & Evaluation --------------------------------------------------------

def generate_quiz(context: str, num_questions: int = 5) -> list[dict]:
    raw = llm_client.complete(
        messages=[{"role": "user", "content": f"Content:\n{context[:6000]}"}],
        system=(
            f"Create {num_questions} multiple-choice questions from the psychology content. "
            "Return a JSON array: "
            '[{"question":"...","options":["A. ...","B. ...","C. ...","D. ..."],"answer":"A","explanation":"..."}] '
            "ONLY return the JSON array, no additional text or markdown."
        ),
        max_tokens=4096, temperature=0.4,
    )
    start, end = raw.find("["), raw.rfind("]") + 1
    if start >= 0 and end > start:
        try:
            return json.loads(raw[start:end])
        except json.JSONDecodeError:
            pass
    return []


def evaluate_rag(question: str, answer: str, contexts: list[str]) -> dict:
    ctx_text = "\n---\n".join(contexts[:5])
    raw = llm_client.complete(
        messages=[{"role": "user", "content": f"Question: {question}\n\nContext:\n{ctx_text}\n\nAnswer: {answer}"}],
        system=(
            "You are a RAG system evaluation expert. Evaluate 3 criteria (scale 0.0-1.0) and return JSON: "
            '{"faithfulness":0.0,"answer_relevancy":0.0,"context_quality":0.0,"feedback":"..."} '
            "faithfulness: is the answer supported by the context? "
            "answer_relevancy: does the answer address the core of the question? "
            "context_quality: does the context contain enough information to answer? "
            "ONLY return JSON."
        ),
        max_tokens=1024, temperature=0.1,
    )
    start, end = raw.find("{"), raw.rfind("}") + 1
    if start >= 0 and end > start:
        try:
            return json.loads(raw[start:end])
        except json.JSONDecodeError:
            pass
    return {"faithfulness": 0, "answer_relevancy": 0, "context_quality": 0, "feedback": "Unable to evaluate"}


def summarize_document(full_text: str) -> str:
    return llm_client.complete(
        messages=[{"role": "user", "content": f"Summarize:\n\n{full_text[:8000]}"}],
        system=(
            "Summarize the psychology document in 5 sections: "
            "Objective: ... Methods: ... "
            "Research Sample: ... Key Findings: ... Limitations: ..."
        ),
        max_tokens=2048, temperature=0.2,
    )
