import streamlit as st
import pdfplumber
from groq import Groq
import pandas as pd
import re
from posthog import Posthog

# -----------------------------
# PAGE CONFIG
# -----------------------------

st.set_page_config(
    page_title="HireSense AI",
    layout="wide"
)

# -----------------------------
# ANALYTICS
# -----------------------------

posthog = Posthog(
    project_api_key=st.secrets["POSTHOG_API_KEY"],
    host="https://app.posthog.com"
)

posthog.capture(
    "anonymous_user",
    "app_opened"
)

# -----------------------------
# GROQ CLIENT
# -----------------------------

client = Groq(
    api_key=st.secrets["GROQ_API_KEY"]
)

# -----------------------------
# APP HEADER
# -----------------------------

st.title("🚀 HireSense AI")
st.subheader("AI-Powered Resume Screening Tool")

st.info(
    "This MVP is for testing purposes only. Please avoid uploading highly sensitive candidate data."
)

# -----------------------------
# PDF TEXT EXTRACTION
# -----------------------------

def extract_text_from_pdf(file):
    text = ""

    with pdfplumber.open(file) as pdf:
        for page in pdf.pages:
            extracted = page.extract_text()

            if extracted:
                text += extracted + "\n"

    return text

# -----------------------------
# FILE UPLOAD
# -----------------------------

uploaded_resumes = st.file_uploader(
    "Upload Resumes",
    type=["pdf"],
    accept_multiple_files=True
)

# -----------------------------
# JOB DESCRIPTION
# -----------------------------

job_description = st.text_area(
    "Paste Job Description",
    height=200
)

# -----------------------------
# ANALYZE RESUMES
# -----------------------------

if uploaded_resumes and job_description:

    if st.button("Analyze All Candidates"):

        all_candidates = []

        for uploaded_resume in uploaded_resumes:

            with st.spinner(f"Analyzing {uploaded_resume.name}..."):

                # -----------------------------
                # EXTRACT RESUME TEXT
                # -----------------------------

                resume_text = extract_text_from_pdf(uploaded_resume)

                # -----------------------------
                # AI PROMPT
                # -----------------------------

                prompt = f"""
Analyze this resume against the job description.

Resume:
{resume_text}

Job Description:
{job_description}

Return STRICTLY in this exact format:

Candidate Summary:
<summary>

Matching Skills:
<comma separated skills>

Missing Skills:
<comma separated missing skills>

Experience Level:
<experience>

Match Score:
<number between 0 and 100>

Rules:
- Match Score MUST always exist
- Match Score MUST only be numeric
- Do not skip any section
"""

                # -----------------------------
                # GROQ API CALL
                # -----------------------------

                response = client.chat.completions.create(
                    model="llama-3.1-8b-instant",
                    messages=[
                        {
                            "role": "user",
                            "content": prompt
                        }
                    ],
                    temperature=0.3
                )

                result = response.choices[0].message.content

                # -----------------------------
                # TRACK ANALYTICS
                # -----------------------------

                posthog.capture(
                    "anonymous_user",
                    "resume_analysis_completed"
                )

                # -----------------------------
                # EXTRACT MATCH SCORE
                # -----------------------------

                match = re.search(
                    r"Match Score:\s*(\d+)",
                    result
                )

                if match:
                    score = int(match.group(1))
                else:
                    score = 0

                # -----------------------------
                # STORE CANDIDATE DATA
                # -----------------------------

                all_candidates.append({
                    "Candidate": uploaded_resume.name,
                    "Match Score": score,
                    "Analysis": result
                })

        # -----------------------------
        # SORT CANDIDATES
        # -----------------------------

        sorted_candidates = sorted(
            all_candidates,
            key=lambda x: x["Match Score"],
            reverse=True
        )

        # -----------------------------
        # DISPLAY RESULTS
        # -----------------------------

        st.subheader("🏆 Candidate Rankings")

        for candidate in sorted_candidates:

            st.divider()

            st.subheader(candidate["Candidate"])

            st.metric(
                "Match Score",
                f'{candidate["Match Score"]}/100'
            )

            # -----------------------------
            # SCORE CATEGORY
            # -----------------------------

            if candidate["Match Score"] >= 80:
                st.success("✅ Strong Match")

            elif candidate["Match Score"] >= 60:
                st.warning("⚠️ Moderate Match")

            else:
                st.error("❌ Weak Match")

            st.write(candidate["Analysis"])

        # -----------------------------
        # EXPORT TO EXCEL
        # -----------------------------

        ranking_df = pd.DataFrame(sorted_candidates)

        excel_file = "candidate_rankings.xlsx"

        ranking_df.to_excel(
            excel_file,
            index=False
        )

        # -----------------------------
        # DOWNLOAD BUTTON
        # -----------------------------

        with open(excel_file, "rb") as file:

            st.download_button(
                label="📥 Download Candidate Rankings",
                data=file,
                file_name="candidate_rankings.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )