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
from backend.models.user import User
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

# Demo user for testing
DEMO_USER_DATA = {
    "email": "test@example.com",
    "name": "Demo User",
    "password": "password",
    "role": "admin",
    "is_admin": True,
}

# ============================================================================
# CLIENT-SPECIFIC CHARTS OF ACCOUNTS
# Each client has their own chart pulled from their accounting software
# ============================================================================

# Construction company - Riverside Construction Ltd (uses Xero)
CONSTRUCTION_ACCOUNTS = [
    # Assets
    {"code": "1000", "name": "Business Current Account", "account_type": "bank", "description": "Main trading account"},
    {"code": "1010", "name": "Deposit Account", "account_type": "bank", "description": "Retention deposits"},
    {"code": "1100", "name": "Trade Debtors", "account_type": "asset", "description": "Customer invoices owing"},
    {"code": "1150", "name": "Retention Receivable", "account_type": "asset", "description": "Contract retentions held"},
    {"code": "1200", "name": "Prepayments", "account_type": "asset", "description": "Prepaid expenses"},
    {"code": "1400", "name": "Plant & Machinery", "account_type": "asset", "description": "Construction equipment"},
    {"code": "1410", "name": "Vehicles", "account_type": "asset", "description": "Vans, trucks, plant vehicles"},
    {"code": "1420", "name": "Tools & Equipment", "account_type": "asset", "description": "Hand tools, power tools"},
    # Liabilities
    {"code": "2000", "name": "Trade Creditors", "account_type": "liability", "description": "Supplier invoices owing"},
    {"code": "2050", "name": "Subcontractor Retention", "account_type": "liability", "description": "Retention held from subcontractors"},
    {"code": "2100", "name": "VAT Control", "account_type": "liability", "description": "VAT liability"},
    {"code": "2110", "name": "CIS Tax Deducted", "account_type": "liability", "description": "Construction Industry Scheme"},
    {"code": "2200", "name": "PAYE & NI", "account_type": "liability", "description": "Payroll taxes"},
    # Equity
    {"code": "3000", "name": "Share Capital", "account_type": "equity", "description": "Issued shares"},
    {"code": "3100", "name": "Retained Profits", "account_type": "equity", "description": "Accumulated profits"},
    # Income
    {"code": "4000", "name": "Contract Income", "account_type": "income", "description": "Main construction contracts"},
    {"code": "4010", "name": "Variation Income", "account_type": "income", "description": "Contract variations"},
    {"code": "4020", "name": "Maintenance Income", "account_type": "income", "description": "Maintenance contracts"},
    {"code": "4100", "name": "Plant Hire Income", "account_type": "income", "description": "Equipment hire to others"},
    # Expenses
    {"code": "5000", "name": "Materials", "account_type": "expense", "description": "Construction materials"},
    {"code": "5010", "name": "Subcontractor Costs", "account_type": "expense", "description": "Subcontractor labour"},
    {"code": "5020", "name": "Plant Hire", "account_type": "expense", "description": "Equipment rental"},
    {"code": "5030", "name": "Skip & Waste Disposal", "account_type": "expense", "description": "Site clearance"},
    {"code": "6000", "name": "Staff Wages", "account_type": "expense", "description": "Direct labour"},
    {"code": "6010", "name": "Site Staff Wages", "account_type": "expense", "description": "Site workers"},
    {"code": "7000", "name": "Premises Costs", "account_type": "expense", "description": "Yard and office rent"},
    {"code": "7200", "name": "Insurance", "account_type": "expense", "description": "Public liability, employers"},
    {"code": "7500", "name": "Vehicle Running Costs", "account_type": "expense", "description": "Fuel, repairs, tax"},
    {"code": "7600", "name": "Professional Fees", "account_type": "expense", "description": "Architects, surveyors"},
    {"code": "7700", "name": "Health & Safety", "account_type": "expense", "description": "PPE, training, compliance"},
]

