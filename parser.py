# parser.py - Accurate Resume Parser
import re
from typing import Dict, List, Tuple, Optional

# Try to load spaCy
try:
    import spacy
    nlp = spacy.load("en_core_web_sm")
except Exception:
    nlp = None


# ==================== SECTION DETECTION ====================

SECTION_PATTERNS = {
    'experience': [
        r'\bWORK\s*EXPERIENCE\b', r'\bPROFESSIONAL\s*EXPERIENCE\b', 
        r'\bEMPLOYMENT\s*HISTORY\b', r'\bWORK\s*HISTORY\b',
        r'\bEXPERIENCE\b', r'\bEMPLOYMENT\b', r'\bWORK\s*PROFILE\b',
        r'experience\s*:', r'work\s*experience\s*:'
    ],
    'education': [
        r'\bEDUCATION\b', r'\bEDUCATIONAL\s*QUALIFICATIONS\b',
        r'\bACADEMIC\s*BACKGROUND\b', r'\bQUALIFICATIONS\b',
        r'\bDEGREES?\b', r'\bACADEMIC\s*CREDENTIALS\b',
        r'education\s*:', r'qualifications\s*:'
    ],
    'skills': [
        r'\bSKILLS\b', r'\bTECHNICAL\s*SKILLS\b', r'\bCORE\s*COMPETENCIES\b',
        r'\bTECHNICAL\s*EXPERTISE\b', r'\bSKILL\s*SET\b',
        r'\bAREAS\s*OF\s*EXPERTISE\b', r'\bPROFICIENCIES\b',
        r'\bTECHNOLOGIES\b', r'\bTOOLS\b', r'\bLANGUAGES\s*&\s*TOOLS\b',
        r'skills\s*:', r'technical\s*skills\s*:'
    ],
    'summary': [
        r'\bSUMMARY\b', r'\bPROFESSIONAL\s*SUMMARY\b', r'\bEXECUTIVE\s*SUMMARY\b',
        r'\bPROFILE\b', r'\bABOUT\s*ME\b', r'\bABOUT\b',
        r'\bPROFESSIONAL\s*PROFILE\b', r'summary\s*:'
    ],
    'objective': [
        r'\bOBJECTIVE\b', r'\bCAREER\s*OBJECTIVE\b',
        r'\bPROFESSIONAL\s*OBJECTIVE\b', r'\bCAREER\s*GOAL\b',
        r'objective\s*:'
    ],
    'projects': [
        r'\bPROJECTS\b', r'\bACADEMIC\s*PROJECTS\b', r'\bKEY\s*PROJECTS\b',
        r'\bTECHNICAL\s*PROJECTS\b', r'\bPROJECT\s*EXPERIENCE\b',
        r'projects\s*:'
    ],
    'certifications': [
        r'\bCERTIFICATIONS\b', r'\bCERTIFICATES?\b', r'\bLICENSES?\b',
        r'\bPROFESSIONAL\s*CERTIFICATIONS\b', r'\bCERTIFIED\b',
        r'certifications\s*:'
    ],
    'languages': [
        r'\bLANGUAGES\b', r'\bLANGUAGE\s*SKILLS\b', r'\bLINGUISTIC\s*ABILITIES\b',
        r'\bSPOKEN\s*LANGUAGES\b', r'languages\s*:'
    ],
    'achievements': [
        r'\bACHIEVEMENTS\b', r'\bAWARDS?\b', r'\bHONORS?\b',
        r'\bRECOGNITION\b', r'\bACCOMPLISHMENTS\b',
        r'achievements\s*:'
    ],
    'interests': [
        r'\bINTERESTS?\b', r'\bHOBBIES?\b', r'\bEXTRACURRICULAR\b',
        r'\bPERSONAL\s*INTERESTS\b', r'\bACTIVITIES\b',
        r'interests\s*:'
    ],
}

