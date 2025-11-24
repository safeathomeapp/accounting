# Platform Integration Guide
## How to Add New Accounting Platforms

**Version:** 1.0  
**Last Updated:** November 22, 2025  
**Purpose:** Technical guide for adding new accounting platform support

---

## 🎯 Overview

This document explains the architecture that allows your system to work with **multiple accounting platforms** (Xero, QuickBooks, and future additions like Sage, FreeAgent, etc.)

**Key Principle:** Write your business logic once, it works with any platform.

---

## 🏗️ Architecture Pattern: Adapter Pattern

### The Problem
Different accounting platforms have different:
- API structures
- Data formats
- Authentication methods
- Feature sets
- Naming conventions

**Without abstraction:**
```python
# ❌ BAD: Tightly coupled to Xero
def analyze_transactions():
    xero = Xero(credentials)
    txns = xero.bank_transactions.all()
    
    for txn in txns:
        amount = txn['Total']  # Xero-specific
        merchant = txn['Contact']['Name']  # Xero-specific
        # ... AI analysis
    
    # Now you want to add QuickBooks?
    # You have to rewrite ALL of this!
```

**With abstraction:**
```python
# ✅ GOOD: Platform-agnostic
def analyze_transactions(client):
    accounting = AccountingClientFactory.create(client)
    txns = accounting.get_transactions()  # Same for all platforms!
    
    for txn in txns:
        amount = txn.amount  # Standardized
        merchant = txn.merchant  # Standardized
        # ... AI analysis
    
    # Adding QuickBooks? Just write a new adapter.
    # Business logic stays unchanged!
```

---

## 📐 The Three Layers

```
┌─────────────────────────────────────────┐
│  LAYER 1: Business Logic                │
│  (AI analysis, reporting, communication)│
│  Platform-agnostic - never changes      │
├─────────────────────────────────────────┤
│  LAYER 2: Abstraction Layer             │
│  (Standard interfaces and data models)  │
│  Define once, use everywhere            │
├─────────────────────────────────────────┤
│  LAYER 3: Platform Adapters             │
│  (Xero, QuickBooks, Sage, etc.)        │
│  One adapter per platform               │
└─────────────────────────────────────────┘
         │          │           │
    ┌────▼───┐ ┌───▼────┐ ┌───▼────┐
    │  Xero  │ │   QB   │ │  Sage  │
    │  API   │ │  API   │ │  API   │
    └────────┘ └────────┘ └────────┘
```

---

## 💻 Layer 1: Business Logic (Platform-Agnostic)

**Rule:** This code should NEVER know which platform it's working with.

```python
# backend/services/transaction_analyzer.py

class TransactionAnalyzer:
    """
    Analyzes transactions from ANY platform.
    Works with standardized data only.
    """
    
    def __init__(self, ai_client, knowledge_base):
        self.ai = ai_client
        self.kb = knowledge_base
    
    def analyze_month(self, client, month, year):
        """
        Analyze a month of transactions.
        Works for Xero, QuickBooks, or any future platform.
        """
        
        # Get accounting client (abstracted)
        accounting = AccountingClientFactory.create(client)
        
        # Get transactions (same interface for all platforms)
        start_date = date(year, month, 1)
        end_date = date(year, month, calendar.monthrange(year, month)[1])
        transactions = accounting.get_transactions(start_date, end_date)
        
        # Analyze with AI (platform-agnostic)
        results = []
        for txn in transactions:
            analysis = self._analyze_transaction(txn, client)
            results.append(analysis)
        
        # Generate summary (platform-agnostic)
        summary = self._generate_summary(results, client)
        
        return {
            'transactions': results,
            'summary': summary,
            'client': client.name,
            'period': f"{month}/{year}"
            # Notice: no mention of Xero or QuickBooks anywhere!
        }
    
    def _analyze_transaction(self, txn, client):
        """
        Analyze single transaction.
        txn is StandardTransaction - works with any platform.
        """
        
        # Load relevant knowledge
        context = self.kb.get_context(
            business_type=client.business_type,
            merchant=txn.merchant,
            transaction_type=txn.type
        )
        
        # AI analysis
        prompt = f"""
        Analyze this transaction:
        Date: {txn.date}
        Merchant: {txn.merchant}
        Amount: £{txn.amount}
        Description: {txn.description}
        Current category: {txn.category}
        
        Context: {context}
        
        Provide: suggested_category, confidence (0-1), reasoning
        """
        
        ai_result = self.ai.analyze(prompt)
        
        return {
            'transaction': txn,
            'suggested_category': ai_result.category,
            'confidence': ai_result.confidence,
            'needs_review': ai_result.confidence < 0.8,
            'reasoning': ai_result.reasoning
        }
```

