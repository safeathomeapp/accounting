# Architecture Principles

> **Last Updated:** November 24, 2025
>
> **Philosophy:** "Build for today, design for tomorrow"
> 
> Write code that solves TODAY's problem, but structured so TOMORROW's features are easy to add.

---

## 🎯 Core Philosophy

**We're NOT:**
- ❌ Building a framework for uncertain futures
- ❌ Over-engineering "just in case"
- ❌ Creating abstractions before we need them
- ❌ Planning for every possible scenario

**We ARE:**
- ✅ Writing clean, simple code that works NOW
- ✅ Structuring it so extensions are easy LATER
- ✅ Following patterns that scale naturally
- ✅ Refactoring when we have REAL need (not imagined)

**Rule:** Make it work → Make it right → Make it fast (in that order)

---

## 🏗️ Core Principles

### 1. Separation of Concerns

**Why:** Easy to extend without breaking existing code

**Bad Example:**
```python
# ❌ DON'T: Everything mixed together
def process_payroll(client):
    # 200 lines of mixed logic
    # - Fetch data from Xero
    # - Calculate gross pay
    # - Calculate tax
    # - Calculate NI
    # - Generate payslip
    # - Send to HMRC
    # - Email employee
    # All in one giant function!
```

**Good Example:**
```python
# ✅ DO: Separate concerns clearly
class PayrollProcessor:
    """
    Process payroll for a client.
    Each method has ONE responsibility.
    """
    
    def __init__(self, client):
        self.client = client
        self.accounting = AccountingClientFactory.create(client)
    
    def process(self):
        """Main workflow - orchestrates other methods."""
        gross = self.calculate_gross()
        deductions = self.calculate_deductions(gross)
        net = self.calculate_net(gross, deductions)
        payslip = self.generate_payslip(gross, deductions, net)
        self.submit_to_hmrc(payslip)
        self.notify_employee(payslip)
        return payslip
    
    def calculate_gross(self):
        """Calculate gross pay only."""
        pass
    
    def calculate_deductions(self, gross):
        """Calculate all deductions only."""
        pass
    
    def calculate_net(self, gross, deductions):
        """Calculate net pay only."""
        pass
    
    def generate_payslip(self, gross, deductions, net):
        """Generate payslip document only."""
        pass
    
    def submit_to_hmrc(self, payslip):
        """Submit to HMRC only."""
        pass
    
    def notify_employee(self, payslip):
        """Send notification only."""
        pass
```

**Benefits:**
- Add expense deductions? Just modify `calculate_deductions()`
- Change payslip format? Just modify `generate_payslip()`
- Add SMS notifications? Just modify `notify_employee()`
- Each change is isolated and safe

---

### 2. Plugin Architecture for Features

**Why:** Add features without changing core code

**Pattern:**
```python
from abc import ABC, abstractmethod

class PortalFeature(ABC):
    """
    Base class for all portal features.
    New features just extend this.
    """
    
    @abstractmethod
    def render(self, user):
        """Render the feature's UI."""
        pass
    
    @abstractmethod
    def process(self, request):
        """Handle user interactions."""
        pass
    
    @abstractmethod
    def is_enabled_for(self, client):
        """Check if feature is enabled for this client."""
        pass


class DocumentUpload(PortalFeature):
    """Document upload feature - Month 7."""
    
    def render(self, user):
        return {
            'component': 'DocumentUpload',
            'props': {
                'max_size': 10_000_000,  # 10MB
                'allowed_types': ['.pdf', '.jpg', '.png']
            }
        }
    
    def process(self, request):
        file = request.files['document']
        # Handle upload logic
        return {'success': True, 'file_id': 'abc123'}
    
    def is_enabled_for(self, client):
        return client.has_feature('document_upload')


class TimesheetSubmission(PortalFeature):
    """Timesheet feature - Month 7."""
    
    def render(self, user):
        return {
            'component': 'TimesheetForm',
            'props': {
                'employee': user.employee_id,
                'week_ending': get_current_week_ending()
            }
        }
    
    def process(self, request):
        # Handle timesheet submission
        return {'success': True}
    
    def is_enabled_for(self, client):
        return client.has_feature('timesheets')


# Future: Expense Claims (Month 10+)
class ExpenseClaims(PortalFeature):
    """Expense claims - IF we decide to build it."""
    
    def render(self, user):
        # Just extend PortalFeature - easy!
        pass
    
    def process(self, request):
        pass
    
    def is_enabled_for(self, client):
        return client.has_feature('expense_claims')


# Portal loads enabled features dynamically
class Portal:
    AVAILABLE_FEATURES = [
        DocumentUpload,
        TimesheetSubmission,
        # ExpenseClaims,  # Add when ready!
    ]
    
    def get_features_for_client(self, client):
        """Return only enabled features for this client."""
        return [
            feature 
            for feature in self.AVAILABLE_FEATURES 
            if feature().is_enabled_for(client)
        ]
```

