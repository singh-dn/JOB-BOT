# ============================
# main.py — FINAL VERSION
# ============================

import os
import io
import re
import json
import streamlit as st
import pandas as pd
from typing import Tuple

# SCRAPERS
from scraper.internshala_realtime import realtime_internshala_scrape
from scraper.naukri_realtime import realtime_naukri_scrape

# RESUME PARSER
from scraper.resume_parser import parse_resume


# ----------------------------------------
# OPTIONAL GEMINI AI SETUP
# ----------------------------------------
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")
USE_GEMINI = False
gemini_model = None

if GEMINI_API_KEY:
    try:
        import google.generativeai as genai
        genai.configure(api_key=GEMINI_API_KEY)
        gemini_model = genai.GenerativeModel("gemini-1.5-flash")
        USE_GEMINI = True
    except:
        USE_GEMINI = False


# ----------------------------------------
# HELPERS
# ----------------------------------------
def to_excel_bytes(df: pd.DataFrame) -> bytes:
    buf = io.BytesIO()
    df.to_excel(buf, index=False, engine="openpyxl")
    buf.seek(0)
    return buf.read()


def simple_tokenize(text: str):
    text = re.sub(r"[^\w\s]", " ", text.lower())
    return {w for w in text.split() if len(w) > 2}


def fallback_match(job_text: str, resume_text: str):
    jt = simple_tokenize(job_text)
    rt = simple_tokenize(resume_text)
    if not jt or not rt:
        return 0, "No matching words."

    inter = jt.intersection(rt)
    score = int(len(inter) / max(len(jt.union(rt)), 1) * 100)
    reason = f"Shared keywords: {', '.join(list(inter)[:6])}"
    return score, reason


def ai_match(job_text: str, resume_text: str) -> Tuple[int, str]:
    if USE_GEMINI and gemini_model:
        try:
            prompt = f"""
            Compare this resume and job description.
            Return JSON ONLY {{ "score": 0-100, "reason": "..." }}.

            RESUME:
            {resume_text}

            JOB:
            {job_text}
            """
            res = gemini_model.generate_content(prompt).text.strip()
            m = re.search(r"\{.*\}", res, re.S)
            if not m:
                raise ValueError()

            obj = json.loads(m.group(0))
            return int(obj["score"]), obj["reason"]

        except:
            pass

    return fallback_match(job_text, resume_text)


# ----------------------------------------
# SKILL TAGS
# ----------------------------------------
def render_skill_tags(skills_list):
    html = """
    <style>
    .chip {
        display:inline-block;
        padding:4px 10px;
        border-radius:12px;
        background:#2d2f34;
        margin:2px;
        color:#ddd;
        font-size:12px;
        border:1px solid #444;
    }
    </style>
    """
    if not skills_list:
        return html + "<span class='chip'>No skills</span>"

    chips = " ".join([f"<span class='chip'>{s}</span>" for s in skills_list])
    return html + chips


# ----------------------------------------
# STREAMLIT UI SETTINGS
# ----------------------------------------
st.set_page_config(page_title="AI Job Matching Scraper", layout="wide")

# WHITE TEXT FIX FOR TABLES
st.markdown("""
<style>

.stDataFrame tbody td, .stDataFrame th {
    color: white !important;
}

table.dataframe, .dataframe th, .dataframe td {
    color: white !important;
    background-color: #0f1116 !important;
    border: 1px solid #333 !important;
}

</style>
""", unsafe_allow_html=True)


# DARK UI PRESERVED
st.markdown(
    """
    <style>
    body, .reportview-container { background-color: #0d0f12; color:#e5e5e5; }
    .stButton>button { background-color:#1f6feb;color:white;border-radius:6px; }
    .stDownloadButton>button { background-color:#1f6feb;color:white;border-radius:6px; }
    .stTextInput>div>div>input { background:#181a1d;color:#fff;border:1px solid #333; }
    .stSelectbox>div>div { background:#181a1d;color:white;border:1px solid #333; }
    .stFileUploader { color:white; }
    </style>
    """,
    unsafe_allow_html=True
)

st.title("🚀 Real-Time AI Job Matching Dashboard")