**Key Points:**
- ✅ Uses `StandardTransaction` objects
- ✅ Uses `AccountingClientFactory` to get right adapter
- ✅ No platform-specific code anywhere
- ✅ Adding new platform requires ZERO changes to this code

---

## 🎨 Layer 2: Abstraction Layer

### 2.1 Abstract Base Class

```python
# backend/accounting/base.py

from abc import ABC, abstractmethod
from typing import List, Optional
from datetime import date
from decimal import Decimal

class AccountingClient(ABC):
    """
    Abstract base class for all accounting platform clients.
    
    Every platform adapter MUST implement all these methods.
    This is the contract that ensures consistency.
    """
    
    def __init__(self, credentials):
        """
        Initialize with platform-specific credentials.
        Each platform handles this differently.
        """
        self.credentials = credentials
        self.platform_name = self.__class__.__name__.replace('Client', '').lower()
    
    # === REQUIRED METHODS (must implement) ===
    
    @abstractmethod
    def get_transactions(self, start_date: date, end_date: date) -> List['StandardTransaction']:
        """
        Get all transactions between dates.
        Returns standardized transaction objects.
        """
        pass
    
    @abstractmethod
    def get_invoices(self, status: Optional[str] = None) -> List['StandardInvoice']:
        """
        Get invoices, optionally filtered by status.
        Status values: 'draft', 'submitted', 'paid', 'overdue'
        """
        pass
    
    @abstractmethod
    def get_contacts(self, contact_type: Optional[str] = None) -> List['StandardContact']:
        """
        Get customers/suppliers.
        contact_type: 'customer', 'supplier', or None for all
        """
        pass
    
    @abstractmethod
    def create_invoice(self, invoice_data: 'StandardInvoice') -> 'StandardInvoice':
        """
        Create invoice from standardized format.
        Returns created invoice with platform-assigned ID.
        """
        pass
    
    @abstractmethod
    def get_chart_of_accounts(self) -> List['StandardAccount']:
        """
        Get chart of accounts.
        Returns standardized account objects.
        """
        pass
    
    # === OPTIONAL METHODS (platform may not support) ===
    
    def get_tracking_categories(self) -> Optional[List[dict]]:
        """
        Get tracking categories (Xero) or classes (QuickBooks).
        Return None if platform doesn't support this.
        """
        return None
    
    def supports_feature(self, feature: str) -> bool:
        """
        Check if platform supports a specific feature.
        
        Features: 'tracking', 'multi_currency', 'projects', 
                 'inventory', 'payroll', 'expenses'
        """
        # Default: assume not supported
        # Subclasses override to declare support
        return False
    
    def get_platform_name(self) -> str:
        """Get the platform name (xero, quickbooks, sage, etc.)"""
        return self.platform_name
```

### 2.2 Standard Data Models

```python
# backend/accounting/models.py

from dataclasses import dataclass, field
from datetime import date
from decimal import Decimal
from typing import Optional, List, Dict, Any

@dataclass
class StandardTransaction:
    """
    Normalized transaction format that works for ANY platform.
    
    Platform adapters convert their native format to this.
    Business logic only works with this format.
    """
    
    # Core fields (every platform has these)
    id: str  # Platform-specific ID
    date: date
    amount: Decimal
    merchant: str
    description: str
    category: str  # Account code/name
    
    # Optional fields
    reference: Optional[str] = None
    type: str = 'expense'  # 'expense', 'income', 'transfer'
    tax_amount: Optional[Decimal] = None
    tax_rate: Optional[Decimal] = None
    
    # Platform tracking
    platform: str = ''  # 'xero', 'quickbooks', etc.
    platform_specific_data: Dict[str, Any] = field(default_factory=dict)
    
    # AI analysis fields (added by our system)
    confidence_score: float = 0.0
    needs_review: bool = False
    ai_suggested_category: Optional[str] = None
    ai_reasoning: Optional[str] = None
    flags: List[str] = field(default_factory=list)
    
    def __post_init__(self):
        """Validate data after initialization"""
        if not self.id:
            raise ValueError("Transaction ID is required")
        if not self.merchant:
            self.merchant = "Unknown"
        if self.amount == 0:
            self.flags.append("zero_amount")

@dataclass
class StandardInvoice:
    """Normalized invoice format"""
    
    id: str
    invoice_number: str
    date: date
    due_date: date
    contact_id: str
    contact_name: str
    
    # Amounts
    subtotal: Decimal
    tax_amount: Decimal
    total: Decimal
    amount_paid: Decimal
    amount_due: Decimal
    
    # Status
    status: str  # 'draft', 'submitted', 'paid', 'overdue', 'voided'
    
    # Line items
    line_items: List[Dict[str, Any]] = field(default_factory=list)
    
    # Platform tracking
    platform: str = ''
    platform_specific_data: Dict[str, Any] = field(default_factory=dict)

@dataclass
class StandardContact:
    """Normalized contact (customer/supplier) format"""
    
    id: str
    name: str
    email: Optional[str] = None
    phone: Optional[str] = None
    contact_type: str = 'customer'  # 'customer', 'supplier', 'both'
    
    # Address (optional)
    address_line_1: Optional[str] = None
    city: Optional[str] = None
    postal_code: Optional[str] = None
    country: Optional[str] = None
    
    # Financial
    balance: Optional[Decimal] = None
    
    # Platform tracking
    platform: str = ''
    platform_specific_data: Dict[str, Any] = field(default_factory=dict)

@dataclass
class StandardAccount:
    """Normalized chart of accounts entry"""
    
    id: str
    code: str  # Account code (e.g., "6000")
    name: str  # Account name (e.g., "Advertising")
    type: str  # 'expense', 'income', 'asset', 'liability', 'equity'
    tax_type: Optional[str] = None
    
    # Platform tracking
    platform: str = ''
    platform_specific_data: Dict[str, Any] = field(default_factory=dict)
```

