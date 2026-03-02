# DeepAudit — Comprehensive Software Audit SaaS API

A total system audit API that produces **750+ structured signals** across **40 categories** covering security, performance, reliability, AI/ML, cost, compliance, and everything in between.

## Quick Start

```bash
# 1. Copy environment config
cp .env.example .env
# Edit .env with your OpenAI or Anthropic API key

# 2. Start all services
docker compose up -d

# 3. Create database tables and seed categories
docker compose exec api python scripts/seed_categories.py

# 4. API is live at http://localhost:8000
#    Docs at http://localhost:8000/docs
```

## Usage

```bash
# Register a tenant
curl -X POST http://localhost:8000/api/v1/tenants \
  -H "Content-Type: application/json" \
  -d '{"name": "My Org", "email": "admin@myorg.com"}'
# Response includes api_key (shown once)

# Create an audit from a GitHub repo
curl -X POST http://localhost:8000/api/v1/audits \
  -H "X-API-Key: da_your_key_here" \
  -H "Content-Type: application/json" \
  -d '{
    "source": {
      "type": "github",
      "repo_url": "https://github.com/org/repo",
      "branch": "main"
    },
    "system_context": {
      "tech_stack": ["Python 3.11", "FastAPI", "PostgreSQL 16"],
      "architecture": "Microservices",
      "cloud_provider": "AWS",
      "databases": ["PostgreSQL 16", "Redis 7"],
      "compliance_requirements": ["SOC2", "GDPR"]
    }
  }'

# Check progress
curl http://localhost:8000/api/v1/audits/{audit_id}/progress \
  -H "X-API-Key: da_your_key_here"

# Get P0 critical findings
curl "http://localhost:8000/api/v1/audits/{audit_id}/signals?severity=P0" \
  -H "X-API-Key: da_your_key_here"

# Get executive summary
curl http://localhost:8000/api/v1/audits/{audit_id}/reports/executive-summary \
  -H "X-API-Key: da_your_key_here"
```

## 40 Audit Categories

| Part | Categories | Focus |
|------|-----------|-------|
| A | 1-5 | Security & Access Control |
| B | 6-12 | Performance & Resources |
| C | 13-18 | Reliability & Fault Tolerance |
| D | 19-22 | Infrastructure & Cloud |
| E | 23-24 | AI/ML Specific |
| F | 25-28 | Observability & Ops |
| G | 29-34 | Quality & Process |
| H | 35-40 | Compliance, Process & Misc |

## 11 Deliverables

1. **Signal Table** — filterable/sortable export of all 750+ signals
2. **Executive Summary** — top 15 findings with impact and cost
3. **Risk Heatmap** — 40 categories x 4 severity levels
4. **SPOF Map** — every single point of failure with blast radius
5. **Failure Mode Catalog** — critical path failures and cascading effects
6. **Performance Profile** — latency, memory, CPU, DB analysis
7. **AI/ML Risk Register** — per-endpoint injection, hallucination, cost risk
8. **Cost Analysis** — optimization opportunities ranked by savings
9. **Observability Scorecard** — maturity rating per subcategory
10. **Compliance Gap Matrix** — regulation to control to gap mapping
11. **Remediation Roadmap** — prioritized timeline (Week 1 P0 through Quarter 2 P3)

## Architecture

- **FastAPI** — async REST API
- **PostgreSQL 16** — persistent storage
- **Redis 7** — job queue, rate limiting, progress events
- **ARQ** — async background workers for audit execution
- **OpenAI / Anthropic** — LLM-driven analysis engine
- **GitPython** — repository cloning and git history analysis

## Development

```bash
# Install dependencies
pip install -r requirements.txt

# Run API locally
uvicorn app.main:app --reload

# Run worker
arq app.workers.audit_worker.WorkerSettings

# Run tests
pytest tests/ -v
```
