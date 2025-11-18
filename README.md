AutoApply AI – Real-Time Job Scraper + AI Resume Analyzer + Auto Job Apply System

AutoApply AI is an end-to-end job automation system designed to simplify and accelerate the job search and application process for students and freshers.
The system scrapes real-time job listings, analyzes resumes using AI, ranks jobs based on relevance, and automatically applies to Internshala jobs using Selenium.

Features
1. Real-Time Job Scraping

Scrapes job listings from:

Internshala (Selenium)

Naukri.com (Selenium)

Indeed (optional future extension)

Extracted details include:

Job Title

Company Name

Skills

Salary

Posted Date

Job Description

Job Link

2. Resume Parser

Supports PDF and DOCX formats.

Extracts:

Skills

Location

Experience keywords

Contact info

Suggested job title

Also includes:

AI Skill Extraction

AI Resume Suggestions

3. AI Job Matching

Each job is matched against the candidate’s resume using:

Gemini AI (if API available)

NLP fallback system (token similarity)

Produces:

AI Match Score (0–100)

Explanation Reason

4. Dashboard UI (Streamlit)

Includes:

Job scraping form

Resume upload section

All jobs table

Matched jobs table

LinkedIn-style job grid view

Expandable job details

Excel export for job data

5. Auto Apply System (Internshala)

Two modes:

Mode 1 — Fully Automatic

Automatically applies to all matching jobs.

Mode 2 — Semi-Automatic

User selects desired jobs → Bot applies only to selected ones.

The automation fills:

Candidate details

Cover letter

Additional questions

Resume upload

Final submission

Project Structure
AutoApply-AI/
│
├── main.py                          # Streamlit dashboard
├── requirements.txt                 # Dependencies
│
├── scraper/
│   ├── internshala_realtime.py      # Selenium scraper (Internshala)
│   ├── naukri_realtime.py           # Selenium scraper (Naukri)
│   ├── resume_parser.py             # Resume text extraction and AI
│   ├── utils.py                     # Helper functions (skills, emails, days)
│   └── selenium_driver.py           # WebDriver manager
│
└── README.md

Installation
1. Clone the Repository
git clone https://github.com/yourusername/AutoApply-AI.git
cd AutoApply-AI

2. Install Dependencies
pip install -r requirements.txt

3. Run the App
streamlit run main.py

Environment Variables (Optional for AI)

To enable Gemini-based AI matching and resume improvement:

GEMINI_API_KEY=your_api_key_here

Technologies Used
Frontend

Streamlit (UI)

Backend

Python

Selenium

BeautifulSoup4

Pandas

Regular Expressions

AI

Google Gemini API

NLP token similarity (fallback)

How It Works

User uploads resume → resume parser extracts skills and suggestions

User enters job search filters

Selenium scrapers collect job data in real time

Job descriptions are matched to the resume

Dashboard displays:

All scraped jobs

AI-matched jobs

Grid view

Job details

User selects auto-apply mode

Selenium bot applies on Internshala automatically

Future Enhancements

Auto apply for Naukri and Indeed

Captcha and OTP handling

Chrome extension for real-time notifications

Cloud-based automated scraping

Scheduling system for daily auto apply

Contributing

Pull requests are welcome.
For major changes, please open an issue first to discuss the proposed changes.