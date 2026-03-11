"""
AI Service
Integrates with Groq API (Llama 3) to generate professional
narrative summaries from parsed sales data.
"""

import os
import httpx
from fastapi import HTTPException

SYSTEM_PROMPT = """You are a senior business analyst at a top consulting firm. 
Your job is to analyze raw sales data and produce a polished, executive-ready brief.

Guidelines:
- Write in a professional, confident tone suitable for C-suite executives.
- Structure the summary with clear sections: Executive Summary, Key Metrics, 
  Notable Trends, and Actionable Recommendations.
- Use specific numbers and percentages from the data.
- Highlight both positive performance and areas of concern.
- Keep the brief concise but comprehensive (300-500 words).
- Format using clean paragraphs, not excessive bullet points.
- End with 2-3 forward-looking strategic recommendations.

Do NOT include any caveats about data quality or mention that you are an AI.
Write as if you are the analyst who has studied this data in depth."""

GROQ_API_URL = "https://api.groq.com/openai/v1/chat/completions"


async def generate_summary(data_text: str) -> str:
    """Generate an AI-powered narrative summary from parsed data."""
    api_key = os.getenv("GROQ_API_KEY", "")
    if not api_key:
        raise HTTPException(
            status_code=503,
            detail="AI service is not configured. Please set the GROQ_API_KEY.",
        )

    try:
        prompt = f"""Analyze the following sales dataset and generate a professional 
executive brief summarizing the key insights:

{data_text}

Generate the executive brief now:"""

        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        }

        payload = {
            "model": os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile"),
            "messages": [
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": prompt},
            ],
            "temperature": 0.7,
            "max_tokens": 2048,
        }

        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(GROQ_API_URL, headers=headers, json=payload)

        if response.status_code != 200:
            error_detail = response.json().get("error", {}).get("message", response.text)
            raise HTTPException(
                status_code=502,
                detail=f"AI service error: {error_detail}",
            )

        data = response.json()
        content = data.get("choices", [{}])[0].get("message", {}).get("content", "")

        if not content:
            raise HTTPException(
                status_code=502,
                detail="AI service returned an empty response. Please try again.",
            )

        return content

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=502,
            detail=f"AI service error: {str(e)}",
        )
