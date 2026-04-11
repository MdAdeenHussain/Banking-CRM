# 🏦 DSA CRM Platform - Banking Loan Distribution System

**A Production-Ready, Enterprise-Grade CRM for Banking DSA Agencies**

> **Status:** ✅ Complete & Ready for Development
> **Build Date:** April 12, 2026
> **Tech Stack:** Python Flask + PostgreSQL + HTML5/CSS3/JavaScript

---

## **🎯 Project Overview**

The DSA CRM Platform is a comprehensive, role-based banking loan distribution and lead management system designed specifically for DSA (Direct Selling Agents) agencies and loan distribution businesses.

### **Key Features:**
✅ Full-featured Lead Management System  
✅ Commission Tracking & Calculation  
✅ Multi-role RBAC (Super Admin, Admin, Employee)  
✅ Document Management with Versioning  
✅ Task & Reminder System  
✅ Real-time Analytics & Reporting  
✅ Bank Application Routing  
✅ Invoice & Payout Management  
✅ CSV/Excel Export Functionality  
✅ Mobile-Responsive Design  
✅ Audit Logging & Compliance  
✅ 2FA Authentication  

---

## **📁 Project Structure**

```
CRM2/
├── app/                          # Main Flask application
│   ├── models/                   # Database models (20 models)
│   ├── routes/                   # API endpoints (13 route files)
│   ├── services/                 # Business logic services (9 services)
│   ├── utils/                    # Utility functions & decorators
│   ├── templates/                # HTML templates (20+ pages)
│   └── static/                   # CSS, JS, Images
├── requirements.txt              # Python dependencies
├── run.py                        # Application entry point
├── wsgi.py                       # WSGI configuration
├── .env.example                  # Environment variables template
├── SETUP.md                      # Installation guide
└── README.md                     # This file
```

---

## **🚀 Quick Start**

### **1. Install Dependencies**
```bash
cd /Users/mohammadadeenhussain/Desktop/CRM2
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### **2. Setup Database**
```bash
# Create PostgreSQL database and configure .env
cp .env.example .env
# Edit .env with your database credentials
```

### **3. Run Application**
```bash
python3 run.py
```

### **4. Access Application**
- URL: `http://localhost:5000`
- Default Admin: `admin@dsacrm.com` / `Admin123!`

**See `SETUP.md` for detailed setup instructions.**

---

## **👥 Roles & Permissions**

### **SUPER_ADMIN** - Full system access
- Employee & User management
- Commission control
- Audit logs & compliance
- System settings

### **ADMIN** - Operations Manager
- Employee management
- Lead assignment
- Performance tracking
- Report generation

### **EMPLOYEE** - Loan Relationship Executive
- Lead creation
- Customer status updates
- Document uploads
- Task management

---

## **📊 Core Modules**

1. **Lead Management** - Create, track, and manage customer leads
2. **Commission Tracker** - Calculate and manage commission payouts
3. **Document Management** - Secure storage and versioning
4. **Task & Reminders** - Task assignment and notifications
5. **Analytics & Reports** - Real-time dashboards and insights
6. **Invoice Generation** - Create and manage invoices
7. **User Management** - Employee & role configuration
8. **Audit Logs** - Compliance and activity tracking

---

## **🔐 Security Features**

✅ Email + Password authentication  
✅ 2FA (OTP-based)  
✅ Role-based access control  
✅ Session management  
✅ Audit logging  
✅ Password hashing  
✅ CSRF protection  
✅ Secure cookies  

---

## **💻 Tech Stack**

**Backend:** Python, Flask, SQLAlchemy  
**Database:** PostgreSQL  
**Frontend:** HTML5, CSS3, JavaScript  
**Analytics:** Chart.js, Matplotlib  

---

## **📋 System Requirements**

- Python 3.8+
- PostgreSQL 11+
- Pip package manager
- Virtual environment

---

## **🆘 Troubleshooting**

1. **Database Connection Error** - Ensure PostgreSQL is running
2. **Port Already in Use** - Change port or kill existing process
3. **Module Not Found** - Verify virtual environment is activated
4. **Missing Dependencies** - Run `pip install -r requirements.txt`

See `SETUP.md` for detailed troubleshooting.

---

## **📚 Documentation**

- **Setup Guide:** `SETUP.md`
- **Models:** `app/models/` - Database schema
- **Routes:** `app/routes/` - API endpoints
- **Services:** `app/services/` - Business logic
- **Templates:** `app/templates/` - HTML pages
- **Static:** `app/static/` - CSS, JS, Images

---

## **✨ Production Ready**

This system includes:
- Modular architecture
- Comprehensive error handling
- Database migrations
- Audit logging
- Role-based security
- Mobile responsiveness
- Scalable design

---

## **📝 License**

Proprietary software. Unauthorized copying prohibited.

---

**Version 1.0.0 | Last Updated: April 12, 2026**

For complete setup instructions, see `SETUP.md`