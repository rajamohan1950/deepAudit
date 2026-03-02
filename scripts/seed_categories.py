"""Seed the 40 audit categories into the database."""

import asyncio
import sys

sys.path.insert(0, ".")

from app.database import async_session_factory, engine, Base
from app.models.category import Category

CATEGORIES = [
    (1, "Authentication & Identity", "A", "Security & Access Control", 25),
    (2, "Authorization & Access Control", "A", "Security & Access Control", 20),
    (3, "Input Validation & Injection", "A", "Security & Access Control", 30),
    (4, "Data Protection & Privacy", "A", "Security & Access Control", 20),
    (5, "Cryptography & Key Management", "A", "Security & Access Control", 15),
    (6, "Memory Leaks & Management", "B", "Performance & Resources", 25),
    (7, "CPU & Compute Performance", "B", "Performance & Resources", 20),
    (8, "Network & I/O Performance", "B", "Performance & Resources", 20),
    (9, "Database & Storage Performance", "B", "Performance & Resources", 25),
    (10, "Caching Performance", "B", "Performance & Resources", 15),
    (11, "OS & Kernel Level", "B", "Performance & Resources", 20),
    (12, "Graceful Shutdown & Lifecycle", "B", "Performance & Resources", 10),
    (13, "Single Points of Failure", "C", "Reliability & Fault Tolerance", 25),
    (14, "Fault Tolerance & Resilience", "C", "Reliability & Fault Tolerance", 25),
    (15, "Concurrency & Race Conditions", "C", "Reliability & Fault Tolerance", 20),
    (16, "Data Integrity & Consistency", "C", "Reliability & Fault Tolerance", 20),
    (17, "Distributed System Failures", "C", "Reliability & Fault Tolerance", 15),
    (18, "Queue & Event Processing", "C", "Reliability & Fault Tolerance", 15),
    (19, "Infrastructure & Cloud Security", "D", "Infrastructure & Cloud", 25),
    (20, "Capacity Planning & Scalability", "D", "Infrastructure & Cloud", 20),
    (21, "Deployment, CI/CD & Release", "D", "Infrastructure & Cloud", 20),
    (22, "Third-Party & Supply Chain", "D", "Infrastructure & Cloud", 15),
    (23, "AI/ML Model Risks", "E", "AI/ML Specific", 20),
    (24, "AI/ML Cost & Operational", "E", "AI/ML Specific", 15),
    (25, "Metrics & Monitoring", "F", "Observability & Ops", 20),
    (26, "Logging", "F", "Observability & Ops", 15),
    (27, "Distributed Tracing", "F", "Observability & Ops", 10),
    (28, "Alerting & Incident Response", "F", "Observability & Ops", 20),
    (29, "Testing & QA", "G", "Quality & Process", 25),
    (30, "Code Quality & Technical Debt", "G", "Quality & Process", 20),
    (31, "API Design & Contracts", "G", "Quality & Process", 15),
    (32, "UX, Accessibility & Client-Side", "G", "Quality & Process", 15),
    (33, "Cost & FinOps", "G", "Quality & Process", 15),
    (34, "Multi-Tenancy & Isolation", "G", "Quality & Process", 10),
    (35, "Compliance & Regulatory", "H", "Compliance, Process & Misc", 15),
    (36, "Disaster Recovery", "H", "Compliance, Process & Misc", 15),
    (37, "Internationalization & Localization", "H", "Compliance, Process & Misc", 10),
    (38, "State Management", "H", "Compliance, Process & Misc", 10),
    (39, "Backward Compatibility & Migration", "H", "Compliance, Process & Misc", 10),
    (40, "Organizational & Knowledge", "H", "Compliance, Process & Misc", 15),
]


async def seed():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with async_session_factory() as session:
        for cat_id, name, part, part_name, min_signals in CATEGORIES:
            existing = await session.get(Category, cat_id)
            if existing:
                existing.name = name
                existing.part = part
                existing.part_name = part_name
                existing.min_signals = min_signals
            else:
                cat = Category(
                    id=cat_id,
                    name=name,
                    part=part,
                    part_name=part_name,
                    description=f"Category {cat_id}: {name}",
                    min_signals=min_signals,
                    checklist=[],
                )
                session.add(cat)

        await session.commit()
        print(f"Seeded {len(CATEGORIES)} categories")


if __name__ == "__main__":
    asyncio.run(seed())