**Benefits:**
- Add expense claims? Just create `ExpenseClaims` class and add to list
- Disable feature? Just remove from list (or check `is_enabled_for`)
- No core portal code changes needed
- Each feature is self-contained

---

### 3. Configuration Over Code

**Why:** Enable/disable features without code changes

**Bad Example:**
```python
# ❌ DON'T: Hardcode feature availability
def get_portal_features(client):
    if client.name == "Sarah's Cafe":
        return ['documents', 'timesheets', 'holiday']
    elif client.name == "TechFix":
        return ['documents', 'timesheets']
    # Have to edit code for every client!
```

**Good Example:**
```python
# ✅ DO: Use database configuration

# In database (clients table):
# sarah_cafe: {"features": {"documents": True, "timesheets": True, "holiday": True}}
# techfix: {"features": {"documents": True, "timesheets": True, "holiday": False}}

class Client(Base):
    __tablename__ = 'clients'
    
    id = Column(Integer, primary_key=True)
    name = Column(String)
    features = Column(JSON)  # Store feature flags
    
    def has_feature(self, feature_name):
        """Check if client has access to a feature."""
        return self.features.get(feature_name, False)

# In code:
def get_portal_features(client):
    available = ['documents', 'timesheets', 'holiday', 'expenses']
    return [f for f in available if client.has_feature(f)]

# To enable expense claims for Sarah's Cafe later:
# Just update database: {"features": {"...", "expenses": True}}
# No code deployment needed!
```

**Benefits:**
- Turn features on/off with database update
- Different features per client (flex pricing)
- Easy A/B testing
- No code deployments for feature toggles

---

### 4. Versioned APIs

**Why:** Add new features without breaking old code

**Pattern:**
```python
from fastapi import APIRouter

# ✅ Version your API routes
v1_router = APIRouter(prefix="/v1")
v2_router = APIRouter(prefix="/v2")  # Future

@v1_router.post("/payroll")
async def process_payroll_v1(data: PayrollRequest):
    """
    Original payroll endpoint.
    Keep this working even when we add v2.
    """
    return {"status": "processed", "payslip_id": 123}


# Future: v2 with enhanced features
@v2_router.post("/payroll")
async def process_payroll_v2(data: EnhancedPayrollRequest):
    """
    Enhanced version with expenses, bonuses, etc.
    Old clients still use v1, new clients use v2.
    """
    return {
        "status": "processed",
        "payslip_id": 123,
        "expenses_processed": True,  # New feature
        "bonuses_applied": True  # New feature
    }

# Or use feature flags in response:
@v1_router.get("/payslip/{payslip_id}")
async def get_payslip(payslip_id: int, client: Client):
    payslip = get_payslip_data(payslip_id)
    
    # Return different data based on client features
    response = {
        "basic_info": payslip.basic_info,
    }
    
    if client.has_feature('interactive_breakdown'):
        response["interactive_data"] = payslip.detailed_breakdown
    
    if client.has_feature('pension_viz'):
        response["pension_data"] = payslip.pension_calculations
    
    return response
```

