# Technology Stack & Architecture

**Version:** 1.0  
**Last Updated:** November 22, 2025

---

## 🏗️ Architecture Overview

```
┌─────────────────────────────────────────────────────────┐
│                   YOUR LAPTOP (Local)                    │
├─────────────────────────────────────────────────────────┤
│                                                          │
│  ┌────────────────┐         ┌──────────────────┐       │
│  │   Frontend     │◄────────│   Backend API    │       │
│  │  (Browser)     │         │   (FastAPI)      │       │
│  │                │         │                  │       │
│  │  - Dashboard   │         │  - QBO Client    │       │
│  │  - Client View │         │  - AI Analyzer   │       │
│  │  - Reports     │         │  - Task Engine   │       │
│  └────────────────┘         └──────────────────┘       │
│                                      │                  │
│                              ┌───────▼────────┐         │
│                              │   Database     │         │
│                              │   (SQLite)     │         │
│                              └────────────────┘         │
│                                                          │
└─────────────────────────────────────────────────────────┘
                      │              │
            ┌─────────▼──┐    ┌──────▼──────┐
            │  QBO API   │    │  Claude API │
            │  (Intuit)  │    │ (Anthropic) │
            └────────────┘    └─────────────┘
                  ▲                   
         ┌────────┴────────┐
         │  Your 5 Mock    │
         │  QBO Companies  │
         └─────────────────┘
```

---

## 🐍 Backend Stack

### Python 3.11+

**Why Python:**
- ✅ Easiest language for accounting + AI integration
- ✅ Excellent libraries for APIs, data, and AI
- ✅ Readable, maintainable code
- ✅ You can learn it while building
- ✅ Great for rapid prototyping
- ✅ Huge community for help

**Alternatives Considered:**
- Node.js: Good, but Python better for data/AI work
- Ruby: Less common, smaller ecosystem
- PHP: Outdated for new projects

**Installation:**
```bash
# Mac/Linux
brew install python@3.11

# Windows
Download from python.org
```

---

### FastAPI Framework

**Why FastAPI:**
- ✅ Modern, fast, easy to learn
- ✅ Automatic API documentation
- ✅ Built-in data validation
- ✅ Async support (important for external APIs)
- ✅ Type hints make code clearer
- ✅ Perfect for your use case

**Alternatives Considered:**
- Flask: Simpler but less features
- Django: Overkill, too heavyweight
- Express (Node): Would mean JavaScript backend

**Example FastAPI Code:**
```python
from fastapi import FastAPI

app = FastAPI()

@app.get("/clients")
async def get_clients():
    """Get all clients - automatically documented"""
    return {"clients": [...]}
```

**Key Features We'll Use:**
- RESTful API endpoints
- Automatic JSON serialization
- Background tasks for long operations
- Dependency injection
- Request validation

---

### Database: SQLite → PostgreSQL

**Phase 1-9: SQLite**

**Why Start with SQLite:**
- ✅ Zero configuration (single file)
- ✅ Perfect for local development
- ✅ No server to manage
- ✅ Easy to backup (copy file)
- ✅ Built into Python
- ✅ Fast enough for your needs

**When It Works:**
- Single user (you)
- Moderate data volume
- Local development
- Simple deployment

**Phase 10+: Consider PostgreSQL**

**Why Upgrade Later:**
- ✅ Better for multiple users
- ✅ More robust for production
- ✅ Better performance at scale
- ✅ Advanced features if needed

**Migration Strategy:**
- SQLAlchemy ORM makes switching easy
- Change one line of configuration
- Same code works with both

**Database Schema Preview:**
```python
# Core tables we'll build

clients
- id (primary key)
- name
- qbo_company_id
- business_type
- monthly_fee
- status (active/inactive)
- created_at

transactions
- id (primary key)
- client_id (foreign key)
- qbo_transaction_id
- date
- amount
- merchant
- category
- description
- needs_review (boolean)
- confidence_score (0-1)
- reviewed_at

tasks
- id (primary key)
- client_id (foreign key)
- description
- priority (high/medium/low)
- due_date
- status (pending/complete)
- created_at

insights
- id (primary key)
- client_id (foreign key)
- insight_type
- insight_text
- priority
- generated_at
- actioned (boolean)

communications
- id (primary key)
- client_id (foreign key)
- direction (to_client/from_client)
- subject
- body
- sent_at
- ai_generated (boolean)
```

