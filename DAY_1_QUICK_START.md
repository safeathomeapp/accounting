# Day 1 Quick Start Guide
**Multi-Platform AI Practice Management System**

**Date:** November 23, 2025  
**Time Required:** 2-3 hours  
**Goal:** Get fully working development environment

---

## ✅ Pre-Flight Checklist

Before starting, confirm:
- [ ] Windows 11
- [ ] Admin rights on laptop
- [ ] Good internet connection
- [ ] 2-3 hours available
- [ ] Coffee ready ☕

---

## 📋 Step 1: Verify Existing Tools (10 mins)

Open GitBash and run these commands:

```bash
# Check Python version (need 3.11+)
python --version

# If Python not found or < 3.11, install from python.org
# Download Python 3.11 or 3.12 installer
# During install: CHECK "Add Python to PATH"

# Check Git (you have this via GitBash)
git --version

# Check PostgreSQL (you said you have this)
psql --version

# If PostgreSQL not found, download from:
# https://www.postgresql.org/download/windows/
```

**Tell me the output of each command.**

---

## 📂 Step 2: Create Project Structure (5 mins)

```bash
# Navigate to your desired location
cd ~
mkdir accountancy
cd accountancy

# Download the initialization files
# (I'll provide download links, or you can copy/paste file contents)

# Verify structure
ls -la
```

**Expected files:**
- PROJECT_INIT.md
- README.md
- .gitignore
- .env.example
- requirements.txt
- MULTI_PLATFORM_ROADMAP.md
- VISION.md
- TECH_STACK.md
- PLATFORM_INTEGRATION_GUIDE.md
- API_COST_OPTIMIZATION.md

---

## 🔧 Step 3: Set Up Virtual Environment (10 mins)

```bash
# Create virtual environment
python -m venv venv

# Activate (GitBash on Windows)
source venv/Scripts/activate

# Your prompt should now show (venv)

# Upgrade pip
pip install --upgrade pip

# Install dependencies
pip install -r requirements.txt

# This will take 5-10 minutes
# Go grab that coffee! ☕
```

**If errors occur, tell me the exact error message.**

---

## 🗄️ Step 4: Set Up PostgreSQL Database (10 mins)

```bash
# Create development database
createdb practice_dev

# Create test database
createdb practice_test

# Verify databases created
psql -l | grep practice

# You should see both databases listed
```

**If PostgreSQL commands not found:**
```bash
# Add PostgreSQL to PATH
# Find your PostgreSQL bin folder (usually C:\Program Files\PostgreSQL\15\bin)
# Add to PATH in Windows Environment Variables
```

---

## 🔑 Step 5: Set Up API Accounts (30 mins)

### 5a. Claude API (5 mins)

1. Go to: https://console.anthropic.com
2. Sign up / Log in
3. Click "API Keys" in sidebar
4. Click "Create Key"
5. Give it a name: "Practice Management Dev"
6. Copy the key (starts with `sk-ant-api03-`)
7. **IMPORTANT:** Save it immediately - shown only once!

### 5b. Xero Developer (10 mins)

1. Go to: https://developer.xero.com
2. Log in with your Xero Partner account
3. Click "My Apps"
4. Click "New App"
5. Fill in:
   - **App name:** Practice Management Dev
   - **Integration type:** Web app
   - **Company/App URL:** http://localhost:8000
   - **OAuth 2.0 redirect URI:** http://localhost:8000/auth/xero/callback
6. Click "Create App"
7. Copy:
   - **Client ID**
   - **Client Secret**

### 5c. QuickBooks Developer (10 mins)

1. Go to: https://developer.intuit.com
2. Log in with your QB Accountant account
3. Click "Dashboard"
4. Click "Create an App"
5. Select "QuickBooks Online and Payments"
6. Fill in:
   - **App name:** Practice Management Dev
   - **Redirect URI:** http://localhost:8000/auth/quickbooks/callback
