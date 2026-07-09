# Pure Work AI

**AI-Powered Workforce Operating System**

Built by Meridian, Manager of HR Intelligence at Pure Technology.

## What It Does

Pure Work AI is a complete HR platform that handles employee management, compliance, training, assessments, and workforce analytics across multiple jurisdictions.

## Platform Modules

| Module | Description |
|--------|-------------|
| **Dashboard** | Real-time workforce metrics and activity feed |
| **Assessments** | 13 interactive assessments (DISC, Big Five, Culture Fit, Safety, Sales Aptitude, and more) |
| **Content Library** | 83 documents across SOPs, policies, JDs, training, onboarding, and comp benchmarking |
| **Onboarding** | Task-based onboarding with manager signoffs and milestone tracking |
| **Policies** | 44 jurisdiction-aware policies with digital acknowledgment and audit trails |
| **Time Off** | PTO request/approval workflow with balance tracking and accrual rules |
| **Performance** | Review cycles with self-assessment, manager review, goal tracking, and 360 feedback |
| **My Profile** | Employee self-service: personal info, compensation, benefits, document vault |
| **Training Studio** | Auto-generates presentations, quizzes, audio scripts, and flashcards from any SOP |
| **Scoring Engines** | 6 AI models: SMART SEARCH, Born To Be Hired, Reputation, BDHT Rules, Interview Framework, Origination Tracking |
| **Reports** | 8 analytics dashboards: Headcount, Turnover, Time-to-Hire, PTO, Compensation, Training, Onboarding, Compliance |

## Jurisdictions Covered

- United States (Federal + state-level: Indiana, New York, California, and more)
- Canada (Ontario, with ESA and OHSA compliance)
- South Africa (BCEA, LRA, EEA, OHSA, COIDA, UIF/PAYE/SDL)

## Industry Verticals

Manufacturing, Healthcare, Hospitality, Construction, Tech/SaaS, Professional Services, Finance, HR, Sales

## Tech Stack

- **Frontend**: Single-page application (vanilla JS, no framework dependencies)
- **Backend**: FastAPI + SQLite (Python)
- **Deployment**: GitHub Pages (static demo) or self-hosted with backend

## Running Locally

```bash
# Install dependencies
pip install fastapi uvicorn

# Start the backend (serves frontend + API on port 8080)
cd backend
python3 server.py
```

Login: admin@demo.com / password123

## Repository Structure

```
public/           Frontend (HTML, CSS, JS)
  assessments/    13 interactive assessment tools
  content/        83 downloadable HR documents (.docx)
backend/          FastAPI server + SQLite database
  server.py       API server (22 endpoints)
  schema.sql      Database schema
  purework.db     SQLite database (auto-created)
```

## Related Repositories

- [meridian-hr-platform](https://github.com/Meridian-PT/meridian-hr-platform) - Scoring engines (standalone Python modules)
- [pf-hr-module](https://github.com/Meridian-PT/pf-hr-module) - Pier Foundations client deployment

---

Pure Technology | Toronto, ON | puretechnology.nyc