# Skills database with variations
SKILLS_DB = {
    'Technical': {
        'python': ['python', 'pytorch', 'tensorflow', 'keras', 'flask', 'django', 'fastapi'],
        'java': ['java', 'spring', 'spring boot', 'hibernate'],
        'javascript': ['javascript', 'js', 'typescript', 'ts', 'node', 'node.js'],
        'cpp': ['c++', 'cpp', 'c/c++'],
        'sql': ['sql', 'mysql', 'postgresql', 'postgres', 'sqlite', 'oracle'],
        'ml': ['machine learning', 'deep learning', 'ai', 'artificial intelligence', 'nlp', 'natural language processing'],
        'cloud': ['aws', 'azure', 'gcp', 'google cloud', 'amazon web services'],
        'devops': ['docker', 'kubernetes', 'k8s', 'jenkins', 'ci/cd', 'terraform', 'ansible'],
        'data': ['pandas', 'numpy', 'scikit-learn', 'sklearn', 'matplotlib', 'seaborn', 'data analysis'],
        'other': ['git', 'linux', 'bash', 'shell', 'rest api', 'graphql', 'microservices']
    },
    'Web': {
        'frontend': ['html', 'css', 'react', 'react.js', 'angular', 'vue', 'vue.js', 'next.js', 'svelte'],
        'styling': ['bootstrap', 'tailwind', 'sass', 'less', 'material-ui', 'ant design'],
        'backend': ['django', 'flask', 'express', 'node.js', 'fastapi', 'spring boot', 'laravel']
    },
    'Soft Skills': {
        'leadership': ['leadership', 'team leadership', 'mentoring'],
        'communication': ['communication', 'presentation', 'public speaking'],
        'teamwork': ['teamwork', 'collaboration', 'cross-functional'],
        'management': ['project management', 'agile', 'scrum', 'kanban'],
        'problem': ['problem solving', 'analytical thinking', 'critical thinking']
    }
}

# Education level keywords with scores
EDUCATION_LEVELS = {
    'phd': 5, 'doctorate': 5, 'ph.d': 5,
    'master': 4, 'ms': 4, 'm.sc': 4, 'm.s': 4, 'mtech': 4, 'm.tech': 4, 'mba': 4, 'ma': 4, 'm.com': 4,
    'bachelor': 3, 'bs': 3, 'b.sc': 3, 'b.s': 3, 'btech': 3, 'b.tech': 3, 'be': 3, 'b.e': 3, 'ba': 3, 'b.com': 3, 'bca': 3,
    'diploma': 2, 'associate': 2,
    'intermediate': 2, 'hsc': 2, '12th': 2, 'high school': 1, 'ssc': 1, 'matric': 1, '10th': 1
}


def find_sections(text: str) -> Dict[str, Tuple[int, int]]:
    """Find section boundaries in text."""
    sections = {}
    text_upper = text.upper()
    
    # Find all section start positions
    section_starts = []
    
    for section_name, patterns in SECTION_PATTERNS.items():
        for pattern in patterns:
            for match in re.finditer(pattern, text_upper):
                # Get the line start position
                line_start = text.rfind('\n', 0, match.start())
                if line_start == -1:
                    line_start = 0
                else:
                    line_start += 1  # Move past the newline
                
                # Get the line end position
                line_end = text.find('\n', match.end())
                if line_end == -1:
                    line_end = len(text)
                
                section_starts.append((line_start, section_name, match.group()))
    
    # Sort by position
    section_starts.sort(key=lambda x: x[0])
    
    # Remove duplicates (keep first occurrence of each section)
    seen = set()
    unique_sections = []
    for pos, name, header in section_starts:
        if name not in seen:
            seen.add(name)
            unique_sections.append((pos, name, header))
    
    # Create section ranges
    for i, (start, name, _) in enumerate(unique_sections):
        if i + 1 < len(unique_sections):
            end = unique_sections[i + 1][0]
        else:
            end = len(text)
        sections[name] = (start, end)
    
    return sections


def extract_section_content(text: str, sections: Dict[str, Tuple[int, int]], section_name: str) -> str:
    """Extract content of a specific section."""
    if section_name not in sections:
        return ""
    
    start, end = sections[section_name]
    
    # Find the actual content start (skip the header line)
    header_end = text.find('\n', start)
    if header_end == -1:
        header_end = len(text)
    
    content = text[header_end + 1:end].strip()
    return content


