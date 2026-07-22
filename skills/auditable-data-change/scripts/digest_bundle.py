#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path


def bundle_digest(path: Path) -> str:
    payload = json.loads(path.read_text(encoding="utf-8"))
    canonical = json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    return f"sha256:{hashlib.sha256(canonical.encode('utf-8')).hexdigest()}"


def main() -> None:
    parser = argparse.ArgumentParser(description="Hash a canonical evidence bundle")
    parser.add_argument("bundle", type=Path)
    parser.add_argument("--expect", help="Fail unless the digest matches this value")
    args = parser.parse_args()
    digest = bundle_digest(args.bundle)
    print(digest)
    if args.expect and args.expect != digest:
        raise SystemExit("Evidence bundle digest mismatch")


if __name__ == "__main__":
    main()
