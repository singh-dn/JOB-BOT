# scraper/internshala_api.py

import requests
from scraper.utils import extract_days, extract_skills, extract_email

BASE_URL = "https://internshala.com/api/internships/search"


def internshala_api_scrape(role: str, location: str = "", recent_days: int = 14):
    print("\n⚡ USING INTERN SHALA API (Instant Scraper)\n")

    params = {
        "page": 1,
        "keywords": role,
        "location": location,
    }

    r = requests.get(BASE_URL, params=params, headers={"User-Agent": "Mozilla/5.0"})
    data = r.json()

    if "internships" not in data:
        print("⚠ No internships in API response.")
        return []

    results = []

    for job in data["internships"]:
        posted = job.get("posted_on_label", "")

        # Filter by days
        if extract_days(posted) > recent_days:
            continue

        jd = job.get("job_details", "")
        desc = jd.replace("<br>", "\n")

        results.append({
            "title": job.get("title"),
            "company": job.get("company_name"),
            "location": ", ".join(job.get("location_names", [])),
            "posted": posted,
            "salary": job.get("stipend", {}).get("salary", ""),
            "skills": job.get("skills", []),
            "description": desc,
            "emails": extract_email(desc),
            "link": "https://internshala.com" + job.get("job_url"),
            "source": "internshala_api"
        })

    print(f"⚡ API scraper extracted {len(results)} jobs.\n")
    return results
