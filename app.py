import streamlit as st
import pdfplumber
import pandas as pd
from groq import Groq
from dotenv import load_dotenv
import os

# -----------------------------------
# LOAD ENV
# -----------------------------------

load_dotenv()

client = Groq(
    api_key=os.getenv("GROQ_API_KEY")
)

# -----------------------------------
# PAGE CONFIG
# -----------------------------------

st.set_page_config(
    page_title="HireSense AI",
    page_icon="📄",
    layout="wide"
)

# -----------------------------------
# HEADER
# -----------------------------------

st.title("📄 HireSense AI")
st.subheader("AI-Powered Resume Screening Tool")

st.markdown("""
Upload multiple resumes and compare candidates against a Job Description using AI.
""")

# -----------------------------------
# PDF TEXT EXTRACTION
# -----------------------------------

def extract_text_from_pdf(file):

    text = ""

    with pdfplumber.open(file) as pdf:

        for page in pdf.pages:

            extracted = page.extract_text()

            if extracted:
                text += extracted + "\n"

    return text

# -----------------------------------
# SIDEBAR
# -----------------------------------

st.sidebar.header("Instructions")

st.sidebar.markdown("""
1. Upload resumes
2. Paste Job Description
3. Click Analyze
4. Download Excel report
""")

# -----------------------------------
# FILE UPLOAD
# -----------------------------------

uploaded_resumes = st.file_uploader(
    "Upload Candidate Resumes",
    type=["pdf"],
    accept_multiple_files=True
)

# -----------------------------------
# JOB DESCRIPTION
# -----------------------------------

job_description = st.text_area(
    "Paste Job Description",
    height=250
)

# -----------------------------------
# ANALYZE BUTTON
# -----------------------------------

if uploaded_resumes and job_description:

    if st.button("🚀 Analyze Candidates"):

        results = []

        progress_bar = st.progress(0)

        for index, uploaded_resume in enumerate(uploaded_resumes):

            with st.spinner(f"Analyzing {uploaded_resume.name}..."):

                try:

                    # Extract Resume Text
                    resume_text = extract_text_from_pdf(uploaded_resume)

                    # Limit text size
                    resume_text = resume_text[:4000]

                    prompt = f"""
                    Analyze this resume against the job description.

                    Resume:
                    {resume_text}

                    Job Description:
                    {job_description}

                    Return ONLY:

                    Match Score: X/100
                    Matching Skills:
                    Missing Skills:
                    Experience Level:
                    Recruiter Summary:
                    """

                    completion = client.chat.completions.create(
                        model="llama-3.1-8b-instant",
                        messages=[
                            {
                                "role": "user",
                                "content": prompt
                            }
                        ],
                        temperature=0.3
                    )

                    result = completion.choices[0].message.content

                    results.append({
                        "Candidate": uploaded_resume.name,
                        "AI Analysis": result
                    })

                except Exception as e:

                    results.append({
                        "Candidate": uploaded_resume.name,
                        "AI Analysis": f"Error: {str(e)}"
                    })

            progress_bar.progress((index + 1) / len(uploaded_resumes))

        # -----------------------------------
        # RESULTS TABLE
        # -----------------------------------

        st.success("Analysis Completed")

        df = pd.DataFrame(results)

        st.subheader("Candidate Analysis Results")

        st.dataframe(df)

        # -----------------------------------
        # DOWNLOAD EXCEL
        # -----------------------------------

        excel_file = "candidate_analysis.xlsx"

        df.to_excel(excel_file, index=False)

        with open(excel_file, "rb") as file:

            st.download_button(
                label="📥 Download Excel Report",
                data=file,
                file_name="candidate_analysis.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )

# -----------------------------------
# FOOTER
# -----------------------------------

st.markdown("---")

st.caption("Built using Streamlit + Groq AI")