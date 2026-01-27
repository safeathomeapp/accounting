#!/usr/bin/env python3
"""
Generate canonical cashflow facts from existing transactions.

Usage:
    python scripts/generate_facts.py                    # Process unmapped transactions
    python scripts/generate_facts.py --rebuild          # Delete and rebuild all facts
    python scripts/generate_facts.py --org-id <uuid>    # Specific organization
    python scripts/generate_facts.py --dry-run          # Preview only, no changes
"""

import sys
import argparse
import json
from pathlib import Path
from uuid import UUID

# Add project root to path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from backend.database import SessionLocal
from backend.canonical.engine import MappingEngine


def main():
    parser = argparse.ArgumentParser(description="Generate canonical cashflow facts")
    parser.add_argument("--rebuild", action="store_true",
                        help="Delete all facts and rebuild from scratch")
    parser.add_argument("--org-id", type=str, default=None,
                        help="Organization UUID to process (default: all)")
    parser.add_argument("--dry-run", action="store_true",
                        help="Preview only, don't commit changes")
    args = parser.parse_args()

    org_id = UUID(args.org_id) if args.org_id else None

    db = SessionLocal()
    try:
        engine = MappingEngine(db)
        loaded = engine.load_mappings()
        print(f"Loaded {loaded} active mappings")

        if loaded == 0:
            print("WARNING: No mappings found. Run seed_canonical_mappings.py first.")
            return

        if args.rebuild:
            print("Rebuilding all facts...")
            stats = engine.rebuild_facts(org_id=org_id)
            print(f"Rebuild complete:")
            print(f"  Deleted facts:      {stats.get('deleted_facts', 0)}")
            print(f"  Deleted quarantine: {stats.get('deleted_quarantine', 0)}")
        else:
            print("Processing unmapped transactions...")
            stats = engine.process_all(org_id=org_id, dry_run=args.dry_run)

        print(f"Results:")
        print(f"  Total:       {stats.get('total', 0)}")
        print(f"  Mapped:      {stats.get('mapped', 0)}")
        print(f"  Quarantined: {stats.get('quarantined', 0)}")
        print(f"  Errors:      {stats.get('errors', 0)}")

        if args.dry_run:
            print("\n[DRY RUN] No changes were committed.")

    finally:
        db.close()


if __name__ == "__main__":
    main()