# Marketing agency - Digital Spark Marketing (uses QuickBooks)
MARKETING_ACCOUNTS = [
    # Assets
    {"code": "100", "name": "Checking Account", "account_type": "bank", "description": "Main operating account"},
    {"code": "110", "name": "PayPal Account", "account_type": "bank", "description": "Online payments"},
    {"code": "120", "name": "Stripe Account", "account_type": "bank", "description": "Card payments"},
    {"code": "130", "name": "Accounts Receivable", "account_type": "asset", "description": "Client invoices"},
    {"code": "140", "name": "Prepaid Software", "account_type": "asset", "description": "Annual subscriptions"},
    {"code": "150", "name": "Computer Equipment", "account_type": "asset", "description": "Macs, monitors"},
    # Liabilities
    {"code": "200", "name": "Accounts Payable", "account_type": "liability", "description": "Vendor bills"},
    {"code": "210", "name": "Credit Card", "account_type": "liability", "description": "Company credit card"},
    {"code": "220", "name": "VAT Payable", "account_type": "liability", "description": "VAT owing"},
    {"code": "230", "name": "Deferred Revenue", "account_type": "liability", "description": "Retainer prepayments"},
    # Equity
    {"code": "300", "name": "Owner's Equity", "account_type": "equity", "description": "Capital invested"},
    {"code": "310", "name": "Retained Earnings", "account_type": "equity", "description": "Accumulated profits"},
    # Income
    {"code": "400", "name": "Retainer Income", "account_type": "income", "description": "Monthly retainers"},
    {"code": "410", "name": "Project Income", "account_type": "income", "description": "One-off projects"},
    {"code": "420", "name": "PPC Management", "account_type": "income", "description": "Google/Meta ads management"},
    {"code": "430", "name": "SEO Services", "account_type": "income", "description": "Search optimisation"},
    {"code": "440", "name": "Social Media Management", "account_type": "income", "description": "Social media services"},
    {"code": "450", "name": "Content Creation", "account_type": "income", "description": "Copywriting, video"},
    {"code": "460", "name": "Web Development", "account_type": "income", "description": "Website builds"},
    # Expenses
    {"code": "500", "name": "Contractor Fees", "account_type": "expense", "description": "Freelancers"},
    {"code": "510", "name": "Ad Spend (Pass-through)", "account_type": "expense", "description": "Client ad budgets"},
    {"code": "520", "name": "Software & Tools", "account_type": "expense", "description": "SaaS subscriptions"},
    {"code": "530", "name": "Stock Images/Video", "account_type": "expense", "description": "Media assets"},
    {"code": "600", "name": "Salaries", "account_type": "expense", "description": "Staff payroll"},
    {"code": "610", "name": "Employer NI", "account_type": "expense", "description": "National Insurance"},
    {"code": "700", "name": "Office Rent", "account_type": "expense", "description": "Coworking space"},
    {"code": "710", "name": "Internet & Phone", "account_type": "expense", "description": "Communications"},
    {"code": "800", "name": "Marketing & PR", "account_type": "expense", "description": "Own marketing"},
    {"code": "810", "name": "Conferences & Events", "account_type": "expense", "description": "Industry events"},
]

