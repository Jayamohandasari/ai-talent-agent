import csv
import io
import json
from datetime import datetime
from html import escape

import requests
import streamlit as st

try:
    import pandas as pd
except ImportError:
    pd = None


st.set_page_config(
    page_title="AI Talent Scouting & Engagement Agent",
    layout="wide",
    initial_sidebar_state="collapsed",
)


def _get_api_url():
    try:
        return st.secrets.get("api_url", "http://127.0.0.1:5000/run-agent")
    except Exception:
        return "http://127.0.0.1:5000/run-agent"


def _inject_styles():
    st.markdown(
        """
        <style>
        :root {
          --panel: rgba(255, 252, 247, 0.92);
          --line: #e8dac8;
          --text: #000000;
          --muted: #000000;
          --accent: #c56b2c;
          --accent-dark: #000000;
          --shadow: 0 16px 40px rgba(79, 52, 25, 0.08);
        }

        [data-testid="stAppViewContainer"] {
          background:
            radial-gradient(circle at top right, rgba(211, 126, 43, 0.16), transparent 26%),
            radial-gradient(circle at left top, rgba(37, 99, 235, 0.08), transparent 20%),
            linear-gradient(180deg, #f8f4ec 0%, #f4efe7 45%, #f8f6f1 100%);
        }

        [data-testid="stAppViewContainer"],
        [data-testid="stAppViewContainer"] p,
        [data-testid="stAppViewContainer"] label,
        [data-testid="stAppViewContainer"] li,
        [data-testid="stAppViewContainer"] span,
        [data-testid="stAppViewContainer"] small,
        [data-testid="stAppViewContainer"] h1,
        [data-testid="stAppViewContainer"] h2,
        [data-testid="stAppViewContainer"] h3,
        [data-testid="stAppViewContainer"] h4,
        [data-testid="stAppViewContainer"] h5,
        [data-testid="stAppViewContainer"] h6,
        [data-testid="stAppViewContainer"] [data-testid="stMarkdownContainer"] *,
        [data-testid="stAppViewContainer"] [data-testid="stMetricLabel"],
        [data-testid="stAppViewContainer"] [data-testid="stMetricValue"],
        [data-testid="stAppViewContainer"] [data-testid="stCaptionContainer"] * {
          color: #000000 !important;
        }

        .main .block-container {
          max-width: 1220px;
          padding-top: 1.15rem;
          padding-bottom: 3rem;
        }

        .hero-shell {
          padding: 1.4rem 1.5rem;
          border: 1px solid var(--line);
          border-radius: 24px;
          background: linear-gradient(135deg, rgba(255,255,255,0.95), rgba(255,246,232,0.95));
          box-shadow: var(--shadow);
          margin-bottom: 1rem;
        }

        .hero-kicker,
        .section-kicker {
          color: var(--accent-dark);
          letter-spacing: 0.08em;
          font-size: 0.74rem;
          font-weight: 700;
          text-transform: uppercase;
        }

        .hero-title {
          color: var(--text);
          font-size: 2.3rem;
          line-height: 1.05;
          font-weight: 800;
          margin: 0.35rem 0 0 0;
        }

        .hero-subtitle,
        .section-copy {
          color: var(--muted);
          font-size: 0.98rem;
          line-height: 1.55;
          margin-top: 0.65rem;
        }

        .section-shell {
          margin: 0.35rem 0 0.8rem 0;
        }

        .section-title {
          color: var(--text);
          font-size: 1.25rem;
          font-weight: 800;
          margin-top: 0.18rem;
        }

        .info-card {
          background: var(--panel);
          border: 1px solid var(--line);
          border-radius: 18px;
          padding: 0.95rem 1rem;
          min-height: 126px;
          box-shadow: 0 8px 24px rgba(65, 44, 20, 0.05);
        }

        .info-label {
          color: var(--muted);
          font-size: 0.76rem;
          letter-spacing: 0.06em;
          text-transform: uppercase;
          font-weight: 700;
          margin-bottom: 0.5rem;
        }

        .info-value {
          color: var(--text);
          font-size: 1.08rem;
          font-weight: 700;
          line-height: 1.25;
          margin-bottom: 0.32rem;
        }

        .info-helper {
          color: var(--muted);
          font-size: 0.9rem;
          line-height: 1.4;
        }

        .spotlight-card,
        .compare-card,
        .shortlist-card {
          background: var(--panel);
          border: 1px solid var(--line);
          border-radius: 22px;
          padding: 1.15rem 1.2rem;
          box-shadow: 0 12px 30px rgba(65, 44, 20, 0.05);
        }

        .spotlight-badge,
        .compare-badge,
        .shortlist-rank {
          display: inline-block;
          padding: 0.28rem 0.65rem;
          border-radius: 999px;
          background: rgba(197, 107, 44, 0.14);
          color: var(--accent-dark);
          font-size: 0.75rem;
          font-weight: 700;
          text-transform: uppercase;
          letter-spacing: 0.05em;
          margin-bottom: 0.8rem;
        }

        .spotlight-title,
        .compare-name,
        .shortlist-title {
          color: var(--text);
          font-size: 1.28rem;
          font-weight: 800;
          margin-bottom: 0.22rem;
        }

        .spotlight-meta,
        .compare-meta,
        .shortlist-meta {
          color: var(--muted);
          font-size: 0.94rem;
          margin-bottom: 0.7rem;
        }

        .spotlight-copy,
        .compare-copy {
          color: var(--text);
          font-size: 0.98rem;
          line-height: 1.55;
        }

        div[data-testid="stMetric"] {
          background: rgba(255, 255, 255, 0.85);
          border: 1px solid var(--line);
          border-radius: 18px;
          padding: 0.9rem 0.95rem;
          box-shadow: 0 8px 24px rgba(65, 44, 20, 0.04);
        }

        div[data-testid="stMetricLabel"] {
          font-size: 0.78rem;
          text-transform: uppercase;
          letter-spacing: 0.06em;
        }

        div.stButton > button,
        div.stDownloadButton > button {
          width: 100%;
          border-radius: 14px;
          min-height: 2.95rem;
          border: 1px solid var(--line);
          font-weight: 700;
          color: #000000 !important;
        }

        div.stDownloadButton > button {
          background: #ffffff !important;
        }

        div.stButton > button[kind="primary"] {
          background: linear-gradient(135deg, var(--accent), #d4864a);
          color: white !important;
          border: none;
        }

        div[data-testid="stTextArea"] textarea,
        div[data-testid="stTextInput"] input {
          border-radius: 16px;
          background: #ffffff !important;
          color: #000000 !important;
        }

        div[data-testid="stSelectbox"] > div,
        div[data-testid="stSelectbox"] [data-baseweb="select"] > div,
        div[data-testid="stSelectbox"] input {
          background: #ffffff !important;
          color: #000000 !important;
        }

        textarea[aria-label="Enter Job Description"] {
          color: #ffffff !important;
          background: #111111 !important;
          caret-color: #ffffff !important;
        }

        textarea[aria-label="Enter Job Description"]::placeholder {
          color: #d4d4d8 !important;
        }

        div[data-testid="stRadio"] label,
        div[data-testid="stRadio"] p,
        div[role="radiogroup"] label,
        div[role="radiogroup"] p {
          color: #000000 !important;
        }

        div[data-testid="stFileUploader"] section {
          border-radius: 18px;
          background: rgba(255, 255, 255, 0.55);
        }

        div[data-testid="stFileUploader"] button {
          background: #ffffff !important;
          color: #000000 !important;
          border: 1px solid var(--line) !important;
        }

        div[data-testid="stTabs"] button {
          border-radius: 999px;
          padding: 0.45rem 0.9rem;
          font-weight: 700;
          color: #000000 !important;
        }

        div[data-testid="stSelectbox"] *,
        div[data-testid="stSlider"] *,
        div[data-testid="stRadio"] *,
        div[data-testid="stFileUploader"] *,
        div[data-testid="stExpander"] * {
          color: #000000 !important;
        }

        div[data-testid="stExpander"] details {
          border: 1px solid var(--line);
          border-radius: 18px;
          background: rgba(255, 255, 255, 0.72);
        }

        @media (max-width: 900px) {
          .main .block-container {
            padding-left: 0.95rem;
            padding-right: 0.95rem;
          }

          .hero-shell,
          .spotlight-card,
          .compare-card,
          .shortlist-card,
          .info-card {
            padding: 1rem;
            border-radius: 18px;
          }

          .hero-title {
            font-size: 1.72rem;
          }
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def _section_header(kicker, title, copy):
    st.markdown(
        f"""
        <div class="section-shell">
          <div class="section-kicker">{escape(kicker)}</div>
          <div class="section-title">{escape(title)}</div>
          <div class="section-copy">{escape(copy)}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def _info_card(label, value, helper=""):
    st.markdown(
        f"""
        <div class="info-card">
          <div class="info-label">{escape(label)}</div>
          <div class="info-value">{escape(str(value))}</div>
          <div class="info-helper">{escape(helper)}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def _candidate_card(rank, candidate, is_top=False):
    marker = "Top Candidate" if is_top else f"Rank #{rank}"
    st.markdown(
        f"""
        <div class="shortlist-card">
          <div class="shortlist-rank">{escape(marker)}</div>
          <div class="shortlist-title">{escape(candidate.get('name', 'Unknown'))} | {escape(candidate.get('title') or 'Candidate')}</div>
          <div class="shortlist-meta">{escape(candidate.get('location') or 'Unknown location')}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def _spotlight_card(candidate):
    st.markdown(
        f"""
        <div class="spotlight-card">
          <div class="spotlight-badge">Top Candidate</div>
          <div class="spotlight-title">{escape(candidate.get('name', 'Unknown'))}</div>
          <div class="spotlight-meta">{escape(candidate.get('title') or 'Candidate')} | {escape(candidate.get('location') or 'Unknown location')}</div>
          <div class="spotlight-copy">{escape(candidate.get('why_selected', 'Top ranked candidate'))}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def _comparison_card(candidate, badge):
    st.markdown(
        f"""
        <div class="compare-card">
          <div class="compare-badge">{escape(badge)}</div>
          <div class="compare-name">{escape(candidate.get('name', 'Unknown'))}</div>
          <div class="compare-meta">{escape(candidate.get('title') or 'Candidate')} | {escape(candidate.get('location') or 'Unknown location')}</div>
          <div class="compare-copy">{escape(candidate.get('why_selected', ''))}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def _split_list_field(value):
    if not value:
        return []

    normalized = str(value).replace("|", ",").replace(";", ",")
    return [item.strip() for item in normalized.split(",") if item.strip()]


def _safe_int(value, default=0):
    try:
        return int(float(str(value).strip()))
    except (TypeError, ValueError):
        return default


def _load_candidates_from_csv(uploaded_file):
    content = uploaded_file.getvalue().decode("utf-8-sig")
    reader = csv.DictReader(io.StringIO(content))

    if not reader.fieldnames:
        raise ValueError("CSV is missing a header row.")

    candidates = []
    for row in reader:
        if not any(str(cell or "").strip() for cell in row.values()):
            continue

        candidate = {
            "name": str(row.get("name", "")).strip(),
            "title": str(row.get("title", "")).strip(),
            "location": str(row.get("location", "")).strip(),
            "experience": _safe_int(row.get("experience"), 0),
            "skills": _split_list_field(row.get("skills", "")),
            "summary": str(row.get("summary", "")).strip(),
            "preferences": {
                "motivation": str(row.get("motivation", "")).strip(),
                "locations": _split_list_field(
                    row.get("preferred_locations", "") or row.get("preferred locations", "")
                ),
            },
        }

        if candidate["name"]:
            candidates.append(candidate)

    if not candidates:
        raise ValueError("CSV did not contain any valid candidate rows.")

    return candidates


def _sample_csv_template():
    output = io.StringIO()
    writer = csv.DictWriter(
        output,
        fieldnames=[
            "name",
            "title",
            "location",
            "experience",
            "skills",
            "summary",
            "motivation",
            "preferred_locations",
        ],
    )
    writer.writeheader()
    writer.writerow(
        {
            "name": "Rahul Sharma",
            "title": "Backend Engineer",
            "location": "Hyderabad",
            "experience": 4,
            "skills": "Python, Flask, PostgreSQL, Docker, AWS",
            "summary": "Backend engineer focused on API development and reliability.",
            "motivation": "Interested in backend ownership and scalable services.",
            "preferred_locations": "Hyderabad, Remote",
        }
    )
    return output.getvalue()


def _build_results_csv(candidates):
    output = io.StringIO()
    writer = csv.DictWriter(
        output,
        fieldnames=[
            "rank",
            "name",
            "title",
            "location",
            "match_score",
            "interest_score",
            "final_score",
            "interest_signal",
            "matched_skills",
            "missing_skills",
            "why_selected",
            "candidate_response",
        ],
    )
    writer.writeheader()

    for rank, candidate in enumerate(candidates, start=1):
        explanation = candidate.get("explanation", {})
        writer.writerow(
            {
                "rank": rank,
                "name": candidate.get("name", ""),
                "title": candidate.get("title", ""),
                "location": candidate.get("location", ""),
                "match_score": candidate.get("match_score", ""),
                "interest_score": candidate.get("interest_score", ""),
                "final_score": candidate.get("final_score", ""),
                "interest_signal": candidate.get("interest_signal", ""),
                "matched_skills": ", ".join(explanation.get("skills_matched", [])),
                "missing_skills": ", ".join(explanation.get("missing_skills", [])),
                "why_selected": candidate.get("why_selected", ""),
                "candidate_response": candidate.get("response", ""),
            }
        )

    return output.getvalue()


def _score_bar(label, value, color):
    safe_value = float(value or 0)
    percent = max(0, min(100, safe_value))
    st.markdown(
        f"""
        <div style="margin:0.35rem 0 0.9rem 0;">
          <div style="display:flex;justify-content:space-between;font-size:0.95rem;">
            <span>{escape(label)}</span>
            <strong>{safe_value:.2f}</strong>
          </div>
          <div style="width:100%;background:#e8edf5;border-radius:999px;height:0.75rem;overflow:hidden;">
            <div style="width:{percent}%;background:{color};height:100%;"></div>
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def _skill_badges(skills, background, border, text_color):
    if not skills:
        return "None"

    badges = []
    for skill in skills:
        badges.append(
            f"<span style=\"display:inline-block;padding:0.2rem 0.55rem;margin:0.15rem;"
            f"border-radius:999px;background:{background};border:1px solid {border};"
            f"color:{text_color};font-size:0.84rem;\">{escape(skill)}</span>"
        )
    return "".join(badges)


_inject_styles()
API_URL = _get_api_url()

if "agent_result" not in st.session_state:
    st.session_state["agent_result"] = None

st.markdown(
    """
    <div class="hero-shell">
      <div class="hero-kicker">Recruiter Workflow</div>
      <div class="hero-title">AI Talent Scouting & Engagement Agent</div>
      <div class="hero-subtitle">
        Parse the JD, source or upload candidates, compare ranked matches, and leave the session
        with a shortlist you can action immediately.
      </div>
    </div>
    """,
    unsafe_allow_html=True,
)

form_left, form_right = st.columns([1.5, 1.0], gap="large")

with form_left:
    _section_header("Job Brief", "Describe the role", "Give the agent the exact JD you want it to match against.")
    jd = st.text_area("Enter Job Description", height=250, label_visibility="collapsed")

with form_right:
    _section_header("Candidate Source", "Choose how to source talent", "Use the built-in pool, generate candidates, paste JSON, or upload CSV.")
    candidate_source = st.radio(
        "Candidate source",
        ["Built-in talent pool", "Auto-generate AI candidates", "Paste JSON", "Upload CSV"],
        horizontal=False,
        label_visibility="collapsed",
    )

sample_json = """[
  {
    "name": "Rahul Sharma",
    "title": "Backend Engineer",
    "skills": ["Python", "Flask", "PostgreSQL"],
    "experience": 4,
    "location": "Hyderabad",
    "summary": "Backend developer focused on APIs and platform reliability."
  }
]"""

uploaded_csv = None
candidates_input = None

if candidate_source == "Paste JSON":
    candidates_input = st.text_area("Candidates JSON", value=sample_json, height=220)
elif candidate_source == "Upload CSV":
    uploaded_csv = st.file_uploader("Upload candidate CSV", type=["csv"])
    st.caption(
        "Expected columns: name, title, location, experience, skills, summary, motivation, preferred_locations"
    )
    template_col, preview_col = st.columns([1.0, 1.1], gap="small")
    with template_col:
        st.download_button(
            "Download CSV template",
            data=_sample_csv_template(),
            file_name="candidate_template.csv",
            mime="text/csv",
        )
    with preview_col:
        if uploaded_csv is not None:
            try:
                preview_candidates = _load_candidates_from_csv(uploaded_csv)
                st.success(f"Loaded {len(preview_candidates)} candidate row(s) from CSV.")
            except ValueError as exc:
                st.error(str(exc))

control_cols = st.columns([1.0, 1.2], gap="large")
with control_cols[0]:
    top_n = st.slider("Shortlist size", min_value=3, max_value=8, value=5)
with control_cols[1]:
    st.markdown("<div style='height:1.7rem'></div>", unsafe_allow_html=True)
    run_agent = st.button("Run Agent", type="primary", use_container_width=True)

if run_agent:
    if not jd.strip():
        st.error("Please enter a job description before running the agent.")
        st.stop()

    payload = {"jd": jd, "top_n": top_n}

    if candidate_source == "Auto-generate AI candidates":
        payload["generate_candidates"] = True
    elif candidate_source == "Paste JSON":
        try:
            payload["candidates"] = json.loads(candidates_input)
        except json.JSONDecodeError:
            st.error("Invalid JSON in candidate pool. Please fix the format and try again.")
            st.stop()
    elif candidate_source == "Upload CSV":
        if uploaded_csv is None:
            st.error("Upload a CSV file before running the agent.")
            st.stop()
        try:
            payload["candidates"] = _load_candidates_from_csv(uploaded_csv)
        except ValueError as exc:
            st.error(str(exc))
            st.stop()

    try:
        with st.spinner("Agent is running - parsing JD, matching candidates, simulating outreach..."):
            response = requests.post(API_URL, json=payload, timeout=120)
        response.raise_for_status()
        st.session_state["agent_result"] = response.json()
    except requests.RequestException as exc:
        st.error(f"Could not reach the agent API: {exc}")
        st.stop()

result = st.session_state.get("agent_result")

if result:
    jd_profile = result.get("jd_profile", {})
    summary = result.get("shortlist_summary", {})
    ranked_candidates = result.get("ranked_candidates", [])
    candidate_source_used = result.get("candidate_source_used", "built_in")

    if not ranked_candidates:
        st.warning("No strong candidates were discovered for this JD.")
        st.stop()

    source_label = {
        "built_in": "Built-in talent pool",
        "generated": "AI-generated candidate profiles",
        "generated_fallback": "Built-in fallback after AI generation was unavailable",
        "provided": "Recruiter-provided candidates",
    }.get(candidate_source_used, candidate_source_used)

    _section_header("Overview", "Role snapshot", "Review the parsed JD and shape the shortlist view.")

    info_cols = st.columns(4, gap="medium")
    with info_cols[0]:
        _info_card("Role", jd_profile.get("role") or "Not identified", "Primary role the agent parsed from the JD.")
    with info_cols[1]:
        _info_card(
            "Experience Target",
            f"{jd_profile.get('experience', 0)} years",
            "Candidate experience is compared against this target.",
        )
    with info_cols[2]:
        _info_card("Location", jd_profile.get("location") or "Not specified", "Role preference used during matching.")
    with info_cols[3]:
        _info_card("Candidate Source", source_label, "Where the shortlist came from for this run.")

    metric_cols = st.columns(4, gap="medium")
    metric_cols[0].metric("Candidate Pool", result.get("candidate_pool_size", 0))
    metric_cols[1].metric("Discovered", result.get("discovered_candidates", 0))
    metric_cols[2].metric("Top Match Score", summary.get("top_match_score", 0))
    metric_cols[3].metric("Top Interest Score", summary.get("top_interest_score", 0))
    st.info(summary.get("recommended_action", ""))

    controls_cols = st.columns([1.1, 1.1, 1.25], gap="medium")
    with controls_cols[0]:
        min_match_score = st.slider("Minimum Match Score", 0, 100, 50)
    with controls_cols[1]:
        sort_option = st.selectbox("Sort By", ["Final Score", "Match Score", "Interest Score"])
    with controls_cols[2]:
        st.markdown("<div style='height:1.7rem'></div>", unsafe_allow_html=True)
        st.caption(f"Showing candidates at or above a match score of {min_match_score}.")

    display_candidates = [
        candidate for candidate in ranked_candidates if float(candidate.get("match_score", 0) or 0) >= min_match_score
    ]

    if sort_option == "Match Score":
        display_candidates.sort(key=lambda candidate: candidate.get("match_score", 0), reverse=True)
    elif sort_option == "Interest Score":
        display_candidates.sort(key=lambda candidate: candidate.get("interest_score", 0), reverse=True)
    else:
        display_candidates.sort(key=lambda candidate: candidate.get("final_score", 0), reverse=True)

    if ranked_candidates and len(ranked_candidates) < top_n:
        st.warning(
            f"Only {len(ranked_candidates)} candidate(s) met the match threshold "
            f"(requested {top_n}). Consider broadening the JD requirements."
        )

    if not display_candidates:
        st.warning("No candidates match the current minimum match score filter.")
        st.stop()

    st.caption(f"Showing {len(display_candidates)} of {len(ranked_candidates)} ranked candidates.")

    overview_tab, analytics_tab, shortlist_tab = st.tabs(["Overview", "Analytics", "Shortlist"])

    with overview_tab:
        top_candidate = display_candidates[0]
        top_explanation = top_candidate.get("explanation", {})

        spot_left, spot_right = st.columns([1.05, 1.15], gap="large")
        with spot_left:
            _spotlight_card(top_candidate)
            st.write("**Why Selected:**", top_candidate.get("why_selected", "Top ranked candidate"))
            st.write("**Interest signal:**", top_candidate.get("interest_signal", "Mixed"))
            st.write("**Candidate response:**", top_candidate.get("response", "No response recorded"))

            top_gap_skills = top_explanation.get("missing_skills", [])
            if top_gap_skills:
                st.warning(f"Skill gaps to validate: {', '.join(top_gap_skills)}")
            else:
                st.success("No major skill gaps detected for the top candidate.")

        with spot_right:
            _section_header("Score Readout", "Top-candidate scoring", "Use the score mix and gap view to explain the ranking quickly.")
            _score_bar("Match Score", top_candidate.get("match_score", 0), "#2563eb")
            _score_bar("Interest Score", top_candidate.get("interest_score", 0), "#f59e0b")
            _score_bar("Final Score", top_candidate.get("final_score", 0), "#16a34a")

            st.write("**Matched Skills**")
            st.markdown(
                _skill_badges(
                    top_explanation.get("skills_matched", []),
                    "#e8f5e9",
                    "#8bc34a",
                    "#256029",
                ),
                unsafe_allow_html=True,
            )
            st.write("**Skill Gaps**")
            st.markdown(
                _skill_badges(
                    top_explanation.get("missing_skills", []),
                    "#fff3e0",
                    "#ffb74d",
                    "#8a4b00",
                ),
                unsafe_allow_html=True,
            )

    with analytics_tab:
        analytics_cols = st.columns([1.1, 1.1], gap="large")
        with analytics_cols[0]:
            _section_header("Downloads", "Export the shortlist", "Download the filtered shortlist in CSV or JSON.")
            download_name = datetime.now().strftime("talent_shortlist_%Y%m%d_%H%M%S")
            download_candidates = display_candidates or ranked_candidates
            st.download_button(
                "Download CSV results",
                data=_build_results_csv(download_candidates),
                file_name=f"{download_name}.csv",
                mime="text/csv",
                use_container_width=True,
            )
            export_payload = dict(result)
            export_payload["ranked_candidates"] = download_candidates
            st.download_button(
                "Download JSON results",
                data=json.dumps(export_payload, indent=2),
                file_name=f"{download_name}.json",
                mime="application/json",
                use_container_width=True,
            )

        with analytics_cols[1]:
            if len(display_candidates) >= 2:
                _section_header("Top 2 Comparison", "Compare your leading options", "This makes recruiter trade-offs easier to discuss.")
                compare_col1, compare_col2 = st.columns(2, gap="small")
                with compare_col1:
                    _comparison_card(display_candidates[0], "Candidate A")
                    st.write("Match:", display_candidates[0]["match_score"])
                    st.write("Interest:", display_candidates[0]["interest_score"])
                    st.write("Final:", display_candidates[0]["final_score"])
                with compare_col2:
                    _comparison_card(display_candidates[1], "Candidate B")
                    st.write("Match:", display_candidates[1]["match_score"])
                    st.write("Interest:", display_candidates[1]["interest_score"])
                    st.write("Final:", display_candidates[1]["final_score"])

        if pd is not None:
            _section_header("Score Chart", "Visualize ranking strength", "Compare the filtered shortlist across match and interest dimensions.")
            chart_data = pd.DataFrame(
                {
                    "Candidate": [candidate["name"] for candidate in display_candidates],
                    "Match Score": [candidate["match_score"] for candidate in display_candidates],
                    "Interest Score": [candidate["interest_score"] for candidate in display_candidates],
                }
            )
            st.bar_chart(chart_data.set_index("Candidate"))

    with shortlist_tab:
        _section_header("Shortlist", "Review ranked candidates", "Each card includes scores, reasoning, strengths, and risks.")
        for rank, candidate in enumerate(display_candidates, start=1):
            _candidate_card(rank, candidate, is_top=(rank == 1))

            score_cols = st.columns(3, gap="medium")
            with score_cols[0]:
                _score_bar("Match Score", candidate.get("match_score", 0), "#2563eb")
            with score_cols[1]:
                _score_bar("Interest Score", candidate.get("interest_score", 0), "#f59e0b")
            with score_cols[2]:
                _score_bar("Final Score", candidate.get("final_score", 0), "#16a34a")

            st.write("**Why Selected:**", candidate.get("why_selected", "Not specified"))
            st.write("**Interest signal:**", candidate.get("interest_signal", "Mixed"))
            st.write("**Interest summary:**", candidate.get("interest_summary", ""))
            st.write("**Candidate response:**", candidate.get("response", "No response recorded"))

            explanation = candidate.get("explanation", {})
            matched_skills = explanation.get("skills_matched", [])
            missing_skills = explanation.get("missing_skills", [])
            strengths = "; ".join(explanation.get("strengths", [])) or "None"
            risks = "; ".join(explanation.get("risks", [])) or "None"

            skill_cols = st.columns(2, gap="medium")
            with skill_cols[0]:
                st.write("**Matched Skills**")
                st.markdown(
                    _skill_badges(matched_skills, "#e8f5e9", "#8bc34a", "#256029"),
                    unsafe_allow_html=True,
                )
            with skill_cols[1]:
                st.write("**Skill Gaps**")
                st.markdown(
                    _skill_badges(missing_skills, "#fff3e0", "#ffb74d", "#8a4b00"),
                    unsafe_allow_html=True,
                )

            with st.expander("Scoring breakdown"):
                st.write("**Strengths:**", strengths)
                st.write("**Risks:**", risks)
