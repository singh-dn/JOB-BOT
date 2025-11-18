# scraper/naukri_api.py

import requests
from scraper.utils import extract_days, extract_email, extract_skills

API_URL = "https://www.naukri.com/jobapi/v3/search"


def naukri_api_scrape(role: str, location: str = "", recent_days: int = 14):
    print("\n⚡ USING NAUKRI API (FAST, Clean Data)\n")

    params = {
        "noOfResults": 20,
        "pageNo": 1,
        "urlType": "search_by_keyword",
        "jobType": "ALL",
        "keyword": role,
        "location": location,
    }

    headers = {
        "appid": "109",
        "systemid": "Naukri",
        "User-Agent": "Mozilla/5.0",
    }

    r = requests.get(API_URL, headers=headers, params=params)
    data = r.json()

    if "jobDetails" not in data:
        print("⚠ No job details found.")
        return []

    final = []

    for j in data["jobDetails"]:
        posted = j.get("footerLabel", "")

        if extract_days(posted) > recent_days:
            continue

        desc = j.get("jobDescription", "").replace("<br/>", "\n")
        skills = j.get("keySkills", "").split(",") if j.get("keySkills") else extract_skills(desc)

        final.append({
            "title": j.get("title"),
            "company": j.get("companyName"),
            "location": ", ".join(j.get("placeholders", [])[1].get("label", "")) if len(j.get("placeholders", [])) > 1 else "",
            "posted": posted,
            "salary": j.get("placeholders", [])[0].get("label", "") if j.get("placeholders") else "",
            "skills": skills,
            "description": desc,
            "emails": extract_email(desc),
            "link": j.get("jdURL"),
            "source": "naukri_api"
        })

    print(f"⚡ Naukri API extracted {len(final)} jobs.\n")
    return final