def extract_name(text: str, sections: Dict[str, Tuple[int, int]]) -> str:
    """Extract name from the header area (before first section)."""
    # Find where content starts
    first_section_start = len(text)
    for _, (start, _) in sections.items():
        first_section_start = min(first_section_start, start)
    
    # Get header text
    header = text[:first_section_start].strip()
    lines = [l.strip() for l in header.split('\n') if l.strip()]
    
    if not lines:
        return ""
    
    # First line is usually the name
    first_line = lines[0]
    
    # Skip if it looks like contact info
    if '@' in first_line:
        return ""
    if re.search(r'\d{3}[-.\s]?\d{3}[-.\s]?\d{4}', first_line):
        return ""
    if 'http' in first_line.lower() or 'www' in first_line.lower() or '.com' in first_line.lower():
        return ""
    if len(first_line) > 60:
        return ""
    
    # Should have 2-5 words
    words = first_line.split()
    if 2 <= len(words) <= 5:
        # Most words should start with capital letter
        capitalized = sum(1 for w in words if w and w[0].isupper())
        if capitalized >= len(words) * 0.7:
            return first_line
    
    # Try spaCy NER as fallback
    if nlp:
        doc = nlp(header[:800])
        for ent in doc.ents:
            if ent.label_ == 'PERSON':
                ent_words = ent.text.split()
                if 2 <= len(ent_words) <= 5:
                    return ent.text.strip()
    
    # Fallback: return first reasonable line
    for line in lines[:3]:
        words = line.split()
        if 2 <= len(words) <= 5 and len(line) < 60:
            if not re.search(r'[@\d]|http|\.com', line):
                return line
    
    return ""