# Healthcare - Northern Healthcare Solutions (uses Xero)
HEALTHCARE_ACCOUNTS = [
    # Assets
    {"code": "1000", "name": "Current Account", "account_type": "bank", "description": "Operating account"},
    {"code": "1100", "name": "Accounts Receivable", "account_type": "asset", "description": "NHS and private invoices"},
    {"code": "1110", "name": "NHS Receivables", "account_type": "asset", "description": "NHS contract payments"},
    {"code": "1200", "name": "Prepayments", "account_type": "asset", "description": "Insurance, subscriptions"},
    {"code": "1300", "name": "Medical Supplies Stock", "account_type": "asset", "description": "Consumables inventory"},
    {"code": "1400", "name": "Medical Equipment", "account_type": "asset", "description": "Clinical equipment"},
    {"code": "1500", "name": "IT Equipment", "account_type": "asset", "description": "Computers, software"},
    # Liabilities
    {"code": "2000", "name": "Trade Creditors", "account_type": "liability", "description": "Supplier invoices"},
    {"code": "2100", "name": "VAT Control", "account_type": "liability", "description": "VAT (mostly exempt)"},
    {"code": "2200", "name": "PAYE & NI", "account_type": "liability", "description": "Payroll taxes"},
    {"code": "2300", "name": "Pension Contributions", "account_type": "liability", "description": "NHS Pension owing"},
    # Equity
    {"code": "3000", "name": "Share Capital", "account_type": "equity", "description": "Issued shares"},
    {"code": "3100", "name": "Reserves", "account_type": "equity", "description": "Retained profits"},
    # Income
    {"code": "4000", "name": "NHS Contract Income", "account_type": "income", "description": "NHS contracts"},
    {"code": "4010", "name": "Private Patient Income", "account_type": "income", "description": "Private consultations"},
    {"code": "4020", "name": "Insurance Patient Income", "account_type": "income", "description": "BUPA, AXA etc"},
    {"code": "4030", "name": "Training & Education", "account_type": "income", "description": "CPD courses"},
    {"code": "4100", "name": "Grant Income", "account_type": "income", "description": "Research grants"},
    # Expenses
    {"code": "5000", "name": "Medical Supplies", "account_type": "expense", "description": "Consumables"},
    {"code": "5010", "name": "Pharmaceuticals", "account_type": "expense", "description": "Drugs and medicines"},
    {"code": "5020", "name": "Laboratory Costs", "account_type": "expense", "description": "Testing services"},
    {"code": "6000", "name": "Clinical Staff Salaries", "account_type": "expense", "description": "Nurses, doctors"},
    {"code": "6010", "name": "Admin Staff Salaries", "account_type": "expense", "description": "Reception, admin"},
    {"code": "6100", "name": "Agency Staff", "account_type": "expense", "description": "Temporary cover"},
    {"code": "6200", "name": "NHS Pension Costs", "account_type": "expense", "description": "Employer contributions"},
    {"code": "7000", "name": "Premises Costs", "account_type": "expense", "description": "Clinic rent, rates"},
    {"code": "7100", "name": "Clinical Waste Disposal", "account_type": "expense", "description": "Sharps, waste"},
    {"code": "7200", "name": "Professional Indemnity", "account_type": "expense", "description": "Malpractice insurance"},
    {"code": "7300", "name": "CQC Registration", "account_type": "expense", "description": "Care Quality Commission"},
    {"code": "7400", "name": "Professional Memberships", "account_type": "expense", "description": "GMC, NMC fees"},
]