**Benefits:**
- Old clients keep working (no breaking changes)
- New features added incrementally
- Portal can check API version / feature availability
- Smooth migrations

---

### 5. Database Design for Growth

**Why:** Add columns/features without painful migrations

**Good Example:**
```python
from sqlalchemy import Column, Integer, String, JSON, DateTime
from datetime import datetime

class Employee(Base):
    __tablename__ = 'employees'
    
    # Standard fields
    id = Column(Integer, primary_key=True)
    client_id = Column(Integer)
    name = Column(String, nullable=False)
    email = Column(String, nullable=False)
    
    # Payroll fields
    hourly_rate = Column(Numeric(10, 2))
    tax_code = Column(String)
    ni_number = Column(String)
    
    # Future-proofing fields (add from Day 1)
    settings = Column(JSON)  # For future preferences
    metadata = Column(JSON)  # For arbitrary data
    feature_flags = Column(JSON)  # For testing new features
    
    # Audit fields (always include)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    created_by = Column(String)
    updated_by = Column(String)

# Usage NOW (Month 7):
employee.settings = {
    'email_notifications': True,
    'portal_access': True
}

# Usage LATER (Month 10) - no migration needed!
employee.settings = {
    'email_notifications': True,
    'portal_access': True,
    'sms_notifications': False,  # New feature
    'expense_approval_limit': 50.00,  # New feature
    'preferred_language': 'en'  # New feature
}
```

**Key JSON Fields:**

**settings:** User preferences, feature opt-ins
**metadata:** Arbitrary data we don't know about yet
**feature_flags:** Testing new features per-user

**Benefits:**
- Add new features without migrations
- Easy to test features per-user
- Flexible for unknown future needs
- Audit trail built in

---

### 6. Event-Driven Architecture

**Why:** Add side effects without touching core code

**Bad Example:**
```python
# ❌ DON'T: Tightly couple actions
def approve_payroll(payroll):
    payroll.status = 'approved'
    db.commit()
    
    send_email(payroll)  # What if we want SMS too?
    log_to_analytics(payroll)  # What if we add Slack?
    # Have to edit this function every time!
```

**Good Example:**
```python
# ✅ DO: Emit events, let listeners handle side effects

from typing import List, Callable

class EventEmitter:
    """Simple event system."""
    
    def __init__(self):
        self._listeners = {}
    
    def on(self, event_name: str, callback: Callable):
        """Register a listener for an event."""
        if event_name not in self._listeners:
            self._listeners[event_name] = []
        self._listeners[event_name].append(callback)
    
    def emit(self, event_name: str, data):
        """Emit an event to all listeners."""
        for callback in self._listeners.get(event_name, []):
            callback(data)

# Global event emitter
events = EventEmitter()

# Core business logic (clean, focused)
def approve_payroll(payroll):
    payroll.status = 'approved'
    db.commit()
    
    # Just emit event - don't know/care what happens next
    events.emit('payroll.approved', payroll)

# Listeners handle side effects (separate files)

# In notifications.py:
@events.on('payroll.approved')
def send_approval_email(payroll):
    send_email(
        to=payroll.employer.email,
        subject='Payroll Approved',
        body=f'Payroll for {payroll.period} has been approved.'
    )

# In notifications.py (add later - no core code change!)
@events.on('payroll.approved')
def send_approval_sms(payroll):
    if payroll.employer.settings.get('sms_notifications'):
        send_sms(
            to=payroll.employer.phone,
            message='Payroll approved for this week.'
        )

# In analytics.py:
@events.on('payroll.approved')
def track_approval(payroll):
    analytics.track('payroll_approved', {
        'client_id': payroll.client_id,
        'amount': payroll.total_amount,
        'employee_count': payroll.employee_count
    })

# In integrations.py (add later):
@events.on('payroll.approved')
def notify_slack(payroll):
    if payroll.client.has_feature('slack_integration'):
        slack.send_message(
            channel=payroll.client.slack_channel,
            text=f'💰 Payroll approved: {payroll.total_amount}'
        )
```

