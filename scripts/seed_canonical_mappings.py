#!/usr/bin/env python3
"""
Seed canonical mappings into the database.

Standalone script for dev/testing outside of Alembic.
Uses the same mapping definitions as the migration.

Usage:
    python scripts/seed_canonical_mappings.py              # Insert missing mappings
    python scripts/seed_canonical_mappings.py --replace     # Delete and re-insert all
    python scripts/seed_canonical_mappings.py --dry-run     # Preview only
"""

import sys
import argparse
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from backend.database import SessionLocal
from backend.canonical.models import PlatformTransactionMapping, NormalizedTxnType, NormalizedTxnStatus, CashflowBucket, DateSource
from backend.canonical.mapping_definitions import PLATFORM_MAPPINGS


def seed_mappings(replace: bool = False, dry_run: bool = False):
    db = SessionLocal()

    try:
        if replace:
            count = db.query(PlatformTransactionMapping).delete()
            print(f"Deleted {count} existing mappings")

        inserted = 0
        skipped = 0

        for m in PLATFORM_MAPPINGS:
            # Check if mapping already exists
            existing = (
                db.query(PlatformTransactionMapping)
                .filter_by(
                    platform_name=m["platform_name"],
                    source_type=m["source_type"],
                    source_status=m["source_status"],
                    is_active=True,
                )
                .first()
            )

            if existing and not replace:
                skipped += 1
                continue

            mapping = PlatformTransactionMapping(
                platform_name=m["platform_name"],
                source_type=m["source_type"],
                source_status=m["source_status"],
                normalized_type=NormalizedTxnType(m["normalized_type"]),
                normalized_status=NormalizedTxnStatus(m["normalized_status"]),
                canonical_bucket=CashflowBucket(m["canonical_bucket"]),
                effective_date_source=DateSource(m.get("effective_date_source", "TRANSACTION_DATE")),
                priority=m.get("priority", 0),
                is_active=True,
            )
            db.add(mapping)
            inserted += 1

        if dry_run:
            db.rollback()
            print(f"[DRY RUN] Would insert {inserted}, skip {skipped}")
        else:
            db.commit()
            print(f"Inserted {inserted} mappings, skipped {skipped} existing")

        # Verify
        total = db.query(PlatformTransactionMapping).filter_by(is_active=True).count()
        print(f"Total active mappings in database: {total}")

    finally:
        db.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Seed canonical mapping definitions")
    parser.add_argument("--replace", action="store_true", help="Delete all and re-insert")
    parser.add_argument("--dry-run", action="store_true", help="Preview only, no changes")
    args = parser.parse_args()

    seed_mappings(replace=args.replace, dry_run=args.dry_run)
