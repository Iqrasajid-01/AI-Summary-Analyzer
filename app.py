import streamlit as st
import pdfplumber
from streamlit_lottie import st_lottie
import requests
import time
import re
import json
from datetime import datetime
from parser import parse_resume, find_sections, extract_section_content
from collections import Counter

# ---------- Config ----------
SKILLS_KEYWORDS = {
    'Technical': ["Python", "Java", "C++", "JavaScript", "SQL", "TensorFlow", "PyTorch", "Keras",
                  "Machine Learning", "Deep Learning", "AI", "NLP", "Computer Vision",
                  "Pandas", "NumPy", "Scikit-learn", "Git", "Docker", "AWS", "Azure"],
    'Web': ["HTML", "CSS", "React", "Angular", "Vue", "Django", "Flask", "Node.js", "REST API"],
    'Soft Skills': ["Project Management", "Leadership", "Teamwork", "Communication",
                    "Critical Thinking", "Time Management", "Problem Solving", "Agile"]
}

INDUSTRY_KEYWORDS = {
    "Software Engineering": ["software", "development", "coding", "programming", "architecture", "system design"],
    "Data Science": ["data", "analytics", "statistics", "modeling", "insights", "visualization"],
    "DevOps": ["ci/cd", "deployment", "automation", "infrastructure", "kubernetes", "monitoring"],
    "Frontend": ["ui", "ux", "frontend", "responsive", "accessibility", "user interface"],
    "Backend": ["api", "database", "server", "backend", "microservices", "scalability"],
    "Management": ["team", "leadership", "strategy", "planning", "coordination", "stakeholder"],
}

ACTION_VERBS = [
    "achieved", "accomplished", "created", "designed", "developed", "engineered", "implemented",
    "improved", "increased", "led", "managed", "optimized", "reduced", "spearheaded", "built",
    "launched", "transformed", "delivered", "executed", "facilitated", "generated", "initiated"
]

def load_lottie(url):
    try:
        return requests.get(url).json()
    except:
        return None