def extract_contact_info(text: str, sections: Dict[str, Tuple[int, int]]) -> Dict:
    """Extract contact information from header area."""
    # Find header area (before first section or first 35% of text)
    first_section_start = len(text)
    for _, (start, _) in sections.items():
        first_section_start = min(first_section_start, start)
    
    header_area = text[:max(first_section_start, len(text) // 3)]
    
    contact = {
        'email': '',
        'phone': '',
        'location': '',
        'links': []
    }
    
    # Email - multiple patterns
    email_patterns = [
        r'[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.(com|org|net|edu|gov|io|co|in|uk|ca|au|de|fr|me|info|biz)',
        r'[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}'
    ]
    for pattern in email_patterns:
        match = re.search(pattern, header_area, re.IGNORECASE)
        if match:
            contact['email'] = match.group(0).lower()
            break
    
    # Phone - multiple formats
    phone_patterns = [
        r'\+?\d{1,3}[-.\s]?\(?\d{2,4}\)?[-.\s]?\d{3,4}[-.\s]?\d{3,4}',  # International
        r'\(\d{3}\)\s*\d{3}[-.\s]?\d{4}',  # (123) 456-7890
        r'\d{3}[-.\s]\d{3}[-.\s]\d{4}',  # 123-456-7890
        r'\d{10,12}',  # Plain digits
    ]
    for pattern in phone_patterns:
        match = re.search(pattern, header_area)
        if match:
            contact['phone'] = match.group(0).strip()
            break
    
    # Location - look for city patterns
    location_patterns = [
        r'(?:location|address|based|located|city)[:\s]+([A-Za-z\s,]+?)(?:\n|$|\||@|\d)',
        r'([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*,\s*[A-Z]{2})',  # City, ST format
    ]
    for pattern in location_patterns:
        match = re.search(pattern, header_area, re.IGNORECASE)
        if match:
            loc = match.group(1).strip() if match.lastindex else match.group(0).strip()
            if 3 < len(loc) < 50:
                contact['location'] = loc
                break
    
    # Known cities (common in resumes)
    cities = ['Karachi', 'Lahore', 'Islamabad', 'Rawalpindi', 'Faisalabad', 
              'Multan', 'Peshawar', 'Quetta', 'Hyderabad', 'Sialkot',
              'New York', 'London', 'Dubai', 'Singapore', 'Toronto', 'Sydney']
    for city in cities:
        if city in header_area:
            # Verify it's not part of company name
            context_start = max(0, header_area.find(city) - 20)
            context = header_area[context_start:header_area.find(city) + len(city)]
            if not any(kw in context.lower() for kw in ['office', 'branch', 'company', 'corp']):
                contact['location'] = city
                break
    
    # Links/URLs
    url_pattern = r'https?://[^\s<>"{}|\\^`\[\]]+'
    urls = re.findall(url_pattern, header_area)
    contact['links'] = list(set(urls))
    
    return contact


def extract_skills(text: str, sections: Dict[str, Tuple[int, int]]) -> Dict[str, List[str]]:
    """Extract and categorize skills."""
    found_skills = {}
    text_lower = text.lower()
    
    # Get skills section if available
    skills_section = extract_section_content(text, sections, 'skills')
    skills_section_lower = skills_section.lower() if skills_section else text_lower
    
    for category, skill_groups in SKILLS_DB.items():
        category_skills = []
        
        for skill_name, variations in skill_groups.items():
            for variation in variations:
                # Use word boundaries for accurate matching
                if re.search(r'\b' + re.escape(variation) + r'\b', skills_section_lower):
                    # Add the canonical skill name
                    if skill_name not in [v for v in variations]:
                        canonical = variation.title()
                    else:
                        canonical = skill_name.title()
                    
                    if canonical not in category_skills:
                        category_skills.append(canonical)
                    break
        
        if category_skills:
            found_skills[category] = category_skills
    
    return found_skills


def parse_education(content: str) -> List[Dict]:
    """Parse education section into structured entries."""
    if not content:
        return []
    
    entries = []
    lines = content.split('\n')
    
    current_entry = {}
    
    for line in lines:
        line = line.strip()
        if not line:
            if current_entry:
                entries.append(current_entry)
                current_entry = {}
            continue
        
        entry = {'raw': line}
        
        # Extract year/duration
        year_patterns = [
            r'(\d{4})\s*[-–]\s*(\d{4}|Present|Current|Now|Ongoing)',
            r'(\d{4})\s*[-–]\s*(\d{2})',  # 2020-24
            r'\b(20\d{2}|19\d{2})\b',  # Single year
        ]
        
        for pattern in year_patterns:
            match = re.search(pattern, line)
            if match:
                if len(match.groups()) >= 2:
                    entry['duration'] = match.group(0)
                else:
                    entry['year'] = match.group(0)
                break
        
        # Extract degree
        for edu_kw in EDUCATION_LEVELS.keys():
            if edu_kw in line.lower():
                # Try to capture full degree
                degree_patterns = [
                    r'((?:Bachelor|Master|PhD|B\.?|M\.?)[^\n,;]*(?:of|in)[^\n,;]*)',
                    r'((?:B\.?|M\.?)?(?:Sc|Tech|Eng|Com|Arts|Business)[^\n,;]*)',
                ]
                for dp in degree_patterns:
                    match = re.search(dp, line, re.IGNORECASE)
                    if match:
                        entry['degree'] = match.group(1).strip()
                        break
                
                if 'degree' not in entry:
                    entry['degree'] = line
                break
        
        # Extract institution
        inst_keywords = ['university', 'college', 'institute', 'school']
        for kw in inst_keywords:
            if kw in line.lower():
                entry['institution'] = line
                break
        
        # Only add if we found meaningful data
        if 'degree' in entry or 'institution' in entry or 'duration' in entry:
            if current_entry and 'duration' not in entry:
                # Continuation of previous entry
                current_entry['raw'] += '\n' + line
            else:
                if current_entry:
                    entries.append(current_entry)
                current_entry = entry
    
    if current_entry:
        entries.append(current_entry)
    
    return entries


def parse_experience(content: str) -> List[Dict]:
    """Parse experience section into structured entries."""
    if not content:
        return []
    
    entries = []
    lines = content.split('\n')
    
    current_entry = None
    
    # Job title keywords
    title_keywords = [
        'engineer', 'developer', 'manager', 'director', 'lead', 'senior', 'junior',
        'principal', 'staff', 'chief', 'head', 'vp', 'vice president', 'cto', 'ceo',
        'analyst', 'designer', 'consultant', 'administrator', 'specialist',
        'coordinator', 'supervisor', 'executive', 'officer', 'intern', 'associate',
        'architect', 'scientist', 'researcher', 'professor', 'instructor', 'admin'
    ]
    
    for line in lines:
        line = line.strip()
        if not line:
            continue
        
        # Check for year range (indicates new entry)
        year_match = re.search(r'(\d{4})\s*[-–]\s*(\d{4}|Present|Current|Now|Ongoing)', line)
        
        if year_match:
            # Save previous entry
            if current_entry:
                entries.append(current_entry)
            
            current_entry = {
                'duration': year_match.group(0),
                'raw': line
            }
            
            # Check if this line has job title
            for kw in title_keywords:
                if kw in line.lower():
                    current_entry['title'] = line
                    break
        elif current_entry:
            # Add to current entry
            if 'title' not in current_entry:
                for kw in title_keywords:
                    if kw in line.lower() and len(line) < 100:
                        current_entry['title'] = line
                        break
            
            if 'company' not in current_entry:
                company_indicators = ['inc', 'ltd', 'llc', 'corp', 'corporation', 
                                     'company', 'technologies', 'solutions', 'systems']
                for ind in company_indicators:
                    if ind in line.lower():
                        current_entry['company'] = line
                        break
            
            current_entry['raw'] = current_entry.get('raw', '') + '\n' + line
        else:
            # First entry without year - look for title
            for kw in title_keywords:
                if kw in line.lower():
                    current_entry = {'title': line, 'raw': line}
                    break
    
    if current_entry:
        entries.append(current_entry)
    
    return entries


def extract_languages(content: str) -> List[str]:
    """Extract languages from content."""
    if not content:
        return []
    
    languages = []
    content_lower = content.lower()
    
    common_languages = [
        'english', 'urdu', 'hindi', 'spanish', 'french', 'german', 'chinese',
        'mandarin', 'arabic', 'japanese', 'korean', 'portuguese', 'italian',
        'russian', 'dutch', 'swedish', 'norwegian', 'danish', 'finnish',
        'turkish', 'polish', 'czech', 'greek', 'hebrew', 'persian', 'thai',
        'vietnamese', 'indonesian', 'malay', 'tagalog', 'bengali', 'tamil',
        'punjabi', 'gujarati', 'marathi', 'telugu', 'kannada', 'malayalam'
    ]
    
    for lang in common_languages:
        if re.search(r'\b' + re.escape(lang) + r'\b', content_lower):
            languages.append(lang.title())
    
    # Look for proficiency patterns
    prof_pattern = r'(\w+)\s*[:\-]?\s*(native|fluent|intermediate|basic|proficient|conversational|elementary)'
    matches = re.findall(prof_pattern, content, re.IGNORECASE)
    for match in matches:
        lang = match[0].title()
        prof = match[1].title()
        entry = f"{lang} ({prof})"
        if entry not in languages and lang not in languages:
            languages.append(entry)
    
    return languages


def extract_summary(text: str, sections: Dict[str, Tuple[int, int]]) -> str:
    """Extract summary/objective section."""
    # Try summary section first
    for section_name in ['summary', 'objective', 'profile']:
        if section_name in sections:
            content = extract_section_content(text, sections, section_name)
            if content:
                # Clean up - remove section header if present
                lines = content.split('\n')
                if lines and any(kw in lines[0].lower() for kw in ['summary', 'objective', 'profile']):
                    lines = lines[1:]
                return '\n'.join(lines).strip()
    
    # Fallback: text between name/contact and first major section
    first_section_start = len(text)
    for section_name in ['experience', 'education', 'skills']:
        if section_name in sections:
            first_section_start = min(first_section_start, sections[section_name][0])
    
    # Get header area
    header_end = 0
    lines = text[:first_section_start].split('\n')
    for i, line in enumerate(lines[:10]):
        if '@' in line or re.search(r'\d{3}[-.\s]?\d{3}', line):
            header_end = i + 1
            break
    
    if header_end > 0 and header_end < len(lines):
        summary_lines = lines[header_end:header_end + 4]
        summary_lines = [l.strip() for l in summary_lines if l.strip() and len(l) > 20]
        if summary_lines:
            return ' '.join(summary_lines)
    
    return ""


def parse_resume(text: str) -> Dict:
    """Main parsing function."""
    # Clean text
    text = text.replace('\r', '\n')
    
    # Find sections
    sections = find_sections(text)
    
    # Extract all fields
    result = {
        'name': extract_name(text, sections),
        'contact': extract_contact_info(text, sections),
        'summary': extract_summary(text, sections),
        'skills': extract_skills(text, sections),
        'education': parse_education(extract_section_content(text, sections, 'education')),
        'experience': parse_experience(extract_section_content(text, sections, 'experience')),
        'languages': extract_languages(extract_section_content(text, sections, 'languages')),
        'certifications': extract_section_content(text, sections, 'certifications'),
        'projects': extract_section_content(text, sections, 'projects'),
        'achievements': extract_section_content(text, sections, 'achievements'),
    }
    
    return result