# ----------------------------------------
# TOP SEARCH FORM
# ----------------------------------------
with st.container():
    st.markdown("## 🔎 Search & Scrape Jobs")

    left, right = st.columns([2, 1])

    # FORM
    with left:
        with st.form("search_form"):
            c1, c2 = st.columns(2)
            with c1:
                role = st.text_input("Job Title", "DevOps Engineer")
                location = st.text_input("Location (optional)")
                job_type = st.selectbox("Job Type", ["Any", "Intern", "Fresher", "Experienced"])

            with c2:
                min_salary = st.number_input("Min Salary ₹", min_value=0, value=0)
                max_salary = st.number_input("Max Salary ₹", min_value=0, value=500000)
                skills_input = st.text_input("Required Skills (comma separated)")

            keyword = st.text_input("Keyword in Description")
            recent_days = st.slider("Posted within (days)", 1, 30, 14)
            headless = st.checkbox("Run Browser Headless", True)

            submitted = st.form_submit_button("🔍 Start Scraping")

    # RESUME PARSER
    with right:
        st.markdown("### 📄 Upload Resume")
        uploaded_resume = st.file_uploader("PDF / DOCX", type=["pdf", "docx"])
        parsed_resume = None
        resume_text = ""

        if uploaded_resume:
            parsed_resume = parse_resume(uploaded_resume)
            resume_text = parsed_resume.get("raw_text", "")
            st.success("Resume Parsed!")
            st.write("Skills:", parsed_resume.get("skills"))
            st.write("AI Skills:", parsed_resume.get("ai_skills"))
            st.write("Suggestions:")
            st.info(parsed_resume.get("ai_suggestions", ""))


# ----------------------------------------
# SCRAPING
# ----------------------------------------
df = pd.DataFrame()

if submitted:
    st.info("⏳ Scraping in real time...")

    all_jobs = []

    try:
        all_jobs += realtime_internshala_scrape(role, headless=headless, recent_days=recent_days)
    except Exception as e:
        st.error(f"Internshala error: {e}")

    try:
        all_jobs += realtime_naukri_scrape(role, location, headless=headless, recent_days=recent_days)
    except Exception as e:
        st.error(f"Naukri error: {e}")

    if not all_jobs:
        st.warning("No jobs found.")
    else:
        df = pd.DataFrame(all_jobs)

        # BASIC FILTERS
        if job_type != "Any":
            df = df[df["title"].str.contains(job_type, case=False, na=False)]

        if location:
            df = df[df["description"].str.contains(location, case=False, na=False)]

        if keyword:
            df = df[df["description"].str.contains(keyword, case=False, na=False)]

        if skills_input:
            required = [x.strip().lower() for x in skills_input.split(",")]
            df = df[df["skills"].apply(lambda sl: all(r in [s.lower() for s in sl] for r in required))]

        st.success(f"🎉 {len(df)} jobs scraped!")


        # ----------------------------------------
        # AI MATCH SCORE
        # ----------------------------------------
        if resume_text:
            st.info("🤖 Calculating AI match scores...")
            scores, reasons = [], []

            for _, row in df.iterrows():
                job_text = f"{row['title']}\n{row['company']}\n{row['description']}"
                s, r = ai_match(job_text, resume_text)
                scores.append(s)
                reasons.append(r)

            df["ai_match_score"] = scores
            df["ai_match_reason"] = reasons

            df = df.sort_values("ai_match_score", ascending=False)


        # ----------------------------------------
        # ALL SCRAPED JOBS — TABLE
        # ----------------------------------------
        st.markdown("## 📋 All Scraped Jobs")

        safe_df = df.copy()
        st.dataframe(safe_df, use_container_width=True)

        st.download_button(
            "📥 Download All Jobs (Excel)",
            to_excel_bytes(df),
            "all_jobs.xlsx"
        )


        # ----------------------------------------
        # LINKEDIN-STYLE CARD GRID
        # ----------------------------------------
        st.markdown("## 🗂️ Grid View (LinkedIn Style)")

        cards_html = """
        <style>
        .card-grid {
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(330px, 1fr));
            grid-gap: 16px;
        }
        .card {
            background: #111418;
            border: 1px solid #333;
            padding: 16px;
            border-radius: 10px;
            color: white;
            box-shadow: 0 0 8px rgba(0,0,0,0.4);
        }
        .card h4 {
            margin: 0 0 6px 0;
            color: #4ea8ff;
        }
        .card small {
            color: #bbb;
        }
        .skill-tag {
            display:inline-block;
            margin:2px 4px 2px 0;
            padding:3px 8px;
            border-radius:10px;
            background:#1f2933;
            font-size:11px;
            border:1px solid #333;
            color:#e5e5e5;
        }
        </style>
        <div class="card-grid">
        """

        for _, r in df.head(50).iterrows():
            skills = "".join([f"<span class='skill-tag'>{s}</span>" for s in r['skills']])
            cards_html += f"""
            <div class="card">
                <h4>{r['title']}</h4>
                <small>{r['company']}</small><br>
                <small>Posted: {r['posted']}</small><br><br>
                <div>{skills}</div>
                <br>
                <a href="{r['link']}" target="_blank" style="color:#4ea8ff;">View Job ↗</a>
            </div>
            """

        cards_html += "</div>"
        st.components.v1.html(cards_html, height=900, scrolling=True)


        # ----------------------------------------
        # AI MATCHED JOBS
        # ----------------------------------------
        st.markdown("## 🤖 AI-Matched Jobs")

        if "ai_match_score" in df.columns:
            matched = df[df["ai_match_score"] > 0]
            st.dataframe(matched, use_container_width=True)

            st.download_button(
                "📥 Download Matched Jobs",
                to_excel_bytes(matched),
                "matched_jobs.xlsx"
            )

        # ----------------------------------------
        # JOB DETAILS
        # ----------------------------------------
        st.markdown("## 🔎 Job Details (Expandable)")

        for _, row in df.iterrows():
            with st.expander(f"{row['title']} — {row['company']}"):
                st.write("**Company:**", row["company"])
                st.write("**Posted:**", row["posted"])
                st.write("### Description")
                st.write(row["description"])
                st.write("### Skills")
                st.markdown(render_skill_tags(row["skills"]), unsafe_allow_html=True)
                st.write("### Link")
                st.write(row["link"])