---

### SQLAlchemy ORM

**Why SQLAlchemy:**
- ✅ Don't write raw SQL
- ✅ Python objects = database tables
- ✅ Type safety and validation
- ✅ Works with SQLite AND PostgreSQL
- ✅ Industry standard

**Example Usage:**
```python
from sqlalchemy import Column, Integer, String, DateTime
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

class Client(Base):
    __tablename__ = 'clients'
    
    id = Column(Integer, primary_key=True)
    name = Column(String)
    qbo_company_id = Column(String)
    business_type = Column(String)
    
    def __repr__(self):
        return f"<Client(name='{self.name}')>"

# Usage
client = Client(name="Sarah's Cafe", business_type="cafe")
session.add(client)
session.commit()
```

---

## 🔌 API Integrations

### QuickBooks Online API

**Library: python-quickbooks or intuitlib**

**Why These:**
- ✅ Handle OAuth complexity for you
- ✅ Clean Python interface to QBO
- ✅ Active maintenance
- ✅ Good documentation

**QBO API Capabilities:**
- OAuth 2.0 authentication
- Access to all QBO data (customers, transactions, invoices, etc.)
- Real-time queries
- Webhooks for changes
- No per-call costs (free!)

**Rate Limits:**
- 500 requests per minute per app
- More than enough for your needs

**Example Usage:**
```python
from intuitlib.client import AuthClient
from quickbooks.objects.customer import Customer

# Authenticate
auth_client = AuthClient(
    client_id=INTUIT_CLIENT_ID,
    client_secret=INTUIT_CLIENT_SECRET,
    redirect_uri=REDIRECT_URI,
    environment='sandbox'  # or 'production'
)

# Get customers
customers = Customer.all(qb=client)
for customer in customers:
    print(customer.DisplayName)
```

**Setup Process:**
1. Create Intuit Developer account
2. Register your app
3. Get Client ID and Secret
4. Implement OAuth flow
5. Store refresh tokens securely

---

### Claude API (Anthropic)

**Library: anthropic (official SDK)**

**Why Claude:**
- ✅ Best at following complex instructions
- ✅ Excellent at maintaining context
- ✅ Great at structured output
- ✅ Can adapt to YOUR voice naturally
- ✅ Strong at reasoning and analysis
- ✅ Good cost/performance ratio

**Pricing:**
- Input: $3/million tokens (~£2.40)
- Output: $15/million tokens (~£12)
- Estimated £25-40/month for development
- £40-60/month with 15 clients

**Models We'll Use:**

**Claude Sonnet 4 (Primary):**
- Best for: Complex analysis, client communications, learning feedback
- Use for: Most tasks

**Claude Haiku (Optional Cost Optimization):**
- 12x cheaper
- Best for: Simple categorizations, routine tasks
- Use for: High-volume, low-complexity tasks

**Example Usage:**
```python
import anthropic

client = anthropic.Anthropic(api_key=CLAUDE_API_KEY)

def analyze_transaction(transaction_data, knowledge_base):
    message = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=1000,
        messages=[{
            "role": "user",
            "content": f"""
            You are a bookkeeper analyzing this transaction:
            {transaction_data}
            
            Your knowledge base:
            {knowledge_base}
            
            Provide: category, confidence (0-1), and reasoning.
            """
        }]
    )
    return message.content[0].text

# Usage
result = analyze_transaction(
    transaction_data="£450 to Amazon on 15 Mar",
    knowledge_base=load_categorization_rules()
)
```

**API Management:**
```python
# We'll build a wrapper to:
- Track token usage
- Implement caching
- Handle rate limits
- Batch requests where possible
- Log costs per client
```

---

## 🎨 Frontend Stack

### Phase 1-6: Plain HTML + Tailwind CSS