**Benefits:**
- Core business logic stays simple
- Easy to add notifications (email, SMS, Slack, etc.)
- Easy to add integrations
- No coupling between features

---

### 7. AI Prompt Templates

**Why:** Improve AI without changing code

**Bad Example:**
```python
# ❌ DON'T: Hardcode prompts in code
def categorize_transaction(transaction):
    prompt = f"Categorize this transaction: {transaction.description}"
    return claude.complete(prompt)
    # Have to redeploy code to improve prompts!
```

**Good Example:**
```python
# ✅ DO: Store prompts in database or config files

# In prompts.yaml:
categorization:
  v1: |
    Categorize this transaction:
    Description: {description}
    Amount: {amount}
    Merchant: {merchant}
  
  v2: |
    Categorize this transaction and explain your reasoning:
    Description: {description}
    Amount: {amount}
    Merchant: {merchant}
    Context: {business_type}
  
  v3: |
    You are an expert bookkeeper. Categorize this transaction:
    
    Transaction Details:
    - Description: {description}
    - Amount: {amount}
    - Merchant: {merchant}
    - Date: {date}
    
    Business Context:
    - Type: {business_type}
    - Industry: {industry}
    
    Provide:
    1. Category (from standard chart of accounts)
    2. Confidence score (0-100)
    3. Brief explanation
    4. Flag if needs human review
  
  active: v3  # Easy to switch versions!

# In code:
class PromptManager:
    def __init__(self):
        self.prompts = self._load_prompts()
    
    def _load_prompts(self):
        with open('prompts.yaml', 'r') as f:
            return yaml.safe_load(f)
    
    def get_prompt(self, name: str, version: str = None):
        """Get a prompt template."""
        prompt_config = self.prompts[name]
        version = version or prompt_config['active']
        return prompt_config[version]

# Usage:
def categorize_transaction(transaction, client):
    prompt_template = prompt_manager.get_prompt('categorization')
    prompt = prompt_template.format(
        description=transaction.description,
        amount=transaction.amount,
        merchant=transaction.merchant,
        business_type=client.business_type,
        industry=client.industry
    )
    return claude.complete(prompt)

# To improve AI: just edit prompts.yaml, no code deployment!
```

**Benefits:**
- Iterate on prompts without deploying code
- Easy A/B testing of prompts
- Version history of prompts
- Non-developers can improve prompts

---

### 8. Feature Flags

**Why:** Test features with subset of clients before full rollout

**Pattern:**
```python
class FeatureFlag:
    """
    Manage feature rollouts safely.
    """
    
    @staticmethod
    def is_enabled(feature_name: str, client: Client) -> bool:
        """Check if feature is enabled for this client."""
        
        # Check database config
        feature_config = get_feature_config(feature_name)
        
        # Globally disabled?
        if not feature_config.get('enabled', False):
            return False
        
        # In beta testing list?
        if client.id in feature_config.get('beta_clients', []):
            return True
        
        # Rolled out to percentage of clients?
        rollout_percentage = feature_config.get('rollout_percentage', 0)
        if rollout_percentage > 0:
            # Use client ID as seed for consistent experience
            client_hash = hash(client.id) % 100
            if client_hash < rollout_percentage:
                return True
        
        return False

# In database:
feature_flags = {
    'expense_claims': {
        'enabled': True,
        'beta_clients': [1, 3, 5],  # Sarah's Cafe, BuildRight, etc.
        'rollout_percentage': 0,  # Not rolled out yet
        'description': 'Employee expense claims feature'
    },
    'interactive_payslip': {
        'enabled': True,
        'beta_clients': [],
        'rollout_percentage': 25,  # Rolled out to 25% of clients
        'description': 'Interactive payslip breakdown'
    }
}

# In code:
def get_portal_features(client):
    features = []
    
    # Always available
    features.append('documents')
    features.append('timesheets')
    
    # Conditional features
    if FeatureFlag.is_enabled('holiday_tracking', client):
        features.append('holiday')
    
    if FeatureFlag.is_enabled('expense_claims', client):
        features.append('expenses')
    
    return features
```

