
import streamlit as st
import fitz
from fpdf import FPDF
import re
from io import BytesIO

def clean_text(text):
    text = text.lower()
    text = re.sub(r'[^a-zA-Z0-9\s]', '', text)
    return text

def extract_keywords(jd_text):
    jd_text = clean_text(jd_text)
    keywords = list(set(jd_text.split()))
    exclusions = {'and', 'or', 'the', 'a', 'an', 'in', 'on', 'with', 'for', 'to', 'of', 'at', 'by', 'as', 'is', 'are'}
    keywords = [word for word in keywords if word not in exclusions and len(word) > 2]
    return keywords

def read_resume(file):
    doc = fitz.open(stream=file.read(), filetype="pdf")
    text = ""
    for page in doc:
        text += page.get_text()
    return text

def modify_resume(base_text, keywords):
    base_text= base_text.encode('utf-8', 'ignore').decode('utf-8')
    updated_text = base_text
    skills_pattern = re.compile(r"(SKILLS\s*[\s\S]*?)(AWARDS|CERTIFICATIONS|PROJECTS|EXPERIENCE)", re.IGNORECASE)
    skills_match = skills_pattern.search(updated_text)
    if skills_match:
        skills_text = skills_match.group(1)
        for keyword in keywords:
            if keyword not in clean_text(skills_text):
                skills_text += f", {keyword.upper()}"
        updated_text = updated_text.replace(skills_match.group(1), skills_text)

    experience_pattern = re.compile(r"(WORK EXPERIENCE\s*[\s\S]*)", re.IGNORECASE)
    experience_match = experience_pattern.search(updated_text)
    if experience_match:
        exp_text = experience_match.group(1)
        exp_lines = exp_text.split('\n')
        new_exp_lines = []
        for line in exp_lines:
            if '-' in line and len(line.strip()) > 10:
                line_keywords = set(clean_text(line).split())
                missing_keywords = [kw for kw in keywords if kw not in line_keywords]
                if missing_keywords:
                    for kw in missing_keywords[:1]:
                        if '(' not in line:
                            line += f" ({kw.upper()})"
            new_exp_lines.append(line)
        updated_exp_text = '\n'.join(new_exp_lines)
        updated_text = updated_text.replace(exp_text, updated_exp_text)

    return updated_text

def save_to_pdf(text):
    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_page()
    pdf.set_font("Arial", size=12)
    for line in text.split('\n'):
        line = line.encode('latin-1', 'ignore').decode('latin-1')
        pdf.cell(0, 10, txt=line.strip(), ln=True)
    pdf_bytes = pdf.output(dest='S').encode('latin-1')
    output = BytesIO(pdf_bytes)
    return output

st.title("Smart Resume Builder")
st.subheader("Tailor your resume instantly for any job description!")

uploaded_resume = st.file_uploader("Upload your Resume (PDF)", type=["pdf"])
jd_text = st.text_area("Paste Job Description Here")

if st.button("Customize Resume"):
    if uploaded_resume is not None and jd_text.strip() != "":
        base_text = read_resume(uploaded_resume)
        keywords = extract_keywords(jd_text)
        modified_text = modify_resume(base_text, keywords)
        pdf_output = save_to_pdf(modified_text)
        st.success("Resume customized successfully!")
        st.download_button(label="Download Updated Resume", data=pdf_output, file_name="Updated_Resume.pdf", mime="application/pdf")
    else:
        st.error("Please upload a resume and paste a job description.")