**Why Start Simple:**
- ✅ No build process needed
- ✅ Fast to iterate
- ✅ Easy to learn
- ✅ Good enough for MVP
- ✅ Focus on functionality, not framework

**Tailwind CSS:**
- Utility-first CSS framework
- No custom CSS needed
- Responsive by default
- Looks professional
- CDN version (no install needed)

**Example:**
```html
<!DOCTYPE html>
<html>
<head>
    <script src="https://cdn.tailwindcss.com"></script>
</head>
<body class="bg-gray-100">
    <div class="container mx-auto p-4">
        <h1 class="text-3xl font-bold text-gray-800">
            Your Practice Dashboard
        </h1>
        <div class="grid grid-cols-3 gap-4 mt-4">
            <!-- Client cards -->
        </div>
    </div>
</body>
</html>
```

---

### Phase 7+: Optional React Upgrade

**When to Consider React:**
- Dashboard feels clunky
- Want more interactivity
- Adding complex features
- Client portal needs polish

**Why React:**
- ✅ Component reusability
- ✅ Better state management
- ✅ Richer interactions
- ✅ Large ecosystem

**Alternative: Stay with HTML**
- Perfectly valid choice
- Simpler to maintain
- Less to learn
- "Good enough" often is

**Decision Point: Month 7**

---

## 🛠️ Development Tools

### Version Control: Git + GitHub

**Why:**
- ✅ Track all changes
- ✅ Easy to revert mistakes
- ✅ Portfolio on GitHub
- ✅ Backup in cloud
- ✅ Industry standard

**Setup:**
```bash
# Initialize project
git init
git add .
git commit -m "Initial commit"

# Create GitHub repo
# Link and push
git remote add origin [your-repo-url]
git push -u origin main
```

**Commit Strategy:**
- Commit after each working feature
- Clear, descriptive messages
- Push to GitHub weekly

---

### Code Editor: VS Code

**Why VS Code:**
- ✅ Free and excellent
- ✅ Great Python support
- ✅ Built-in Git integration
- ✅ Terminal included
- ✅ Extensions for everything

**Essential Extensions:**
- Python (Microsoft)
- Pylance (type checking)
- SQLite Viewer
- GitLens
- Prettier (code formatting)
- REST Client (test APIs)

**Alternatives:**
- PyCharm: More powerful, heavier
- Sublime: Lighter, less features
- Vim: Steep learning curve

---

### Environment Management: venv

**Why Virtual Environments:**
- ✅ Isolate project dependencies
- ✅ Avoid version conflicts
- ✅ Reproducible setup
- ✅ Python best practice

**Setup:**
```bash
# Create virtual environment
python -m venv venv

# Activate
# Mac/Linux:
source venv/bin/activate
# Windows:
venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

**requirements.txt:**
```
fastapi==0.104.1
uvicorn==0.24.0
sqlalchemy==2.0.23
python-quickbooks==0.9.5
anthropic==0.7.0
python-dotenv==1.0.0
pydantic==2.5.0
```

---

### API Testing: Postman or HTTPie

**For Testing Endpoints:**

**Postman (GUI):**
- Visual interface
- Save requests
- Good for beginners

**HTTPie (CLI):**
- Command line tool
- Fast and simple
- Good for scripting

**Example:**
```bash
# Test your API
http GET localhost:8000/clients

# With authentication
http GET localhost:8000/clients Authorization:"Bearer token"
```

---

## 🔒 Security & Configuration

### Environment Variables (.env)

**Never commit secrets to Git!**

```bash
# .env file (DO NOT COMMIT)
INTUIT_CLIENT_ID=your_client_id
INTUIT_CLIENT_SECRET=your_client_secret
INTUIT_REDIRECT_URI=http://localhost:8000/callback

CLAUDE_API_KEY=your_anthropic_key

DATABASE_URL=sqlite:///./practice.db

SECRET_KEY=generate_random_string_here
```

**.gitignore:**
```
.env
venv/
__pycache__/
*.pyc
*.db
.DS_Store
```

**Loading Environment Variables:**
```python
from dotenv import load_dotenv
import os

load_dotenv()