**Benefits:**
- Safe rollout (beta test with 2-3 clients first)
- Easy rollback (set enabled=False)
- Gradual rollout (5% → 25% → 50% → 100%)
- Production testing without risk

---

## 📁 Folder Structure for Growth

**Organize code so new features are easy to add:**

```
backend/
├── core/                 # Core infrastructure (rarely changes)
│   ├── __init__.py
│   ├── database.py      # DB connection, base models
│   ├── auth.py          # Authentication
│   ├── events.py        # Event system
│   └── utils.py         # Shared utilities
│
├── accounting/          # Platform abstraction (Month 1-2)
│   ├── __init__.py
│   ├── base.py          # Abstract AccountingClient
│   ├── models.py        # Standard data models
│   ├── factory.py       # Factory pattern
│   ├── xero/
│   │   ├── __init__.py
│   │   ├── client.py    # XeroClient implementation
│   │   ├── auth.py      # Xero OAuth
│   │   └── mapper.py    # Xero → Standard mapping
│   └── quickbooks/
│       ├── __init__.py
│       ├── client.py    # QuickBooksClient (Month 7)
│       ├── auth.py
│       └── mapper.py
│
├── features/            # Business features (easy to add/remove)
│   ├── __init__.py
│   ├── payroll/
│   │   ├── __init__.py
│   │   ├── processor.py
│   │   ├── calculator.py
│   │   └── models.py
│   ├── documents/       # Month 7
│   │   ├── __init__.py
│   │   ├── uploader.py
│   │   ├── ocr.py
│   │   └── categorizer.py
│   ├── timesheets/      # Month 7
│   │   ├── __init__.py
│   │   ├── submission.py
│   │   └── approval.py
│   ├── holidays/        # Month 8
│   │   ├── __init__.py
│   │   ├── tracker.py
│   │   └── calculator.py
│   └── expenses/        # Future (if we build it)
│       ├── __init__.py
│       ├── claims.py
│       └── approval.py
│
├── ai/                  # AI/ML logic
│   ├── __init__.py
│   ├── categorizer.py   # Transaction categorization
│   ├── chatbot.py       # Employee Q&A
│   ├── fraud_detector.py  # Fraud detection (Month 10)
│   └── prompts.yaml     # Prompt templates
│
├── portal/              # Portal features (Month 7+)
│   ├── __init__.py
│   ├── features/
│   │   ├── base.py      # PortalFeature base class
│   │   ├── documents.py
│   │   ├── timesheets.py
│   │   └── holidays.py
│   ├── auth.py
│   └── routes.py
│
├── models/              # Database models
│   ├── __init__.py
│   ├── client.py
│   ├── employee.py
│   ├── transaction.py
│   └── payroll.py
│
├── api/                 # API routes
│   ├── __init__.py
│   ├── v1/              # Current version
│   │   ├── __init__.py
│   │   ├── payroll.py
│   │   ├── clients.py
│   │   └── portal.py
│   └── v2/              # Future version (if needed)
│       └── __init__.py
│
├── integrations/        # Third-party integrations
│   ├── __init__.py
│   ├── claude.py        # Claude API wrapper
│   ├── email.py         # Email service
│   └── slack.py         # Slack (if we add it)
│
└── tests/               # Test suite
    ├── __init__.py
    ├── unit/            # Unit tests
    ├── integration/     # Integration tests
    └── fixtures/        # Test data
```

**Benefits:**
- Clear where new features go
- Easy to find code
- Minimal conflicts (separate folders)
- Easy to delete unused features

---

## 🧪 Testing Strategy

**Write tests that don't break when adding features:**

**Bad Example:**
```python
# ❌ DON'T: Test exact implementation
def test_portal_features():
    features = get_portal_features(client)
    assert features == ['documents', 'timesheets']
    # Breaks when we add holidays!
```

