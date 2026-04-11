# DSA CRM - Setup & Installation Guide

## **Prerequisites**

- Python 3.8 or higher
- PostgreSQL 11 or higher
- Git
- Virtual Environment Manager (venv)

---

## **1. Environment Setup**

### **Step 1: Clone/Navigate to Project**
```bash
cd /Users/mohammadadeenhussain/Desktop/CRM2
```

### **Step 2: Create Virtual Environment**
```bash
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### **Step 3: Install Dependencies**
```bash
pip install -r requirements.txt
```

### **Step 4: Configure Environment Variables**
```bash
# Copy the example file
cp .env.example .env

# Edit .env with your configuration
nano .env  # or use your preferred editor
```

**Important Environment Variables:**
```
FLASK_ENV=development
FLASK_DEBUG=True
DATABASE_URL=postgresql://postgres:password@localhost:5432/crm_dsa
SECRET_KEY=your-secret-key-here
JWT_SECRET_KEY=your-jwt-secret-here
MAIL_SERVER=smtp.gmail.com
MAIL_USERNAME=your-email@gmail.com
MAIL_PASSWORD=your-app-password
```

---

## **2. Database Setup**

### **Step 1: Create PostgreSQL Database**
```bash
# Connect to PostgreSQL
psql -U postgres

# Create database
CREATE DATABASE crm_dsa;
CREATE USER crm_user WITH PASSWORD 'secure_password';
ALTER ROLE crm_user SET client_encoding TO 'utf8';
ALTER ROLE crm_user SET default_transaction_isolation TO 'read committed';
ALTER ROLE crm_user SET default_transaction_deferrable TO on;
ALTER ROLE crm_user SET default_transaction_read_committed TO on;
\q
```

### **Step 2: Grant Privileges**
```bash
psql -U postgres -c "GRANT ALL PRIVILEGES ON DATABASE crm_dsa TO crm_user;"
```

### **Step 3: Update DATABASE_URL in .env
```
DATABASE_URL=postgresql://crm_user:secure_password@localhost:5432/crm_dsa
```

### **Step 4: Initialize Database**
```bash
python3 run.py
```

This will:
- Create all database tables
- Initialize default roles (SUPER_ADMIN, ADMIN, EMPLOYEE)

---

## **3. Create Initial Admin User**

### **Option A: Via Python Shell**
```bash
python3
>>> from app import create_app
>>> from app.models.user import User, db
>>> from app.models.role import Role
>>> app = create_app('development')
>>> with app.app_context():
...     role = Role.query.filter_by(name='SUPER_ADMIN').first()
...     admin_user = User(
...         email='admin@dsacrm.com',
...         full_name='Administrator',
...         mobile='9876543210',
...         role_id=role.id
...     )
...     admin_user.set_password('Admin123!')
...     db.session.add(admin_user)
...     db.session.commit()
>>>  print("Admin user created successfully!")
```

### **Option B: Via Script**
Create `create_admin.py`:
```python
from app import create_app
from app.models.user import User, db
from app.models.role import Role

app = create_app('development')
with app.app_context():
    role = Role.query.filter_by(name='SUPER_ADMIN').first()
    admin_user = User(
        email='admin@dsacrm.com',
        full_name='Administrator',
        mobile='9876543210',
        role_id=role.id
    )
    admin_user.set_password('Admin123!')
    db.session.add(admin_user)
    db.session.commit()
    print("Admin user created successfully!")
```

Run it:
```bash
python3 create_admin.py
```

---

## **4. Run the Application**

### **Development Mode:**
```bash
python3 run.py
```

The application will be available at: **http://localhost:5000**

### **Production Mode (with Gunicorn):**
```bash
# Install Gunicorn
pip install gunicorn

# Run with Gunicorn
gunicorn -w 4 -b 0.0.0.0:5000 wsgi:app
```

---

## **5. Default Login Credentials**

**Email:** admin@dsacrm.com  
**Password:** Admin123!  
**Role:** Super Admin

---

## **6. Database Migrations (If Needed)**

### **Create Migration**
```bash
flask db migrate -m "Description of changes"
```

### **Apply Migration**
```bash
flask db upgrade
```

### **Downgrade Migration**
```bash
flask db downgrade
```

---

## **7. File Uploads**

The system supports file uploads for documents. Ensure the uploads folder exists:
```bash
mkdir -p app/uploads
chmod 755 app/uploads
```

---

## **8. Testing the Setup**

### **Test Database Connection**
```bash
python3
>>> from app import create_app
>>> app = create_app('development')  
>>> app.config['SQLALCHEMY_DATABASE_URI']
```

### **Test Email Service**
```python
from app.services.email_service import EmailService
EmailService.send_email('test@email.com', 'Test Subject', 'Test Body')
```

### **Run Unit Tests**
```bash
pytest tests/
```

---

## **9. Deactivate Virtual Environment**
```bash
deactivate
```

---

## **10. Troubleshooting**

### **Database Connection Error**
```
Error: psycopg2.OperationalError: could not translate host name "localhost" to address
```
**Solution:** Ensure PostgreSQL is running
```bash
# On macOS
brew services start postgresql

# On Linux
sudo systemctl start postgresql
```

### **ModuleNotFoundError**
```
ModuleNotFoundError: No module named 'app'
```
**Solution:** Ensure you're in the correct directory and virtual environment is activated
```bash
cd /Users/mohammadadeenhussain/Desktop/CRM2
source venv/bin/activate
```

### **Port Already in Use**
```
Address already in use
```
**Solution:** Change the port in `run.py` or kill the process using port 5000
```bash
# Find process using port 5000
lsof -i :5000

# Kill process
kill -9 <PID>
```

---

## **11. Project Features**

✅ **Authentication & Authorization**
- Email/Password Login
- 2FA Support
- Role-Based Access Control (RBAC)
- Session Management

✅ **Lead Management**
- Lead Creation & Management
- Lead Status Pipeline (Kanban)
- Customer Financial Details
- Lead Search & Filtering

✅ **Commission Tracking**
- Commission Calculation
- Employee/Admin/Company Splits
- Payout Management
- Commission Reports

✅ **Document Management**
- Secure Document Upload
- Document Verification
- Version Management
- Automatic Storage

✅ **Task & Reminder System**
- Task Management
- Automated Reminders
- Task Notifications
- Due Date Tracking

✅ **Analytics & Reports**
- Performance Dashboard
- Commission Analytics
- Lead Analytics
- Export to CSV/Excel

✅ **User Management** (Super Admin Only)
- Employee Management
- Role & Permission Management
- User Activity Logs
- Audit Trails

---

## **12. Development Server**

For additional development features, use Flask's development server with auto-reload:
```bash
FLASK_APP=run.py FLASK_ENV=development FLASK_DEBUG=True python3 run.py
```

---

## **13. Production Deployment**

See `DEPLOYMENT.md` for production deployment instructions (AWS, Heroku, DigitalOcean, etc.)

---

## **Support & Documentation**

- **Project Folder:** `/Users/mohammadadeenhussain/Desktop/CRM2`
- **Main App Entry:** `run.py`
- **WSGI Entry:** `wsgi.py`
- **Configuration:** `app/config.py`
- **Database Models:** `app/models/`
- **API Routes:** `app/routes/`
- **Services:** `app/services/`
- **Templates:** `app/templates/`

---

**Last Updated:** April 12, 2026