CLAUDE_API_KEY = os.getenv("CLAUDE_API_KEY")
```

---

## 📁 Project Structure

```
qbo-ai-practice/
│
├── .git/                       # Git repository
├── .env                        # Environment variables (not in git)
├── .gitignore                  # Files to ignore
├── requirements.txt            # Python dependencies
├── README.md                   # Project overview
│
├── docs/                       # Documentation
│   ├── PROJECT_ROADMAP.md
│   ├── VISION.md
│   ├── TECH_STACK.md          # This file
│   ├── SETUP_GUIDE.md
│   └── API_COST_OPTIMIZATION.md
│
├── knowledge-base/             # AI knowledge base
│   ├── practice/
│   │   ├── philosophy.md
│   │   ├── services.md
│   │   └── communication-style.md
│   ├── technical/
│   │   ├── chart-of-accounts/
│   │   ├── categorization-rules.md
│   │   └── industry-guides/
│   ├── scenarios/
│   │   └── [50+ scenario playbooks]
│   └── templates/
│       └── emails/
│
├── mock-clients/               # Mock client data
│   ├── sarah-cafe/
│   ├── techfix-solutions/
│   ├── buildright-construction/
│   ├── shoplocal-online/
│   └── property-portfolio/
│
├── backend/                    # Python backend
│   ├── __init__.py
│   ├── main.py                 # FastAPI app entry
│   ├── config.py               # Configuration
│   ├── database.py             # Database setup
│   ├── models.py               # SQLAlchemy models
│   │
│   ├── qbo/                    # QBO integration
│   │   ├── __init__.py
│   │   ├── client.py           # QBO API client
│   │   ├── sync.py             # Data synchronization
│   │   └── utils.py
│   │
│   ├── ai/                     # AI integration
│   │   ├── __init__.py
│   │   ├── analyzer.py         # Transaction analysis
│   │   ├── categorizer.py      # Categorization engine
│   │   ├── communicator.py     # Email generation
│   │   └── knowledge_base.py   # KB loader
│   │
│   └── api/                    # API routes
│       ├── __init__.py
│       ├── routes.py           # Endpoint definitions
│       └── middleware.py
│
├── frontend/                   # Frontend code
│   ├── index.html              # Main page
│   ├── dashboard.html          # Practice dashboard
│   ├── client-view.html        # Client portal
│   ├── css/
│   │   └── styles.css          # Custom styles
│   └── js/
│       └── app.js              # Frontend logic
│
├── scripts/                    # Utility scripts
│   ├── daily_review.py         # Daily analysis
│   ├── sync_all_clients.py     # Sync all QBO data
│   ├── analyze_client.py       # Per-client analysis
│   └── generate_report.py      # Report generation
│
├── tests/                      # Test suite
│   ├── test_qbo_client.py
│   ├── test_analyzer.py
│   └── test_categorizer.py
│
└── data/                       # Data storage
    ├── practice.db             # SQLite database
    ├── backups/                # Database backups
    └── exports/                # CSV exports
```

---

## 🚀 Deployment Strategy

### Phase 1-9: Local Only

**Why:**
- ✅ Simplest to develop
- ✅ No hosting costs
- ✅ Complete control
- ✅ Fast iteration
- ✅ Secure (data never leaves laptop)

**How to Run:**
```bash
# Start backend
cd backend
uvicorn main:app --reload

# Open frontend
# Just open index.html in browser
# Or use simple HTTP server:
python -m http.server 8080
```

---

### Phase 10+: Optional Cloud Deployment

**If You Want Remote Access:**

**Option 1: Railway.app**
- ✅ Easy deployment
- ✅ Free tier available
- ✅ PostgreSQL included
- ✅ Automatic HTTPS
- Cost: £10-20/month

**Option 2: Render.com**
- Similar to Railway
- Good free tier
- Simple to use

**Option 3: DigitalOcean**
- More control
- Cheaper at scale
- More technical
- Cost: £5-10/month

**Deployment Checklist:**
- [ ] Migrate to PostgreSQL
- [ ] Set up environment variables
- [ ] Configure HTTPS
- [ ] Set up automated backups
- [ ] Test thoroughly
- [ ] Monitor costs

---

## 💾 Data & Backup Strategy

### Development Phase (Local)

**Daily Automatic Backups:**
```bash
# Cron job or script
DATE=$(date +%Y%m%d)
cp data/practice.db data/backups/practice_$DATE.db

