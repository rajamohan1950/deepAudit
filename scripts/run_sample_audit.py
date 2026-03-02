"""End-to-end demo: create a tenant, submit an audit, check results."""

import asyncio
import sys
import httpx

API_BASE = "http://localhost:8000/api/v1"


async def main():
    async with httpx.AsyncClient(timeout=30) as client:
        print("=== DeepAudit Sample Run ===\n")

        print("1. Registering tenant...")
        resp = await client.post(f"{API_BASE}/tenants", json={
            "name": "Demo Tenant",
            "email": "demo@example.com",
        })
        if resp.status_code == 201:
            data = resp.json()
            api_key = data["api_key"]
            print(f"   Tenant created. API Key: {api_key}\n")
        elif resp.status_code == 409:
            print("   Tenant already exists. Please use your existing API key.")
            return
        else:
            print(f"   Error: {resp.status_code} {resp.text}")
            return

        headers = {"X-API-Key": api_key}

        print("2. Creating audit...")
        audit_resp = await client.post(f"{API_BASE}/audits", json={
            "source": {
                "type": "github",
                "repo_url": "https://github.com/tiangolo/fastapi",
                "branch": "master",
            },
            "system_context": {
                "tech_stack": ["Python 3.11", "FastAPI", "Starlette"],
                "architecture": "Framework / Library",
                "cloud_provider": "N/A",
                "databases": [],
                "scale": "Open source framework",
                "compliance_requirements": [],
            },
            "config": {
                "categories": [1, 2, 3],
                "max_signals_per_category": 10,
            },
        }, headers=headers)

        if audit_resp.status_code == 202:
            audit = audit_resp.json()
            audit_id = audit["id"]
            print(f"   Audit created: {audit_id}")
            print(f"   Status: {audit['status']}\n")
        else:
            print(f"   Error: {audit_resp.status_code} {audit_resp.text}")
            return

        print("3. Polling for progress...")
        for i in range(60):
            await asyncio.sleep(10)
            progress = await client.get(
                f"{API_BASE}/audits/{audit_id}/progress", headers=headers
            )
            if progress.status_code == 200:
                p = progress.json()
                print(f"   Phase {p['current_phase']}/10 | "
                      f"Signals: {p['signals_so_far']} | "
                      f"Status: {p['status']}")
                if p["status"] in ("completed", "failed"):
                    break

        print("\n4. Fetching signal summary...")
        summary = await client.get(
            f"{API_BASE}/audits/{audit_id}/signals/summary", headers=headers
        )
        if summary.status_code == 200:
            s = summary.json()
            print(f"   Total signals: {s['total']}")
            print(f"   By severity: {s['by_severity']}")

        print("\n5. Fetching P0 signals...")
        p0 = await client.get(
            f"{API_BASE}/audits/{audit_id}/signals?severity=P0", headers=headers
        )
        if p0.status_code == 200:
            data = p0.json()
            for sig in data["signals"][:5]:
                print(f"   [{sig['severity']}] {sig['signal_text'][:100]}...")

        print("\n=== Done ===")


if __name__ == "__main__":
    asyncio.run(main())
