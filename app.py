import json
import logging
import os

from candidate_store import DEFAULT_CANDIDATES
from conversation import simulate_conversation
from discovery import discover_candidates
from flask import Flask, jsonify, request
from jd_parser import parse_jd
from scorer import final_score

try:
    from openai import OpenAI
except ImportError:
    OpenAI = None

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)


def _make_client():
    if OpenAI is None:
        return None
    if not os.getenv("OPENAI_API_KEY"):
        return None
    try:
        return OpenAI(max_retries=0, timeout=5.0)
    except Exception as exc:
        logger.warning("OpenAI client init failed in app.py, using fallback logic: %s", exc)
        return None


client = _make_client()


def _validate_candidate(candidate):
    if not isinstance(candidate, dict):
        return False
    if not candidate.get("name"):
        return False
    candidate.setdefault("skills", [])
    candidate.setdefault("experience", 0)
    candidate.setdefault("summary", "")
    candidate.setdefault("location", "Unknown")
    candidate.setdefault("title", "")
    candidate.setdefault("preferences", {})
    return True


def _fallback_rank_reason(candidate, match_score, interest_score, explanation):
    matched_skills = explanation.get("skills_matched", [])
    strengths = explanation.get("strengths", [])
    reason_parts = []

    if matched_skills:
        reason_parts.append(f"Strong skill alignment in {', '.join(matched_skills[:3])}")
    elif strengths:
        reason_parts.append(strengths[0])
    else:
        reason_parts.append("Profile aligns reasonably well with the role requirements")

    if interest_score >= 70:
        reason_parts.append("the candidate also showed strong simulated interest")
    elif interest_score >= 50:
        reason_parts.append("the candidate showed moderate simulated interest")
    else:
        reason_parts.append("interest should be validated in recruiter outreach")

    return " and ".join(reason_parts) + "."


def _generate_rank_reason(candidate, jd_text, match_score, interest_score, explanation):
    global client

    if not client:
        return _fallback_rank_reason(candidate, match_score, interest_score, explanation)

    prompt = f"""
    Explain in exactly 1 short sentence why this candidate is ranked for the role.

    Candidate: {candidate.get("name", "Candidate")}
    Title: {candidate.get("title", "")}
    Match Score: {match_score}
    Interest Score: {interest_score}
    Skills: {candidate.get("skills", [])}
    Matching Notes: {explanation}
    JD: {jd_text}
    """

    try:
        response = client.chat.completions.create(
            model="gpt-4.1-mini",
            messages=[{"role": "user", "content": prompt}],
        )
        if response.choices:
            content = (response.choices[0].message.content or "").strip()
            if content:
                return content
    except Exception as exc:
        client = None
        logger.warning("AI rank explanation failed for %s: %s", candidate.get("name"), exc)

    return _fallback_rank_reason(candidate, match_score, interest_score, explanation)


def _normalize_generated_candidate(candidate, fallback_title):
    normalized = dict(candidate)
    normalized.setdefault("name", "")
    normalized.setdefault("title", fallback_title or "Candidate")
    normalized.setdefault("skills", [])
    normalized.setdefault("experience", 0)
    normalized.setdefault("location", "Remote")
    normalized.setdefault("summary", "")
    normalized.setdefault("preferences", {})

    if isinstance(normalized["skills"], str):
        normalized["skills"] = [skill.strip() for skill in normalized["skills"].split(",") if skill.strip()]

    if not isinstance(normalized["preferences"], dict):
        normalized["preferences"] = {}

    normalized["preferences"].setdefault("motivation", "Open to relevant opportunities.")
    normalized["preferences"].setdefault("locations", [normalized.get("location", "Remote")])
    return normalized


def _parse_generated_candidates(content):
    cleaned = (content or "").strip()
    cleaned = cleaned.removeprefix("```json").removeprefix("```").removesuffix("```").strip()
    parsed = json.loads(cleaned)
    if isinstance(parsed, dict):
        parsed = parsed.get("candidates", [])
    if not isinstance(parsed, list):
        raise ValueError("Generated candidates must be a JSON list.")
    return parsed


