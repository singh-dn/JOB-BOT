# scraper/naukri_realtime.py (FIXED SELECTORS ONLY)

import time
from bs4 import BeautifulSoup
from urllib.parse import urljoin
from scraper.selenium_driver import create_driver
from scraper.utils import extract_days, extract_skills, extract_email

BASE_URL = "https://www.naukri.com"


def realtime_naukri_scrape(role, location="", headless=True, recent_days=14):
    print("\n🟧 REAL-TIME NAUKRI SCRAPING STARTED...\n")

    driver = create_driver(headless)

    role_slug = role.replace(" ", "-").lower()
    location_slug = location.replace(" ", "-").lower() if location else ""

    if location_slug:
        search_url = f"{BASE_URL}/{role_slug}-jobs-in-{location_slug}"
    else:
        search_url = f"{BASE_URL}/{role_slug}-jobs"

    print(f"🔗 Searching → {search_url}")
    driver.get(search_url)
    time.sleep(2)

    print("📜 Scrolling to load jobs...")
    for _ in range(12):
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(1.5)

    soup = BeautifulSoup(driver.page_source, "html.parser")

    cards = soup.select(".cust-job-tuple, .jobTuple, .srp-jobtuple-wrapper")
    print(f"🟧 Found {len(cards)} job cards\n")

    job_card_data = []
    job_links = []

    for c in cards:
        try:
            title_el = c.select_one("a.title")
            if not title_el:
                continue

            title = title_el.get_text(strip=True)
            link = title_el["href"]

            company = c.select_one(".subTitle").get_text(strip=True) if c.select_one(".subTitle") else ""
            location_text = c.select_one(".locWdth").get_text(strip=True) if c.select_one(".locWdth") else ""

            posted_el = c.find(string=lambda t: t and ("day" in t.lower() or "week" in t.lower() or "today" in t.lower()))
            posted = posted_el.strip() if posted_el else ""

            # FIXED salary selector
            salary_el = c.select_one("span.compensation")
            salary = salary_el.get_text(strip=True) if salary_el else ""

            if extract_days(posted) > recent_days:
                continue

            job_card_data.append({
                "title": title,
                "company": company,
                "location": location_text,
                "posted": posted,
                "salary": salary,
                "link": link,
            })
            job_links.append(link)

        except Exception:
            continue

    print(f"🟧 Recent jobs: {len(job_card_data)}\n")

    # ----------------------------------------
    # FIXED DETAILS SCRAPING
    # ----------------------------------------
    final_jobs = []

    for idx, item in enumerate(job_card_data):
        link = item["link"]
        print(f"[NK] {idx+1}/{len(job_card_data)} → {link}")

        try:
            driver.get(link)
            time.sleep(2)

            page = BeautifulSoup(driver.page_source, "html.parser")

            # FIXED description selector
            desc_el = (
                page.select_one("div#jobDescription")
                or page.select_one("section.job-desc")
                or page.select_one("div.jd-text")
            )
            description = desc_el.get_text("\n", strip=True) if desc_el else ""

            # FIXED skills selector
            skill_tags = page.select("a.chip, a.skill-chip, .chips a")
            if skill_tags:
                skills = [s.get_text(strip=True) for s in skill_tags]
            else:
                skills = extract_skills(description)

            final_jobs.append({
                "title": item["title"],
                "company": item["company"],
                "location": item["location"],
                "posted": item["posted"],
                "salary": item.get("salary", ""),
                "skills": skills,
                "emails": extract_email(description),
                "description": description,
                "link": link,
                "source": "naukri"
            })

            print("   ✔ Added job")

        except Exception as e:
            print("   ⚠ Error:", e)
            continue

    driver.quit()
    print(f"\n🟧 Naukri scraping completed — Total: {len(final_jobs)} jobs\n")
    return final_jobs
