"""
Database Seed Script
====================
Populates the PostgreSQL database with realistic mock data for development/testing.

Creates:
- 1 Organization (accountancy practice)
- Standard UK chart of accounts
- 5 Clients (UK businesses)
- 500 Transactions (100 per client)

Usage:
    python scripts/seed_database.py

Author: Claude Code
Created: January 24, 2026
"""

import sys
import os
from datetime import date, datetime, timedelta
from decimal import Decimal
import random
import uuid

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from backend.models import Base
from backend.models.organization import Organization
from backend.models.account import Account
from backend.models.client import Client
from backend.models.transaction import Transaction
from backend.config import settings


# ============================================================================
# SEED DATA DEFINITIONS
# ============================================================================

ORGANIZATION_DATA = {
    "name": "Thompson & Associates Accountants",
    "email": "info@thompson-associates.co.uk",
    "phone": "020 7946 0958",
    "address_line1": "42 Chancery Lane",
    "address_line2": "Suite 15",
    "city": "London",
    "postal_code": "WC2A 1JE",
    "country": "UK",
    "timezone": "Europe/London",
    "currency": "GBP",
}

# Standard UK Chart of Accounts
CHART_OF_ACCOUNTS = [
    # Assets
    {"code": "1000", "name": "Current Account", "account_type": "bank", "description": "Main business bank account"},
    {"code": "1010", "name": "Savings Account", "account_type": "bank", "description": "Business savings account"},
    {"code": "1100", "name": "Accounts Receivable", "account_type": "asset", "description": "Trade debtors"},
    {"code": "1200", "name": "Prepayments", "account_type": "asset", "description": "Prepaid expenses"},
    {"code": "1300", "name": "Stock", "account_type": "asset", "description": "Inventory on hand"},
    {"code": "1500", "name": "Office Equipment", "account_type": "asset", "description": "Computers, furniture, etc."},
    {"code": "1510", "name": "Accumulated Depreciation", "account_type": "asset", "description": "Accumulated depreciation"},

    # Liabilities
    {"code": "2000", "name": "Accounts Payable", "account_type": "liability", "description": "Trade creditors"},
    {"code": "2100", "name": "VAT Liability", "account_type": "liability", "description": "VAT owed to HMRC"},
    {"code": "2200", "name": "PAYE Liability", "account_type": "liability", "description": "PAYE owed to HMRC"},
    {"code": "2300", "name": "Corporation Tax", "account_type": "liability", "description": "Corporation tax payable"},
    {"code": "2400", "name": "Accruals", "account_type": "liability", "description": "Accrued expenses"},
    {"code": "2500", "name": "Bank Loan", "account_type": "liability", "description": "Business loan"},

    # Equity
    {"code": "3000", "name": "Share Capital", "account_type": "equity", "description": "Issued share capital"},
    {"code": "3100", "name": "Retained Earnings", "account_type": "equity", "description": "Accumulated profits"},
    {"code": "3200", "name": "Dividends", "account_type": "equity", "description": "Dividends declared"},

    # Income
    {"code": "4000", "name": "Sales Revenue", "account_type": "income", "description": "Revenue from sales"},
    {"code": "4100", "name": "Service Revenue", "account_type": "income", "description": "Revenue from services"},
    {"code": "4200", "name": "Consulting Income", "account_type": "income", "description": "Consulting fees"},
    {"code": "4300", "name": "Interest Income", "account_type": "income", "description": "Bank interest received"},
    {"code": "4400", "name": "Other Income", "account_type": "income", "description": "Miscellaneous income"},

    # Expenses
    {"code": "5000", "name": "Cost of Sales", "account_type": "expense", "description": "Direct costs"},
    {"code": "6000", "name": "Salaries & Wages", "account_type": "expense", "description": "Staff salaries"},
    {"code": "6100", "name": "Employer NI", "account_type": "expense", "description": "National Insurance contributions"},
    {"code": "6200", "name": "Pension Contributions", "account_type": "expense", "description": "Employer pension contributions"},
    {"code": "6300", "name": "Staff Training", "account_type": "expense", "description": "Training costs"},
    {"code": "7000", "name": "Rent", "account_type": "expense", "description": "Office rent"},
    {"code": "7100", "name": "Utilities", "account_type": "expense", "description": "Electric, gas, water"},
    {"code": "7200", "name": "Insurance", "account_type": "expense", "description": "Business insurance"},
    {"code": "7300", "name": "Office Supplies", "account_type": "expense", "description": "Stationery, consumables"},
    {"code": "7400", "name": "Telephone & Internet", "account_type": "expense", "description": "Communications"},
    {"code": "7500", "name": "Software Subscriptions", "account_type": "expense", "description": "Software licenses"},
    {"code": "7600", "name": "Professional Fees", "account_type": "expense", "description": "Legal, accounting fees"},
    {"code": "7700", "name": "Marketing", "account_type": "expense", "description": "Advertising, marketing"},
    {"code": "7800", "name": "Travel & Subsistence", "account_type": "expense", "description": "Business travel"},
    {"code": "7900", "name": "Bank Charges", "account_type": "expense", "description": "Bank fees"},
    {"code": "8000", "name": "Depreciation", "account_type": "expense", "description": "Asset depreciation"},
    {"code": "8100", "name": "Bad Debts", "account_type": "expense", "description": "Uncollectable debts"},
    {"code": "8200", "name": "Repairs & Maintenance", "account_type": "expense", "description": "Equipment repairs"},
    {"code": "8300", "name": "Motor Expenses", "account_type": "expense", "description": "Vehicle costs"},
    {"code": "8900", "name": "Sundry Expenses", "account_type": "expense", "description": "Miscellaneous expenses"},
]

