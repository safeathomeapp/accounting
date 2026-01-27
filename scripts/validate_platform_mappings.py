#!/usr/bin/env python3
"""
Validate that all transaction type/status combinations have canonical mappings.

Checks every distinct (platform_name, transaction_type, status) combination in the
transactions table against the platform_transaction_mapping table.

Exit code 0: All types are mapped (CI-safe).
Exit code 1: Gaps found - some transaction types have no mapping.

Usage:
    python scripts/validate_platform_mappings.py
    python scripts/validate_platform_mappings.py --org-id <uuid>
    python scripts/validate_platform_mappings.py --platform xero
"""

import sys
import argparse
from pathlib import Path
from uuid import UUID

# Add project root to path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from sqlalchemy import func, distinct
from backend.database import SessionLocal
from backend.models import Transaction
from backend.canonical.models import PlatformTransactionMapping


def validate(org_id=None, platform=None):
    db = SessionLocal()
    try:
        # Get all distinct combos in transactions
        query = db.query(
            Transaction.platform_name,
            Transaction.transaction_type,
            Transaction.status,
            func.count(Transaction.id).label("count"),
        )
        if org_id:
            query = query.filter(Transaction.organization_id == org_id)
        if platform:
            query = query.filter(Transaction.platform_name == platform)

        combos = (
            query
            .group_by(
                Transaction.platform_name,
                Transaction.transaction_type,
                Transaction.status,
            )
            .all()
        )

        if not combos:
            print("No transactions found in database.")
            return 0

        # Get all active mappings
        mappings = (
            db.query(PlatformTransactionMapping)
            .filter(PlatformTransactionMapping.is_active == True)
            .all()
        )

        mapped_keys = {
            (m.platform_name.lower(), m.source_type.lower(), m.source_status.lower())
            for m in mappings
        }

        print(f"Found {len(combos)} distinct (platform, type, status) combinations")
        print(f"Found {len(mapped_keys)} active mappings\n")

        gaps = []
        mapped_count = 0

        for platform_name, txn_type, status, count in combos:
            key = (
                (platform_name or "").lower(),
                (txn_type or "").lower(),
                (status or "").lower(),
            )
            if key in mapped_keys:
                mapped_count += 1
            else:
                gaps.append({
                    "platform": platform_name or "(none)",
                    "type": txn_type or "(none)",
                    "status": status or "(none)",
                    "count": count,
                })

        if gaps:
            print(f"GAPS FOUND: {len(gaps)} unmapped combinations\n")
            print(f"{'Platform':<15} {'Type':<20} {'Status':<20} {'Txns':>6}")
            print("-" * 65)
            for g in sorted(gaps, key=lambda x: x["count"], reverse=True):
                print(f"{g['platform']:<15} {g['type']:<20} {g['status']:<20} {g['count']:>6}")
            print(f"\nTotal gaps: {len(gaps)}")
            print(f"Mapped: {mapped_count}/{len(combos)}")
            return 1
        else:
            print(f"ALL MAPPED: {mapped_count}/{len(combos)} combinations have active mappings")
            return 0

    finally:
        db.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Validate platform mapping coverage")
    parser.add_argument("--org-id", type=str, default=None, help="Filter by organization UUID")
    parser.add_argument("--platform", type=str, default=None, help="Filter by platform name")
    args = parser.parse_args()

    org_id = UUID(args.org_id) if args.org_id else None
    exit_code = validate(org_id=org_id, platform=args.platform)
    sys.exit(exit_code)
