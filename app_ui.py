# app.py
import streamlit as st
from io import BytesIO
import pdfplumber
import docx
import re
from PIL import Image
import pytesseract
import spacy
from sentence_transformers import SentenceTransformer, util
import yake
import textstat
import math
import matplotlib.pyplot as plt

st.set_page_config(page_title="AI Resume Analyzer — Pro", layout="wide")

# ---------------------------
# Cached model loading
# ---------------------------
@st.cache_resource(show_spinner=False)
def load_resources():
    nlp = spacy.load("en_core_web_sm")
    embedder = SentenceTransformer("all-MiniLM-L6-v2")  # fast & good
    kw = yake.KeywordExtractor(lan="en", n=1, top=40)
    return nlp, embedder, kw

nlp, embedder, kw_extractor = load_resources()

# ---------------------------
# Utils: text extraction
# ---------------------------
def extract_text_pdf(file_bytes):
    text = []
    with pdfplumber.open(BytesIO(file_bytes)) as pdf:
        for page in pdf.pages:
            p = page.extract_text() or ""
            text.append(p)
    return "\n".join(text)

def extract_text_docx(file_bytes):
    doc = docx.Document(BytesIO(file_bytes))
    return "\n".join([p.text for p in doc.paragraphs])

def extract_text_image(file_bytes):
    image = Image.open(BytesIO(file_bytes))
    return pytesseract.image_to_string(image)

def extract_text_generic(up_file):
    name = up_file.name.lower()
    b = up_file.read()
    if name.endswith(".pdf"):
        return extract_text_pdf(b)
    elif name.endswith(".docx"):
        return extract_text_docx(b)
    elif name.endswith(".txt"):
        try:
            return b.decode('utf-8', errors='ignore')
        except:
            return str(b)
    elif any(name.endswith(ext) for ext in (".png",".jpg",".jpeg","bmp","tiff")):
        return extract_text_image(b)
    else:
        return ""

# ---------------------------
# NLP helpers
# ---------------------------
def extract_skills(text, top_k=20):
    keywords = kw_extractor.extract_keywords(text)
    skills = [k for k,score in keywords]
    # clean up, split phrases, dedupe
    cleaned = []
    seen = set()
    for s in skills:
        parts = re.split(r'[,\n;/\|]', s)
        for p in parts:
            token = p.strip()
            if len(token) > 1 and token.lower() not in seen:
                seen.add(token.lower())
                cleaned.append(token)
    return cleaned[:top_k]

def extract_entities(text):
    doc = nlp(text)
    ents = {"ORG": [], "GPE": [], "PERSON": [], "DATE": []}
    for e in doc.ents:
        if e.label_ in ents:
            ents[e.label_].append(e.text)
    # dedupe
    for k in ents:
        ents[k] = list(dict.fromkeys(ents[k]))
    return ents

def estimate_experience_years(text):
    # Look for patterns like "5 years", "3+ years", "2018 - 2022"
    yrs = []
    for m in re.finditer(r'(\d{1,2})\s*\+?\s*(?:years|yrs)\b', text, flags=re.I):
        yrs.append(int(m.group(1)))
    # date ranges -> compute differences, prefer recent ranges
    for m in re.finditer(r'(\b(19|20)\d{2})\s*[-–to]{1,3}\s*((19|20)\d{2}\b)', text):
        try:
            start = int(m.group(1)); end = int(m.group(3))
            if end >= start:
                yrs.append(end - start)
        except:
            pass
    if yrs:
        # heuristic: take max mentioned years (candidate's total experience)
        return max(yrs)
    return 0

def passive_sentence_fraction(text):
    doc = nlp(text)
    total = 0
    passive = 0
    for sent in doc.sents:
        total += 1
        # heuristic: look for 'auxpass' or 'nsubjpass' dependency tokens
        if any(tok.dep_ in ("auxpass","nsubjpass") for tok in sent):
            passive += 1
        # or existence of 'was|were|is|are|been' + VBN form
        elif re.search(r'\b(was|were|is|are|been|be)\b', sent.text, flags=re.I) and any(tok.tag_ == "VBN" for tok in sent):
            passive += 1
    return (passive / total) if total>0 else 0