# ----------------------------------------
# 🤖 AUTO APPLY (INTERN SHALA)
# ----------------------------------------

from scraper.auto_apply_internshala import batch_apply, save_cookies, load_cookies
import tempfile

st.markdown("## 🤖 Auto-Apply (Internshala)")

# Choose mode
apply_mode = st.radio(
    "Auto-Apply Mode",
    options=["Fully automatic (apply all)", "Semi-automatic (choose)"]
)

mode = "auto" if apply_mode.startswith("Fully") else "semi"

# --------------------------
# LOGIN OPTIONS — CREDENTIALS / COOKIES
# --------------------------
st.write("### Login Options")

col1, col2 = st.columns(2)

with col1:
    use_credentials = st.checkbox("Use email/password login")
    ai_email, ai_password = "", ""

    if use_credentials:
        ai_email = st.text_input("Internshala Email", key="auto_email")
        ai_password = st.text_input("Internshala Password", type="password", key="auto_pwd")

with col2:
    use_saved_cookies = st.checkbox("Use saved cookies (preferred)")
    cookie_path = st.text_input("Cookies File", value=".intern_cookies.json")

# --------------------------
# Applicant Form Details
# --------------------------
st.write("### Applicant Information")

name = st.text_input("Full Name")
phone = st.text_input("Phone Number")
email = st.text_input("Applicant Email", value=name and ai_email or "")
college = st.text_input("College / Institute")
linkedin = st.text_input("LinkedIn Profile URL")

resume_file = st.file_uploader("Upload Resume (PDF/DOCX)", type=["pdf", "docx"])

# --------------------------
# Build Job Links List
# --------------------------
job_links = []

if 'df' in locals() and not df.empty:

    if mode == "semi":
        st.write("### Select Jobs to Apply")

        selected_links = []
        for i, row in df.iterrows():
            chk = st.checkbox(
                f"{row['title']} — {row['company']}",
                key=f"apply_{i}"
            )
            if chk:
                selected_links.append(row['link'])

        job_links = df["link"].tolist()

    else:
        job_links = df["link"].tolist()

# Prepare applicant info dict
applicant_info = {
    "name": name,
    "email": email or ai_email,
    "phone": phone,
    "college": college,
    "linkedin": linkedin
}

if mode == "semi":
    applicant_info["apply_list"] = [
        row["link"] for i, row in df.iterrows()
        if st.session_state.get(f"apply_{i}", False)
    ]

# Save resume
resume_path = None
if resume_file:
    tmp = tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(resume_file.name)[1])
    tmp.write(resume_file.getvalue())
    tmp.flush()
    tmp.close()
    resume_path = tmp.name

