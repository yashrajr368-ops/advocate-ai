# ⚖️ Legal AI Assistant & Practice Management Portal
### *Official Digital Chambers of Advocate Mukesh Singh Rathod — Private Advocate & Legal Counsel*

[![Python](https://img.shields.io/badge/Python-3.12+-blue.svg?logo=python&logoColor=white)](https://www.python.org/)
[![Flask](https://img.shields.io/badge/Flask-3.1-black.svg?logo=flask&logoColor=white)](https://flask.palletsprojects.com/)
[![Gemini AI](https://img.shields.io/badge/Google_Gemini-AI_Triage-orange.svg?logo=google&logoColor=white)](https://ai.google.dev/)
[![Bootstrap](https://img.shields.io/badge/Bootstrap-5.3-purple.svg?logo=bootstrap&logoColor=white)](https://getbootstrap.com/)
[![SQLite](https://img.shields.io/badge/SQLite-Database-003B57.svg?logo=sqlite&logoColor=white)](https://www.sqlite.org/)
[![Bilingual](https://img.shields.io/badge/Language-English_%7C_%E0%A4%B9%E0%A4%BF%E0%A4%82%E0%A4%A6%E0%A4%8 need-green.svg)](#-bilingual-support-english--हिंदी)
[![Tests](https://img.shields.io/badge/Tests-10%2F10_Passing-brightgreen.svg)](#-automated-testing)

---

## 📌 Overview

A production-grade, full-stack Legal Assistance and Case Practice Management platform built for **Advocate Mukesh Singh Rathod — Private Advocate & Legal Counsel** practicing before the **District & Sessions Courts (Khandwa)**, **Sub-Divisional Civil & Criminal Courts (Harsud-Chhanera)**, Revenue Courts, and Consumer Dispute Redressal Commissions in Madhya Pradesh.

The system combines **LLM-driven legal triage (Google Gemini AI)** with an end-to-end **Legal Practice Management System (PMS)**, providing instantaneous legal guidance to citizens and streamlining case tracking, document discovery, and client consultation for legal chambers.

---

## ✨ Key Features

### 🌐 Bilingual Support (English & हिंदी)
- **Instant UI Translation**: 1-click toggle (🌐 English | हिंदी) in top navigation bar translating all pages without page reloads.
- **Bilingual AI Triage Engine**: Automatically detects whether user query is written in Hindi (Devanagari script) or English and responds in the matching language.
- **Persistent Preferences**: Language selection is saved locally across user sessions.

### 🤖 Gemini AI Legal Analysis Desk
- **Structured 5-Point Legal Memorandum**:
  1. **Case Categorization** (Civil, Criminal, Family, Revenue, Consumer, Labour)
  2. **Applicable Laws & Sections** (BNS / IPC, BNSS / CrPC, BSA / Indian Evidence Act, Hindu Marriage Act, NI Act, etc.)
  3. **Required Evidentiary Documentation**
  4. **Next Legal Procedural Steps**
  5. **Executive Legal Summary & Counsel Disclaimer**
- **Strict Indian Law Guardrails**: Domain filtering rejects non-legal prompts with polite guidance.
- **Smart Court Jurisdiction Suggestion**: Automatically maps dispute to appropriate district forum.

### 🏛️ Role-Based Practice Management (RBAC)
- **Advocate Portal**:
  - Live docket overview with stage tracking (*Drafting, Evidence, Cross-Examination, Arguments, Judgment*).
  - Hearing calendar and timeline management.
  - Document discovery and evidence vault.
- **Client Portal**:
  - Transparent case status and next hearing date tracker.
  - Document upload and case note history.
  - 1-click appointment booking with private counsel.
- **Administrator Dashboard**:
  - System-wide caseload analytics, user management, and platform metrics.

### 📑 Court-Ready Legal Dossier
- Generates printable case briefs formatted with official chambers letterhead, bar registration details, court jurisdiction, and Attorney-Client Privilege confidentiality footers.

---

## 🏗️ Technical Architecture

`
[ Client Browser / Mobile ]
            │
    (HTTPS / REST / JSON)
            │
            ▼
┌────────────────────────────────────────────────────────┐
│                   Flask Application                    │
│  ├─ Authentication & Sessions (Flask-Login, Werkzeug)  │
│  ├─ Role-Based Access Control (Advocate, Client, Admin)│
│  ├─ File Upload & Vault Management                     │
│  └─ Dynamic Bilingual View Rendering (Jinja2)          │
└───────────────┬────────────────────────┬───────────────┘
                │                        │
                ▼                        ▼
┌─────────────────────────────┐   ┌──────────────────────────────┐
│       SQLite / SQLAlchemy   │   │     Google Gemini AI Engine  │
│  ├─ User Credentials & Roles│   │  ├─ Language Auto-Detection  │
│  ├─ Cases & Timelines       │   │  ├─ Indian Law Domain Filters│
│  ├─ Evidence Documents      │   │  ├─ 5-Point Legal Memo Gen   │
│  └─ Appointment Bookings    │   │  └─ Case Category Classifier │
└─────────────────────────────┘   └──────────────────────────────┘
`

---

## 🛠️ Tech Stack

| Layer | Technology |
| :--- | :--- |
| **Backend Framework** | Python 3.12+, Flask 3.1 |
| **AI / LLM Engine** | Google Gemini API (gemini-1.5-flash / google-generativeai) |
| **Database & ORM** | SQLite 3, SQLAlchemy ORM, Flask-SQLAlchemy |
| **Authentication** | Flask-Login, Werkzeug Password Hashing (PBKDF2-SHA256) |
| **Frontend & UI** | Bootstrap 5.3, FontAwesome 6, Chart.js, Custom Vanilla JS |
| **WSGI / Production Server** | Gunicorn 21+ |
| **Testing Suite** | Python unittest (10/10 automated tests passing) |

---

## 🚀 Quick Start (Local Installation)

### 1. Clone the Repository
`ash
git clone https://github.com/<your-username>/legal-ai-assistant.git
cd legal-ai-assistant
`

### 2. Set Up Virtual Environment
`ash
# Windows
python -m venv venv
venv\Scripts\activate

# macOS / Linux
python3 -m venv venv
source venv/bin/activate
`

### 3. Install Dependencies
`ash
pip install -r requirements.txt
`

### 4. Configure Environment Variables
Create a .env file in the project root:
`env
SECRET_KEY=your-super-secret-key-for-development
GEMINI_API_KEY=your_google_gemini_api_key_here
`
*(Get a free Gemini API key from [Google AI Studio](https://aistudio.google.com/))*

### 5. Run the Application
`ash
python app.py
`
Open your browser and navigate to: **http://127.0.0.1:5000**

---

## 🧪 Automated Testing

The repository includes a comprehensive 10-point test suite covering authentication, role permissions, AI legal guardrails, case intake, and appointment booking:

`ash
python test_app.py
`

`
----------------------------------------------------------------------
Ran 10 tests in 0.782s

OK
[PASS] Home page loaded with lead counsel Advocate Mukesh Singh Rathod.
[PASS] AI Chatbot legal query returned structured response.
[PASS] AI Chatbot non-legal query was politely declined by guardrail.
[PASS] Client logged in and accessed client dashboard.
[PASS] New case submitted and automatic AI legal analysis generated successfully.
[PASS] Document uploaded, database linked, and downloaded successfully.
[PASS] Advocate dashboard accessed and case status updated successfully.
[PASS] Printable / PDF Case Report view rendered with court formatting.
[PASS] Appointment booking and simulated confirmation email completed.
[PASS] Admin dashboard loaded with system analytics and user controls.
`

---

## 🔐 Demo Accounts (Pre-Seeded)

| Role | Email Address | Password | Description |
| :--- | :--- | :--- | :--- |
| **Advocate** | dvocate@example.com | password123 | Adv. Mukesh Singh Rathod (Senior Private Counsel) |
| **Client** | client@example.com | password123 | Active client portal with pre-loaded civil suit |
| **Admin** | dmin@example.com | password123 | Practice administrator with analytical metrics |

---

## ☁️ 1-Click Free Cloud Deployment (Render.com)

1. Push your repository to **GitHub**.
2. Go to [Render.com](https://render.com) and sign in with GitHub.
3. Click **New +** → **Web Service** → Select this repository.
4. Set the following configuration:
   - **Environment**: Python
   - **Build Command**: pip install -r requirements.txt
   - **Start Command**: gunicorn app:app
5. In **Environment Variables**, add:
   - GEMINI_API_KEY: *(Your Google Gemini API Key)*
   - SECRET_KEY: *(Random secure string)*
6. Click **Deploy Web Service**. Your live URL will be ready at:
   https://<your-service-name>.onrender.com

## 👨‍💻 Author & Lead Engineer

**Yash Raj Singh Rathod**  
- **Degree**: B.Tech in Computer Science & Engineering (Artificial Intelligence)  
- **Institution**: Medi-Caps University, Indore  
- **GitHub**: [@yashrajr368-ops](https://github.com/yashrajr368-ops)  
- **Project Scope**: Designed and engineered for the official practice of **Advocate Mukesh Singh Rathod — Private Advocate & Legal Counsel**.

---

## ⚖️ Legal Disclaimer

This software is an AI-augmented decision support and practice management system built under the guidelines of the **Advocates Act, 1961**. The AI analysis is designed to assist in legal research and preliminary triage. It does not constitute formal legal advice or create an attorney-client relationship without a signed vakalatnama or formal engagement with Advocate Mukesh Singh Rathod.

---

## 📄 License

Distributed under the **MIT License**. See `LICENSE` for more information.

