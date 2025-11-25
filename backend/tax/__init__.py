"""
Tax compliance module.

Handles tax types, rates, liabilities, calculations, and compliance reporting.
"""

from backend.tax.manager import TaxManager
from backend.tax.calculator import TaxCalculator
from backend.tax.liability import TaxLiabilityManager
from backend.tax.compliance import TaxComplianceReporter

__all__ = ["TaxManager", "TaxCalculator", "TaxLiabilityManager", "TaxComplianceReporter"]