### 2.3 Factory Pattern

```python
# backend/accounting/factory.py

from .base import AccountingClient
from .xero.client import XeroClient
from .quickbooks.client import QuickBooksClient
# Future imports:
# from .sage.client import SageClient
# from .freeagent.client import FreeAgentClient

class AccountingClientFactory:
    """
    Factory that creates the right accounting client for a given platform.
    
    This is the ONLY place that knows about specific platform classes.
    """
    
    # Registry of supported platforms
    PLATFORMS = {
        'xero': XeroClient,
        'quickbooks': QuickBooksClient,
        # Add new platforms here:
        # 'sage': SageClient,
        # 'freeagent': FreeAgentClient,
    }
    
    @classmethod
    def create(cls, client) -> AccountingClient:
        """
        Create appropriate accounting client for the given client.
        
        Args:
            client: Client model with platform and credentials
        
        Returns:
            AccountingClient subclass instance
        
        Raises:
            ValueError: If platform not supported
        """
        platform = client.platform.lower()
        
        if platform not in cls.PLATFORMS:
            raise ValueError(
                f"Unsupported platform: {platform}. "
                f"Supported platforms: {', '.join(cls.PLATFORMS.keys())}"
            )
        
        client_class = cls.PLATFORMS[platform]
        credentials = client.get_decrypted_credentials()
        
        return client_class(credentials)
    
    @classmethod
    def supported_platforms(cls) -> List[str]:
        """Get list of supported platform names"""
        return list(cls.PLATFORMS.keys())
    
    @classmethod
    def register_platform(cls, platform_name: str, client_class: type):
        """
        Register a new platform dynamically.
        Useful for plugins or extensions.
        """
        if not issubclass(client_class, AccountingClient):
            raise TypeError(f"{client_class} must inherit from AccountingClient")
        
        cls.PLATFORMS[platform_name] = client_class
```

---

## 🔌 Layer 3: Platform Adapters

### 3.1 Xero Adapter Example