**Good Example:**
```python
# ✅ DO: Test minimums and contracts
def test_portal_features():
    features = get_portal_features(client)
    
    # Test minimums (always present)
    assert 'documents' in features
    assert 'timesheets' in features
    
    # Don't test exact list - allows adding features
    assert isinstance(features, list)
    assert len(features) >= 2

def test_portal_feature_contract():
    """Test that all features follow the contract."""
    for feature_class in Portal.AVAILABLE_FEATURES:
        feature = feature_class()
        
        # All features must have these methods
        assert hasattr(feature, 'render')
        assert hasattr(feature, 'process')
        assert hasattr(feature, 'is_enabled_for')
        
        # Methods must be callable
        assert callable(feature.render)
```

**Benefits:**
- Tests still pass when adding features
- Test contracts, not implementations
- Easy to add new feature tests

---

## 📚 Documentation Standards

**Document for future maintainers (including future you):**

**Module Docstrings:**
```python
"""
Payroll processing module.

This module handles all payroll calculation and processing logic.

Dependencies:
- accounting.base.AccountingClient (for platform data)
- ai.categorizer (for transaction categorization)
- models.Employee (for employee data)

Extension Points:
- To add new deduction types: Extend PayrollCalculator.calculate_deductions()
- To add new payslip formats: Extend PayslipGenerator.generate()
- To add new submission methods: Extend PayrollSubmitter.submit()

Future Considerations:
- Multi-currency support (see CurrencyConverter)
- Multiple pay frequencies (currently monthly only)
- Contractor payments (different from PAYE employees)

Author: [Your name]
Created: December 2025
Last Updated: December 2025
"""
```

**Class Docstrings:**
```python
class PayrollProcessor:
    """
    Process payroll for a single client.
    
    This class orchestrates the entire payroll process from data
    fetching through to payslip generation and HMRC submission.
    
    Attributes:
        client (Client): The client being processed
        accounting (AccountingClient): Platform adapter (Xero/QB)
        period_start (date): Start of payroll period
        period_end (date): End of payroll period
    
    Example:
        >>> processor = PayrollProcessor(client)
        >>> payroll = processor.process()
        >>> print(payroll.total_amount)
        12450.50
    
    Extension Points:
        To add new features:
        - Expenses: Extend calculate_deductions()
        - Bonuses: Extend calculate_gross()
        - New payslip format: Extend generate_payslip()
    
    Thread Safety:
        This class is NOT thread-safe. Create separate instances
        for concurrent processing.
    """
```

**Function Docstrings:**
```python
def calculate_tax(gross_pay: Decimal, tax_code: str) -> Decimal:
    """
    Calculate income tax based on gross pay and tax code.
    
    Uses HMRC 2025/26 tax tables. Handles emergency tax codes
    and Scottish tax codes (S prefix).
    
    Args:
        gross_pay: Gross pay for the period (before deductions)
        tax_code: Employee's tax code (e.g., "1257L", "S1257L")
    
    Returns:
        Tax amount to deduct this period
    
    Raises:
        ValueError: If tax code is invalid format
        ValueError: If gross_pay is negative
    
    Example:
        >>> calculate_tax(Decimal('2000.00'), '1257L')
        Decimal('165.00')
    
    Notes:
        - Tax is calculated on cumulative basis (year to date)
        - Emergency tax (1257L W1/M1) uses non-cumulative basis
        - Scottish codes (S prefix) use different tax bands
    
    See Also:
        - calculate_national_insurance()
        - HMRC documentation: https://...
    """
```

**Inline Comments:**
```python
def process_payroll(self):
    # Fetch timesheet data
    timesheets = self.accounting.get_timesheets(
        start_date=self.period_start,
        end_date=self.period_end
    )
    
    # Calculate gross pay
    # Note: This includes overtime at 1.5x rate
    gross = self.calculate_gross(timesheets)
    
    # Apply deductions (tax, NI, pension)
    # TODO: Add student loan deduction (Month 10)
    deductions = self.calculate_deductions(gross)
    
    # Generate payslip PDF
    # Uses template from templates/payslip_v2.html
    payslip = self.generate_payslip(gross, deductions)
    
    return payslip
```

---

## 🔄 When to Refactor

**Don't over-engineer now, but refactor when you hit these triggers:**

