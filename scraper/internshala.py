# # scraper/internshala.py

# import time
# from bs4 import BeautifulSoup
# from urllib.parse import urljoin
# from .utils import extract_email, extract_skills

# BASE_URL = "https://internshala.com"


# def build_url(role, page):
#     slug = role.lower().replace(" ", "-")
#     if not slug.endswith("-internship"):
#         slug += "-internship"
#     if page == 1:
#         return f"{BASE_URL}/internships/{slug}"
#     return f"{BASE_URL}/internships/{slug}/page-{page}"


# def fetch_listings(role, max_pages, driver):
#     jobs = []

#     for page in range(1, max_pages + 1):
#         url = build_url(role, page)
#         print(f"[IS] Fetching list → {url}")
#         driver.get(url)
#         time.sleep(2)

#         soup = BeautifulSoup(driver.page_source, "html.parser")
#         links = soup.find_all("a", href=lambda x: x and "/internship/detail/" in x)

#         seen = set()
#         for a in links:
#             link = urljoin(BASE_URL, a["href"])
#             if link in seen:
#                 continue
#             seen.add(link)

#             title = a.get_text(strip=True)
#             parent = a.find_parent("div")

#             company = parent.select_one(".company_name")
#             company = company.get_text(strip=True) if company else "Unknown"

#             jobs.append({
#                 "title": title,
#                 "company": company,
#                 "link": link,
#                 "source": "internshala"
#             })

#     print(f"[IS] Jobs found: {len(jobs)}")
#     return jobs


# def fetch_details(url, driver):
#     print(f"[IS] Scrape details → {url}")
#     driver.get(url)
#     time.sleep(2)

#     soup = BeautifulSoup(driver.page_source, "html.parser")

#     desc = soup.select_one(".internship_details")
#     job_description = desc.get_text("\n", strip=True) if desc else ""

#     posted_el = soup.select_one(".profile_on") or soup.find(
#         string=lambda t: t and "posted" in t.lower()
#     )
#     posted = posted_el.get_text(strip=True) if hasattr(posted_el, "get_text") else posted_el or ""

#     return {
#         "job_description": job_description,
#         "hr_emails": extract_email(job_description),
#         "skills": extract_skills(job_description),
#         "posted_date": posted,
#         "link": url,
#         "source": "internshala"
#     }