# Import/Export - Coastal Imports & Exports (uses Xero)
IMPORT_EXPORT_ACCOUNTS = [
    # Assets
    {"code": "1000", "name": "GBP Current Account", "account_type": "bank", "description": "Sterling account"},
    {"code": "1010", "name": "USD Account", "account_type": "bank", "description": "Dollar account"},
    {"code": "1020", "name": "EUR Account", "account_type": "bank", "description": "Euro account"},
    {"code": "1100", "name": "Trade Debtors", "account_type": "asset", "description": "Customer invoices"},
    {"code": "1110", "name": "Export Debtors", "account_type": "asset", "description": "Overseas customers"},
    {"code": "1200", "name": "Stock - UK Warehouse", "account_type": "asset", "description": "Inventory in UK"},
    {"code": "1210", "name": "Stock - In Transit", "account_type": "asset", "description": "Goods in shipping"},
    {"code": "1220", "name": "Stock - Bonded", "account_type": "asset", "description": "Bonded warehouse"},
    # Liabilities
    {"code": "2000", "name": "Trade Creditors GBP", "account_type": "liability", "description": "UK suppliers"},
    {"code": "2010", "name": "Trade Creditors USD", "account_type": "liability", "description": "US suppliers"},
    {"code": "2020", "name": "Trade Creditors EUR", "account_type": "liability", "description": "EU suppliers"},
    {"code": "2100", "name": "VAT Control", "account_type": "liability", "description": "VAT liability"},
    {"code": "2110", "name": "Import VAT Deferred", "account_type": "liability", "description": "Postponed VAT"},
    {"code": "2200", "name": "Customs Duty Accrual", "account_type": "liability", "description": "Duty owing"},
    # Equity
    {"code": "3000", "name": "Share Capital", "account_type": "equity", "description": "Issued shares"},
    {"code": "3100", "name": "Retained Profits", "account_type": "equity", "description": "Accumulated profits"},
    # Income
    {"code": "4000", "name": "UK Sales", "account_type": "income", "description": "Domestic sales"},
    {"code": "4010", "name": "EU Export Sales", "account_type": "income", "description": "Sales to EU"},
    {"code": "4020", "name": "ROW Export Sales", "account_type": "income", "description": "Rest of world"},
    {"code": "4100", "name": "Commission Income", "account_type": "income", "description": "Agency commissions"},
    {"code": "4900", "name": "FX Gains", "account_type": "income", "description": "Currency gains"},
    # Expenses
    {"code": "5000", "name": "Cost of Goods - UK", "account_type": "expense", "description": "UK purchases"},
    {"code": "5010", "name": "Cost of Goods - Import", "account_type": "expense", "description": "Imported goods"},
    {"code": "5100", "name": "Customs Duty", "account_type": "expense", "description": "Import duties"},
    {"code": "5110", "name": "Customs Clearance", "account_type": "expense", "description": "Agent fees"},
    {"code": "5200", "name": "Shipping - Sea Freight", "account_type": "expense", "description": "Container shipping"},
    {"code": "5210", "name": "Shipping - Air Freight", "account_type": "expense", "description": "Air cargo"},
    {"code": "5220", "name": "Haulage", "account_type": "expense", "description": "UK delivery"},
    {"code": "5300", "name": "Warehousing", "account_type": "expense", "description": "Storage costs"},
    {"code": "6000", "name": "Staff Salaries", "account_type": "expense", "description": "Payroll"},
    {"code": "7000", "name": "Office Costs", "account_type": "expense", "description": "Rent, utilities"},
    {"code": "7500", "name": "FX Losses", "account_type": "expense", "description": "Currency losses"},
    {"code": "7600", "name": "Bank Charges", "account_type": "expense", "description": "International transfers"},
]