```python
# backend/accounting/xero/client.py

from xero import Xero
from xero.auth import OAuth2Credentials
from datetime import date, datetime
from decimal import Decimal
from typing import List, Optional

from ..base import AccountingClient
from ..models import StandardTransaction, StandardInvoice, StandardContact

class XeroClient(AccountingClient):
    """
    Xero platform adapter.
    Converts between Xero's format and our standard format.
    """
    
    def __init__(self, credentials):
        super().__init__(credentials)
        
        # Initialize Xero client
        oauth_credentials = OAuth2Credentials(
            client_id=credentials['client_id'],
            client_secret=credentials['client_secret'],
            token=credentials['token']
        )
        
        self.xero = Xero(oauth_credentials)
    
    def get_transactions(self, start_date: date, end_date: date) -> List[StandardTransaction]:
        """Get Xero bank transactions, normalized"""
        
        # Xero-specific API call
        xero_transactions = self.xero.banktransactions.filter(
            since=start_date,
            where=f'Date >= DateTime({start_date.year},{start_date.month},{start_date.day}) AND '
                  f'Date <= DateTime({end_date.year},{end_date.month},{end_date.day})'
        )
        
        # Convert each Xero transaction to standard format
        return [self._normalize_transaction(txn) for txn in xero_transactions]
    
    def _normalize_transaction(self, xero_txn) -> StandardTransaction:
        """Convert Xero format → Standard format"""
        
        # Extract from Xero structure
        line_item = xero_txn['LineItems'][0] if xero_txn.get('LineItems') else {}
        contact = xero_txn.get('Contact', {})
        
        return StandardTransaction(
            id=xero_txn['BankTransactionID'],
            date=self._parse_xero_date(xero_txn['Date']),
            amount=Decimal(str(xero_txn['Total'])),
            merchant=contact.get('Name', 'Unknown'),
            description=line_item.get('Description', ''),
            category=line_item.get('AccountCode', ''),
            reference=xero_txn.get('Reference', ''),
            type=self._map_xero_type(xero_txn['Type']),
            tax_amount=Decimal(str(line_item.get('TaxAmount', 0))),
            platform='xero',
            platform_specific_data=xero_txn  # Store original for reference
        )
    
    def get_invoices(self, status: Optional[str] = None) -> List[StandardInvoice]:
        """Get Xero invoices, normalized"""
        
        # Xero-specific API call
        if status:
            xero_status = self._map_to_xero_status(status)
            invoices = self.xero.invoices.filter(where=f'Status=="{xero_status}"')
        else:
            invoices = self.xero.invoices.all()
        
        return [self._normalize_invoice(inv) for inv in invoices]
    
    def _normalize_invoice(self, xero_inv) -> StandardInvoice:
        """Convert Xero invoice → Standard format"""
        
        return StandardInvoice(
            id=xero_inv['InvoiceID'],
            invoice_number=xero_inv['InvoiceNumber'],
            date=self._parse_xero_date(xero_inv['Date']),
            due_date=self._parse_xero_date(xero_inv['DueDate']),
            contact_id=xero_inv['Contact']['ContactID'],
            contact_name=xero_inv['Contact']['Name'],
            subtotal=Decimal(str(xero_inv['SubTotal'])),
            tax_amount=Decimal(str(xero_inv['TotalTax'])),
            total=Decimal(str(xero_inv['Total'])),
            amount_paid=Decimal(str(xero_inv.get('AmountPaid', 0))),
            amount_due=Decimal(str(xero_inv.get('AmountDue', 0))),
            status=self._map_xero_status_to_standard(xero_inv['Status']),
            line_items=[self._normalize_line_item(item) for item in xero_inv.get('LineItems', [])],
            platform='xero',
            platform_specific_data=xero_inv
        )
    
    def get_contacts(self, contact_type: Optional[str] = None) -> List[StandardContact]:
        """Get Xero contacts, normalized"""
        
        # Xero doesn't distinguish customer/supplier in same way
        # Get all and filter if needed
        xero_contacts = self.xero.contacts.all()
        
        contacts = [self._normalize_contact(c) for c in xero_contacts]
        
        if contact_type:
            contacts = [c for c in contacts if c.contact_type == contact_type]
        
        return contacts
    
    def _normalize_contact(self, xero_contact) -> StandardContact:
        """Convert Xero contact → Standard format"""
        
        # Determine contact type
        is_customer = xero_contact.get('IsCustomer', False)
        is_supplier = xero_contact.get('IsSupplier', False)
        
        if is_customer and is_supplier:
            contact_type = 'both'
        elif is_supplier:
            contact_type = 'supplier'
        else:
            contact_type = 'customer'
        
        # Get address (if exists)
        addresses = xero_contact.get('Addresses', [])
        address = addresses[0] if addresses else {}
        
        return StandardContact(
            id=xero_contact['ContactID'],
            name=xero_contact['Name'],
            email=xero_contact.get('EmailAddress'),
            phone=xero_contact.get('Phone'),
            contact_type=contact_type,
            address_line_1=address.get('AddressLine1'),
            city=address.get('City'),
            postal_code=address.get('PostalCode'),
            country=address.get('Country'),
            balance=None,  # Xero doesn't provide this easily
            platform='xero',
            platform_specific_data=xero_contact
        )
    
    def create_invoice(self, invoice_data: StandardInvoice) -> StandardInvoice:
        """Create Xero invoice from standard format"""
        
        # Convert standard format → Xero format
        xero_invoice = {
            'Type': 'ACCREC',  # Accounts Receivable
            'Contact': {
                'ContactID': invoice_data.contact_id
            },
            'Date': invoice_data.date.isoformat(),
            'DueDate': invoice_data.due_date.isoformat(),
            'LineItems': [
                self._convert_line_item_to_xero(item)
                for item in invoice_data.line_items
            ],
            'Status': self._map_standard_status_to_xero(invoice_data.status)
        }
        
        # Create in Xero
        created = self.xero.invoices.put(xero_invoice)[0]
        
        # Return as standard format
        return self._normalize_invoice(created)
    
    def get_chart_of_accounts(self) -> List[StandardAccount]:
        """Get Xero chart of accounts, normalized"""
        
        xero_accounts = self.xero.accounts.all()
        return [self._normalize_account(acc) for acc in xero_accounts]
    
    def _normalize_account(self, xero_account):
        """Convert Xero account → Standard format"""
        
        return StandardAccount(
            id=xero_account['AccountID'],
            code=xero_account['Code'],
            name=xero_account['Name'],
            type=self._map_xero_account_type(xero_account['Type']),
            tax_type=xero_account.get('TaxType'),
            platform='xero',
            platform_specific_data=xero_account
        )
    
    # === Xero-specific features ===
    
    def get_tracking_categories(self) -> List[dict]:
        """Xero supports tracking categories"""
        return self.xero.trackingcategories.all()
    
    def supports_feature(self, feature: str) -> bool:
        """Declare what Xero supports"""
        xero_features = {
            'tracking': True,
            'multi_currency': True,
            'projects': True,
            'inventory': True,
            'payroll': True,
            'expenses': True
        }
        return xero_features.get(feature, False)
    
    # === Helper methods ===
    
    def _parse_xero_date(self, xero_date_str):
        """Parse Xero's date format"""
        # Xero uses /Date(timestamp)/
        import re
        match = re.search(r'/Date\((\d+)\)/', str(xero_date_str))
        if match:
            timestamp = int(match.group(1)) / 1000
            return datetime.fromtimestamp(timestamp).date()
        return datetime.fromisoformat(xero_date_str).date()
    
    def _map_xero_type(self, xero_type):
        """Map Xero transaction type to standard"""
        mapping = {
            'SPEND': 'expense',
            'RECEIVE': 'income',
            'RECEIVE-OVERPAYMENT': 'income',
            'SPEND-OVERPAYMENT': 'expense'
        }
        return mapping.get(xero_type, 'expense')
    
    def _map_xero_status_to_standard(self, xero_status):
        """Map Xero invoice status to standard"""
        mapping = {
            'DRAFT': 'draft',
            'SUBMITTED': 'submitted',
            'AUTHORISED': 'submitted',
            'PAID': 'paid',
            'VOIDED': 'voided'
        }
        return mapping.get(xero_status, 'unknown')
    
    def _map_to_xero_status(self, standard_status):
        """Map standard status to Xero"""
        mapping = {
            'draft': 'DRAFT',
            'submitted': 'AUTHORISED',
            'paid': 'PAID',
            'voided': 'VOIDED'
        }
        return mapping.get(standard_status, 'AUTHORISED')
    
    def _map_xero_account_type(self, xero_type):
        """Map Xero account type to standard"""
        mapping = {
            'EXPENSE': 'expense',
            'REVENUE': 'income',
            'FIXED': 'asset',
            'CURRENT': 'asset',
            'CURRLIAB': 'liability',
            'LIABILITY': 'liability',
            'EQUITY': 'equity'
        }
        return mapping.get(xero_type, 'expense')
```

