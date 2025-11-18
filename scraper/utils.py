# scraper/utils.py

import re
from datetime import datetime

# skill keywords to detect in JD
SKILL_KEYWORDS = [
    "python", "java", "javascript", "react", "node", "aws", "docker",
    "kubernetes", "terraform", "linux", "git", "github", "ci/cd",
    "mongo", "sql", "shell", "bash", "ansible", "devops", "cloud"
]

def extract_email(text: str):
    return list(set(re.findall(
        r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}",
        text or ""
    )))

def extract_skills(text: str):
    result = []
    t = (text or "").lower()

    for sk in SKILL_KEYWORDS:
        if sk in t:
            result.append(sk)

    return result


# Convert posted text into "days ago"
def extract_days(text: str) -> int:
    if not text:
        return 999
    
    t = text.lower().strip()

    if "today" in t or "just posted" in t or "just now" in t:
        return 0

    if "actively hiring" in t:
        return 3

    # Case: Posted on 27 Jan' 25
    m = re.search(r"posted on\s*([\d]{1,2}\s*\w+\s*'?\d{2})", t)
    if m:
        try:
            dt = datetime.strptime(m.group(1), "%d %b'%y")
            return (datetime.now() - dt).days
        except:
            pass

    # Case: X days ago
    m = re.search(r"(\d+)\s*day", t)
    if m:
        return int(m.group(1))

    # Case: X weeks ago
    m = re.search(r"(\d+)\s*week", t)
    if m:
        return int(m.group(1)) * 7

    return 999
