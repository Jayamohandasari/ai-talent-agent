from matcher import calculate_match_score

MIN_MATCH_THRESHOLD = 25


def _normalize_candidate(candidate):
    normalized = dict(candidate)
    normalized.setdefault("skills", [])
    normalized.setdefault("experience", 0)
    normalized.setdefault("summary", "")
    normalized.setdefault("location", "Unknown")
    normalized.setdefault("title", "")
    normalized.setdefault("preferences", {})
    return normalized


def discover_candidates(jd, jd_text, candidate_pool, top_n=5):
    """
    Score every candidate once and carry the result forward.
    The caller should use the score and explanation from this function
    directly rather than re-calling calculate_match_score.
    """
    shortlisted = []

    for candidate in candidate_pool:
        candidate = _normalize_candidate(candidate)
        match_score, explanation = calculate_match_score(candidate, jd, jd_text)

        if match_score < MIN_MATCH_THRESHOLD:
            continue

        shortlisted.append({
            "candidate": candidate,
            "match_score": match_score,
            "explanation": explanation,
        })

    shortlisted.sort(
        key=lambda item: (item["match_score"], item["candidate"].get("experience", 0)),
        reverse=True,
    )
    return shortlisted[:top_n]