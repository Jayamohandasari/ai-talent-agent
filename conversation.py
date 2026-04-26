import logging
import os
import re

logger = logging.getLogger(__name__)

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
    except Exception as exc:
        logger.warning("OpenAI client init failed, will use fallback: %s", exc)
        return None


client = _make_client()


def _fallback_conversation(candidate, jd_text):
    skills = ", ".join(candidate.get("skills", [])) or "relevant skills"
    preferences = candidate.get("preferences", {})
    motivation = preferences.get("motivation", "Interested in roles that align with my background.")

    response = (
        f"I'm interested in this opportunity because it aligns with my experience in {skills}. "
        f"{motivation} I'd like to learn more about the role and team."
    )

    # Start from a neutral baseline; only add for genuine positive signals.
    interest_score = 55
    summary = (candidate.get("summary") or "").lower()
    if any(w in summary for w in ["lead", "senior", "expert"]):
        interest_score += 10
    if jd_text and any(skill.lower() in jd_text.lower() for skill in candidate.get("skills", [])):
        interest_score += 8
    if preferences.get("locations") and "remote" in [loc.lower() for loc in preferences["locations"]]:
        interest_score += 5

    return {
        "response": response,
        "interest_score": min(100, interest_score),
        "signal": "Positive" if interest_score >= 70 else "Mixed",
        "summary": "Estimated interest based on profile and role alignment.",
    }


def _extract_score(text):
    match = re.search(r"\d+", text or "")
    if not match:
        logger.warning("Could not extract interest score from: %r", text)
        return 50
    return max(0, min(100, int(match.group())))


def simulate_conversation(candidate, jd_text):
    global client

    if not client:
        return _fallback_conversation(candidate, jd_text)

    prompt = (
        f"You are a candidate.\n\n"
        f"Profile: {candidate}\n\n"
        f"Recruiter: Are you interested in this role?\n\n{jd_text}\n\n"
        f"Reply naturally in 2-3 sentences."
    )

    try:
        res = client.chat.completions.create(
            model="gpt-4.1-mini",
            messages=[{"role": "user", "content": prompt}],
        )
        if not res.choices:
            logger.warning("Empty choices in conversation response for %s", candidate.get("name"))
            return _fallback_conversation(candidate, jd_text)

        reply = res.choices[0].message.content or ""

        score_prompt = (
            f"Based on this candidate response, give an interest score from 0 to 100.\n\n"
            f"Response: {reply}\n\nReturn only the number."
        )
        score_res = client.chat.completions.create(
            model="gpt-4.1-mini",
            messages=[{"role": "user", "content": score_prompt}],
        )

        if not score_res.choices:
            logger.warning("Empty choices in score response for %s", candidate.get("name"))
            interest_score = 50
        else:
            interest_score = _extract_score(score_res.choices[0].message.content)

        return {
            "response": reply,
            "interest_score": interest_score,
            "signal": "Positive" if interest_score >= 70 else "Mixed" if interest_score >= 45 else "Low",
            "summary": "Simulated outreach response scored from generated candidate reply.",
        }

    except Exception as exc:
        client = None
        logger.error("Conversation simulation failed for %s: %s", candidate.get("name"), exc)
        return _fallback_conversation(candidate, jd_text)
