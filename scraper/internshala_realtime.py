# scraper/internshala_realtime.py

import time
from bs4 import BeautifulSoup
from urllib.parse import urljoin
from scraper.utils import extract_email, extract_skills, extract_days
from scraper.selenium_driver import create_driver

BASE_URL = "https://internshala.com"


def realtime_internshala_scrape(role: str, headless=True, recent_days=14):
    print("\n🚀 REAL-TIME INTERN SHALA SCRAPING STARTED...\n")

    driver = create_driver(headless)
    role_slug = role.replace(" ", "-").lower()
    if not role_slug.endswith("-internship"):
        role_slug += "-internship"

    url = f"{BASE_URL}/internships/{role_slug}"
    driver.get(url)
    time.sleep(3)

    # ---------- SCROLL TO LOAD ALL JOBS ----------
    print("📜 Scrolling to load all jobs...")
    last_height = driver.execute_script("return document.body.scrollHeight")

    scroll_times = 12   # scroll 12 times (loads 150+ internships)
    for _ in range(scroll_times):
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(2)
        new_height = driver.execute_script("return document.body.scrollHeight")

        if new_height == last_height:
            break
        last_height = new_height

    print("✔ All jobs loaded.\n")

    # ---------- PARSE ALL JOB LINKS ----------
    soup = BeautifulSoup(driver.page_source, "html.parser")
    links = soup.find_all("a", href=lambda x: x and "/internship/detail/" in x)

    job_links = []
    for a in links:
        full = urljoin(BASE_URL, a["href"])
        if full not in job_links:
            job_links.append(full)

    print(f"🔗 Total jobs found: {len(job_links)}\n")

    final_jobs = []

    # ---------- SCRAPE EACH JOB ----------
    for idx, link in enumerate(job_links, 1):
        print(f"[{idx}/{len(job_links)}] Scraping → {link}")

        try:
            driver.get(link)
            time.sleep(2)

            soup = BeautifulSoup(driver.page_source, "html.parser")

            # Title
            title_el = soup.select_one("h1")
            title = title_el.get_text(strip=True) if title_el else "Unknown"

            # Company
            company_el = soup.select_one(".container .heading_6")
            company = company_el.get_text(strip=True) if company_el else "Unknown"

            # Description
            jd_el = soup.select_one(".internship_details")
            jd = jd_el.get_text("\n", strip=True) if jd_el else ""

            # Posted date
            posted_el = soup.find(string=lambda t: t and "posted" in t.lower())
            posted = posted_el.strip() if posted_el else ""

            # Filter
            if extract_days(posted) > recent_days:
                print("   ❌ Skipped (old job)")
                continue

            final_jobs.append({
                "title": title,
                "company": company,
                "posted": posted,
                "skills": extract_skills(jd),
                "emails": extract_email(jd),
                "description": jd,
                "link": link,
                "source": "internshala"
            })

            print("   ✔ Added (recent job)\n")

        except Exception as e:
            print("   ⚠ Error:", e)
            continue

    driver.quit()
    return final_jobs