# 5 UK business clients with realistic details
CLIENTS_DATA = [
    {
        "name": "Riverside Construction Ltd",
        "email": "accounts@riversideconstruction.co.uk",
        "phone": "0161 234 5678",
        "website": "www.riversideconstruction.co.uk",
        "address_line1": "Unit 7, Riverside Industrial Estate",
        "address_line2": "",
        "city": "Manchester",
        "postal_code": "M17 1HH",
        "country": "UK",
        "contact_type": "customer",
        "industry": "Construction",
        "tax_number": "GB123456789",
    },
    {
        "name": "Digital Spark Marketing",
        "email": "hello@digitalspark.co.uk",
        "phone": "0121 456 7890",
        "website": "www.digitalspark.co.uk",
        "address_line1": "The Innovation Hub",
        "address_line2": "45 Temple Street",
        "city": "Birmingham",
        "postal_code": "B2 5DP",
        "country": "UK",
        "contact_type": "customer",
        "industry": "Marketing & Advertising",
        "tax_number": "GB987654321",
    },
    {
        "name": "Northern Healthcare Solutions",
        "email": "finance@northernhealthcare.co.uk",
        "phone": "0113 789 0123",
        "website": "www.northernhealthcare.co.uk",
        "address_line1": "Healthcare House",
        "address_line2": "12 Wellington Place",
        "city": "Leeds",
        "postal_code": "LS1 4AP",
        "country": "UK",
        "contact_type": "customer",
        "industry": "Healthcare",
        "tax_number": "GB456789123",
    },
    {
        "name": "Coastal Imports & Exports",
        "email": "accounts@coastalimports.co.uk",
        "phone": "023 8012 3456",
        "website": "www.coastalimports.co.uk",
        "address_line1": "Port House",
        "address_line2": "Dock Gate 5",
        "city": "Southampton",
        "postal_code": "SO14 2AQ",
        "country": "UK",
        "contact_type": "customer",
        "industry": "Import/Export",
        "tax_number": "GB789123456",
    },
    {
        "name": "GreenLeaf Organic Foods",
        "email": "info@greenleaforganic.co.uk",
        "phone": "01onal 567 8901",
        "website": "www.greenleaforganic.co.uk",
        "address_line1": "The Old Barn",
        "address_line2": "Meadow Farm",
        "city": "Bristol",
        "postal_code": "BS9 3EF",
        "country": "UK",
        "contact_type": "customer",
        "industry": "Food & Beverage",
        "tax_number": "GB321654987",
    },
]

