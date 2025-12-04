# **AutoApply AI – Real-Time Job Scraper + AI Resume Analyzer + Auto Job Apply System**

AutoApply AI is a complete **job automation ecosystem** designed for students, freshers, and job seekers who want to speed up their job search and application process. It automates **job scraping**, **AI resume analysis**, **job matching**, and **auto-application** on Internshala using Selenium.

---

## 🚀 **Features**

### 🔍 **Real-Time Job Scraping**

Scrapes fresh job listings from:

* **Internshala (Selenium)**
* **Naukri.com (Selenium)**
* **Indeed** *(future extension)*

Extracted job fields:

* Job Title
* Company Name
* Skills Required
* Salary
* Posted Date
* Job Description
* Job Link

---

### 📝 **AI-Powered Resume Parser**

Supports **PDF** and **DOCX** formats.

Extracts:

* Skills
* Experience Keywords
* Location
* Contact Details
* Suggested Job Title

Additional AI features:

* **AI Skill Extraction**
* **AI Resume Improvement Suggestions**

---

### 🤖 **AI Job Matching**

Each scraped job is matched with the candidate resume using:

* **Gemini AI** *(if API key available)*
* **NLP Token Similarity** *(fallback)*

Produces:

* **AI Match Score (0–100)**
* **Reason for Score / Match Explanation**

---

### 📊 **Interactive Dashboard (Streamlit)**

The dashboard provides:

* Job Scraping Form
* Resume Upload Section
* All Jobs Table
* Matched Jobs Table
* LinkedIn-style Grid View
* Expandable Job Details
* Export Data to Excel

---

### ⚙️ **Auto Apply System (Internshala)**

Two modes are supported:

#### **Mode 1 — Fully Automatic**

Automatically applies to all relevant job postings.

#### **Mode 2 — Semi-Automatic**

User selects desired jobs → Bot applies only to selected ones.

The automation fills:

* Candidate Details
* Cover Letter
* Additional Questions
* Resume Upload
* Final Submission

---

## 📁 **Project Structure**

```
AutoApply-AI/
│
├── main.py                   # Streamlit dashboard
├── requirements.txt          # Dependencies
│
├── scraper/
│   ├── internshala_realtime.py   # Internshala Selenium scraper
│   ├── naukri_realtime.py        # Naukri Selenium scraper
│   ├── resume_parser.py          # Resume text extraction + AI
│   ├── utils.py                  # Helper functions
│   └── selenium_driver.py        # WebDriver manager
│
└── README.md
```

---

## 🛠️ **Installation & Setup**

### **1️⃣ Clone the Repository**

```bash
git clone https://github.com/yourusername/AutoApply-AI.git
cd AutoApply-AI
```

### **2️⃣ Install Dependencies**

```bash
pip install -r requirements.txt
```

### **3️⃣ Run the Application**

```bash
streamlit run main.py
```

---

## 🔐 **Environment Variables (Optional for AI)**

To enable Gemini‑based job matching and resume enhancement:

```
GEMINI_API_KEY=your_api_key_here
```

---

## 🧠 **Technologies Used**

### **Frontend**

* Streamlit

### **Backend**

* Python
* Selenium
* BeautifulSoup4
* Pandas
* Regex

### **AI & NLP**

* Google Gemini API
* Token Similarity (Fallback)

---

## 🧩 **How It Works**

1. User uploads resume → System extracts skills using parser + AI.
2. User enters job search filters.
3. Selenium scrapers fetch real-time job data.
4. AI/NLP matches job descriptions with the resume.
5. Dashboard displays:

   * All Jobs
   * Matched Jobs
   * Grid View
   * Detailed View
6. User selects **Auto Apply** mode.
7. Selenium bot applies automatically on Internshala.

---

## 🔮 **Future Enhancements**

* Auto Apply for Naukri & Indeed
* OTP & Captcha Handling
* Browser Extension for Real-Time Alerts
* Cloud-Based Automated Scraper
* Auto Scheduling (Daily Apply System)

---

## 🤝 **Contributing**

Pull requests are welcome.
For major changes, open an issue first to discuss improvements.

---

## 📄 **License**

This project is open-source under the MIT License.