# Food & Beverage - GreenLeaf Organic Foods (uses FreeAgent)
FOOD_BEVERAGE_ACCOUNTS = [
    # Assets
    {"code": "010", "name": "Business Account", "account_type": "bank", "description": "Main account"},
    {"code": "011", "name": "Savings Account", "account_type": "bank", "description": "Reserve funds"},
    {"code": "020", "name": "Trade Debtors", "account_type": "asset", "description": "Customer invoices"},
    {"code": "021", "name": "Wholesale Debtors", "account_type": "asset", "description": "Retail customers"},
    {"code": "030", "name": "Raw Materials Stock", "account_type": "asset", "description": "Ingredients"},
    {"code": "031", "name": "Packaging Stock", "account_type": "asset", "description": "Boxes, labels"},
    {"code": "032", "name": "Finished Goods Stock", "account_type": "asset", "description": "Ready to sell"},
    {"code": "040", "name": "Kitchen Equipment", "account_type": "asset", "description": "Production equipment"},
    {"code": "041", "name": "Refrigeration", "account_type": "asset", "description": "Cold storage"},
    {"code": "042", "name": "Delivery Van", "account_type": "asset", "description": "Refrigerated van"},
    # Liabilities
    {"code": "050", "name": "Trade Creditors", "account_type": "liability", "description": "Supplier invoices"},
    {"code": "051", "name": "Farmer Creditors", "account_type": "liability", "description": "Farm suppliers"},
    {"code": "060", "name": "VAT Liability", "account_type": "liability", "description": "VAT owing"},
    {"code": "061", "name": "PAYE Liability", "account_type": "liability", "description": "Payroll taxes"},
    # Equity
    {"code": "070", "name": "Capital", "account_type": "equity", "description": "Owner investment"},
    {"code": "071", "name": "Retained Profits", "account_type": "equity", "description": "Accumulated profits"},
    # Income
    {"code": "100", "name": "Direct Sales", "account_type": "income", "description": "Farm shop sales"},
    {"code": "101", "name": "Farmers Market Sales", "account_type": "income", "description": "Market stall"},
    {"code": "102", "name": "Online Sales", "account_type": "income", "description": "Website orders"},
    {"code": "103", "name": "Wholesale Sales", "account_type": "income", "description": "Retail/restaurant"},
    {"code": "104", "name": "Subscription Boxes", "account_type": "income", "description": "Veg box scheme"},
    # Expenses
    {"code": "200", "name": "Organic Produce", "account_type": "expense", "description": "Raw ingredients"},
    {"code": "201", "name": "Non-Organic Produce", "account_type": "expense", "description": "Conventional items"},
    {"code": "202", "name": "Packaging Materials", "account_type": "expense", "description": "Eco packaging"},
    {"code": "210", "name": "Production Labour", "account_type": "expense", "description": "Kitchen staff"},
    {"code": "211", "name": "Delivery Wages", "account_type": "expense", "description": "Drivers"},
    {"code": "212", "name": "Shop Staff", "account_type": "expense", "description": "Retail staff"},
    {"code": "300", "name": "Premises Rent", "account_type": "expense", "description": "Kitchen, shop rent"},
    {"code": "301", "name": "Utilities", "account_type": "expense", "description": "Electric, gas, water"},
    {"code": "302", "name": "Market Stall Fees", "account_type": "expense", "description": "Pitch fees"},
    {"code": "310", "name": "Van Running Costs", "account_type": "expense", "description": "Fuel, maintenance"},
    {"code": "320", "name": "Organic Certification", "account_type": "expense", "description": "Soil Association"},
    {"code": "321", "name": "Food Hygiene", "account_type": "expense", "description": "EHO compliance"},
    {"code": "330", "name": "Waste Disposal", "account_type": "expense", "description": "Compost, recycling"},
]

# Map client names to their charts of accounts
CLIENT_ACCOUNTS_MAP = {
    "Riverside Construction Ltd": CONSTRUCTION_ACCOUNTS,
    "Digital Spark Marketing": MARKETING_ACCOUNTS,
    "Northern Healthcare Solutions": HEALTHCARE_ACCOUNTS,
    "Coastal Imports & Exports": IMPORT_EXPORT_ACCOUNTS,
    "GreenLeaf Organic Foods": FOOD_BEVERAGE_ACCOUNTS,
}