### 3.2 QuickBooks Adapter Structure

```python
# backend/accounting/quickbooks/client.py

from intuitlib.client import AuthClient
from quickbooks import QuickBooks
from quickbooks.objects import Purchase, Invoice, Customer

from ..base import AccountingClient
from ..models import StandardTransaction, StandardInvoice, StandardContact

class QuickBooksClient(AccountingClient):
    """
    QuickBooks platform adapter.
    Structure similar to XeroClient but uses QB API.
    """
    
    def __init__(self, credentials):
        super().__init__(credentials)
        
        # Initialize QuickBooks client
        self.qb = QuickBooks(
            auth_client=self._create_auth_client(credentials),
            company_id=credentials['company_id']
        )
    
    def get_transactions(self, start_date: date, end_date: date) -> List[StandardTransaction]:
        """Get QB purchases, normalized to standard format"""
        
        # QuickBooks-specific query
        query = f"""
        SELECT * FROM Purchase 
        WHERE TxnDate >= '{start_date}' 
        AND TxnDate <= '{end_date}'
        ORDER BY TxnDate DESC
        """
        
        qb_purchases = Purchase.query(query, qb=self.qb)
        
        # Convert to standard format
        return [self._normalize_transaction(txn) for txn in qb_purchases]
    
    def _normalize_transaction(self, qb_txn) -> StandardTransaction:
        """Convert QB format → Standard format"""
        
        # QuickBooks structure is different from Xero
        # But we normalize to same StandardTransaction!
        
        line = qb_txn.Line[0] if qb_txn.Line else None
        
        return StandardTransaction(
            id=str(qb_txn.Id),
            date=qb_txn.TxnDate,
            amount=Decimal(str(qb_txn.TotalAmt)),
            merchant=qb_txn.EntityRef.name if qb_txn.EntityRef else 'Unknown',
            description=line.Description if line else '',
            category=line.AccountRef.value if line and line.AccountRef else '',
            reference=qb_txn.DocNumber or '',
            type='expense',  # QB Purchase is always expense
            tax_amount=None,  # QB handles tax differently
            platform='quickbooks',
            platform_specific_data=qb_txn.__dict__
        )
    
    def get_invoices(self, status: Optional[str] = None) -> List[StandardInvoice]:
        """Get QB invoices, normalized"""
        
        query = "SELECT * FROM Invoice"
        if status:
            qb_status = self._map_to_qb_status(status)
            query += f" WHERE TxnStatus = '{qb_status}'"
        
        qb_invoices = Invoice.query(query, qb=self.qb)
        
        return [self._normalize_invoice(inv) for inv in qb_invoices]
    
    def _normalize_invoice(self, qb_inv) -> StandardInvoice:
        """Convert QB invoice → Standard format"""
        
        # Similar to Xero adapter but for QB structure
        return StandardInvoice(
            id=str(qb_inv.Id),
            invoice_number=qb_inv.DocNumber,
            date=qb_inv.TxnDate,
            due_date=qb_inv.DueDate,
            contact_id=str(qb_inv.CustomerRef.value),
            contact_name=qb_inv.CustomerRef.name,
            subtotal=Decimal(str(qb_inv.TotalAmt - qb_inv.TxnTaxDetail.TotalTax)) if qb_inv.TxnTaxDetail else Decimal(str(qb_inv.TotalAmt)),
            tax_amount=Decimal(str(qb_inv.TxnTaxDetail.TotalTax)) if qb_inv.TxnTaxDetail else Decimal('0'),
            total=Decimal(str(qb_inv.TotalAmt)),
            amount_paid=Decimal('0'),  # QB calculates differently
            amount_due=Decimal(str(qb_inv.Balance)),
            status=self._map_qb_status_to_standard(qb_inv.EmailStatus),
            line_items=[],  # Implement if needed
            platform='quickbooks',
            platform_specific_data=qb_inv.__dict__
        )
    
    # ... rest of implementation similar to Xero adapter
    
    def supports_feature(self, feature: str) -> bool:
        """Declare what QuickBooks supports"""
        qb_features = {
            'tracking': False,  # QB uses Classes instead
            'classes': True,  # QB-specific
            'multi_currency': True,
            'projects': True,
            'inventory': True,
            'payroll': True,
            'expenses': True
        }
        return qb_features.get(feature, False)
    
    def get_classes(self) -> List[dict]:
        """QuickBooks-specific: Get Classes (similar to Xero tracking)"""
        from quickbooks.objects import Class
        return Class.all(qb=self.qb)
```

