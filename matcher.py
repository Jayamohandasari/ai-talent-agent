from embedding_matcher import semantic_match

# Role mismatch is treated as a hard penalty rather than a soft 55.
ROLE_MATCH_SCORE = 100
ROLE_MISMATCH_SCORE = 20
ROLE_UNKNOWN_SCORE = 70

LOCATION_MATCH_SCORE = 100
LOCATION_MISMATCH_SCORE = 65
LOCATION_UNKNOWN_SCORE = 75


def calculate_match_score(candidate, jd, jd_text):
    candidate_skills = {s.strip().lower() for s in candidate.get("skills", []) if s}
    jd_skills = {s.strip().lower() for s in jd.get("skills", []) if s}
    candidate_title = (candidate.get("title") or "").lower()
    jd_role = (jd.get("role") or "").lower()
    candidate_location = (candidate.get("location") or "").lower()
    jd_location = (jd.get("location") or "").lower()

    matched = sorted(candidate_skills & jd_skills)
    missing = sorted(jd_skills - candidate_skills)

    keyword_score = (len(matched) / len(jd_skills)) * 100 if jd_skills else 0
    semantic_score = semantic_match(candidate, jd_text)

    if jd_role:
        role_score = ROLE_MATCH_SCORE if jd_role in candidate_title else ROLE_MISMATCH_SCORE
    else:
        role_score = ROLE_UNKNOWN_SCORE

    if jd_location:
        location_score = LOCATION_MATCH_SCORE if jd_location in candidate_location else LOCATION_MISMATCH_SCORE
    else:
        location_score = LOCATION_UNKNOWN_SCORE

    candidate_experience = candidate.get("experience") or 0
    jd_experience = jd.get("experience") or 0
    exp_score = min(candidate_experience / jd_experience, 1) * 100 if jd_experience else 100

    match_score = (
        0.35 * keyword_score
        + 0.25 * semantic_score
        + 0.20 * exp_score
        + 0.10 * role_score
        + 0.10 * location_score
    )

    strengths = []
    if matched:
        strengths.append(f"Matched skills: {', '.join(matched[:5])}")
    if jd_experience and candidate_experience >= jd_experience:
        strengths.append("Meets or exceeds the experience target")
    if jd_role and jd_role in candidate_title:
        strengths.append("Current title aligns with the target role")
    if jd_location and jd_location in candidate_location:
        strengths.append("Location aligns with the role requirement")

    risks = []
    if missing:
        risks.append(f"Missing skills: {', '.join(missing[:5])}")
    if jd_experience and candidate_experience < jd_experience:
        risks.append("Experience is below the JD target")
    if jd_role and jd_role not in candidate_title:
        risks.append("Current title does not align with target role")
    if jd_location and jd_location not in candidate_location:
        risks.append("Location may require recruiter confirmation")

    return round(match_score, 2), {
        "skills_matched": matched,
        "missing_skills": missing,
        "experience": candidate_experience,
        "role_alignment": round(role_score, 2),
        "location_alignment": round(location_score, 2),
        "strengths": strengths,
        "risks": risks,
    }