def readability_score(text):
    # textstat returns Flesch Reading Ease (0-100). Map to 0-1
    try:
        score = textstat.flesch_reading_ease(text)
    except:
        score = 50.0
    # clamp and normalize: 0 -> worst, 100 -> best
    score = max(min(score,100),0)
    return score/100.0

# ---------------------------
# Similarity / scoring
# ---------------------------
def embedding_similarity(a_text, b_text):
    # returns cosine similarity (0..1)
    a = embedder.encode(a_text, convert_to_tensor=True)
    b = embedder.encode(b_text, convert_to_tensor=True)
    sim = util.pytorch_cos_sim(a,b).item()
    # cosine may be -1..1; map to 0..1
    return (sim + 1) / 2

def compute_scores(resume_text, jd_text=None, weights=None):
    if weights is None:
        # default weights: Technical Skills 40%, Experience 30%, Readability+Grammar 20%, JD relevance 10%
        weights = {"skills":0.4, "experience":0.3, "grammar":0.2, "jd":0.1}
    # Skill score: how many top skills are strong tokens (heuristic: count extracted keywords)
    skills = extract_skills(resume_text, top_k=30)
    skill_score = min(len(skills)/15.0, 1.0)  # 15+ skills => full marks

    # Experience score: map years to 0..1 (0->0, 5 years->0.5, 10+ ->1)
    years = estimate_experience_years(resume_text)
    exp_score = min(years / 10.0, 1.0)

    # Grammar/readability: combine readability and passive sentence fraction
    read = readability_score(resume_text)
    passive_frac = passive_sentence_fraction(resume_text)
    grammar_score = read * (1 - passive_frac)  # penalize passive voice

    # JD similarity
    jd_score = 0.0
    if jd_text and jd_text.strip():
        try:
            jd_score = embedding_similarity(resume_text, jd_text)
        except Exception:
            jd_score = 0.0

    # If no JD provided, redistribute jd weight proportionally to other buckets
    if not jd_text or not jd_text.strip():
        total_no_jd = weights["skills"] + weights["experience"] + weights["grammar"]
        # normalize remaining weights
        normalized = {
            "skills": weights["skills"]/total_no_jd,
            "experience": weights["experience"]/total_no_jd,
            "grammar": weights["grammar"]/total_no_jd
        }
        final_score = (skill_score * normalized["skills"] +
                       exp_score * normalized["experience"] +
                       grammar_score * normalized["grammar"])
    else:
        final_score = (skill_score * weights["skills"] +
                       exp_score * weights["experience"] +
                       grammar_score * weights["grammar"] +
                       jd_score * weights["jd"])

    # round components
    return {
        "overall": round(float(final_score), 3),
        "skills": round(float(skill_score),3),
        "experience": round(float(exp_score),3),
        "grammar": round(float(grammar_score),3),
        "jd": round(float(jd_score),3),
        "years": years,
        "skills_list": skills
    }

# ---------------------------
# Streamlit UI
# ---------------------------
st.title("AI Resume Analyzer — Pro (Streamlit)")
st.write("Upload resumes (PDF/DOCX/TXT/Image). Paste Job Description to compare. Advanced scoring with embeddings and heuristics.")

col1, col2 = st.columns([1,2])
with col1:
    uploaded = st.file_uploader("Upload one or more resumes", type=['pdf','docx','txt','png','jpg','jpeg'], accept_multiple_files=True)
    jd_text = st.text_area("Optional: Paste Job Description (JD) here", height=200)
    st.markdown("**Scoring weights (editable):**")
    w_skills = st.slider("Technical Skills weight", 0.0, 0.8, 0.4, 0.05)
    w_exp = st.slider("Experience weight", 0.0, 0.8, 0.3, 0.05)
    w_grammar = st.slider("Grammar/Readability weight", 0.0, 0.8, 0.2, 0.05)
    w_jd = st.slider("JD relevance weight", 0.0, 0.4, 0.1, 0.05)
    analyze = st.button("Analyze Resumes")

