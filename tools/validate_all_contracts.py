"""Validate every JSON contract under contracts/."""
from __future__ import annotations
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(Path(__file__).resolve().parent))
from validate_contract import validate  # noqa: E402

def main() -> int:
    files = sorted((ROOT / "contracts").rglob("*.json"))
    if not files:
        print("No contract files found.")
        return 1
    failures = 0
    for path in files:
        errors = validate(path)
        if errors:
            failures += 1
            print(f"INVALID: {path}")
            for error in errors: print(f"- {error}")
        else:
            print(f"VALID: {path}")
    print(f"contracts={len(files)} failures={failures}")
    return 1 if failures else 0

if __name__ == "__main__": sys.exit(main())
