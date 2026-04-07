import os
import json
import hashlib
from google import genai

# Initialize client once
client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

SYSTEM_PROMPT = """You are an expert, unbiased technical recruiter AI. Analyze resumes objectively.
Return structured JSON only. Never include markdown, code fences, or explanations — just raw JSON."""


def score_to_recommendation(score: int) -> str:
    if score >= 85:
        return "Strong Yes"
    elif score >= 65:
        return "Yes"
    elif score >= 45:
        return "Maybe"
    else:
        return "No"


def content_hash(text: str) -> str:
    return hashlib.sha256(text.encode()).hexdigest()


def clean_json(text: str) -> str:
    """Removes markdown/code fences safely"""
    text = text.strip()

    if text.startswith("```"):
        text = text.split("```")[1]
        if text.startswith("json"):
            text = text[4:]

    return text.strip()


def screen_resume(resume_text: str, job_description: str) -> dict:
    prompt = f"""{SYSTEM_PROMPT}

Job Description:
{job_description}

Resume:
{resume_text[:8000]}

Analyze this resume against the job description. Return ONLY this JSON:
{{
  "name": "Full name or 'Unknown Candidate'",
  "email": "Email address or empty string",
  "phone": "Phone number or empty string",
  "location": "City/country or empty string",
  "score": <integer 0-100>,
  "experience": "e.g. '5 years' or 'Entry-level'",
  "experience_years": <float>,
  "education": "Highest degree and field",
  "current_role": "Most recent job title and company",
  "skills": ["up to 12 skills"],
  "matched_skills": [],
  "missing_skills": [],
  "strengths": [],
  "red_flags": [],
  "summary": "",
  "blind_summary": ""
}}"""

    # ✅ Correct API call
    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=prompt
    )

    text = clean_json(response.text)

    try:
        data = json.loads(text)
    except json.JSONDecodeError:
        # fallback safety
        return {
            "error": "Invalid JSON from model",
            "raw_output": text
        }

    # Post-processing
    score = int(data.get("score", 0))
    data["recommendation"] = score_to_recommendation(score)
    data["content_hash"] = content_hash(resume_text)

    return data