### ✅ Refactor When:

**1. Rule of Three**
- You've copy-pasted code 3 times
- Create a shared function/class

**2. Adding Third Similar Feature**
- Two features work similarly: OK
- Third feature needs same pattern: Time to abstract

**Example:**
```python
# Month 7: Add documents
def upload_document(file):
    validate_file(file)
    store_in_s3(file)
    create_db_record(file)

# Month 7: Add timesheets
def upload_timesheet(file):
    validate_file(file)
    store_in_s3(file)
    create_db_record(file)

# Month 8: Add holiday requests (third time!)
# NOW refactor to shared FileUploader class
class FileUploader:
    def upload(self, file, file_type):
        self.validate(file)
        url = self.store(file)
        self.record(file, file_type, url)
        return url
```

**3. Function > 50 Lines**
- Break into smaller functions
- Each function should do ONE thing

**4. File > 500 Lines**
- Split into multiple files
- Organize by concern

**5. Tests Become Hard to Write**
- Too many dependencies? Decouple.
- Hard to mock? Add dependency injection.

**6. Adding Third Platform**
- Two platforms (Xero, QB): Current approach works
- Third platform (Sage): Time to refactor common patterns

---

### ❌ DON'T Refactor When:

**1. "Might need it someday"**
- Don't abstract until you have REAL second use case

**2. "This could be more elegant"**
- Working code beats elegant code
- Only refactor if it's causing problems

**3. "I learned a new pattern"**
- Don't refactor just to use new pattern
- Consistency > novelty

**4. "Someone might want to..."**
- Don't build for hypothetical users
- Build for real needs only

---

## 🎯 Key Design Patterns to Use

### 1. Adapter Pattern (Already Using)
```python
# For multi-platform support
class AccountingClient(ABC):
    @abstractmethod
    def get_transactions(self): pass

class XeroClient(AccountingClient):
    def get_transactions(self): # Xero-specific implementation

class QuickBooksClient(AccountingClient):
    def get_transactions(self): # QB-specific implementation
```

### 2. Factory Pattern (Already Using)
```python
# For creating platform clients
class AccountingClientFactory:
    @classmethod
    def create(cls, client):
        if client.platform == 'xero':
            return XeroClient(client)
        elif client.platform == 'quickbooks':
            return QuickBooksClient(client)
```

### 3. Strategy Pattern (For AI)
```python
# For different AI categorization strategies
class CategorizationStrategy(ABC):
    @abstractmethod
    def categorize(self, transaction): pass

class SimpleAIStrategy(CategorizationStrategy):
    def categorize(self, transaction):
        # Simple prompt, fast, cheap

class AdvancedAIStrategy(CategorizationStrategy):
    def categorize(self, transaction):
        # Complex prompt, slow, accurate

# Choose strategy based on client tier
strategy = AdvancedAIStrategy() if client.is_premium else SimpleAIStrategy()
category = strategy.categorize(transaction)
```

### 4. Observer Pattern (For Events)
```python
# For event-driven features
events = EventEmitter()

@events.on('transaction.categorized')
def update_dashboard(transaction):
    # Update dashboard automatically

@events.on('transaction.categorized')
def check_for_fraud(transaction):
    # Check for fraud automatically

events.emit('transaction.categorized', transaction)
```

---

## 💡 Practical Examples

### Example 1: Right Amount of Future-Proofing

**Month 7 - Building Portal:**

```python
# ✅ Good: Simple plugin system
class PortalFeature(ABC):
    @abstractmethod
    def render(self): pass
    @abstractmethod
    def process(self): pass

class DocumentUpload(PortalFeature):
    def render(self):
        # Build complete, working feature
        pass
    
    def process(self, request):
        # Handle uploads
        pass

# Simple registry
PORTAL_FEATURES = [DocumentUpload]

# Future (Month 10) - Easy to add!
class ExpenseClaims(PortalFeature):
    def render(self): pass
    def process(self, request): pass

PORTAL_FEATURES = [DocumentUpload, ExpenseClaims]  # Just append!
```

