# 🧠 AI Resume Analyzer Pro

A powerful Streamlit-based resume analysis tool that provides **ATS compatibility scoring**, **keyword analysis**, **job description matching**, and **resume comparison** with beautiful, customizable themes.

![Features](https://img.shields.io/badge/Features-ATS%20Scoring%20%7C%20JD%20Matching%20%7C%20Comparison-blue)
![Python](https://img.shields.io/badge/Python-3.10+-green)
![Streamlit](https://img.shields.io/badge/Streamlit-1.55+-red)

---

## ✨ Features

### 📊 ATS Compatibility Score
Get a detailed **0-100 score** based on:
- 📞 Contact Information (15 pts)
- 🛠️ Skills Detection (30 pts)
- 💼 Work Experience (25 pts)
- 🎓 Education (20 pts)
- 🎯 Industry Keywords (10 pts bonus)

### 💼 Job Description Matching
- Paste any job description
- Get **match percentage** score
- See **matched keywords** (green)
- Identify **missing keywords** (red) to add

### 📁 Resume Comparison
- Upload multiple resumes
- Compare scores **side-by-side**
- Get **recommendation** for best version
- Track improvements across versions

### 📊 Keyword Density Analysis
- Top 20 keywords with frequency
- Density percentage for each word
- Visual progress bars
- Writing statistics

### 🎨 Beautiful Themes
Choose from 4 professional themes:
- **🌊 Ocean** - Blue gradient, professional
- **🌅 Sunset** - Warm orange tones, energetic
- **🌲 Forest** - Green palette, balanced
- **🌙 Midnight** - Dark mode, modern

### 🎯 Industry Optimization
Select your target industry for optimized scoring:
- Software Engineering
- Data Science
- DevOps
- Frontend Development
- Backend Development
- Management

### 📥 Multiple Export Formats
- **JSON Report** - Full structured data
- **Text Report** - Human-readable summary

### 💡 Smart Suggestions
Get actionable feedback on:
- Missing contact information
- Skills gaps
- Action verb usage
- Quantifiable achievements
- Format improvements

---

## 🚀 Quick Start

### Prerequisites
- Python 3.10 or higher
- pip or uv package manager

### Installation

1. **Clone the repository**
```bash
git clone <your-repo-url>
cd AI_Summary
```

2. **Create virtual environment**
```bash
# Using uv (recommended)
uv venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Or using venv
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
```

3. **Install dependencies**
```bash
# Using uv
uv pip install pdfplumber streamlit streamlit-lottie requests spacy

# Using pip
pip install pdfplumber streamlit streamlit-lottie requests spacy
```

4. **Download spaCy model**
```bash
python -m spacy download en_core_web_sm
```

5. **Run the application**
```bash
streamlit run app.py
```

6. **Open in browser**
```
http://localhost:8501
```

---

## 📖 How to Use

### Basic Analysis
1. **Upload Resume** - Drag & drop or click to upload PDF
2. **View Score** - Check your ATS compatibility score (0-100)
3. **Review Breakdown** - See scores for each category
4. **Read Suggestions** - Follow recommendations to improve
5. **Download Report** - Export analysis as JSON or TXT

### Job Description Matching
1. Enable **"Job Description Matching"** in options
2. Paste the job description text
3. View match percentage
4. Add missing keywords to your resume
5. Re-upload to see improved score

### Resume Comparison
1. Upload your first resume → Note the score
2. Make improvements to your resume
3. Upload the new version
4. Compare both versions side-by-side
5. See which performs better

### Keyword Analysis
1. Enable **"Show Keyword Density"** in sidebar
2. View top keywords and their frequency
3. Check for overused or missing terms
4. Optimize your resume's language

---

## 🎛️ Sidebar Features

| Feature | Description |
|---------|-------------|
| **🎨 Theme** | Switch between 4 color themes |
| **🎯 Industry** | Select target industry for optimization |
| **📜 Show Raw Text** | View extracted text from PDF |
| **🐛 Debug Info** | See technical parsing details |
| **📊 Keyword Density** | Enable keyword analysis panel |
| **📁 Resume Comparison** | View stored resumes count |

---

## 📊 Scoring System

### ATS Score Breakdown

| Category | Points | Criteria |
|----------|--------|----------|
| **Contact Info** | 15 | Email (5), Phone (5), Location (3), Name (2) |
| **Skills** | 30 | 3 points per skill detected (max 10 skills) |
| **Experience** | 25 | 8 points per role (max 3 roles) |
| **Education** | 20 | 7 points per entry (max 3 entries) |
| **Industry Bonus** | 10 | 3 points per industry keyword match |

### Score Ratings
- **🟢 80-100**: Excellent - Will pass most ATS filters
- **🟡 60-79**: Good - May pass some filters
- **🔴 Below 60**: Needs Improvement - Likely to be rejected

---

## 🛠️ Technology Stack

- **Frontend**: Streamlit
- **PDF Processing**: pdfplumber
- **NLP**: spaCy (en_core_web_sm)
- **Visualization**: Custom CSS with gradients
- **Animation**: Lottie files

---

## 📁 Project Structure

```
AI_Summary/
├── app.py              # Main Streamlit application
├── parser.py           # Resume parsing logic
├── requirements.txt    # Python dependencies
├── pyproject.toml      # Project configuration
├── README.md           # This file
└── .venv/              # Virtual environment
```

---

## 🎯 Tips for Best Results

### Resume Format
✅ Use standard PDF format
✅ Include clear section headings
✅ Place contact info at the top
✅ Use standard fonts (Arial, Calibri, Times New Roman)

### Content Optimization
✅ List 8-15 technical skills
✅ Include dates for all experience
✅ Use action verbs (led, developed, managed)
✅ Add quantifiable achievements (%, $, numbers)
✅ Tailor keywords to job description

### What to Avoid

❌ Image-only PDFs (scanned resumes)

❌ Complex multi-column layouts

❌ Graphics and icons instead of text

❌ Unusual section names

❌ Tables and text boxes

---

## 🔧 Troubleshooting

### Issue: Low ATS Score
**Solution**: Add more skills, include dates in experience, add a summary section

### Issue: Name Not Detected
**Solution**: Ensure name is at the top of the resume, not in a header/footer

### Issue: Skills Not Detected
**Solution**: List skills explicitly, use common skill names (Python, not "Py")

### Issue: Text Not Extracted
**Solution**: Ensure PDF is text-based, not image-only. Try saving as new PDF.

---

## 📝 Example Output

```json
{
  "name": "John Doe",
  "contact": {
    "email": "john@email.com",
    "phone": "+1-234-567-8900",
    "location": "New York, NY"
  },
  "summary": "Experienced software engineer...",
  "skills": {
    "Technical": ["Python", "Java", "AWS"],
    "Web": ["React", "Node.js"],
    "Soft Skills": ["Leadership", "Communication"]
  },
  "education": [...],
  "experience": [...],
  "ats_score": 85,
  "analyzed_at": "2026-03-08T10:30:00"
}
```

---

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Submit a pull request

---

## 📄 License

This project is open source and available under the MIT License.

---

## 🙏 Acknowledgments

- **Streamlit** - For the amazing web framework
- **spaCy** - For NLP capabilities
- **Lottie** - For beautiful animations
- **pdfplumber** - For PDF text extraction

---

## 📞 Support

For issues, questions, or suggestions:
- Open an issue on GitHub
- Check existing documentation
- Review troubleshooting section

---

**Made with ❤️ for job seekers everywhere**

*Last Updated: March 2026*