# Transaction templates for generating realistic transactions
TRANSACTION_TEMPLATES = {
    "invoice": [
        {"description": "Professional services - {month}", "min_amount": 500, "max_amount": 5000},
        {"description": "Consulting fees - {month}", "min_amount": 1000, "max_amount": 8000},
        {"description": "Project work - Phase {phase}", "min_amount": 2000, "max_amount": 15000},
        {"description": "Monthly retainer - {month}", "min_amount": 1500, "max_amount": 3500},
        {"description": "Support services - {month}", "min_amount": 300, "max_amount": 1500},
        {"description": "Implementation services", "min_amount": 3000, "max_amount": 12000},
        {"description": "Training delivery", "min_amount": 800, "max_amount": 2500},
        {"description": "Additional work - {month}", "min_amount": 400, "max_amount": 2000},
    ],
    "bill": [
        {"description": "Office supplies", "min_amount": 50, "max_amount": 500},
        {"description": "Software subscription - {month}", "min_amount": 20, "max_amount": 200},
        {"description": "Utilities - {month}", "min_amount": 100, "max_amount": 400},
        {"description": "Internet services - {month}", "min_amount": 40, "max_amount": 120},
        {"description": "Professional services received", "min_amount": 200, "max_amount": 1500},
        {"description": "Equipment purchase", "min_amount": 150, "max_amount": 2000},
        {"description": "Marketing materials", "min_amount": 100, "max_amount": 800},
        {"description": "Travel expenses", "min_amount": 50, "max_amount": 600},
    ],
}

STATUSES = ["draft", "submitted", "approved", "paid", "overdue"]
MONTHS = ["January", "February", "March", "April", "May", "June",
          "July", "August", "September", "October", "November", "December"]


# ============================================================================
# SEED FUNCTIONS
# ============================================================================

def generate_reference_number(prefix: str, number: int) -> str:
    """Generate a realistic reference number."""
    return f"{prefix}-2025-{number:04d}"


def generate_transaction_date(days_back: int = 365) -> date:
    """Generate a random date within the last N days."""
    days_ago = random.randint(1, days_back)
    return date.today() - timedelta(days=days_ago)


def generate_amount(min_amount: int, max_amount: int) -> tuple:
    """Generate amount, tax (20% VAT), and total."""
    amount = Decimal(str(random.uniform(min_amount, max_amount))).quantize(Decimal("0.01"))
    tax_amount = (amount * Decimal("0.20")).quantize(Decimal("0.01"))
    total_amount = amount + tax_amount
    return amount, tax_amount, total_amount