**❌ Bad: Over-engineering:**

```python
# ❌ DON'T build complex framework Day 1
class PortalFeatureFactory:
    class FeatureRegistry:
        class PluginLoader:
            class DependencyInjector:
                class ConfigurationManager:
                    # 500 lines of framework code you don't need yet
                    # Just to load one feature!
```

**Lesson:** Build what you need TODAY, structure for TOMORROW.

---

### Example 2: Database Design

**Month 1 - Employee Table:**

```python
# ✅ Good: Flexible from Day 1
class Employee(Base):
    __tablename__ = 'employees'
    
    # Core fields (need now)
    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    email = Column(String, nullable=False)
    hourly_rate = Column(Numeric(10, 2))
    
    # Future-proof fields (cost nothing now, save time later)
    settings = Column(JSON)  # For future preferences
    metadata = Column(JSON)  # For unknown future data
    
    # Audit fields (always include)
    created_at = Column(DateTime)
    updated_at = Column(DateTime)

# Month 7: Use settings for portal
employee.settings = {'portal_access': True}

# Month 10: Add more - no migration!
employee.settings = {
    'portal_access': True,
    'expense_claims_enabled': True  # New feature!
}
```

**❌ Bad: Rigid schema:**

```python
# ❌ DON'T: No flexibility
class Employee(Base):
    id = Column(Integer)
    name = Column(String)
    # That's it! Have to migrate for every new field
```

---

## 📋 Pre-Development Checklist

**Before writing code for a new feature, ask:**

1. ✅ **Does this solve a REAL problem TODAY?**
   - If "might need it later" → Don't build yet

2. ✅ **Is this in the roadmap?**
   - If not → Add to FUTURE_FEATURES.md, don't build

3. ✅ **Does this belong in core bookkeeping?**
   - If no (HR, scheduling, etc.) → Don't build

4. ✅ **Can I build the simplest version first?**
   - Complex abstractions can wait

5. ✅ **Am I following the patterns?**
   - Separation of concerns
   - Configuration over code
   - Event-driven where appropriate

6. ✅ **Will this be easy to extend later?**
   - Plugin architecture
   - Feature flags
   - Versioned APIs

7. ✅ **Am I documenting as I go?**
   - Docstrings
   - Comments for "why"
   - Architecture decisions

---

## 🎓 Learning Resources

**Read these if you want to go deeper:**

- "Clean Code" by Robert Martin - Principles of clean coding
- "Refactoring" by Martin Fowler - When and how to refactor
- "Design Patterns" by Gang of Four - Classic patterns
- "The Pragmatic Programmer" - Practical wisdom
- "Domain-Driven Design" by Eric Evans - Modeling business logic

**But remember:** Books teach principles, real code teaches practice.

---

## ✅ Summary: The Golden Rules

1. **YAGNI** - You Aren't Gonna Need It (don't build for hypothetical)
2. **KISS** - Keep It Simple, Stupid (simple code is easy to extend)
3. **DRY** - Don't Repeat Yourself (but don't abstract too early)
4. **Separation of Concerns** - Each piece does ONE thing
5. **Configuration > Code** - Use database/files for flexibility
6. **Events > Coupling** - Emit events, let listeners handle side effects
7. **Test Contracts** - Test behavior, not implementation
8. **Document Intent** - Explain "why", not "what"
9. **Refactor at Three** - Copy-paste twice is OK, third time refactor
10. **Make it Work → Make it Right → Make it Fast** - In that order

---

## 🚀 Final Reminder

**We're building a bookkeeping practice, not a software company.**

**Good architecture helps us:**
- ✅ Add features quickly
- ✅ Fix bugs easily
- ✅ Scale smoothly
- ✅ Maintain sanity

**Good architecture does NOT:**
- ❌ Mean building frameworks
- ❌ Mean abstracting everything
- ❌ Mean over-engineering
- ❌ Mean planning for every possibility

**Build for today. Design for tomorrow. Ship working code.** 💪

---

**Now go build something great!** 🎯
