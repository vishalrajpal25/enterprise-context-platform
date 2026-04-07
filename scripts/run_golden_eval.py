#!/usr/bin/env python3
"""Run golden_queries.yaml against a live ECP API; exit non-zero if any case fails."""
from __future__ import annotations

import asyncio
import sys

from src.evals.golden_queries import run_golden_queries


async def main() -> int:
    base = sys.argv[1] if len(sys.argv) > 1 else "http://127.0.0.1:8080"
    suite = await run_golden_queries(base_url=base.rstrip("/"))
    print(f"Golden suite: {suite.passed}/{suite.total} passed ({suite.accuracy_pct:.1f}%)")
    for r in suite.results:
        if not r.passed:
            print(f"  FAIL {r.query_name}: {r.mismatches}")
    return 0 if suite.failed == 0 else 1


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
