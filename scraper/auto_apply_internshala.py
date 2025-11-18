# scraper/auto_apply_internshala.py
"""
Internshala Auto-Apply module (Selenium).
Supports:
 - login_with_credentials(driver, email, password)
 - save_cookies(driver, path)
 - load_cookies(driver, path)
 - apply_to_job(driver, job_link, applicant_info, resume_path)
 - batch_apply(job_links, mode, applicant_info, resume_path, headless)

Notes:
 - applicant_info is a dict: {"name","email","phone","college","city","linkedin","portfolio", ...}
 - resume_path: local path to resume file to upload
 - cookie_path default: ".intern_cookies.json"
 - For production, store credentials/cookies securely (this code has minimal storage helpers).
"""

import time
import json
import os
from typing import List, Dict, Optional

from selenium.webdriver.common.by import By
from selenium.common.exceptions import NoSuchElementException, ElementClickInterceptedException
from selenium.webdriver.common.action_chains import ActionChains

from scraper.selenium_driver import create_driver
from urllib.parse import urlparse

COOKIE_PATH_DEFAULT = ".intern_cookies.json"


# ------------------------
# LOGIN & COOKIE HELPERS
# ------------------------
def login_with_credentials(driver, email: str, password: str, headless=True, wait_after=3) -> bool:
    """
    Log into Internshala using provided credentials. Returns True on success.
    """
    try:
        driver.get("https://internshala.com/login/student")
        time.sleep(2 if headless else 1)

        # email field
        try:
            e = driver.find_element(By.ID, "login_email")
        except:
            # fallback selector
            e = driver.find_element(By.NAME, "email")
        e.clear()
        e.send_keys(email)
        time.sleep(0.3)

        # password
        try:
            p = driver.find_element(By.ID, "login_password")
        except:
            p = driver.find_element(By.NAME, "password")
        p.clear()
        p.send_keys(password)
        time.sleep(0.3)

        # Click login
        try:
            btn = driver.find_element(By.CSS_SELECTOR, "button[type='submit']")
        except:
            btn = driver.find_element(By.XPATH, "//button[contains(.,'Login') or contains(.,'Log in')]")
        driver.execute_script("arguments[0].click();", btn)
        time.sleep(wait_after + 2)

        # Check login success by looking for profile link or logout
        if "login" in driver.current_url.lower():
            # still on login page → login failed or 2FA/captcha
            return False
        return True
    except Exception as e:
        print("login error:", e)
        return False


def save_cookies(driver, path: str = COOKIE_PATH_DEFAULT):
    cookies = driver.get_cookies()
    with open(path, "w", encoding="utf-8") as f:
        json.dump(cookies, f)
    print(f"[cookies] saved to {path}")


def load_cookies(driver, path: str = COOKIE_PATH_DEFAULT):
    if not os.path.exists(path):
        raise FileNotFoundError(path)
    driver.get("https://internshala.com")
    time.sleep(1)
    with open(path, "r", encoding="utf-8") as f:
        cookies = json.load(f)
    for c in cookies:
        # remove problematic fields
        c.pop("sameSite", None)
        try:
            driver.add_cookie(c)
        except Exception:
            pass
    driver.refresh()
    time.sleep(1)
    print("[cookies] loaded")


# ------------------------
# APPLY HELPERS
# ------------------------
def safe_click(driver, element):
    try:
        driver.execute_script("arguments[0].scrollIntoView({block:'center'});", element)
        time.sleep(0.2)
        element.click()
        return True
    except (ElementClickInterceptedException, Exception):
        try:
            driver.execute_script("arguments[0].click();", element)
            return True
        except Exception:
            return False


def upload_file_input(driver, file_path):
    """
    Find a file input and upload. Returns True if uploaded.
    """
    try:
        # common internshala selector for file input
        inputs = driver.find_elements(By.CSS_SELECTOR, "input[type='file']")
        if not inputs:
            return False
        # choose the largest visible input (heuristic)
        for inp in inputs:
            try:
                driver.execute_script("arguments[0].style.display='block';", inp)
                inp.send_keys(file_path)
                time.sleep(1)
                return True
            except Exception:
                continue
        return False
    except Exception as e:
        print("upload error:", e)
        return False


