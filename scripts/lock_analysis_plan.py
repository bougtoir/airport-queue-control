from __future__ import annotations

import argparse
import hashlib
from pathlib import Path


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> None:
    parser = argparse.ArgumentParser(description="Create or verify the locked-plan hash")
    parser.add_argument(
        "--plan",
        type=Path,
        default=Path("ANALYSIS_PLAN_LOCKED.yaml"),
    )
    parser.add_argument(
        "--hash-file",
        type=Path,
        default=Path("ANALYSIS_PLAN_LOCKED.sha256"),
    )
    args = parser.parse_args()

    value = digest(args.plan)
    expected = f"{value}  {args.plan.name}\n"
    if args.hash_file.exists():
        if args.hash_file.read_text(encoding="utf-8") != expected:
            raise SystemExit("Locked analysis plan hash mismatch")
        print(value)
        return
    args.hash_file.write_text(expected, encoding="utf-8")
    print(value)


if __name__ == "__main__":
    main()
