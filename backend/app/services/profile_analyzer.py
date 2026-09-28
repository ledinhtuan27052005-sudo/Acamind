import json
from app.services.llm_client import get_default_client

llm_client = get_default_client()


def analyze_symptoms(symptoms: list[dict]) -> str:
    """Generate AI health insight from a list of symptom records."""
    if not symptoms:
        return "No symptoms have been recorded yet."

    symptom_text = ""
    for i, s in enumerate(symptoms, 1):
        symptom_text += (
            f"{i}. Region: {s.get('region_name', '?')} | "
            f"Description: {s.get('description', '?')} | "
            f"Pain Level: {s.get('pain_level', '?')}/10 | "
            f"Duration: {s.get('duration', 'unknown')} | "
            f"Date: {str(s.get('reported_at', '?'))[:10]}\n"
        )

    prompt = f"""Based on the following patient symptom history, provide an overall assessment of the health condition:

{symptom_text}

Requirements:
1. Summarize the most affected body regions
2. Comment on pain trends (increasing/decreasing/stable)
3. Suggest 2-3 recommended actions (health checkups, lifestyle changes, etc.)
4. IMPORTANT note: This is only a preliminary assessment, not a substitute for professional medical advice

Respond concisely in 200-300 words.
IMPORTANT: Use plain text only. Do NOT use any markdown formatting (no ##, **, -, or any other markdown syntax). Use line breaks and numbering for structure."""

    return llm_client.complete(
        messages=[{"role": "user", "content": prompt}],
        system=(
            "You are an AI health assistant. Analyze symptoms professionally, "
            "honestly, and always remind users to consult a doctor. "
            "Respond in plain text only, do not use any markdown formatting."
        ),
        max_tokens=1024,
        temperature=0.3,
    )


def analyze_chat_patterns(chat_records: list[dict]) -> str:
    """Analyze user's learning patterns from chat history."""
    if not chat_records:
        return "No chat history available yet."

    topics = [r.get("query", "")[:80] for r in chat_records[-10:]]
    topics_text = "\n".join(f"- {t}" for t in topics)

    prompt = f"""The user has asked about the following topics:
{topics_text}

Provide a brief analysis (100 words):
1. Main topics of interest
2. Medical/health fields of focus
3. Suggested documents or topics for further learning"""

    return llm_client.complete(
        messages=[{"role": "user", "content": prompt}],
        system="You are an AI academic assistant. Analyze learning trends. Respond in plain text only, do not use any markdown formatting.",
        max_tokens=512,
        temperature=0.3,
    )