---

## 📝 Adding a New Platform (Step-by-Step)

### Let's add Sage 50cloud as an example

**Step 1: Create directory structure**
```
backend/accounting/sage/
├── __init__.py
├── client.py    # Main adapter
├── auth.py      # Sage-specific OAuth
└── mapper.py    # Sage → Standard format helpers
```

**Step 2: Implement SageClient**
```python
# backend/accounting/sage/client.py

from ..base import AccountingClient
from ..models import StandardTransaction, StandardInvoice, StandardContact

class SageClient(AccountingClient):
    """Sage 50cloud platform adapter"""
    
    def __init__(self, credentials):
        super().__init__(credentials)
        # Initialize Sage client
        self.sage = self._initialize_sage_client(credentials)
    
    def get_transactions(self, start_date, end_date):
        """Get Sage transactions, normalize to standard format"""
        
        # Sage-specific API call
        sage_transactions = self.sage.get_transactions(
            from_date=start_date,
            to_date=end_date
        )
        
        # Convert to StandardTransaction
        return [self._normalize_transaction(t) for t in sage_transactions]
    
    def _normalize_transaction(self, sage_txn):
        """Convert Sage format → Standard format"""
        
        return StandardTransaction(
            id=sage_txn['id'],
            date=sage_txn['date'],
            amount=Decimal(sage_txn['net_amount']),
            merchant=sage_txn['contact_name'],
            description=sage_txn['details'],
            category=sage_txn['ledger_account']['nominal_code'],
            platform='sage',
            platform_specific_data=sage_txn
        )
    
    # Implement all other required methods...
    def get_invoices(self, status=None): ...
    def get_contacts(self, contact_type=None): ...
    def create_invoice(self, invoice_data): ...
    def get_chart_of_accounts(self): ...
    
    def supports_feature(self, feature):
        """What Sage supports"""
        sage_features = {
            'tracking': False,
            'multi_currency': True,
            'inventory': True,
            # ... etc
        }
        return sage_features.get(feature, False)
```