def apply_to_job(driver, job_link: str, applicant_info: Dict, resume_path: Optional[str] = None, wait_after=2) -> Dict:
    """
    Try to apply to a single Internshala job page.
    Returns dict: {"status": "applied"/"skipped"/"error", "message": "...", "link": job_link}
    This is best-effort: site layout changes or additional required fields may need custom handling.
    """
    result = {"link": job_link, "status": "skipped", "message": ""}

    try:
        driver.get(job_link)
        time.sleep(2)

        # Look for an 'Apply' or 'Apply now' button
        apply_btn = None
        try:
            apply_btn = driver.find_element(By.XPATH, "//a[contains(@class,'apply') or contains(.,'Apply') or contains(.,'Apply now')]")
        except Exception:
            try:
                # new layout: buttons with text "Apply"
                apply_btn = driver.find_element(By.XPATH, "//button[contains(.,'Apply') or contains(.,'Apply now')]")
            except Exception:
                apply_btn = None

        if not apply_btn:
            result["message"] = "Apply button not found"
            return result

        # Click the apply button
        clicked = safe_click(driver, apply_btn)
        time.sleep(1.2)

        # After clicking, a modal or form appears. Fill fields.
        # Fill common fields by name or placeholder heuristics
        field_map = {
            "name": ["name", "full_name", "applicant_name"],
            "email": ["email", "applicant_email"],
            "phone": ["phone", "mobile", "contact"],
            "college": ["college", "institute", "university"],
            "location": ["location", "city"],
            "linkedin": ["linkedin", "linkedin_profile", "profile_link"],
            "portfolio": ["portfolio", "portfolio_link", "website"]
        }

        # find inputs and fill
        inputs = driver.find_elements(By.CSS_SELECTOR, "input, textarea")
        for inp in inputs:
            try:
                n = inp.get_attribute("name") or ""
                ph = inp.get_attribute("placeholder") or ""
                labels = (n + " " + ph).lower()
                for key, candidates in field_map.items():
                    if any(c in labels for c in candidates):
                        val = applicant_info.get(key)
                        if val:
                            try:
                                inp.clear()
                            except Exception:
                                pass
                            inp.send_keys(str(val))
                            time.sleep(0.15)
            except Exception:
                continue

        # Try to upload resume if present
        uploaded = False
        if resume_path:
            uploaded = upload_file_input(driver, resume_path)

        # Some internshala forms may have a submit button like input[type=submit] or button[type=submit]
        try:
            submit_el = driver.find_element(By.XPATH, "//button[contains(.,'Submit') or contains(.,'Apply') or @type='submit']")
            safe_click(driver, submit_el)
            time.sleep(wait_after)
            result["status"] = "applied"
            result["message"] = "Applied (clicked submit)"
            return result
        except Exception:
            # maybe modal requires closing or another flow — treat as manual
            result["status"] = "manual_required"
            result["message"] = "Form visible but auto-submit not found; manual submit may be needed"
            return result

    except Exception as e:
        result["status"] = "error"
        result["message"] = str(e)
        return result


# ------------------------
# BATCH APPLY
# ------------------------
def batch_apply(job_links: List[str],
                mode: str,
                applicant_info: Dict,
                resume_path: Optional[str] = None,
                cookie_path: Optional[str] = COOKIE_PATH_DEFAULT,
                credentials: Optional[Dict] = None,
                headless: bool = False):
    """
    job_links: list of internship detail URLs (Internshala)
    mode: "auto" or "semi"  (auto = Mode1 fully automatic, semi = Mode2 semi-automatic)
    applicant_info: dict for filling fields
    resume_path: path to resume file to upload
    cookie_path: optional path for cookies
    credentials: optional {"email","password"} to login if cookies not present
    headless: whether to run driver headless
    """
    driver = create_driver(headless=headless)

    # Prefer cookies if present
    try:
        if cookie_path and os.path.exists(cookie_path):
            load_cookies(driver, cookie_path)
            print("[batch_apply] loaded cookies")
        elif credentials:
            ok = login_with_credentials(driver, credentials.get("email"), credentials.get("password"), headless=headless)
            if not ok:
                print("[batch_apply] login failed with provided credentials")
            else:
                # save cookies for future runs
                try:
                    save_cookies(driver, cookie_path)
                except Exception:
                    pass
    except Exception as e:
        print("cookie/login warning:", e)

    results = []
    if mode == "auto":
        # fully automatic: apply to all links
        for link in job_links:
            res = apply_to_job(driver, link, applicant_info, resume_path)
            results.append(res)
    else:
        # semi automatic: return list and allow caller to choose which to apply.
        # For convenience: apply only to links that the caller marked in applicant_info['apply_list'] if present
        apply_list = applicant_info.get("apply_list")
        if not apply_list:
            # if none provided, just return job metadata for caller to display and choose
            for link in job_links:
                results.append({"link": link, "status": "pending", "message": "awaiting selection"})
        else:
            for link in job_links:
                if link in apply_list:
                    res = apply_to_job(driver, link, applicant_info, resume_path)
                else:
                    res = {"link": link, "status": "skipped", "message": "user did not select"}
                results.append(res)

    driver.quit()
    return results
