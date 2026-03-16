"""
Claude Vision OCR Service for Document Extraction.

Uses Claude's vision capabilities to extract structured data from invoices,
bills, and receipts. Returns data in a format compatible with the document
draft workflow.
"""

import base64
import json
import logging
import re
from datetime import date, datetime
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import anthropic

from backend.config import settings

logger = logging.getLogger(__name__)


class ClaudeOCRError(Exception):
    """Raised when Claude OCR extraction fails."""
    pass


class ClaudeOCRService:
    """
    Service for extracting structured invoice data from documents using Claude Vision.

    Supports PDF and image files (PNG, JPEG, GIF, WebP).
    """

    # Supported MIME types for Claude Vision
    SUPPORTED_IMAGE_TYPES = {
        "image/png": "png",
        "image/jpeg": "jpeg",
        "image/jpg": "jpeg",
        "image/gif": "gif",
        "image/webp": "webp",
    }

    SUPPORTED_PDF_TYPE = "application/pdf"

    # Extraction prompt for invoices/bills/receipts
    EXTRACTION_PROMPT = """Analyze this document and extract the following information as structured JSON.

The document is likely an invoice, bill, receipt, or similar financial document.

Extract and return a JSON object with this exact structure:
{
    "doc_type": "invoice" | "bill" | "receipt" | "credit_note" | "unknown",
    "vendor": {
        "name": "The VENDOR/SUPPLIER/SELLER company name - look at the LETTERHEAD, LOGO, or company name at TOP of document. This is the business that ISSUED the invoice. Do NOT use invoice reference numbers or customer names.",
        "address_line1": "First line of vendor address or null",
        "address_line2": "Second line of vendor address or null",
        "city": "Vendor city or null",
        "postcode": "Vendor postcode/ZIP or null",
        "country": "Vendor country or null",
        "vat_number": "Vendor VAT/Tax registration number or null",
        "phone": "Vendor phone number or null",
        "email": "Vendor email address or null",
        "website": "Vendor website or null"
    },
    "customer": {
        "name": "The customer/buyer name - who the invoice is addressed TO",
        "address_line1": "First line of customer address or null",
        "address_line2": "Second line of customer address or null",
        "city": "Customer city or null",
        "postcode": "Customer postcode/ZIP or null",
        "country": "Customer country or null",
        "reference": "Customer reference/account number if shown or null"
    },
    "doc_date": "YYYY-MM-DD format or null if not found",
    "due_date": "YYYY-MM-DD format or null if not found (look for 'due date', 'payment due', 'balance due by')",
    "currency": "3-letter currency code like GBP, USD, EUR",
    "invoice_no": "Invoice number, reference number, or order number - look for 'Invoice #', 'Inv No', 'Reference', 'Order #'",
    "order_no": "Order/PO number if different from invoice number, or null",
    "payment_terms": "Payment terms if shown (e.g., 'Net 30', '14 days') or null",
    "payment_status": "paid | unpaid | partial | null",
    "totals": {
        "net": "Net/subtotal amount BEFORE VAT/tax as decimal string",
        "vat": "VAT/tax amount as decimal string",
        "gross": "Gross/total amount INCLUDING VAT as decimal string - this is the final 'Total' or 'Amount Due'"
    },
    "lines": [
        {
            "line_no": 1,
            "description": "Item/service description",
            "qty": "Quantity as decimal string (default 1 if not shown)",
            "unit_price": "Unit price EXCLUDING VAT as decimal string",
            "net": "Line net amount (qty * unit_price) as decimal string",
            "vat": "Line VAT amount as decimal string or 0.00",
            "gross": "Line gross amount (net + vat) as decimal string",
            "vat_code": "VAT rate: 'VAT20' for 20%, 'VAT5' for 5%, 'VAT0' or 'ZERO' for 0%, 'EXEMPT' for exempt",
            "nominal_code": null,
            "confidence": "0.00 to 1.00 - how confident you are in this line's data"
        }
    ],
    "raw_text": "Any additional relevant text, notes, or payment details from the document",
    "confidence": "Overall extraction confidence 0.00 to 1.00"
}

CRITICAL RULES:
1. VENDOR NAME = The company in the LETTERHEAD/LOGO at the TOP of the document. This is who ISSUED/SENT the invoice. NOT the invoice reference, NOT the customer name.
2. CUSTOMER NAME = The person/company in "Bill To", "Invoice To", "Att:", or similar - who the invoice is addressed TO.
3. All amounts as strings with 2 decimal places (e.g., "100.00", "0.00")
4. If you cannot find a value, use null (not empty string)
5. For UK: default GBP, standard VAT is 20%
6. gross = net + vat (verify this adds up)
7. Invoice reference/ref fields are NOT vendor names - they are reference numbers
8. Return ONLY the JSON object, no other text

Extract the data now:"""

    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize the Claude OCR service.

        Args:
            api_key: Anthropic API key. Falls back to settings.claude_api_key
        """
        self.api_key = api_key or settings.claude_api_key
        if not self.api_key:
            raise ClaudeOCRError("Claude API key not configured. Set CLAUDE_API_KEY in .env")

        self.client = anthropic.Anthropic(api_key=self.api_key)
        self.model = settings.claude_model
        self.max_tokens = settings.claude_max_tokens

    def _read_file_as_base64(self, file_path: str) -> Tuple[str, str]:
        """
        Read a file and return its base64 encoding and media type.

        Args:
            file_path: Path to the file

        Returns:
            Tuple of (base64_data, media_type)
        """
        path = Path(file_path)
        if not path.exists():
            raise ClaudeOCRError(f"File not found: {file_path}")

        # Determine media type from extension
        ext = path.suffix.lower()
        media_type = None

        if ext == ".pdf":
            media_type = self.SUPPORTED_PDF_TYPE
        elif ext in (".png",):
            media_type = "image/png"
        elif ext in (".jpg", ".jpeg"):
            media_type = "image/jpeg"
        elif ext == ".gif":
            media_type = "image/gif"
        elif ext == ".webp":
            media_type = "image/webp"
        else:
            raise ClaudeOCRError(f"Unsupported file type: {ext}")

        with open(file_path, "rb") as f:
            data = base64.standard_b64encode(f.read()).decode("utf-8")

        return data, media_type

    def _build_message_content(self, file_path: str, mime_type: Optional[str] = None) -> List[Dict]:
        """
        Build the message content with image/document for Claude.

        Args:
            file_path: Path to the document
            mime_type: Optional MIME type override

        Returns:
            List of content blocks for Claude message
        """
        base64_data, detected_media_type = self._read_file_as_base64(file_path)
        media_type = mime_type or detected_media_type

        if media_type == self.SUPPORTED_PDF_TYPE:
            # For PDFs, use document type
            return [
                {
                    "type": "document",
                    "source": {
                        "type": "base64",
                        "media_type": "application/pdf",
                        "data": base64_data,
                    },
                },
                {
                    "type": "text",
                    "text": self.EXTRACTION_PROMPT,
                },
            ]
        else:
            # For images, use image type
            return [
                {
                    "type": "image",
                    "source": {
                        "type": "base64",
                        "media_type": media_type,
                        "data": base64_data,
                    },
                },
                {
                    "type": "text",
                    "text": self.EXTRACTION_PROMPT,
                },
            ]

    def _parse_decimal(self, value: Any, default: str = "0.00") -> Decimal:
        """Safely parse a value to Decimal."""
        if value is None:
            return Decimal(default)
        try:
            # Remove any currency symbols and whitespace
            if isinstance(value, str):
                value = re.sub(r'[£$€\s,]', '', value)
            return Decimal(str(value)).quantize(Decimal("0.01"))
        except (InvalidOperation, ValueError):
            return Decimal(default)

    def _parse_date(self, value: Any) -> Optional[date]:
        """Safely parse a date string."""
        if not value:
            return None
        try:
            if isinstance(value, str):
                # Try ISO format first
                return datetime.strptime(value, "%Y-%m-%d").date()
        except ValueError:
            pass

        # Try common UK formats
        formats = ["%d/%m/%Y", "%d-%m-%Y", "%d.%m.%Y", "%d %B %Y", "%d %b %Y"]
        for fmt in formats:
            try:
                return datetime.strptime(value, fmt).date()
            except ValueError:
                continue

        return None

    def _validate_and_normalize(self, data: Dict) -> Dict:
        """
        Validate and normalize the extracted data.

        Args:
            data: Raw extracted data from Claude

        Returns:
            Normalized data dict
        """
        # Normalize doc_type
        doc_type = (data.get("doc_type") or "unknown").lower()
        if doc_type not in ("invoice", "bill", "receipt", "credit_note"):
            doc_type = "invoice"  # Default assumption

        # Parse totals
        totals_raw = data.get("totals") or {}
        totals = {
            "net": self._parse_decimal(totals_raw.get("net")),
            "vat": self._parse_decimal(totals_raw.get("vat")),
            "gross": self._parse_decimal(totals_raw.get("gross")),
        }

        # If gross is 0 but we have net+vat, calculate it
        if totals["gross"] == 0 and (totals["net"] > 0 or totals["vat"] > 0):
            totals["gross"] = totals["net"] + totals["vat"]

        # Parse lines
        lines_raw = data.get("lines") or []
        lines = []
        for i, line_raw in enumerate(lines_raw):
            line = {
                "line_no": line_raw.get("line_no") or (i + 1),
                "description": line_raw.get("description") or "Item",
                "qty": self._parse_decimal(line_raw.get("qty"), "1.00"),
                "unit_price": self._parse_decimal(line_raw.get("unit_price")),
                "net": self._parse_decimal(line_raw.get("net")),
                "vat": self._parse_decimal(line_raw.get("vat")),
                "gross": self._parse_decimal(line_raw.get("gross")),
                "vat_code": line_raw.get("vat_code"),
                "nominal_code": line_raw.get("nominal_code"),
                "confidence": self._parse_decimal(line_raw.get("confidence"), "0.80"),
            }

            # Calculate gross if missing
            if line["gross"] == 0 and line["net"] > 0:
                line["gross"] = line["net"] + line["vat"]

            lines.append(line)

        # If no lines but we have totals, create a single line
        if not lines and totals["gross"] > 0:
            lines.append({
                "line_no": 1,
                "description": "Document total",
                "qty": Decimal("1.00"),
                "unit_price": totals["net"],
                "net": totals["net"],
                "vat": totals["vat"],
                "gross": totals["gross"],
                "vat_code": "VAT20" if totals["vat"] > 0 else "ZERO",
                "nominal_code": None,
                "confidence": Decimal("0.70"),
            })

        # Extract vendor details (new format) or fall back to counterparty_name (old format)
        vendor_raw = data.get("vendor") or {}
        vendor = {
            "name": vendor_raw.get("name") or data.get("counterparty_name") or "Unknown",
            "address_line1": vendor_raw.get("address_line1"),
            "address_line2": vendor_raw.get("address_line2"),
            "city": vendor_raw.get("city"),
            "postcode": vendor_raw.get("postcode"),
            "country": vendor_raw.get("country"),
            "vat_number": vendor_raw.get("vat_number"),
            "phone": vendor_raw.get("phone"),
            "email": vendor_raw.get("email"),
            "website": vendor_raw.get("website"),
        }

        # Extract customer details
        customer_raw = data.get("customer") or {}
        customer = {
            "name": customer_raw.get("name") or data.get("customer_name"),
            "address_line1": customer_raw.get("address_line1"),
            "address_line2": customer_raw.get("address_line2"),
            "city": customer_raw.get("city"),
            "postcode": customer_raw.get("postcode"),
            "country": customer_raw.get("country"),
            "reference": customer_raw.get("reference"),
        }

        return {
            "doc_type": doc_type,
            "counterparty_name": vendor["name"],  # Keep for backward compat
            "vendor": vendor,
            "customer": customer,
            "doc_date": self._parse_date(data.get("doc_date")) or date.today(),
            "due_date": self._parse_date(data.get("due_date")),
            "currency": (data.get("currency") or "GBP").upper()[:3],
            "invoice_no": data.get("invoice_no"),
            "order_no": data.get("order_no"),
            "payment_terms": data.get("payment_terms"),
            "payment_status": data.get("payment_status"),
            "totals": totals,
            "lines": lines,
            "raw_text": data.get("raw_text") or "",
            "confidence": self._parse_decimal(data.get("confidence"), "0.80"),
        }

    def extract_document(self, file_path: str, mime_type: Optional[str] = None) -> Dict[str, Any]:
        """
        Extract structured data from a document using Claude Vision.

        Args:
            file_path: Path to the document file (PDF or image)
            mime_type: Optional MIME type of the file

        Returns:
            Dict containing extracted document data in the format expected
            by the document draft workflow.

        Raises:
            ClaudeOCRError: If extraction fails
        """
        logger.info(f"Starting Claude OCR extraction for: {file_path}")

        try:
            # Build message content with document
            content = self._build_message_content(file_path, mime_type)

            # Call Claude API
            logger.debug(f"Calling Claude API with model: {self.model}")
            response = self.client.messages.create(
                model=self.model,
                max_tokens=self.max_tokens,
                messages=[
                    {
                        "role": "user",
                        "content": content,
                    }
                ],
            )

            # Extract text response
            response_text = response.content[0].text if response.content else ""
            logger.debug(f"Claude response length: {len(response_text)}")

            # Parse JSON from response
            # Try to find JSON in the response (Claude might include extra text)
            json_match = re.search(r'\{[\s\S]*\}', response_text)
            if not json_match:
                raise ClaudeOCRError("No JSON found in Claude response")

            json_str = json_match.group()
            raw_data = json.loads(json_str)

            # Validate and normalize
            normalized = self._validate_and_normalize(raw_data)

            logger.info(
                f"Extraction complete: {normalized['doc_type']} from "
                f"{normalized['counterparty_name']}, "
                f"total: {normalized['totals']['gross']} {normalized['currency']}"
            )

            return normalized

        except anthropic.APIError as e:
            logger.error(f"Claude API error: {e}")
            raise ClaudeOCRError(f"Claude API error: {e}")
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse Claude response as JSON: {e}")
            raise ClaudeOCRError(f"Failed to parse extraction result: {e}")
        except Exception as e:
            logger.error(f"Unexpected error during extraction: {e}")
            raise ClaudeOCRError(f"Extraction failed: {e}")


# Singleton instance for convenience
_service_instance: Optional[ClaudeOCRService] = None


def get_claude_ocr_service() -> ClaudeOCRService:
    """Get or create the Claude OCR service instance."""
    global _service_instance
    if _service_instance is None:
        _service_instance = ClaudeOCRService()
    return _service_instance


def extract_document(file_path: str, mime_type: Optional[str] = None) -> Dict[str, Any]:
    """
    Convenience function to extract document data.

    Args:
        file_path: Path to the document
        mime_type: Optional MIME type

    Returns:
        Extracted document data
    """
    service = get_claude_ocr_service()
    return service.extract_document(file_path, mime_type)
