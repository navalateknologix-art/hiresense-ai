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

uploaded_resume = st.file_uploader(
    "Upload Resume",
    type=["pdf"]
)

# -----------------------------
# JOB DESCRIPTION
# -----------------------------

job_description = st.text_area(
    "Paste Job Description",
    height=200
)

# -----------------------------
# PROCESS RESUME
# -----------------------------

if uploaded_resume:

    resume_text = extract_text_from_pdf(uploaded_resume)

    st.subheader("Extracted Resume Text")

    st.text_area(
        "Resume Content",
        resume_text,
        height=300
    )

    # -----------------------------
    # ANALYZE BUTTON
    # -----------------------------

    if st.button("Analyze Candidate"):

        with st.spinner("Analyzing candidate..."):

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
            # ANALYTICS EVENT
            # -----------------------------

            posthog.capture(
                "anonymous_user",
                "resume_analysis_completed"
            )

            # -----------------------------
            # MATCH SCORE EXTRACTION
            # -----------------------------

            match = re.search(r"Match Score:\s*(\d+)", result)

            if match:
                score = int(match.group(1))
            else:
                score = 0

            # -----------------------------
            # RESULTS UI
            # -----------------------------

            st.subheader("📊 AI Candidate Analysis")

            st.metric(
                "Match Score",
                f"{score}/100"
            )

            # -----------------------------
            # SCORE CATEGORY
            # -----------------------------

            if score >= 80:
                st.success("✅ Strong Match")

            elif score >= 60:
                st.warning("⚠️ Moderate Match")

            else:
                st.error("❌ Weak Match")

            # -----------------------------
            # DISPLAY RESULT
            # -----------------------------

            st.write(result)

            # -----------------------------
            # EXPORT TO EXCEL
            # -----------------------------

            candidate_data = {
                "Match Score": [score],
                "Analysis": [result]
            }

            df = pd.DataFrame(candidate_data)

            excel_file = "candidate_analysis.xlsx"

            df.to_excel(
                excel_file,
                index=False
            )

            with open(excel_file, "rb") as file:
                st.download_button(
                    label="📥 Download Analysis Report",
                    data=file,
                    file_name="candidate_analysis.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                )