# Keep last 30 days
find data/backups/ -mtime +30 -delete
```

**Weekly GitHub Push:**
- Code changes
- Documentation updates
- Knowledge base additions
- (Never commit .db or .env files!)

**Monthly Full Export:**
```python
# Export all data to JSON
# In case you need to migrate later
import json

def export_all_data():
    data = {
        "clients": [...],
        "transactions": [...],
        "tasks": [...],
        # etc
    }
    with open(f"export_{date}.json", "w") as f:
        json.dump(data, f)
```

---

## 🔧 Development Workflow

### Daily Development Cycle

**Morning:**
```bash
# Start the day
cd ~/qbo-ai-practice
source venv/bin/activate

# Pull latest if working across machines
git pull

# Start backend
uvicorn backend.main:app --reload
```

**During Development:**
```bash
# Make changes
# Test in browser
# Check backend logs for errors

# Commit when something works
git add .
git commit -m "Add transaction categorization"
```

**End of Day:**
```bash
# Push to GitHub
git push

# Review what you built
# Update learning log
# Plan tomorrow's tasks
```

---

## 📊 Monitoring & Optimization

### Performance Tracking

**What to Monitor:**
- API response times
- Database query speeds
- Claude API token usage
- Costs per client
- System resource usage

**Simple Logging:**
```python
import logging

logging.basicConfig(
    filename='app.log',
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

# Log important events
logging.info(f"Analyzed {client_name}: {transactions} transactions")
logging.warning(f"High token usage: {tokens} tokens")
```

**Weekly Review:**
- Check API costs
- Review slow queries
- Identify optimization opportunities
- Celebrate improvements!

---

## 🎓 Learning Resources

### Documentation to Bookmark

**Python & FastAPI:**
- python.org/docs
- fastapi.tiangolo.com
- docs.python.org/3/tutorial

**QuickBooks API:**
- developer.intuit.com/docs
- python-quickbooks.readthedocs.io

**Claude API:**
- docs.anthropic.com
- Anthropic Cookbook (examples)

**Database:**
- docs.sqlalchemy.org
- sqlite.org/docs.html

**Frontend:**
- tailwindcss.com/docs
- developer.mozilla.org (HTML/JS)

---

## 🚦 Technology Decision Log

### Key Decisions & Rationale

**Python over JavaScript:**
- Better for data/AI work
- Easier for beginners
- Better accounting libraries

**FastAPI over Flask:**
- Modern, fast, well-documented
- Automatic API docs
- Better async support

**SQLite over PostgreSQL (initially):**
- Zero configuration
- Perfect for learning
- Easy migration path

**Local-first over Cloud:**
- Cheaper during development
- Complete control
- Faster iteration
- Deploy later if needed

**Tailwind over custom CSS:**
- Faster development
- Consistent design
- No CSS expertise needed

**Claude over GPT-4:**
- Better at following instructions
- Excellent context handling
- Good cost/performance
- Great API experience

---

## ✅ Technology Checklist

### What You'll Install (Week 1)

- [ ] Python 3.11+
- [ ] VS Code
- [ ] Git
- [ ] GitHub account set up
- [ ] Virtual environment created
- [ ] Dependencies installed (pip install -r requirements.txt)
- [ ] QuickBooks Developer account
- [ ] Claude API account
- [ ] .env file configured
- [ ] Database initialized
- [ ] First API call successful

**Total setup time: 3-4 hours**

---

## 📄 Related Documents

- [PROJECT_ROADMAP.md](./PROJECT_ROADMAP.md) - 12-month timeline
- [SETUP_GUIDE.md](./SETUP_GUIDE.md) - Step-by-step installation
- [API_COST_OPTIMIZATION.md](./API_COST_OPTIMIZATION.md) - Minimize API costs
- [VISION.md](./VISION.md) - Project philosophy

---

**Questions about technology choices? Let's discuss before you start building!**
