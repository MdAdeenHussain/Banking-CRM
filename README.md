# 🏦 AI-Powered Banking CRM SaaS

### Multi-Tenant FinTech CRM with AI, Fraud Detection & Automation

---

## 🚀 Overview

This project is a **production-grade AI-integrated Banking CRM SaaS platform** designed for **DSA (Direct Selling Agents), NBFCs, and loan processing agencies**.

It enables businesses to:

* Manage leads, customers, and loan applications
* Automate workflows and follow-ups
* Detect fraud using AI + anomaly detection
* Recommend lenders intelligently
* Analyze performance with advanced dashboards
* Operate as a scalable **multi-tenant SaaS platform**

---

## ✨ Core Features

### 📊 CRM & Workflow

* Lead management with pipeline tracking
* Customer 360 profiles
* Loan application workflow engine
* Multi-branch & role-based dashboards

### 🤖 AI & Intelligence

* Lead scoring (ML)
* Loan eligibility prediction
* Lender recommendation engine
* AI assistant (call summaries, next actions, message drafts)
* RAG-based memory system

### 🛡 Fraud Detection

* Rule-based + AI anomaly detection
* Document forensic analysis
* Device fingerprinting & identity graph
* Fraud risk scoring + alerts

### ⚙️ Automation Engine

* Email, SMS, WhatsApp automation
* Follow-up sequences
* SLA reminders & escalation
* Meta Ads lead integration

### 📈 Analytics & Reports

* Funnel analysis
* Branch & agent leaderboard
* Lender performance heatmaps
* Exportable reports (PDF/CSV)

### 💳 SaaS Billing

* Subscription plans (Starter, Growth, Enterprise)
* Razorpay + Stripe integration
* Usage metering (AI, users, storage)
* Invoice generation

### 🏢 Multi-Tenant SaaS

* White-label branding
* Tenant management
* Platform admin dashboard
* Usage monitoring + SLA tracking

### 🔐 Compliance System

* Maker-checker workflow
* Audit logs (immutable)
* KYC verification
* Blacklist engine

---

## 🧱 Tech Stack

### Frontend

* HTML5, CSS3, JavaScript
* Tailwind CSS + Bootstrap
* Bento Grid UI + Neumorphism

### Backend

* Python 3.11 + Flask
* SQLAlchemy ORM
* PostgreSQL

### AI / ML

* Scikit-learn (ML models)
* Local LLM (Ollama, Llama, Mistral)
* OpenAI / Claude / Gemini (fallback)
* RAG (FAISS / ChromaDB)

### Infrastructure

* Redis (caching)
* Celery (async tasks)
* Gunicorn + Nginx
* Docker

### Cloud / Deployment

* Render / AWS / VPS
* S3 / Cloudinary

---

## 📂 Project Structure

```
project_root/
│
├── app/
│   ├── templates/        # HTML pages
│   ├── static/           # CSS, JS, assets
│   ├── models/           # DB models
│   ├── services/         # business logic
│   ├── ai_engine/        # ML + LLM
│   ├── rag_engine/       # vector memory
│   ├── fraud_ai/         # fraud detection
│   ├── automation_engine/
│   ├── analytics_engine/
│   ├── billing_engine/
│   ├── compliance_engine/
│   ├── platform_admin/
│
├── docker/
├── migrations/
├── tests/
├── run.py
├── requirements.txt
```

---

## 🔑 Demo Credentials

Use these credentials to test the system:

| Role           | Email                                                 | Password |
| -------------- | ----------------------------------------------------- | -------- |
| Owner Admin    | [demo@bankcrm.ai](mailto:demo@bankcrm.ai)             | Demo@123 |
| Branch Manager | [branch@bankcrm.ai](mailto:branch@bankcrm.ai)         | Demo@123 |
| Agent          | [agent@bankcrm.ai](mailto:agent@bankcrm.ai)           | Demo@123 |
| Compliance     | [compliance@bankcrm.ai](mailto:compliance@bankcrm.ai) | Demo@123 |
| Super Admin    | [superadmin@bankcrm.ai](mailto:superadmin@bankcrm.ai) | Demo@123 |

**Tenant Slug:** `demo-bank`

---

## 🧪 Demo Mode

Enable demo mode in config:

```python
DEMO_MODE = True
```

Features in demo mode:

* Mock AI responses
* Dummy data preloaded
* No real payment/API calls
* Safe testing environment

---

## ⚙️ Installation

### 1. Clone Repository

```bash
git clone https://github.com/your-username/banking-crm.git
cd banking-crm
```

---

### 2. Create Virtual Environment

```bash
python -m venv venv
source venv/bin/activate   # Mac/Linux
venv\Scripts\activate      # Windows
```

---

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

---

### 4. Setup Environment Variables

Create `.env` file:

```env
SECRET_KEY=your_secret
DATABASE_URL=postgresql://user:pass@localhost/db
REDIS_URL=redis://localhost:6379
JWT_SECRET_KEY=your_jwt_secret

OPENAI_API_KEY=your_key
STRIPE_SECRET=your_key
RAZORPAY_KEY=your_key
```

---

### 5. Run Database Migrations

```bash
flask db upgrade
```

---

### 6. Run Server

```bash
python run.py
```

App runs at:
👉 http://127.0.0.1:5000

---

## 🐳 Docker Setup

```bash
docker-compose up --build
```

---

## 📡 API Endpoints (Examples)

```
POST /api/v1/ai/lead-score
POST /api/v1/ai/eligibility
POST /api/v1/fraud/check
GET  /api/v1/analytics/funnel
POST /api/v1/billing/subscribe
```

---

## 🔁 Workflow Example

```
Lead → Customer → Documents → Eligibility → Lender → Application → Fraud Check → Approval → Disbursal
```

---

## 📊 AI Capabilities

* Lead conversion prediction
* Loan eligibility scoring
* Fraud risk detection
* Lender ranking
* Call summarization
* Next best action recommendation

---

## 🔐 Security Features

* JWT Authentication
* Role-based access control (RBAC)
* Tenant isolation
* Audit logs
* Secure password hashing
* API validation

---

## 📈 Deployment

### Render

* Add `render.yaml`
* Deploy web + worker services

### AWS

* EC2 (App)
* RDS (PostgreSQL)
* S3 (storage)
* Nginx + Gunicorn

---

## 🧠 Future Enhancements

* Real-time analytics (Kafka)
* Mobile app (React Native)
* Voice AI assistant
* Credit bureau integrations
* Advanced CV-based document fraud detection

---

## 👨‍💻 Author

**Md Adeen Hussain**
Web Developer | AI SaaS Builder

---

## 📄 License

This project is licensed under the MIT License.

---

## ⭐ Final Note

This is a **full-scale AI-powered FinTech CRM SaaS system** designed for:

* startups
* agencies
* enterprise deployment

If you build and deploy this successfully —
👉 you have a **real SaaS product, not just a project.**