**Step 3: Register in Factory**
```python
# backend/accounting/factory.py

from .sage.client import SageClient

class AccountingClientFactory:
    PLATFORMS = {
        'xero': XeroClient,
        'quickbooks': QuickBooksClient,
        'sage': SageClient,  # ← Add here
    }
```

**Step 4: Test**
```python
# Create test client
from models import Client

sage_client = Client(
    name="Test Sage Client",
    platform='sage',
    credentials={...}
)

# Use it!
accounting = AccountingClientFactory.create(sage_client)
transactions = accounting.get_transactions(start_date, end_date)

# Your business logic works unchanged! ✅
```

**That's it!** Your entire system now works with Sage.
- No changes to AI analysis
- No changes to dashboard
- No changes to business logic
- Just added the adapter

---

## 🧪 Testing Strategy

### Test Each Layer Independently

**Layer 1 Tests: Business Logic**
```python
# tests/test_analyzer.py

def test_analyze_transactions_platform_agnostic():
    """Test that analyzer works with mock StandardTransactions"""
    
    # Create mock standard transactions (not platform-specific!)
    mock_transactions = [
        StandardTransaction(
            id='1',
            date=date.today(),
            amount=Decimal('100.00'),
            merchant='Test Merchant',
            description='Test',
            category='6000',
            platform='mock'  # Could be any platform
        )
    ]
    
    analyzer = TransactionAnalyzer(ai_client, knowledge_base)
    results = analyzer.analyze(mock_transactions)
    
    # Test works regardless of platform
    assert len(results) > 0
```

**Layer 2 Tests: Abstraction**
```python
# tests/test_base.py

def test_all_platforms_implement_interface():
    """Ensure all platform clients implement required methods"""
    
    for platform_name, client_class in AccountingClientFactory.PLATFORMS.items():
        # Check class inherits from base
        assert issubclass(client_class, AccountingClient)
        
        # Check implements all abstract methods
        required_methods = [
            'get_transactions',
            'get_invoices',
            'get_contacts',
            'create_invoice',
            'get_chart_of_accounts'
        ]
        
        for method in required_methods:
            assert hasattr(client_class, method)
```

**Layer 3 Tests: Platform Adapters**
```python
# tests/test_xero_client.py

def test_xero_transaction_normalization():
    """Test Xero adapter converts correctly"""
    
    # Mock Xero transaction (their format)
    xero_txn = {
        'BankTransactionID': '123',
        'Date': '/Date(1638316800000)/',
        'Total': '100.50',
        'Contact': {'Name': 'Test Ltd'},
        'LineItems': [{
            'Description': 'Test purchase',
            'AccountCode': '6000'
        }],
        'Type': 'SPEND'
    }
    
    client = XeroClient(mock_credentials)
    standard_txn = client._normalize_transaction(xero_txn)
    
    # Check normalized correctly
    assert standard_txn.id == '123'
    assert standard_txn.amount == Decimal('100.50')
    assert standard_txn.merchant == 'Test Ltd'
    assert standard_txn.platform == 'xero'
```

---

## ⚠️ Common Pitfalls & Solutions

### Pitfall 1: Platform-Specific Code Leaking

**Problem:**
```python
# ❌ BAD: Xero code in business logic
def generate_report(client):
    xero = Xero(credentials)
    txns = xero.banktransactions.all()
    # Now you can't use this with QuickBooks!
```

**Solution:**
```python
# ✅ GOOD: Use abstraction
def generate_report(client):
    accounting = AccountingClientFactory.create(client)
    txns = accounting.get_transactions(start, end)
    # Works with any platform!
```

**How to check:**
- Search codebase for `xero.` or `quickbooks.` 
- Should only appear in adapter files
- If found elsewhere, refactor

---

### Pitfall 2: Incomplete Normalization

**Problem:**
```python
# ❌ BAD: Leaving platform-specific data structure
def _normalize_transaction(self, xero_txn):
    return {
        'xero_id': xero_txn['BankTransactionID'],  # Xero-specific key!
        'xero_total': xero_txn['Total'],  # Xero-specific key!
    }
```

**Solution:**
```python
# ✅ GOOD: Use standard field names
def _normalize_transaction(self, xero_txn):
    return StandardTransaction(
        id=xero_txn['BankTransactionID'],  # Normalized
        amount=xero_txn['Total'],  # Normalized
        platform='xero',  # Track source
        platform_specific_data=xero_txn  # Store original if needed
    )
```

---

### Pitfall 3: Assuming Feature Parity

