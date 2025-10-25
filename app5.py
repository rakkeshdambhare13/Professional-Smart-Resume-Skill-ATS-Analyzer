import re                              # For text cleaning & pattern matching (regular expressions)
import streamlit as st                 # To create the user interface for the web app
from PyPDF2 import PdfReader           # To extract text from PDF files
from docx import Document              # To read Microsoft Word (.docx) files
import google.generativeai as genai    # For connecting and communicating with Gemini AI

# ---------------- Gemini API Setup (ATS connect with Gemini API) ----------------
genai.configure(api_key="AIzaSyDUmxHV0f4yyZSb7-LHDtvADtIaWq2Bwek")

def get_gemini_response(prompt):
    """Send prompt to Gemini Pro model and return response text."""
    model = genai.GenerativeModel('gemini-2.5-pro')
    response = model.generate_content(prompt)
    return response.text

# ---------------- File Readers (reading files: PDF, TXT, DOCX) ----------------
def read_pdf(file):
    text = ""
    reader = PdfReader(file)
    for page in reader.pages:
        if page.extract_text():                # Extracts readable text from each PDF page
            text += page.extract_text() + " "
    return text.strip()

def read_txt(file):
    return file.read().decode("utf-8")         # Decodes bytes into readable string (UTF-8 format)

def read_docx(file):
    doc = Document(file)
    text = ""
    for para in doc.paragraphs:
        text += para.text + " "                # Combines all paragraphs into one string
    return text.strip()

# ---------------- Text Cleaner ----------------
def clean_text(text):
    text = text.lower()
    text = re.sub(r'[^a-z\s]', ' ', text)      # Removes all non-letter characters, keeps spaces
    return text.split()                        # Splits text into individual words

# ---------------- ATS Score Calculator ----------------
def calculate_ats_score(resume_text, required_skills):
    """
    Compares resume words with required skills and calculates ATS score.
    """
    resume_words = set(clean_text(resume_text))      # Convert resume words to set (no duplicates)
    required_skills = set(map(str.lower, required_skills))  # Lowercase skills for case-insensitive match

    matched = required_skills & resume_words         # Common words between resume and job description
    missing = required_skills - resume_words         # Skills not found in the resume
    score = (len(matched) / len(required_skills) * 100) if required_skills else 0
    return round(score, 2), matched, missing

# ---------------- Gemini Prompt Builder (for Skills Only) ----------------
def construct_skills_prompt(resume, job_description):
    return f"""
    Act as a professional HR and ATS evaluator.
    Compare the resume below with the job description.
    Identify and list:
    1️⃣ Skills present in the resume that match the job description.
    2️⃣ Important or missing skills required by the job but not found in the resume.
    Keep the output clear and formatted for easy reading.

    Resume:
    {resume}

    Job Description:
    {job_description}
    """

# ---------------- Streamlit App (UI for uploading & analyzing resumes) ----------------
st.set_page_config(page_title="Gemini Skill & ATS Analyzer", page_icon="🧠")
st.title("🧠 Professional Smart Resume Skill & ATS Analyzer")

uploaded_file = st.file_uploader("📄 Upload Resume (PDF/TXT/DOCX)", type=["pdf", "txt", "docx"])
job_description = st.text_area("💼 Paste the Job Description Here")

if uploaded_file and job_description:
    # Read uploaded resume
    if uploaded_file.name.endswith(".pdf"):
        resume_text = read_pdf(uploaded_file)
    elif uploaded_file.name.endswith(".txt"):
        resume_text = read_txt(uploaded_file)
    elif uploaded_file.name.endswith(".docx"):
        resume_text = read_docx(uploaded_file)
    else:
        st.error("Unsupported file type!")
        st.stop()

    # Build Gemini prompt
    skills_prompt = construct_skills_prompt(resume_text, job_description)

    # Get response from Gemini
    with st.spinner("🔍 Analyzing skills with Gemini Pro..."):
        skills_response = get_gemini_response(skills_prompt)

    # Extract skills for ATS scoring (basic heuristic: split by commas/newlines)
    required_skills = re.findall(r'\b[a-zA-Z]+\b', job_description)

    # Calculate ATS score
    score, matched, missing = calculate_ats_score(resume_text, required_skills)

    # Display Results
    st.subheader("✅ Skill Analysis Result (Gemini)")
    st.write(skills_response.strip())

    st.subheader("📊 ATS Match Score")
    st.write(f"**ATS Score:** {score}%")

    st.write("✅ **Matched Skills:**", ", ".join(matched) if matched else "None")
    st.write("❌ **Missing Skills:**", ", ".join(missing) if missing else "None")

    # Optional: Download Report
    st.download_button(
        label="⬇️ Download Skill & ATS Report",
        data=f"ATS Score: {score}%\nMatched: {', '.join(matched)}\nMissing: {', '.join(missing)}\n\nGemini Analysis:\n{skills_response.strip()}",
        file_name="ATS_Skill_Analysis_Report.txt",
        mime="text/plain"
    )
