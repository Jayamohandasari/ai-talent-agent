import json
import os
import re

try:
    from openai import OpenAI
except ImportError:
    OpenAI = None


def _make_client():
    if OpenAI is None:
        return None
    if not os.getenv("OPENAI_API_KEY"):
        return None
    try:
        return OpenAI(max_retries=0, timeout=5.0)
    except Exception:
        return None


client = _make_client()

KNOWN_SKILLS = {
    "python", "flask", "django", "fastapi", "postgresql", "mysql", "sql",
    "docker", "kubernetes", "aws", "azure", "gcp", "react", "next.js",
    "typescript", "javascript", "redis", "nlp", "tensorflow", "pytorch",
    "machine learning", "mlops", "terraform", "ci/cd", "linux", "rest api",
    "tableau", "a/b testing", "boolean search", "crm",
}

ROLE_PATTERNS = [
    "backend engineer", "python developer", "software engineer",
    "full stack engineer", "frontend engineer", "data scientist",
    "ml engineer", "devops engineer", "product analyst",
    "talent intelligence specialist",
]


def _fallback_parse_jd(jd_text):
    text = jd_text or ""
    text_lower = text.lower()

    skills = []
    for skill in KNOWN_SKILLS:
        # Use word boundaries to avoid "sql" matching inside "mysql"
        pattern = r"\b" + re.escape(skill) + r"\b"
        if re.search(pattern, text_lower):
            skills.append(skill.title())

    exp_match = re.search(r"(\d+)\+?\s+years?", text, flags=re.IGNORECASE)
    role = next((p.title() for p in ROLE_PATTERNS if p in text_lower), "")
    if not role:
        role_match = re.search(
            r"\b(engineer|developer|analyst|manager|designer|architect)\b",
            text, flags=re.IGNORECASE,
        )
        role = role_match.group(1).title() if role_match else ""

    location_match = re.search(
        r"\b(remote|hyderabad|bengaluru|bangalore|pune|chennai|delhi|gurugram|noida|mumbai)\b",
        text, flags=re.IGNORECASE,
    )

    return {
        "skills": skills[:15],
        "experience": int(exp_match.group(1)) if exp_match else 0,
        "role": role,
        "location": location_match.group(1).title() if location_match else "",
        "summary": text[:240],
    }


def parse_jd(jd_text):
    global client

    if not jd_text or not jd_text.strip():
        return {"skills": [], "experience": 0, "role": "", "location": "", "summary": ""}

    if not client:
        return _fallback_parse_jd(jd_text)

    prompt = f"""Extract structured info from this job description.

Return ONLY JSON with no extra text or markdown:
{{
  "skills": [],
  "experience": number,
  "role": "",
  "location": "",
  "summary": ""
}}

JD: {jd_text}"""

    try:
        res = client.chat.completions.create(
            model="gpt-4.1-mini",
            messages=[{"role": "user", "content": prompt}],
        )
        # Guard against empty choices before indexing
        if not res.choices:
            return _fallback_parse_jd(jd_text)

        content = res.choices[0].message.content or "{}"
        content = content.strip().lstrip("```json").lstrip("```").rstrip("```").strip()
        parsed = json.loads(content)

    except (json.JSONDecodeError, ValueError, KeyError, TypeError, IndexError):
        client = None
        return _fallback_parse_jd(jd_text)
    except Exception:
        client = None
        return _fallback_parse_jd(jd_text)

    return {
        "skills": parsed.get("skills") or [],
        "experience": parsed.get("experience") or 0,
        "role": parsed.get("role") or "",
        "location": parsed.get("location") or "",
        "summary": parsed.get("summary") or jd_text[:240],
    }
