#!/usr/bin/env python3
"""Security behavior smoke checks against a running ECP API."""
from __future__ import annotations

import asyncio
import sys

import httpx


async def main() -> int:
    base_url = (sys.argv[1] if len(sys.argv) > 1 else "http://127.0.0.1:8080").rstrip("/")
    api_key = sys.argv[2] if len(sys.argv) > 2 else ""

    missing_key_headers = {"x-ecp-user-id": "alice"}
    valid_headers = {
        "x-ecp-user-id": "alice",
        "x-ecp-department": "finance",
        "x-ecp-role": "analyst",
    }
    if api_key:
        valid_headers["x-ecp-api-key"] = api_key

    async with httpx.AsyncClient(timeout=20.0) as client:
        # Resolve once as owner.
        resolve_resp = await client.post(
            f"{base_url}/api/v1/resolve",
            json={"concept": "APAC revenue last quarter"},
            headers=valid_headers,
        )
        if resolve_resp.status_code != 200:
            print(f"FAILED: resolve returned {resolve_resp.status_code}")
            return 1
        resolution_id = resolve_resp.json().get("resolution_id")
        if not resolution_id:
            print("FAILED: resolve missing resolution_id")
            return 1

        # Owner can read provenance.
        owner_prov = await client.get(
            f"{base_url}/api/v1/provenance/{resolution_id}",
            headers=valid_headers,
        )
        if owner_prov.status_code != 200:
            print(f"FAILED: owner provenance returned {owner_prov.status_code}")
            return 1

        # Different user is blocked (IDOR guard).
        intruder = dict(valid_headers)
        intruder["x-ecp-user-id"] = "mallory"
        intruder_prov = await client.get(
            f"{base_url}/api/v1/provenance/{resolution_id}",
            headers=intruder,
        )
        if intruder_prov.status_code != 403:
            print(f"FAILED: intruder provenance expected 403 got {intruder_prov.status_code}")
            return 1

        # Optional API key smoke: if key was provided, call without key should fail.
        if api_key:
            no_key = await client.post(
                f"{base_url}/api/v1/resolve",
                json={"concept": "revenue"},
                headers=missing_key_headers,
            )
            if no_key.status_code != 401:
                print(f"FAILED: expected 401 without API key, got {no_key.status_code}")
                return 1

    print("Security smoke PASSED")
    return 0


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
