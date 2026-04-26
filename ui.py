import json
import streamlit as st

from jd_parser import parse_jd
from discovery import discover_candidates
from conversation import simulate_conversation
from scorer import final_score
from candidate_store import DEFAULT_CANDIDATES

st.set_page_config(page_title="AI Talent Agent", layout="wide")

st.title("AI Talent Scouting & Engagement Agent")

# ================= INPUT =================

jd = st.text_area("Enter Job Description", height=200)

sample_json = """[
  {
    "name": "Rahul Sharma",
    "title": "Backend Engineer",
    "skills": ["Python", "Flask", "PostgreSQL"],
    "experience": 4,
    "location": "Hyderabad",
    "summary": "Backend developer"
  }
]"""

candidate_source = st.radio(
    "Candidate Source",
    ["Built-in", "Auto-generate", "Paste JSON"]
)

candidates_input = None
if candidate_source == "Paste JSON":
    candidates_input = st.text_area("Paste Candidates JSON", value=sample_json)

top_n = st.slider("Top Candidates", 1, 10, 5)

# ================= RUN =================

if st.button("Run Agent"):

    if not jd.strip():
        st.error("Enter Job Description")
        st.stop()

    try:
        candidates = json.loads(candidates_input) if candidates_input else None
    except:
        st.error("Invalid JSON format")
        st.stop()

    jd_data = parse_jd(jd)

    if candidates:
        candidate_pool = candidates
    elif candidate_source == "Auto-generate":
        candidate_pool = DEFAULT_CANDIDATES[:3]
    else:
        candidate_pool = DEFAULT_CANDIDATES

    shortlisted = discover_candidates(jd_data, jd, candidate_pool, top_n=top_n)

    results = []

    for item in shortlisted:
        candidate = item["candidate"]
        match_score = item["match_score"]
        explanation = item["explanation"]

        convo = simulate_conversation(candidate, jd)
        interest_score = convo["interest_score"]

        results.append({
            "name": candidate["name"],
            "title": candidate.get("title", ""),
            "location": candidate.get("location", ""),
            "match_score": match_score,
            "interest_score": interest_score,
            "final_score": final_score(match_score, interest_score),
            "response": convo["response"],
            "explanation": explanation
        })

    results.sort(key=lambda x: x["final_score"], reverse=True)

    # ================= OUTPUT =================

    st.success("Results Generated")

    for r in results:
        st.subheader(r["name"])

        col1, col2, col3 = st.columns(3)
        col1.metric("Match Score", r["match_score"])
        col2.metric("Interest Score", r["interest_score"])
        col3.metric("Final Score", r["final_score"])

        st.write("📍 Location:", r["location"])
        st.write("💬 Response:", r["response"])

        st.write("✅ Matched Skills:", r["explanation"]["skills_matched"])
        st.write("❌ Missing Skills:", r["explanation"]["missing_skills"])

        st.markdown("---")