7. Click "Create App"
8. Go to "Keys & OAuth" tab
9. Copy:
   - **Client ID**
   - **Client Secret**
10. Select "Sandbox" environment (for now)

### 5d. Configure Environment Variables (5 mins)

```bash
# Copy template
cp .env.example .env

# Open .env in your editor
# (Notepad++, VS Code, or any text editor)
notepad .env

# Fill in these values:
# - DATABASE_URL (change username/password if needed)
# - CLAUDE_API_KEY (from step 5a)
# - XERO_CLIENT_ID (from step 5b)
# - XERO_CLIENT_SECRET (from step 5b)
# - QB_CLIENT_ID (from step 5c)
# - QB_CLIENT_SECRET (from step 5c)
# - SECRET_KEY (generate random string)
# - ENCRYPTION_KEY (generate random string)

# Generate random keys:
python -c "import secrets; print('SECRET_KEY=' + secrets.token_urlsafe(32))"
python -c "from cryptography.fernet import Fernet; print('ENCRYPTION_KEY=' + Fernet.generate_key().decode())"

# Save and close .env
```

---

## 🧪 Step 6: Test Setup (30 mins)

### 6a. Test Database Connection

I'll provide this script:

```python
# test_db.py
import os
from sqlalchemy import create_engine, text
from dotenv import load_dotenv

load_dotenv()

def test_database():
    """Test PostgreSQL connection"""
    try:
        db_url = os.getenv('DATABASE_URL')
        engine = create_engine(db_url)
        
        with engine.connect() as conn:
            result = conn.execute(text("SELECT version();"))
            version = result.fetchone()[0]
            print(f"✅ PostgreSQL connected successfully!")
            print(f"Version: {version}")
            return True
    except Exception as e:
        print(f"❌ Database connection failed: {e}")
        return False

if __name__ == "__main__":
    test_database()
```

**Run it:**
```bash
python test_db.py
```

**Expected:** ✅ PostgreSQL connected successfully!

---

### 6b. Test Claude API

I'll provide this script:

```python
# test_claude.py
import os
from anthropic import Anthropic
from dotenv import load_dotenv

load_dotenv()

def test_claude():
    """Test Claude API connection"""
    try:
        api_key = os.getenv('CLAUDE_API_KEY')
        if not api_key:
            print("❌ CLAUDE_API_KEY not found in .env")
            return False
        
        client = Anthropic(api_key=api_key)
        
        message = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=100,
            messages=[
                {"role": "user", "content": "Say 'Hello from Practice Management System!' and nothing else."}
            ]
        )
        
        response = message.content[0].text
        print(f"✅ Claude API connected successfully!")
        print(f"Response: {response}")
        print(f"Tokens used: {message.usage.input_tokens} in, {message.usage.output_tokens} out")
        
        return True
    except Exception as e:
        print(f"❌ Claude API connection failed: {e}")
        return False

if __name__ == "__main__":
    test_claude()
```

**Run it:**
```bash
python test_claude.py
```

**Expected:** ✅ Claude API connected successfully!

---

### 6c. Test Xero OAuth Flow

I'll provide this script (more complex - OAuth flow):

```python
# test_xero.py
import os
from dotenv import load_dotenv

load_dotenv()

def test_xero_credentials():
    """Test Xero credentials are set"""
    client_id = os.getenv('XERO_CLIENT_ID')
    client_secret = os.getenv('XERO_CLIENT_SECRET')
    
    if not client_id or not client_secret:
        print("❌ Xero credentials not found in .env")
        return False
    
    print(f"✅ Xero Client ID: {client_id[:8]}...")
    print(f"✅ Xero Client Secret: {client_secret[:8]}...")
    print("\nNote: Full OAuth test requires running web server")
    print("We'll do that in Step 7")
    
    return True

if __name__ == "__main__":
    test_xero_credentials()
```

**Run it:**
```bash
python test_xero.py
```

**Expected:** ✅ Credentials confirmed