# --------------------------
# RUN AUTO APPLY
# --------------------------
if st.button("🚀 Start Auto Apply"):

    credentials = None
    if use_credentials and ai_email and ai_password:
        credentials = {"email": ai_email, "password": ai_password}

    with st.spinner("Applying automatically — watch console…"):
        results = batch_apply(
            job_links=job_links,
            mode=mode,
            applicant_info=applicant_info,
            resume_path=resume_path,
            cookie_path=cookie_path if use_saved_cookies else None,
            credentials=credentials,
            headless=False   # GUI mode recommended for apply forms
        )

    st.success("Auto-apply process completed!")
    st.write(results)


# ----------------------------------------
# AI RESUME REWRITE
# ----------------------------------------
st.markdown("---")
st.header("✍️ AI Resume Rewrite")

if uploaded_resume:
    target_role = st.text_input("Target Role (optional)", role)

    if st.button("Rewrite Resume Summary"):
        if USE_GEMINI:
            try:
                prompt = f"""
                Rewrite resume summary in powerful ATS-friendly style.
                Target role: {target_role}
                Resume:
                {resume_text}
                """
                new = gemini_model.generate_content(prompt).text
                st.success("Rewritten Summary:")
                st.code(new)
            except Exception as e:
                st.error(f"Gemini error: {e}")
        else:
            st.warning("Gemini not available. Showing fallback.")
            st.code(f"{target_role} professional skilled in ...")

else:
    st.info("Upload a resume to enable rewriting.")

st.markdown("----")
st.write("Made with ❤️ — Fully Real-Time Scraper + AI Matcher + Grid UI")


# # ============================
# # main.py — SUPER FAST VERSION
# # ============================

# import os
# import io
# import re
# import json
# import streamlit as st
# import pandas as pd
# from typing import Tuple

# # -------------- NEW FAST SCRAPERS -------------------
# from scraper.internshala_api import internshala_api_scrape
# from scraper.naukri_api import naukri_api_scrape
# from scraper.indeed_scraper import indeed_scrape

# # Resume Parser
# from scraper.resume_parser import parse_resume


# # ----------------------------------------
# # OPTIONAL GEMINI AI SETUP
# # ----------------------------------------
# GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")
# USE_GEMINI = False
# gemini_model = None

# if GEMINI_API_KEY:
#     try:
#         import google.generativeai as genai
#         genai.configure(api_key=GEMINI_API_KEY)
#         gemini_model = genai.GenerativeModel("gemini-1.5-flash")
#         USE_GEMINI = True
#     except:
#         USE_GEMINI = False


# # ----------------------------------------
# # HELPERS
# # ----------------------------------------
# def to_excel_bytes(df: pd.DataFrame) -> bytes:
#     buf = io.BytesIO()
#     df.to_excel(buf, index=False, engine="openpyxl")
#     buf.seek(0)
#     return buf.read()


# def simple_tokenize(text: str):
#     """Basic tokenizer for fallback matching."""
#     text = re.sub(r"[^\w\s]", " ", text.lower())
#     return {w for w in text.split() if len(w) > 2}


# def fallback_match(job_text: str, resume_text: str):
#     jt = simple_tokenize(job_text)
#     rt = simple_tokenize(resume_text)

#     if not jt or not rt:
#         return 0, "No matching words."

#     inter = jt.intersection(rt)
#     score = int(len(inter) / max(len(jt.union(rt)), 1) * 100)
#     reason = f"Shared keywords: {', '.join(list(inter)[:6])}"

#     return score, reason


# def ai_match(job_text: str, resume_text: str) -> Tuple[int, str]:
#     """AI-Enhanced Match Score with Gemini (fallback to offline)."""

#     if USE_GEMINI and gemini_model:
#         try:
#             prompt = f"""
#             Compare this resume and job description.
#             Return JSON ONLY {{ "score": 0-100, "reason": "..." }}.

#             RESUME:
#             {resume_text}

#             JOB:
#             {job_text}
#             """

#             res = gemini_model.generate_content(prompt).text.strip()
#             m = re.search(r"\{.*\}", res, re.S)
#             if not m:
#                 raise ValueError()

#             obj = json.loads(m.group(0))
#             return int(obj["score"]), obj["reason"][:300]

#         except:
#             pass  # fallback

#     return fallback_match(job_text, resume_text)


# # ----------------------------------------
# # SKILL TAG RENDERER
# # ----------------------------------------
# def render_skill_tags(skills_list):
#     html = """
#     <style>
#     .chip {
#         display:inline-block;
#         padding:4px 10px;
#         border-radius:12px;
#         background:#2d2f34;
#         margin:2px;
#         color:#ddd;
#         font-size:12px;
#         border:1px solid #444;
#     }
#     </style>
#     """
#     if not skills_list:
#         return html + "<span class='chip'>No skills</span>"