def _generate_candidates_from_jd(jd_text, jd):
    global client

    if not client:
        return None

    prompt = f"""
    Generate 3 realistic candidate profiles for this job description.

    Return ONLY a JSON list. Each object must contain:
    name, title, skills, experience, location, summary, preferences

    The preferences object must contain:
    motivation, locations

    Job Description:
    {jd_text}
    """

    try:
        response = client.chat.completions.create(
            model="gpt-4.1-mini",
            messages=[{"role": "user", "content": prompt}],
        )
        if not response.choices:
            return None

        generated = _parse_generated_candidates(response.choices[0].message.content)
        normalized = [
            _normalize_generated_candidate(candidate, jd.get("role", "Candidate"))
            for candidate in generated
            if isinstance(candidate, dict)
        ]
        valid = [candidate for candidate in normalized if _validate_candidate(candidate)]
        return valid or None
    except Exception as exc:
        client = None
        logger.warning("AI candidate generation failed: %s", exc)
        return None


@app.route("/run-agent", methods=["POST"])
def run_agent():
    data = request.get_json(silent=True) or {}
    jd_text = (data.get("jd") or "").strip()
    candidates = data.get("candidates")
    generate_candidates = bool(data.get("generate_candidates"))

    # Accept int or float, coerce safely
    try:
        top_n = int(data.get("top_n", 5))
        if top_n <= 0:
            raise ValueError
    except (ValueError, TypeError):
        return jsonify({"error": "Field 'top_n' must be a positive integer."}), 400

    if not jd_text:
        return jsonify({"error": "Field 'jd' is required."}), 400

    if candidates is not None and not isinstance(candidates, list):
        return jsonify({"error": "Field 'candidates' must be a list."}), 400

    jd = parse_jd(jd_text)

    provided_candidates = candidates if candidates else None

    if provided_candidates is not None:
        candidate_pool = provided_candidates
        candidate_source_used = "provided"
    elif generate_candidates:
        generated_candidates = _generate_candidates_from_jd(jd_text, jd)
        if generated_candidates:
            candidate_pool = generated_candidates
            candidate_source_used = "generated"
        else:
            candidate_pool = DEFAULT_CANDIDATES[:3]
            candidate_source_used = "generated_fallback"
    else:
        candidate_pool = DEFAULT_CANDIDATES
        candidate_source_used = "built_in"

    # discover_candidates scores each candidate exactly once
    shortlisted = discover_candidates(jd, jd_text, candidate_pool, top_n=top_n)

    ranked_candidates = []
    for item in shortlisted:
        candidate = item["candidate"]
        if not _validate_candidate(candidate):
            continue

        # Reuse the score already computed during discovery — no double call
        match_score = item["match_score"]
        explanation = item["explanation"]

        convo = simulate_conversation(candidate, jd_text)
        interest_score = convo["interest_score"]
        why_selected = _generate_rank_reason(candidate, jd_text, match_score, interest_score, explanation)

        ranked_candidates.append({
            "name": candidate["name"],
            "title": candidate.get("title", ""),
            "location": candidate.get("location", "Unknown"),
            "match_score": match_score,
            "interest_score": interest_score,
            "final_score": final_score(match_score, interest_score),
            "response": convo["response"],
            "interest_signal": convo.get("signal", "Mixed"),
            "interest_summary": convo.get("summary", ""),
            "why_selected": why_selected,
            "explanation": explanation,
        })

    ranked_candidates.sort(key=lambda c: c["final_score"], reverse=True)

    response = {
        "jd_profile": jd,
        "candidate_source_used": candidate_source_used,
        "candidate_pool_size": len(candidate_pool),
        "discovered_candidates": len(shortlisted),
        "ranked_candidates": ranked_candidates,
        "shortlist_summary": {
            "top_match_score": ranked_candidates[0]["match_score"] if ranked_candidates else 0,
            "top_interest_score": ranked_candidates[0]["interest_score"] if ranked_candidates else 0,
            "recommended_action": (
                "Review top 3 candidates first."
                if ranked_candidates
                else "Broaden the candidate pool or relax JD constraints."
            ),
        },
    }

    return jsonify(response)


if __name__ == "__main__":
    app.run(debug=True)