---

## 🏗️ Step 7: Create Base Project Structure (15 mins)

I'll guide you through creating the folder structure:

```bash
# Create backend structure
mkdir -p backend/accounting/xero
mkdir -p backend/accounting/quickbooks
mkdir -p backend/ai
mkdir -p backend/models
mkdir -p backend/api

# Create other directories
mkdir -p scripts
mkdir -p tests
mkdir -p knowledge-base/universal
mkdir -p knowledge-base/xero-specific
mkdir -p knowledge-base/quickbooks-specific
mkdir -p mock-clients/xero
mkdir -p mock-clients/quickbooks
mkdir -p logs
mkdir -p docs

# Create __init__.py files
touch backend/__init__.py
touch backend/accounting/__init__.py
touch backend/accounting/xero/__init__.py
touch backend/accounting/quickbooks/__init__.py
touch backend/ai/__init__.py
touch backend/models/__init__.py
touch backend/api/__init__.py

# Verify structure
tree -L 3
# Or: find . -type d
```

---

## 🎯 Step 8: Initialize Git Repository (10 mins)

```bash
# Initialize git
git init

# Add all files
git add .

# First commit
git commit -m "[INIT] Initial project setup - Day 1

- Created project structure
- Added core documentation
- Set up development environment
- Configured API credentials
- Tested database and API connections

Ready to begin development."

# Create GitHub repository (on github.com)
# Then link it:
git remote add origin https://github.com/your-username/accountancy.git
git branch -M main
git push -u origin main
```

---

## ✅ Step 9: Verify Everything Works (10 mins)

**Run all tests:**
```bash
# Test database
python test_db.py

# Test Claude API
python test_claude.py

# Test Xero credentials
python test_xero.py

# Check Python environment
python --version
pip list | head -20

# Check PostgreSQL
psql -d practice_dev -c "SELECT 1;"
```

**All should show ✅ green checkmarks!**

---

## 🎉 Success Criteria

**You're done when you can say YES to all:**
- [ ] Python 3.11+ installed and verified
- [ ] PostgreSQL databases created (practice_dev, practice_test)
- [ ] Virtual environment active
- [ ] All dependencies installed (requirements.txt)
- [ ] .env file configured with all API keys
- [ ] Claude API test passes ✅
- [ ] Xero credentials confirmed ✅
- [ ] Database connection works ✅
- [ ] Project structure created
- [ ] Git repository initialized
- [ ] First commit pushed to GitHub

---

## 🐛 Troubleshooting

### Python not found
```bash
# Windows: Add Python to PATH
# Control Panel → System → Advanced → Environment Variables
# Add: C:\Python311\ and C:\Python311\Scripts\
```

### PostgreSQL commands not found
```bash
# Add PostgreSQL bin to PATH
# C:\Program Files\PostgreSQL\15\bin
```

### Virtual environment won't activate
```bash
# GitBash on Windows:
source venv/Scripts/activate

# If still not working:
python -m venv venv --clear
source venv/Scripts/activate
```

### Pip install errors
```bash
# Upgrade pip first
pip install --upgrade pip

# Try again
pip install -r requirements.txt

# If specific package fails, tell me which one
```

### PostgreSQL connection refused
```bash
# Start PostgreSQL service (Windows)
# Services → PostgreSQL → Start

# Or: pg_ctl -D "C:\Program Files\PostgreSQL\15\data" start
```

---

## 📞 Next Steps

**When all tests pass, you're ready for:**
1. Creating database schema
2. Building abstraction layer
3. Implementing Xero adapter
4. Creating first mock client
5. Pulling real data from Xero!

**We'll do that in Session 2 (later today or tomorrow).**

---

## 💬 Report Back

**Tell me:**
1. Which step you're on
2. Any errors you hit
3. Output of the test scripts
4. Questions or confusion

**I'll be here to help debug and guide you through!**

---

**You've got this! Let's build something amazing.** 🚀