# Platform used by each client
CLIENT_PLATFORM_MAP = {
    "Riverside Construction Ltd": "xero",
    "Digital Spark Marketing": "quickbooks",
    "Northern Healthcare Solutions": "xero",
    "Coastal Imports & Exports": "xero",
    "GreenLeaf Organic Foods": "freeagent",
}

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
            session.query(User).delete()
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
        # 1b. Create Demo User
        # ----------------------------------------------------------------
        print("\n1b. Creating Demo User...")
        demo_user = User(
            id=uuid.uuid4(),
            email=DEMO_USER_DATA["email"],
            name=DEMO_USER_DATA["name"],
            organization_id=org.id,
            role=DEMO_USER_DATA["role"],
            is_admin=DEMO_USER_DATA["is_admin"],
            is_active=True,
        )
        demo_user.set_password(DEMO_USER_DATA["password"])
        session.add(demo_user)
        session.flush()
        print(f"   Created: {demo_user.email} (Role: {demo_user.role})")
        print(f"   Login with: {DEMO_USER_DATA['email']} / {DEMO_USER_DATA['password']}")

        # ----------------------------------------------------------------
        # 2. Create Clients
        # ----------------------------------------------------------------
        print("\n2. Creating Clients...")
        clients = []
        for i, client_data in enumerate(CLIENTS_DATA):
            platform_name = CLIENT_PLATFORM_MAP.get(client_data["name"], "xero")
            client = Client(
                id=uuid.uuid4(),
                organization_id=org.id,
                platform_id=f"{platform_name}-client-{i+1:03d}",
                platform_name=platform_name,
                last_synced_at=datetime.now(),
                **client_data
            )
            session.add(client)
            clients.append(client)
            print(f"   Created: {client.name} (Platform: {platform_name})")
        session.flush()

        # ----------------------------------------------------------------
        # 3. Create Client-Specific Charts of Accounts
        # ----------------------------------------------------------------
        print("\n3. Creating Client-Specific Charts of Accounts...")
        client_accounts = {}  # {client_id: {code: account}}
        total_accounts = 0

        for client in clients:
            client_name = client.name
            chart = CLIENT_ACCOUNTS_MAP.get(client_name, [])
            platform_name = CLIENT_PLATFORM_MAP.get(client_name, "xero")

            client_accounts[client.id] = {}

            for i, acc_data in enumerate(chart):
                account = Account(
                    id=uuid.uuid4(),
                    organization_id=org.id,
                    client_id=client.id,
                    platform_id=f"{platform_name}-account-{client.id}-{i+1:03d}",
                    platform_name=platform_name,
                    **acc_data
                )
                session.add(account)
                client_accounts[client.id][acc_data["code"]] = account
                total_accounts += 1

            print(f"   {client_name}: {len(chart)} accounts")

        session.flush()
        print(f"   Total: {total_accounts} accounts across {len(clients)} clients")

        # ----------------------------------------------------------------
        # 4. Create Transactions (100 per client)
        # ----------------------------------------------------------------
        print("\n4. Creating Transactions (100 per client)...")

        transaction_count = 0
        invoice_num = 1
        bill_num = 1

        for client in clients:
            print(f"   Creating transactions for {client.name}...")

            # Get this client's accounts
            accounts = client_accounts.get(client.id, {})
            if not accounts:
                print(f"   WARNING: No accounts found for {client.name}, skipping transactions")
                continue

            # Separate income and expense accounts for this client
            income_accounts = [acc for code, acc in accounts.items()
                              if acc.account_type == "income"]
            expense_accounts = [acc for code, acc in accounts.items()
                               if acc.account_type == "expense"]

            # Fallback if no income/expense accounts
            if not income_accounts:
                income_accounts = list(accounts.values())
            if not expense_accounts:
                expense_accounts = list(accounts.values())

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
        print(f"Demo User:    {DEMO_USER_DATA['email']} / {DEMO_USER_DATA['password']}")
        print(f"Clients:      {len(clients)}")
        print(f"Accounts:     {total_accounts} (across all clients)")
        print(f"Transactions: {transaction_count}")
        print("\nClient Account Breakdown:")
        for client in clients:
            chart_size = len(CLIENT_ACCOUNTS_MAP.get(client.name, []))
            platform = CLIENT_PLATFORM_MAP.get(client.name, "unknown")
            print(f"  - {client.name}: {chart_size} accounts ({platform})")
        print("=" * 60)

    except Exception as e:
        print(f"\nERROR: {e}")
        session.rollback()
        raise
    finally:
        session.close()


if __name__ == "__main__":
    seed_database()
