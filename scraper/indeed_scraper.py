# scraper/indeed_scraper.py

import requests
from bs4 import BeautifulSoup
from scraper.utils import extract_email, extract_skills, extract_days

def indeed_scrape(role: str, location: str, recent_days: int = 14):
    print("\n⚡ INDEED SCRAPER STARTED\n")

    url = f"https://in.indeed.com/jobs?q={role.replace(' ', '+')}&l={location.replace(' ', '+')}"
    r = requests.get(url, headers={"User-Agent": "Mozilla/5.0"})
    soup = BeautifulSoup(r.text, "html.parser")

    results = []

    cards = soup.select("div.job_seen_beacon")
    print(f"🔗 Found {len(cards)} jobs")

    for c in cards:
        try:
            title = c.select_one("h2 a").text.strip()
            link = "https://in.indeed.com" + c.select_one("h2 a")["href"]
            company = c.select_one(".companyName").text.strip() if c.select_one(".companyName") else ""
            salary = c.select_one(".salary-snippet").text.strip() if c.select_one(".salary-snippet") else ""
            posted = c.select_one(".date").text.strip() if c.select_one(".date") else "Unknown"

            if extract_days(posted) > recent_days:
                continue

            # Open job page for description
            jd_page = requests.get(link, headers={"User-Agent": "Mozilla/5.0"})
            jd_soup = BeautifulSoup(jd_page.text, "html.parser")
            desc = jd_soup.select_one("#jobDescriptionText")
            desc_text = desc.get_text("\n", strip=True) if desc else ""

            results.append({
                "title": title,
                "company": company,
                "location": location,
                "salary": salary,
                "posted": posted,
                "description": desc_text,
                "skills": extract_skills(desc_text),
                "emails": extract_email(desc_text),
                "link": link,
                "source": "indeed"
            })
        except:
            continue

    print(f"⚡ Indeed extracted {len(results)} jobs.\n")
    return results