#     chips = " ".join([f"<span class='chip'>{s}</span>" for s in skills_list])
#     return html + chips


# # ----------------------------------------
# # STREAMLIT UI SETTINGS
# # ----------------------------------------
# st.set_page_config(page_title="AI Job Matching Scraper", layout="wide")

# # WHITE TABLE TEXT FIX
# st.markdown("""
# <style>
# .stDataFrame tbody td, .stDataFrame th {
#     color: white !important;
# }

# table.dataframe, .dataframe th, .dataframe td {
#     color: white !important;
#     background-color: #0f1116 !important;
#     border: 1px solid #333 !important;
# }
# </style>
# """, unsafe_allow_html=True)

# # DARK UI
# st.markdown("""
# <style>
# body, .reportview-container { background-color: #0d0f12; color:#e5e5e5; }
# .stButton>button, .stDownloadButton>button {
#     background-color:#1f6feb;color:white;border-radius:6px;
# }
# .stTextInput>div>div>input, .stSelectbox>div>div {
#     background:#181a1d;color:white;border:1px solid #333;
# }
# </style>
# """, unsafe_allow_html=True)


# # ----------------------------------------
# # UI TITLE
# # ----------------------------------------
# st.title("🚀 AI Job Matching Dashboard — Ultra Fast Scraper (API Based)")


# # ----------------------------------------
# # SEARCH FORM + RESUME UPLOAD
# # ----------------------------------------
# with st.container():
#     st.markdown("## 🔎 Search & Scrape Jobs")

#     left, right = st.columns([2, 1])

#     with left:
#         with st.form("search_form"):
#             c1, c2 = st.columns(2)

#             with c1:
#                 role = st.text_input("Job Title", "DevOps Engineer")
#                 location = st.text_input("Location (optional)")
#                 job_type = st.selectbox("Job Type", ["Any", "Intern", "Fresher", "Experienced"])

#             with c2:
#                 min_salary = st.number_input("Min Salary ₹", min_value=0, value=0)
#                 max_salary = st.number_input("Max Salary ₹", min_value=0, value=500000)
#                 skills_input = st.text_input("Required Skills (comma separated)")

#             keyword = st.text_input("Keyword in Description")
#             recent_days = st.slider("Posted within (days)", 1, 30, 14)

#             submitted = st.form_submit_button("🔍 Start Scraping")

#     with right:
#         st.markdown("### 📄 Upload Resume")

#         uploaded_resume = st.file_uploader("PDF / DOCX", type=["pdf", "docx"])
#         parsed_resume = None
#         resume_text = ""

#         if uploaded_resume:
#             parsed_resume = parse_resume(uploaded_resume)
#             resume_text = parsed_resume.get("raw_text", "")

#             st.success("Resume Parsed!")
#             st.write("Skills:", parsed_resume.get("skills"))
#             st.write("AI Skills:", parsed_resume.get("ai_skills"))
#             st.info(parsed_resume.get("ai_suggestions", ""))


# # ----------------------------------------
# # SCRAPING SECTION
# # ----------------------------------------
# df = pd.DataFrame()

# if submitted:
#     st.info("⏳ Scraping jobs from all platforms...")

#     all_jobs = []

#     # NEW FAST SCRAPERS
#     try:
#         all_jobs += internshala_api_scrape(role, location, recent_days)
#     except Exception as e:
#         st.error(f"Internshala API error: {e}")

#     try:
#         all_jobs += naukri_api_scrape(role, location, recent_days)
#     except Exception as e:
#         st.error(f"Naukri API error: {e}")

#     try:
#         all_jobs += indeed_scrape(role, location, recent_days)
#     except Exception as e:
#         st.error(f"Indeed error: {e}")

#     if not all_jobs:
#         st.warning("No jobs found.")
#     else:
#         df = pd.DataFrame(all_jobs)

#         # Basic filters
#         if job_type != "Any":
#             df = df[df["title"].str.contains(job_type, case=False, na=False)]

#         if location:
#             df = df[df["description"].str.contains(location, case=False, na=False)]

#         if keyword:
#             df = df[df["description"].str.contains(keyword, case=False, na=False)]

#         if skills_input:
#             required = [x.strip().lower() for x in skills_input.split(",")]
#             df = df[df["skills"].apply(lambda sl: all(r in [s.lower() for s in sl] for r in required))]

