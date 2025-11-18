# scraper/db.py
import os
import sqlite3
import hashlib
import secrets
from typing import Optional, List, Dict

DB_PATH = os.path.join("data", "users.db")

def _get_conn():
    os.makedirs("data", exist_ok=True)
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    return conn

def init_db():
    """
    Initialize database and required tables.
    This creates a 'users' table with resume fields included and a saved_searches table.
    """
    conn = _get_conn()
    cur = conn.cursor()

    cur.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE,
        email TEXT UNIQUE,
        pwd_hash TEXT,
        salt TEXT,
        resume_text TEXT,
        resume_skills TEXT,
        resume_location TEXT,
        resume_job_title TEXT,
        resume_experience TEXT,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP
    )
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS saved_searches (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        name TEXT,
        role TEXT,
        location TEXT,
        job_type TEXT,
        min_salary INTEGER,
        max_salary INTEGER,
        skills TEXT,
        keyword TEXT,
        recent_days INTEGER,
        headless INTEGER,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY(user_id) REFERENCES users(id)
    )
    """)
    conn.commit()
    conn.close()

# ---------- Password hashing (PBKDF2) ----------
def _hash_password(password: str, salt: Optional[bytes] = None):
    if salt is None:
        salt = secrets.token_bytes(16)
    pwd_hash = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, 150000)
    return pwd_hash.hex(), salt.hex()

def _verify_password(password: str, stored_hash_hex: str, salt_hex: str) -> bool:
    salt = bytes.fromhex(salt_hex)
    pwd_hash = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, 150000)
    return pwd_hash.hex() == stored_hash_hex

# ---------- User CRUD ----------
def create_user(username: str, email: str, password: str) -> bool:
    conn = _get_conn()
    cur = conn.cursor()
    try:
        pwd_hash, salt = _hash_password(password)
        cur.execute("INSERT INTO users (username, email, pwd_hash, salt) VALUES (?, ?, ?, ?)",
                    (username, email, pwd_hash, salt))
        conn.commit()
        return True
    except sqlite3.IntegrityError:
        return False
    finally:
        conn.close()

def authenticate_user(email_or_username: str, password: str) -> Optional[Dict]:
    conn = _get_conn()
    cur = conn.cursor()
    cur.execute("SELECT id, username, email, pwd_hash, salt FROM users WHERE email=? OR username=?",
                (email_or_username, email_or_username))
    row = cur.fetchone()
    conn.close()
    if not row:
        return None
    uid, username, email, stored_hash, salt = row
    if _verify_password(password, stored_hash, salt):
        return {"id": uid, "username": username, "email": email}
    return None

def get_user_by_id(user_id: int) -> Optional[Dict]:
    conn = _get_conn()
    cur = conn.cursor()
    cur.execute("SELECT id, username, email, resume_text, resume_skills, resume_location, resume_job_title, resume_experience FROM users WHERE id=?", (user_id,))
    r = cur.fetchone()
    conn.close()
    if not r:
        return None
    return {
        "id": r[0],
        "username": r[1],
        "email": r[2],
        "resume_text": r[3],
        "resume_skills": r[4],
        "resume_location": r[5],
        "resume_job_title": r[6],
        "resume_experience": r[7]
    }

# Update resume fields for a user
def update_resume(user_id: int, resume_text: str, resume_skills: str = "", resume_location: str = "", resume_job_title: str = "", resume_experience: str = "") -> bool:
    conn = _get_conn()
    cur = conn.cursor()
    try:
        cur.execute("""
        UPDATE users SET resume_text=?, resume_skills=?, resume_location=?, resume_job_title=?, resume_experience=?
        WHERE id=?
        """, (resume_text, resume_skills, resume_location, resume_job_title, resume_experience, user_id))
        conn.commit()
        return True
    except Exception:
        return False
    finally:
        conn.close()

# ---------- Saved searches ----------
def save_search(user_id: int, name: str, params: dict) -> bool:
    """
    params expected keys: role, location, job_type, min_salary, max_salary, skills, keyword, recent_days, headless
    """
    conn = _get_conn()
    cur = conn.cursor()
    try:
        cur.execute("""
        INSERT INTO saved_searches
        (user_id, name, role, location, job_type, min_salary, max_salary, skills, keyword, recent_days, headless)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            user_id,
            name,
            params.get("role"),
            params.get("location"),
            params.get("job_type"),
            int(params.get("min_salary") or 0),
            int(params.get("max_salary") or 0),
            params.get("skills") or "",
            params.get("keyword") or "",
            int(params.get("recent_days") or 14),
            1 if params.get("headless") else 0
        ))
        conn.commit()
        return True
    except Exception:
        return False
    finally:
        conn.close()

def list_saved_searches(user_id: int) -> List[Dict]:
    conn = _get_conn()
    cur = conn.cursor()
    cur.execute("""
    SELECT id, name, role, location, job_type, min_salary, max_salary, skills, keyword, recent_days, headless, created_at
    FROM saved_searches WHERE user_id=? ORDER BY created_at DESC
    """, (user_id,))
    rows = cur.fetchall()
    conn.close()
    results = []
    for r in rows:
        results.append({
            "id": r[0],
            "name": r[1],
            "role": r[2],
            "location": r[3],
            "job_type": r[4],
            "min_salary": r[5],
            "max_salary": r[6],
            "skills": r[7],
            "keyword": r[8],
            "recent_days": r[9],
            "headless": bool(r[10]),
            "created_at": r[11]
        })
    return results

def get_saved_search(user_id:int, search_id:int) -> Optional[Dict]:
    conn = _get_conn()
    cur = conn.cursor()
    cur.execute("""
    SELECT id, name, role, location, job_type, min_salary, max_salary, skills, keyword, recent_days, headless
    FROM saved_searches WHERE user_id=? AND id=?
    """, (user_id, search_id))
    r = cur.fetchone()
    conn.close()
    if not r:
        return None
    return {
        "id": r[0],
        "name": r[1],
        "role": r[2],
        "location": r[3],
        "job_type": r[4],
        "min_salary": r[5],
        "max_salary": r[6],
        "skills": r[7],
        "keyword": r[8],
        "recent_days": r[9],
        "headless": bool(r[10])
    }

def delete_saved_search(user_id:int, search_id:int) -> bool:
    conn = _get_conn()
    cur = conn.cursor()
    cur.execute("DELETE FROM saved_searches WHERE user_id=? AND id=?", (user_id, search_id))
    conn.commit()
    affected = cur.rowcount
    conn.close()
    return affected > 0