def seed_database():
    """Main function to seed the database with mock data."""

    print("=" * 60)
    print("DATABASE SEED SCRIPT")
    print("=" * 60)

    # Create database connection
    print(f"\nConnecting to: {settings.database_url}")
    engine = create_engine(settings.database_url)
    Session = sessionmaker(bind=engine)
    session = Session()

    try:
        # Check for existing data
        existing_orgs = session.query(Organization).count()
        if existing_orgs > 0:
            print(f"\nWARNING: Database already contains {existing_orgs} organization(s).")
            response = input("Do you want to clear existing data and reseed? (yes/no): ")
            if response.lower() != "yes":
                print("Aborting. No changes made.")
                return

            # Clear existing data
            print("\nClearing existing data...")
            session.query(Transaction).delete()
            session.query(Client).delete()
            session.query(Account).delete()
            session.query(Organization).delete()
            session.commit()
            print("Existing data cleared.")

        # ----------------------------------------------------------------
        # 1. Create Organization
        # ----------------------------------------------------------------
        print("\n1. Creating Organization...")
        org = Organization(
            id=uuid.uuid4(),
            **ORGANIZATION_DATA
        )
        session.add(org)
        session.flush()  # Get the ID
        print(f"   Created: {org.name} (ID: {org.id})")

        # ----------------------------------------------------------------
        # 2. Create Chart of Accounts
        # ----------------------------------------------------------------
        print("\n2. Creating Chart of Accounts...")
        accounts = {}
        for i, acc_data in enumerate(CHART_OF_ACCOUNTS):
            account = Account(
                id=uuid.uuid4(),
                organization_id=org.id,
                platform_id=f"mock-account-{i+1:03d}",
                platform_name="mock",
                **acc_data
            )
            session.add(account)
            accounts[acc_data["code"]] = account
        session.flush()
        print(f"   Created {len(CHART_OF_ACCOUNTS)} accounts")

        # ----------------------------------------------------------------
        # 3. Create Clients
        # ----------------------------------------------------------------
        print("\n3. Creating Clients...")
        clients = []
        for i, client_data in enumerate(CLIENTS_DATA):
            client = Client(
                id=uuid.uuid4(),
                organization_id=org.id,
                platform_id=f"mock-client-{i+1:03d}",
                platform_name="mock",
                last_synced_at=datetime.now(),
                **client_data
            )
            session.add(client)
            clients.append(client)
            print(f"   Created: {client.name}")
        session.flush()

        # ----------------------------------------------------------------
        # 4. Create Transactions (100 per client)
        # ----------------------------------------------------------------
        print("\n4. Creating Transactions (100 per client)...")

        # Get account IDs for transactions
        income_accounts = [acc for code, acc in accounts.items() if code.startswith("4")]
        expense_accounts = [acc for code, acc in accounts.items() if code.startswith(("5", "6", "7", "8"))]

        transaction_count = 0
        invoice_num = 1
        bill_num = 1

        for client in clients:
            print(f"   Creating transactions for {client.name}...")

            for i in range(100):
                # 70% invoices (income), 30% bills (expenses)
                is_invoice = random.random() < 0.7

                if is_invoice:
                    template = random.choice(TRANSACTION_TEMPLATES["invoice"])
                    txn_type = "invoice"
                    ref_num = generate_reference_number("INV", invoice_num)
                    invoice_num += 1
                    account = random.choice(income_accounts)
                else:
                    template = random.choice(TRANSACTION_TEMPLATES["bill"])
                    txn_type = "bill"
                    ref_num = generate_reference_number("BILL", bill_num)
                    bill_num += 1
                    account = random.choice(expense_accounts)

                # Generate transaction details
                txn_date = generate_transaction_date()
                due_date = txn_date + timedelta(days=30)
                amount, tax_amount, total_amount = generate_amount(
                    template["min_amount"],
                    template["max_amount"]
                )

                # Format description
                month = MONTHS[txn_date.month - 1]
                description = template["description"].format(
                    month=month,
                    phase=random.randint(1, 5)
                )

                # Determine status based on date
                days_old = (date.today() - txn_date).days
                if days_old < 7:
                    status = random.choice(["draft", "submitted"])
                elif days_old < 30:
                    status = random.choice(["submitted", "approved"])
                elif days_old < 60:
                    status = random.choice(["approved", "paid"])
                else:
                    status = random.choice(["paid", "paid", "paid", "overdue"])

                transaction = Transaction(
                    id=uuid.uuid4(),
                    organization_id=org.id,
                    client_id=client.id,
                    account_id=account.id,
                    platform_id=f"mock-txn-{transaction_count+1:05d}",
                    platform_name="mock",
                    transaction_type=txn_type,
                    reference_number=ref_num,
                    description=description,
                    amount=amount,
                    tax_amount=tax_amount,
                    total_amount=total_amount,
                    currency="GBP",
                    transaction_date=txn_date,
                    due_date=due_date,
                    status=status,
                    is_reconciled=(status == "paid"),
                    last_synced_at=datetime.now(),
                )
                session.add(transaction)
                transaction_count += 1

            # Flush after each client to show progress
            session.flush()

        print(f"   Created {transaction_count} transactions total")

        # ----------------------------------------------------------------
        # 5. Commit all changes
        # ----------------------------------------------------------------
        print("\n5. Committing changes to database...")
        session.commit()
        print("   Done!")

        # ----------------------------------------------------------------
        # Summary
        # ----------------------------------------------------------------
        print("\n" + "=" * 60)
        print("SEED COMPLETE - SUMMARY")
        print("=" * 60)
        print(f"Organization: {org.name}")
        print(f"Accounts:     {len(CHART_OF_ACCOUNTS)}")
        print(f"Clients:      {len(clients)}")
        print(f"Transactions: {transaction_count}")
        print("=" * 60)

    except Exception as e:
        print(f"\nERROR: {e}")
        session.rollback()
        raise
    finally:
        session.close()


if __name__ == "__main__":
    seed_database()