#         st.success(f"🎉 {len(df)} jobs scraped successfully!")


#         # ----------------------------------------
#         # AI MATCH SCORE
#         # ----------------------------------------
#         if resume_text:
#             st.info("🤖 Calculating AI match scores...")

#             scores, reasons = [], []
#             for _, row in df.iterrows():
#                 job_text = f"{row['title']} {row['company']} {row['description']}"
#                 s, r = ai_match(job_text, resume_text)
#                 scores.append(s)
#                 reasons.append(r)

#             df["ai_match_score"] = scores
#             df["ai_match_reason"] = reasons

#             df = df.sort_values("ai_match_score", ascending=False)


#         # ----------------------------------------
#         # SHOW ALL JOBS — TABLE
#         # ----------------------------------------
#         st.markdown("## 📋 All Jobs")

#         st.dataframe(df, use_container_width=True)

#         st.download_button("📥 Download Excel", to_excel_bytes(df),
#                            "jobs.xlsx", mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")

#         # ----------------------------------------
#         # GRID VIEW (LINKEDIN STYLE)
#         # ----------------------------------------
#         st.markdown("## 🗂️ Grid View")

#         cards_html = """
#         <style>
#         .grid {
#             display:grid;
#             grid-template-columns:repeat(auto-fill, minmax(320px,1fr));
#             gap:16px;
#         }
#         .card {
#             background:#111418;
#             border:1px solid #333;
#             padding:16px;
#             border-radius:8px;
#             color:white;
#         }
#         .skill {
#             display:inline-block;
#             padding:4px 8px;
#             margin:2px;
#             background:#1f2933;
#             border-radius:8px;
#             font-size:11px;
#             border:1px solid #333;
#         }
#         </style>
#         <div class="grid">
#         """

#         for _, r in df.iterrows():
#             skills = "".join([f"<span class='skill'>{s}</span>" for s in r["skills"]])

#             cards_html += f"""
#             <div class="card">
#                 <h4>{r['title']}</h4>
#                 <small>{r['company']}</small><br>
#                 <small>Posted: {r['posted']}</small><br>
#                 <div>{skills}</div>
#                 <br>
#                 <a href="{r['link']}" target="_blank" style="color:#4ea8ff">Open Job ↗</a>
#             </div>
#             """

#         cards_html += "</div>"

#         st.components.v1.html(cards_html, height=900, scrolling=True)


#         # ----------------------------------------
#         # AI-MATCHED JOBS
#         # ----------------------------------------
#         st.markdown("## 🤖 AI Matched Jobs")

#         if "ai_match_score" in df.columns:
#             matched = df[df["ai_match_score"] > 0]
#             st.dataframe(matched, use_container_width=True)

#             st.download_button("📥 Download Matched", to_excel_bytes(matched),
#                                "matched_jobs.xlsx")


#         # ----------------------------------------
#         # JOB DETAILS
#         # ----------------------------------------
#         st.markdown("## 🔎 Job Details")

#         for _, row in df.iterrows():
#             with st.expander(f"{row['title']} — {row['company']}"):
#                 st.write("**Company:**", row["company"])
#                 st.write("**Posted:**", row["posted"])
#                 st.write("**Salary:**", row.get("salary", ""))
#                 st.write("**Description:**")
#                 st.write(row["description"])
#                 st.write("**Skills:**")
#                 st.markdown(render_skill_tags(row["skills"]), unsafe_allow_html=True)
#                 st.write("**Link:**", row["link"])


# # ----------------------------------------------------
# # AI RESUME REWRITE
# # ----------------------------------------------------
# st.markdown("---")
# st.header("✍️ AI Resume Rewrite")

# if uploaded_resume:
#     target_role = st.text_input("Target Role", role)

#     if st.button("Rewrite Resume Summary"):
#         if USE_GEMINI:
#             try:
#                 prompt = f"Rewrite resume summary for role {target_role}:\n{resume_text}"
#                 new = gemini_model.generate_content(prompt).text
#                 st.success("Your improved summary:")
#                 st.code(new)
#             except Exception as e:
#                 st.error(f"Gemini error: {e}")
#         else:
#             st.warning("Gemini not available. Using fallback.")
#             st.code(f"{target_role} professional experienced in multiple technologies...")

# else:
#     st.info("Upload a resume to enable rewriting.")

# st.markdown("----")
# st.write("Made with ❤️ — Fast API Scraper + AI Matching Dashboard")