# ---------- Streamlit Config ----------
st.set_page_config(
    page_title="🧠 AI Resume Analyzer Pro",
    page_icon="🧠",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ---------- Session State ----------
if 'uploaded_resumes' not in st.session_state:
    st.session_state.uploaded_resumes = []
if 'jd_text' not in st.session_state:
    st.session_state.jd_text = ""

# ---------- Sidebar ----------
with st.sidebar:
    st.markdown("### ⚙️ Settings")
    
    theme = st.radio(
        "🎨 Theme",
        options=["Ocean", "Sunset", "Forest", "Midnight"],
        index=0,
        horizontal=True
    )
    
    st.markdown("---")
    st.markdown("### 🎯 Industry Focus")
    industry = st.selectbox(
        "Select Industry",
        options=["General", "Software Engineering", "Data Science", "DevOps", "Frontend", "Backend", "Management"],
        index=0
    )
    
    st.markdown("---")
    st.markdown("### 📊 Analysis Options")
    show_raw = st.checkbox("📜 Show Raw Text", value=False)
    show_debug = st.checkbox("🐛 Debug Info", value=False)
    show_keyword_density = st.checkbox("📊 Show Keyword Density", value=False)
    
    st.markdown("---")
    
    # Resume comparison
    st.markdown("### 📁 Resume Comparison")
    if len(st.session_state.uploaded_resumes) > 0:
        st.success(f"✅ {len(st.session_state.uploaded_resumes)} resume(s) stored")
        if st.button("🗑️ Clear All Resumes"):
            st.session_state.uploaded_resumes = []
            st.rerun()
    else:
        st.info("Upload resumes to compare them")
    
    st.markdown("---")
    st.info("💡 **Tip:** Upload a PDF resume to get started.")

# ---------- Theme CSS ----------
themes = {
    "Ocean": {
        "bg_color": "#f0f4f8", "card_bg": "#ffffff", "text_primary": "#1a202c",
        "text_secondary": "#4a5568", "accent_color": "#0077b6", "accent_light": "#00b4d8",
        "border_color": "#cbd5e0",
        "header_gradient": "linear-gradient(135deg, #0077b6 0%, #00b4d8 50%, #90e0ef 100%)",
        "score_card_gradient": "linear-gradient(135deg, #0077b6 0%, #00b4d8 100%)",
        "metric_bg": "#e8f4f8", "suggestion_bg": "#fff5f5", "success_bg": "#e6fffa",
        "skill_gradient": "linear-gradient(135deg, #0077b6 0%, #00b4d8 100%)",
        "skill_soft": "linear-gradient(135deg, #f687b3 0%, #f687b3 100%)",
        "skill_web": "linear-gradient(135deg, #4299e1 0%, #667eea 100%)",
    },
    "Sunset": {
        "bg_color": "#fffaf5", "card_bg": "#ffffff", "text_primary": "#2d1818",
        "text_secondary": "#744210", "accent_color": "#dd6b20", "accent_light": "#f6ad55",
        "border_color": "#fbd38d",
        "header_gradient": "linear-gradient(135deg, #dd6b20 0%, #f6ad55 50%, #fef3c7 100%)",
        "score_card_gradient": "linear-gradient(135deg, #dd6b20 0%, #f6ad55 100%)",
        "metric_bg": "#fffaf0", "suggestion_bg": "#fff5f5", "success_bg": "#f0fff4",
        "skill_gradient": "linear-gradient(135deg, #dd6b20 0%, #f6ad55 100%)",
        "skill_soft": "linear-gradient(135deg, #ed64a6 0%, #d53f8c 100%)",
        "skill_web": "linear-gradient(135deg, #f6ad55 0%, #ed8936 100%)",
    },
    "Forest": {
        "bg_color": "#f0f7f4", "card_bg": "#ffffff", "text_primary": "#1a362d",
        "text_secondary": "#2f855a", "accent_color": "#2f855a", "accent_light": "#68d391",
        "border_color": "#9ae6b4",
        "header_gradient": "linear-gradient(135deg, #2f855a 0%, #68d391 50%, #c6f6d5 100%)",
        "score_card_gradient": "linear-gradient(135deg, #2f855a 0%, #68d391 100%)",
        "metric_bg": "#e6fffa", "suggestion_bg": "#fff5f5", "success_bg": "#f0fff4",
        "skill_gradient": "linear-gradient(135deg, #2f855a 0%, #68d391 100%)",
        "skill_soft": "linear-gradient(135deg, #f687b3 0%, #ed64a6 100%)",
        "skill_web": "linear-gradient(135deg, #68d391 0%, #4299e1 100%)",
    },
    "Midnight": {
        "bg_color": "#0f172a", "card_bg": "#1e293b", "text_primary": "#f1f5f9",
        "text_secondary": "#94a3b8", "accent_color": "#8b5cf6", "accent_light": "#a78bfa",
        "border_color": "#334155",
        "header_gradient": "linear-gradient(135deg, #8b5cf6 0%, #a78bfa 50%, #c4b5fd 100%)",
        "score_card_gradient": "linear-gradient(135deg, #8b5cf6 0%, #a78bfa 100%)",
        "metric_bg": "#334155", "suggestion_bg": "#2d1f1f", "success_bg": "#1f2d1f",
        "skill_gradient": "linear-gradient(135deg, #8b5cf6 0%, #a78bfa 100%)",
        "skill_soft": "linear-gradient(135deg, #f472b6 0%, #ec4899 100%)",
        "skill_web": "linear-gradient(135deg, #22d3ee 0%, #3b82f6 100%)",
    }
}

t = themes.get(theme, themes["Ocean"])

st.markdown(f"""
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap');
        .stApp {{ background: {t["bg_color"]}; }}
        html, body, [class*="css"] {{ font-family: 'Inter', sans-serif; color: {t["text_primary"]}; }}
        
        /* Remove background from Lottie container */
        .stLottie, .stLottie > div, .stLottie svg {{
            background: transparent !important;
            box-shadow: none !important;
        }}
        
        /* Remove background from columns */
        .stColumn {{
            background: transparent !important;
        }}
        
        .main-header {{
            background: {t["header_gradient"]};
            padding: 2.5rem;
            border-radius: 25px;
            text-align: center;
            margin-bottom: 2rem;
            box-shadow: 0 15px 50px rgba(0, 119, 182, 0.25);
        }}
        .main-header h1 {{ color: #ffffff; font-size: 2.8rem; margin: 0; font-weight: 700; text-shadow: 1px 1px 3px rgba(0,0,0,0.3); }}
        .main-header p {{ color: #ffffff; font-size: 1.2rem; margin-top: 0.8rem; opacity: 0.95; text-shadow: 1px 1px 2px rgba(0,0,0,0.3); }}
        
        .card {{
            background: {t["card_bg"]};
            padding: 20px;
            border-radius: 18px;
            box-shadow: 0 4px 20px rgba(0,0,0,0.08);
            margin-bottom: 15px;
            border-left: 5px solid {t["accent_color"]};
            transition: all 0.3s ease;
        }}
        .card:hover {{ transform: translateY(-3px); box-shadow: 0 8px 30px rgba(0,0,0,0.15); }}
        
        .section-title {{
            font-weight: 700;
            color: {t["text_primary"]};
            font-size: 1.15rem;
            margin-bottom: 12px;
            display: flex;
            align-items: center;
            gap: 10px;
        }}
        
        .skill-tag {{
            display: inline-block;
            background: {t["skill_gradient"]};
            color: #000000;
            padding: 6px 14px;
            border-radius: 25px;
            margin: 4px;
            font-size: 0.85rem;
            font-weight: 600;
            text-shadow: none;
        }}
        .skill-tag.soft {{ background: {t["skill_soft"]}; color: #000000; }}
        .skill-tag.web {{ background: {t["skill_web"]}; color: #000000; }}
        .skill-tag.missing {{ background: #e53e3e; color: #ffffff; }}
        .skill-tag.matched {{ background: #48bb78; color: #ffffff; }}
        
        .score-card {{
            background: {t["score_card_gradient"]};
            padding: 30px;
            border-radius: 25px;
            text-align: center;
            color: #ffffff;
            margin-bottom: 25px;
            box-shadow: 0 10px 40px rgba(0,0,0,0.2);
        }}
        .score-value {{ font-size: 4rem; font-weight: 800; color: #ffffff; text-shadow: 2px 2px 4px rgba(0,0,0,0.3); }}
        .score-label {{ font-size: 1.3rem; color: #ffffff; opacity: 0.95; margin-top: 8px; text-shadow: 1px 1px 2px rgba(0,0,0,0.3); }}
        
        .metric-box {{
            background: {t["metric_bg"]};
            padding: 18px;
            border-radius: 16px;
            text-align: center;
            box-shadow: 0 3px 15px rgba(0,0,0,0.08);
        }}
        .metric-value {{ font-size: 2rem; font-weight: 700; color: {t["accent_color"]}; }}
        .metric-label {{ font-size: 0.9rem; color: {t["text_secondary"]}; margin-top: 6px; }}
        
        .suggestion-box {{
            background: {t["suggestion_bg"]};
            border-left: 5px solid #fc8181;
            padding: 16px;
            border-radius: 12px;
            margin: 12px 0;
            color: {t["text_primary"]};
        }}
        .success-box {{
            background: {t["success_bg"]};
            border-left: 5px solid #48bb78;
            padding: 16px;
            border-radius: 12px;
            margin: 12px 0;
            color: {t["text_primary"]};
        }}
        
        .keyword-box {{
            background: {t["metric_bg"]};
            padding: 15px;
            border-radius: 12px;
            margin: 10px 0;
            color: {t["text_primary"]};
        }}
        
        .stButton>button {{
            background: {t["score_card_gradient"]};
            color: #ffffff;
            border: none;
            padding: 14px 35px;
            border-radius: 30px;
            font-weight: 700;
            text-shadow: 1px 1px 2px rgba(0,0,0,0.3);
        }}
        
        .upload-box {{
            background: rgba(102, 126, 234, 0.1);
            border: 3px dashed {t["accent_color"]};
            border-radius: 25px;
            padding: 35px;
            text-align: center;
            color: {t["text_primary"]};
        }}
        
        .progress-bar {{
            background: {t["metric_bg"]};
            border-radius: 10px;
            height: 10px;
            overflow: hidden;
            margin: 5px 0;
        }}
        .progress-fill {{
            height: 100%;
            background: {t["score_card_gradient"]};
            border-radius: 10px;
        }}
        
        .comparison-table {{
            width: 100%;
            border-collapse: collapse;
            margin: 15px 0;
        }}
        .comparison-table th {{
            background: {t["accent_color"]};
            color: #ffffff;
            padding: 12px;
            text-align: left;
        }}
        .comparison-table td {{
            padding: 10px;
            border-bottom: 1px solid {t["border_color"]};
            color: {t["text_primary"]};
        }}
        .comparison-table tr:hover {{
            background: {t["metric_bg"]};
        }}
        
        /* Ensure all text elements have proper color */
        .stMarkdown, .stMarkdown p, .stMarkdown div, .stMarkdown h1, .stMarkdown h2, .stMarkdown h3,
        .stMarkdown h4, .stMarkdown h5, .stMarkdown h6, .st-expander, .st-expander * {{
            color: {t["text_primary"]} !important;
        }}
    </style>
""", unsafe_allow_html=True)

# ---------- Header ----------
st.markdown("""
    <div class="main-header">
        <h1>🧠 AI Resume Analyzer Pro</h1>
        <p>📊 Advanced ATS scoring, keyword analysis, and resume comparison</p>
    </div>
""", unsafe_allow_html=True)

# ---------- Main Content ----------
col1, col2 = st.columns([1, 2])

with col1:
    lottie_data = load_lottie("https://assets10.lottiefiles.com/packages/lf20_ktwnwv5m.json")
    if lottie_data:
        st_lottie(lottie_data, height=280, key="resume")
    else:
        st.markdown("📄")

with col2:
    st.markdown('<div class="upload-box">', unsafe_allow_html=True)
    uploaded_file = st.file_uploader("", type=["pdf"], label_visibility="collapsed")
    st.markdown('</div>', unsafe_allow_html=True)

# Job Description Section
st.markdown("### 💼 Job Description Matching (Optional)")
jd_text = st.text_area(
    "Paste the job description to compare against your resume",
    value=st.session_state.jd_text,
    height=120,
    placeholder="Paste job description here to see keyword match and missing skills...",
    key="jd_input"
)
st.session_state.jd_text = jd_text

# ---------- Analysis Functions ----------
def calculate_ats_score(parsed, text, industry="General"):
    """Calculate ATS compatibility score."""
    score = 0
    details = {}
    
    # Contact Info (15 points)
    contact_score = 0
    if parsed.get('contact', {}).get('email'): contact_score += 5
    if parsed.get('contact', {}).get('phone'): contact_score += 5
    if parsed.get('contact', {}).get('location'): contact_score += 3
    if parsed.get('name'): contact_score += 2
    details['contact'] = min(contact_score, 15)
    score += details['contact']
    
    # Skills (30 points)
    all_skills = []
    for category_skills in parsed.get('skills', {}).values():
        all_skills.extend(category_skills)
    details['skills'] = min(len(all_skills) * 3, 30)
    score += details['skills']
    
    # Industry bonus (10 points)
    if industry != "General":
        industry_kws = INDUSTRY_KEYWORDS.get(industry, [])
        text_lower = text.lower()
        matches = sum(1 for kw in industry_kws if kw.lower() in text_lower)
        details['industry'] = min(matches * 3, 10)
        score += details['industry']
    else:
        details['industry'] = 0
    
    # Experience (25 points)
    exp_count = len(parsed.get('experience', []))
    details['experience'] = min(exp_count * 8, 25)
    score += details['experience']
    
    # Education (20 points)
    edu_count = len(parsed.get('education', []))
    details['education'] = min(edu_count * 7, 20)
    score += details['education']
    
    return min(round(score, 1), 100), details

def get_suggestions(parsed, score_details):
    """Generate improvement suggestions."""
    critical = []
    suggestions = []
    
    contact = parsed.get('contact', {})
    
    if not contact.get('email'):
        critical.append(("📧", "Add your email address (critical for contact)"))
    
    if not contact.get('phone'):
        critical.append(("📱", "Add your phone number"))
    
    all_skills = []
    for cat_skills in parsed.get('skills', {}).values():
        all_skills.extend(cat_skills)
    
    if len(all_skills) < 5:
        critical.append(("🛠️", "Add more technical skills (aim for 8-15 skills)"))
    
    if len(parsed.get('experience', [])) < 2:
        suggestions.append(("💼", "Include more work experience with dates"))
    
    if len(parsed.get('education', [])) < 1:
        suggestions.append(("🎓", "Add your educational background"))
    
    if not parsed.get('summary'):
        suggestions.append(("📝", "Add a professional summary"))
    
    # Check for action verbs
    exp_text = ' '.join([e.get('raw', '') for e in parsed.get('experience', [])]).lower()
    verb_count = sum(1 for v in ACTION_VERBS if v in exp_text)
    if verb_count < 3:
        suggestions.append(("💪", "Use more action verbs (led, developed, managed, created)"))
    
    # Check for quantifiable achievements
    numbers = re.findall(r'\d+%|\d+x|\$\d+|\d+\s*(years?|months?|people|team)', exp_text)
    if len(numbers) < 2:
        suggestions.append(("📊", "Add quantifiable achievements (%, $, numbers)"))
    
    if not critical and not suggestions:
        suggestions.append(("✅", "Great job! Your resume looks comprehensive."))
    
    return critical, suggestions

def analyze_keyword_density(text):
    """Analyze keyword density in resume."""
    # Remove common words
    stop_words = {'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 
                  'of', 'with', 'by', 'from', 'is', 'are', 'was', 'were', 'be', 'been',
                  'being', 'have', 'has', 'had', 'do', 'does', 'did', 'will', 'would',
                  'could', 'should', 'may', 'might', 'must', 'shall', 'can', 'need',
                  'dare', 'ought', 'used', 'i', 'me', 'my', 'myself', 'we', 'our', 'ours'}
    
    words = re.findall(r'\b[a-zA-Z]{3,}\b', text.lower())
    filtered_words = [w for w in words if w not in stop_words]
    
    word_counts = Counter(filtered_words)
    total_words = len(filtered_words)
    
    # Get top keywords with density
    top_keywords = []
    for word, count in word_counts.most_common(20):
        density = (count / total_words * 100) if total_words > 0 else 0
        top_keywords.append({
            'word': word,
            'count': count,
            'density': round(density, 2)
        })
    
    return top_keywords

def calculate_jd_match(text, jd_text):
    """Calculate job description match."""
    if not jd_text or not text:
        return 0, [], []
    
    text_lower = text.lower()
    jd_lower = jd_text.lower()
    
    # Find skills in JD
    jd_keywords = []
    for category, skills in SKILLS_KEYWORDS.items():
        for skill in skills:
            if skill.lower() in jd_lower:
                jd_keywords.append(skill)
    
    # Add industry keywords
    for industry, keywords in INDUSTRY_KEYWORDS.items():
        for kw in keywords:
            if kw.lower() in jd_lower and kw not in jd_keywords:
                jd_keywords.append(kw)
    
    # Check matches
    matched = [kw for kw in jd_keywords if kw.lower() in text_lower]
    missing = [kw for kw in jd_keywords if kw.lower() not in text_lower]
    
    match_score = round((len(matched) / len(jd_keywords) * 100), 1) if jd_keywords else 0
    
    return match_score, matched, missing

def get_score_color(score):
    if score >= 80: return "🟢"
    elif score >= 60: return "🟡"
    else: return "🔴"

# ---------- Process Resume ----------
if uploaded_file:
    with st.spinner("🔄 Analyzing your resume..."):
        time.sleep(0.5)
        
        # Extract text
        text = ""
        with pdfplumber.open(uploaded_file) as pdf:
            for page in pdf.pages:
                text += (page.extract_text() or "") + "\n"
        
        # Parse resume
        parsed = parse_resume(text)
        
        # Calculate scores
        ats_score, score_details = calculate_ats_score(parsed, text, industry)
        critical_suggestions, suggestions = get_suggestions(parsed, score_details)
        
        # JD matching
        jd_match_score, jd_matched, jd_missing = (0, [], [])
        if jd_text:
            jd_match_score, jd_matched, jd_missing = calculate_jd_match(text, jd_text)
        
        # Keyword density
        keyword_density = analyze_keyword_density(text)
        
        # Store in session
        st.session_state.uploaded_resumes.append({
            'name': uploaded_file.name,
            'parsed': parsed,
            'score': ats_score,
            'text': text
        })
    
    st.success("✅ Resume Analyzed Successfully!")
    
    # ---------- ATS Score Display ----------
    st.markdown(f"""
        <div class="score-card">
            <div class="score-value">{get_score_color(ats_score)} {ats_score}/100</div>
            <div class="score-label">📊 ATS Compatibility Score</div>
        </div>
    """, unsafe_allow_html=True)
    
    if industry != "General":
        st.markdown(f"""
            <div style="text-align: center; margin-bottom: 20px;">
                <span class="skill-tag">🎯 Optimized for {industry}</span>
                <span class="skill-tag" style="margin-left: 10px;">+{score_details.get('industry', 0)} industry bonus</span>
            </div>
        """, unsafe_allow_html=True)
    
    # Score Breakdown
    st.markdown("### 📈 Score Breakdown")
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown(f"""
            <div class="metric-box">
                <div class="metric-value">{score_details.get('contact', 0)}/15</div>
                <div class="metric-label">📞 Contact</div>
            </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown(f"""
            <div class="metric-box">
                <div class="metric-value">{score_details.get('skills', 0)}/30</div>
                <div class="metric-label">🛠️ Skills</div>
            </div>
        """, unsafe_allow_html=True)
    
    with col3:
        st.markdown(f"""
            <div class="metric-box">
                <div class="metric-value">{score_details.get('experience', 0)}/25</div>
                <div class="metric-label">💼 Experience</div>
            </div>
        """, unsafe_allow_html=True)
    
    # JD Match Section
    if jd_text and jd_match_score > 0:
        st.markdown("### 💼 Job Description Match")
        
        match_color = "#48bb78" if jd_match_score >= 70 else "#ecc94b" if jd_match_score >= 40 else "#f56565"
        
        st.markdown(f"""
            <div class="card" style="border-left-color: {match_color};">
                <div style="display: flex; justify-content: space-between; align-items: center;">
                    <span style="font-size: 1.2rem; font-weight: 700;">📋 Match Score</span>
                    <span style="font-size: 2rem; font-weight: 800; color: {match_color};">{jd_match_score}%</span>
                </div>
                <div class="progress-bar">
                    <div class="progress-fill" style="width: {jd_match_score}%; background: {match_color};"></div>
                </div>
            </div>
        """, unsafe_allow_html=True)
        
        col_m1, col_m2 = st.columns(2)
        
        with col_m1:
            if jd_matched:
                st.markdown(f"""
                    <div class="success-box">
                        <strong>✅ Matched Keywords ({len(jd_matched)})</strong><br><br>
                        {' '.join([f'<span class="skill-tag matched">{s}</span>' for s in jd_matched[:15]])}
                    </div>
                """, unsafe_allow_html=True)
        
        with col_m2:
            if jd_missing:
                st.markdown(f"""
                    <div class="suggestion-box">
                        <strong>⚠️ Missing Keywords ({len(jd_missing)})</strong><br><br>
                        {' '.join([f'<span class="skill-tag missing">{s}</span>' for s in jd_missing[:15]])}
                    </div>
                """, unsafe_allow_html=True)
    
    # Keyword Density
    if show_keyword_density:
        st.markdown("### 📊 Keyword Density Analysis")
        
        col_kd1, col_kd2 = st.columns(2)
        
        with col_kd1:
            st.markdown("**🔤 Top Keywords**")
            for kw in keyword_density[:10]:
                st.markdown(f"""
                    <div class="keyword-box">
                        <div style="display: flex; justify-content: space-between;">
                            <span><b>{kw['word']}</b></span>
                            <span>{kw['count']}x ({kw['density']}%)</span>
                        </div>
                        <div class="progress-bar">
                            <div class="progress-fill" style="width: {min(kw['density'] * 5, 100)}%;"></div>
                        </div>
                    </div>
                """, unsafe_allow_html=True)
        
        with col_kd2:
            st.markdown("**📈 Stats**")
            st.metric("Total Words", len(text.split()))
            st.metric("Unique Words", len(set(text.lower().split())))
            st.metric("Action Verbs Found", sum(1 for v in ACTION_VERBS if v in text.lower()))
            
            # Check for numbers/quantifiers
            numbers = re.findall(r'\d+%|\d+x|\$\d+', text)
            st.metric("Quantifiable Metrics", len(numbers))
    
    # Suggestions
    st.markdown("### 💡 Improvement Suggestions")
    
    if critical_suggestions:
        st.markdown("**🔴 Critical Issues:**")
        for icon, suggestion in critical_suggestions:
            st.markdown(f'<div class="suggestion-box">{icon} {suggestion}</div>', unsafe_allow_html=True)
    
    if suggestions:
        st.markdown("**🟡 Recommendations:**")
        for icon, suggestion in suggestions:
            if "✅" in icon:
                st.markdown(f'<div class="success-box">{icon} {suggestion}</div>', unsafe_allow_html=True)
            else:
                st.markdown(f'<div class="suggestion-box">{icon} {suggestion}</div>', unsafe_allow_html=True)
    
    # ---------- Structured Preview ----------
    st.markdown("### ✨ Structured Resume Preview")
    
    col1, col2 = st.columns([1, 1])
    
    with col1:
        if parsed['name']:
            st.markdown(f"<div class='card'><div class='section-title'>👤 Name</div>{parsed['name']}</div>", unsafe_allow_html=True)
        
        contact = parsed.get('contact', {})
        if any([contact.get('email'), contact.get('phone'), contact.get('location')]):
            contact_parts = []
            if contact.get('email'): contact_parts.append(f"📧 {contact['email']}")
            if contact.get('phone'): contact_parts.append(f"📱 {contact['phone']}")
            if contact.get('location'): contact_parts.append(f"📍 {contact['location']}")
            st.markdown(f"<div class='card'><div class='section-title'>📞 Contact</div>{'<br>'.join(contact_parts)}</div>", unsafe_allow_html=True)
        
        if parsed.get('summary'):
            st.markdown(f"<div class='card'><div class='section-title'>📝 Summary</div>{parsed['summary'][:300]}{'...' if len(parsed['summary']) > 300 else ''}</div>", unsafe_allow_html=True)
    
    with col2:
        if parsed.get('skills'):
            skills_html = "<div class='card'><div class='section-title'>🛠️ Skills</div>"
            for category, skills in parsed['skills'].items():
                skills_html += f"<div style='margin: 8px 0;'><b>{category}:</b><br>"
                for s in skills:
                    if category == 'Technical':
                        skills_html += f"<span class='skill-tag'>{s}</span>"
                    elif category == 'Web':
                        skills_html += f"<span class='skill-tag web'>{s}</span>"
                    else:
                        skills_html += f"<span class='skill-tag soft'>{s}</span>"
                skills_html += "</div>"
            skills_html += "</div>"
            st.markdown(skills_html, unsafe_allow_html=True)
    
    if parsed.get('education'):
        edu_text = ""
        for edu in parsed['education']:
            edu_text += f"📌 {edu.get('raw', '')}<br>"
        st.markdown(f"<div class='card'><div class='section-title'>🎓 Education</div>{edu_text}</div>", unsafe_allow_html=True)
    
    if parsed.get('experience'):
        exp_text = ""
        for exp in parsed['experience'][:5]:
            exp_text += f"⬆️ {exp.get('raw', '')}<br>"
        st.markdown(f"<div class='card'><div class='section-title'>💼 Experience</div>{exp_text}</div>", unsafe_allow_html=True)
    
    if parsed.get('languages'):
        st.markdown(f"<div class='card'><div class='section-title'>🗣️ Languages</div>{', '.join(parsed['languages'])}</div>", unsafe_allow_html=True)
    
    # Download
    structured_json = {
        "name": parsed.get('name', ''),
        "contact": parsed.get('contact', {}),
        "summary": parsed.get('summary', ''),
        "skills": parsed.get('skills', {}),
        "education": parsed.get('education', []),
        "experience": parsed.get('experience', []),
        "languages": parsed.get('languages', []),
        "ats_score": ats_score,
        "industry": industry,
        "jd_match_score": jd_match_score if jd_text else None,
        "keyword_density": keyword_density[:15],
        "analyzed_at": datetime.now().isoformat()
    }
    
    col_dl1, col_dl2 = st.columns(2)
    
    with col_dl1:
        st.download_button(
            "💾 Download JSON Report",
            data=json.dumps(structured_json, indent=2),
            file_name=f"resume_analysis_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
            mime="application/json"
        )
    
    with col_dl2:
        # Export as text
        text_report = f"""
RESUME ANALYSIS REPORT
======================
Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

NAME: {parsed.get('name', 'N/A')}
ATS SCORE: {ats_score}/100

CONTACT:
- Email: {parsed.get('contact', {}).get('email', 'N/A')}
- Phone: {parsed.get('contact', {}).get('phone', 'N/A')}
- Location: {parsed.get('contact', {}).get('location', 'N/A')}

SKILLS: {', '.join([s for cat in parsed.get('skills', {}).values() for s in cat])}

EDUCATION:
{chr(10).join([e.get('raw', '') for e in parsed.get('education', [])])}

EXPERIENCE:
{chr(10).join([e.get('raw', '') for e in parsed.get('experience', [])[:3]])}

SUGGESTIONS:
{chr(10).join([f"- {s[1]}" for s in critical_suggestions + suggestions])}
"""
        st.download_button(
            "📄 Download Text Report",
            data=text_report,
            file_name=f"resume_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt",
            mime="text/plain"
        )
    
    if show_raw:
        with st.expander("📜 View Raw Extracted Text"):
            st.text_area("Extracted Text", text, height=400)
    
    if show_debug:
        with st.expander("🐛 Debug Information"):
            st.json(parsed)
            st.write(f"**Total characters:** {len(text)}")
            st.write(f"**Total lines:** {len(text.splitlines())}")

# ---------- Resume Comparison Section ----------
if len(st.session_state.uploaded_resumes) >= 2:
    st.markdown("---")
    st.markdown("### 📊 Resume Comparison")
    
    resumes = st.session_state.uploaded_resumes
    
    # Create comparison table
    comparison_data = []
    for r in resumes:
        comparison_data.append({
            'Resume': r['name'],
            'ATS Score': f"{r['score']}/100",
            'Skills': len([s for cat in r['parsed'].get('skills', {}).values() for s in cat]),
            'Experience': len(r['parsed'].get('experience', [])),
            'Education': len(r['parsed'].get('education', [])),
        })
    
    # Display as table
    col_comp = st.columns(len(resumes))
    for i, (col, r) in enumerate(zip(col_comp, resumes)):
        with col:
            st.markdown(f"""
                <div class="card" style="text-align: center;">
                    <div style="font-weight: 700; font-size: 1.1rem;">{r['name']}</div>
                    <div style="font-size: 2.5rem; margin: 15px 0;">{get_score_color(r['score'])} {r['score']}</div>
                    <div>Skills: {len([s for cat in r['parsed'].get('skills', {}).values() for s in cat])}</div>
                    <div>Experience: {len(r['parsed'].get('experience', []))} roles</div>
                    <div>Education: {len(r['parsed'].get('education', []))} entries</div>
                </div>
            """, unsafe_allow_html=True)
    
    # Best resume recommendation
    best_resume = max(resumes, key=lambda x: x['score'])
    st.markdown(f"""
        <div class="success-box" style="text-align: center;">
            <strong>🏆 Best Performing Resume:</strong> {best_resume['name']} (Score: {best_resume['score']}/100)
        </div>
    """, unsafe_allow_html=True)

else:
    st.markdown("---")
    st.info(f"📁 Upload {2 - len(st.session_state.uploaded_resumes)} more resume(s) to enable comparison")

# Empty state
if not uploaded_file and len(st.session_state.uploaded_resumes) == 0:
    st.markdown(f"""
        <div style="text-align: center; padding: 50px; opacity: 0.6;">
            <div style="font-size: 4rem;">📄</div>
            <h3 style="color: {t['text_primary']};">Upload your resume to get started</h3>
            <p style="color: {t['text_secondary']};">Get accurate ATS scoring, keyword analysis, and improvement suggestions</p>
            <div style="margin-top: 30px;">
                <span class="skill-tag">🎯 Industry Optimization</span>
                <span class="skill-tag" style="background: {t['skill_web']}">💼 JD Matching</span>
                <span class="skill-tag" style="background: {t['skill_soft']}">📊 Keyword Density</span>
                <span class="skill-tag">📁 Resume Comparison</span>
            </div>
        </div>
    """, unsafe_allow_html=True)