with col2:
    st.info("Tip: For best JD-matching, paste the full job description (responsibilities + key skills).")

if uploaded and analyze:
    resumes = []
    with st.spinner("Extracting & analyzing..."):
        for file in uploaded:
            txt = extract_text_generic(file)
            if not txt.strip():
                st.error(f"No text extracted from {file.name}. If resume is image-based, enable OCR or upload a better scan.")
                continue
            ents = extract_entities(txt)
            sco = compute_scores(txt, jd_text, weights={"skills":w_skills,"experience":w_exp,"grammar":w_grammar,"jd":w_jd})
            resumes.append({
                "name": file.name,
                "text": txt,
                "entities": ents,
                "scores": sco
            })

    if not resumes:
        st.warning("No usable resumes processed.")
    else:
        # ranking if JD given (use overall score)
        resumes = sorted(resumes, key=lambda r: r["scores"]["overall"], reverse=True)

        # show leaderboard
        st.subheader("Resume Rankings")
        names = [r["name"] for r in resumes]
        scores = [r["scores"]["overall"] for r in resumes]
        fig, ax = plt.subplots(figsize=(6, max(2, len(names)*0.6)))
        ax.barh(names[::-1], scores[::-1])
        ax.set_xlabel("Overall Score (0-1)")
        ax.set_xlim(0,1)
        st.pyplot(fig)

        # show detailed cards
        for r in resumes:
            st.markdown("---")
            st.subheader(r["name"])
            sc = r["scores"]
            c1, c2, c3 = st.columns([1,2,2])
            with c1:
                st.metric("Overall", f"{sc['overall']*100:.1f}%")
                st.write(f"Years exp (estimated): **{sc['years']}**")
            with c2:
                st.write("**Score breakdown**")
                st.write(f"- Skills: {sc['skills']*100:.0f}%")
                st.write(f"- Experience: {sc['experience']*100:.0f}%")
                st.write(f"- Grammar/Readability: {sc['grammar']*100:.0f}%")
                if jd_text.strip():
                    st.write(f"- JD relevance: {sc['jd']*100:.0f}%")
            with c3:
                st.write("**Top extracted skills**")
                st.write(", ".join(sc['skills_list'][:20]) if sc['skills_list'] else "No skills found")

            st.write("**Sample entities (ORG / GPE / DATE):**")
            st.write(r["entities"])
            with st.expander("Show extracted full text"):
                st.text_area("Extracted text", value=r["text"][:20000], height=300)

            # suggestions (basic heuristics)
            st.write("**Suggestions:**")
            sugg = []
            if sc['skills'] < 0.5:
                sugg.append("- Add/expand a dedicated 'Skills' section with role-specific keywords (e.g., 'Python', 'SQL', 'TensorFlow').")
            if sc['experience'] < 0.4:
                sugg.append("- Emphasize measurable projects & responsibilities; quantify achievements (e.g., 'reduced X by 20%').")
            if sc['grammar'] < 0.5:
                sugg.append("- Improve readability: shorter sentences, active voice; fix grammar/spelling issues.")
            if jd_text.strip() and sc['jd'] < 0.4:
                sugg.append("- Tailor resume to the JD: include keywords & responsibilities mentioned in the job posting.")
            if not sugg:
                sugg.append("- Resume looks strong; consider custom tailoring per role.")
            for s in sugg:
                st.write(s)

st.markdown("---")
st.write("Built with spaCy, YAKE, sentence-transformers. Want CSV export of scores, or integration with ATS? Ask and I’ll add it.")