**Problem:**
```python
# ❌ BAD: Assuming all platforms have tracking
def get_tracking_info(client):
    accounting = AccountingClientFactory.create(client)
    return accounting.get_tracking_categories()  # QB doesn't have this!
```

**Solution:**
```python
# ✅ GOOD: Check feature support
def get_tracking_info(client):
    accounting = AccountingClientFactory.create(client)
    
    if accounting.supports_feature('tracking'):
        return accounting.get_tracking_categories()
    elif accounting.supports_feature('classes'):
        return accounting.get_classes()  # QB alternative
    else:
        return None  # Not supported
```

---

## 📚 Knowledge Base Organization

### Universal vs Platform-Specific

```
knowledge-base/
├── universal/                   # Works for ANY platform
│   ├── categorization-rules.md
│   │   # Screwfix → Materials (true for Xero and QB)
│   │   # HMRC VAT → VAT Payment (true for Xero and QB)
│   │
│   ├── vat-guidelines.md
│   │   # UK VAT rates (same regardless of platform)
│   │
│   └── scenarios/
│       ├── new-employee.md      # Concept same for all
│       └── vat-threshold.md     # UK rule, not platform-specific
│
├── xero-specific/               # Xero quirks ONLY
│   ├── tracking-categories.md   # Xero feature
│   ├── bank-rules.md           # How Xero does them
│   └── api-quirks.md           # Xero API gotchas
│
└── quickbooks-specific/         # QB quirks ONLY
    ├── classes-system.md        # QB feature
    ├── bank-rules.md           # How QB does them
    └── api-quirks.md           # QB API gotchas
```

**AI Prompt Construction:**
```python
def get_knowledge_base_context(client, transaction):
    """Load relevant knowledge for analysis"""
    
    context = []
    
    # Always include universal knowledge
    context.append(load('universal/categorization-rules.md'))
    
    # Add platform-specific if needed
    if is_ambiguous(transaction):
        platform_kb = f'{client.platform}-specific/'
        if transaction.needs_bank_rule_advice:
            context.append(load(f'{platform_kb}bank-rules.md'))
    
    return '\n\n'.join(context)
```

---

## 🎯 Design Principles Summary

### 1. **Single Responsibility**
- Adapters: Convert between formats
- Business logic: Process standard formats
- Factory: Create right adapter

### 2. **Open/Closed Principle**
- Open for extension (add new platforms)
- Closed for modification (don't change existing code)

### 3. **Dependency Inversion**
- High-level code depends on abstractions
- Not on concrete platform implementations

### 4. **Don't Repeat Yourself (DRY)**
- Write business logic once
- Reuse for all platforms

### 5. **Fail Fast**
- Validate at adapter boundaries
- Raise clear errors for unsupported features

---

## ✅ Adding New Platform Checklist

When adding a new platform, use this checklist:

- [ ] **Create adapter directory** (`backend/accounting/[platform]/`)
- [ ] **Implement AccountingClient subclass**
- [ ] **Implement all required abstract methods**
  - [ ] `get_transactions()`
  - [ ] `get_invoices()`
  - [ ] `get_contacts()`
  - [ ] `create_invoice()`
  - [ ] `get_chart_of_accounts()`
- [ ] **Implement normalization methods**
  - [ ] `_normalize_transaction()`
  - [ ] `_normalize_invoice()`
  - [ ] `_normalize_contact()`
  - [ ] `_normalize_account()`
- [ ] **Declare feature support** (`supports_feature()`)
- [ ] **Implement OAuth/authentication**
- [ ] **Handle platform-specific quirks**
- [ ] **Register in Factory** (`PLATFORMS` dict)
- [ ] **Create platform-specific knowledge base** folder
- [ ] **Write adapter tests**
- [ ] **Test with mock client**
- [ ] **Document platform differences**
- [ ] **Update UI** to show platform badge
- [ ] **Add to supported platforms list**

**Time estimate:** 2-3 weeks per platform once abstraction is solid

---

## 🚀 Future Platform Ideas

**Easy to add (similar APIs):**
- FreeAgent (UK)
- Sage 50cloud (UK)
- Zoho Books

**Medium difficulty:**
- Wave Accounting
- Kashflow (UK)
- ClearBooks (UK)

**More complex (different paradigms):**
- Excel/CSV imports
- Bank statement processing
- Open Banking feeds

---

## 📞 Questions?

If you're adding a new platform and get stuck:

1. **Check existing adapters** - Xero and QB are your templates
2. **Review this guide** - covers most scenarios
3. **Test incrementally** - get one method working at a time
4. **Document quirks** - help future you (and others)
5. **Ask for help** - I'm here to guide you!

**Remember:** The abstraction layer is your friend. Invest time in getting it right, and adding platforms becomes easy. 🎯
