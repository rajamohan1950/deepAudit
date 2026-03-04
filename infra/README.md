# DeepAudit Infrastructure

Cloud deployment templates for the DeepAudit Intelligence Platform.

## Contents

| Path | Description |
|------|-------------|
| `aws/cloudformation.yaml` | AWS CloudFormation template (VPC, ECS Fargate, RDS, ElastiCache, ALB) |
| `azure/deploy.json` | Azure ARM template (Container Apps, PostgreSQL, Redis, ACR) |
| `COST_ESTIMATE.md` | Monthly cost estimates for AWS and Azure |

## Architecture

Both templates deploy:

- **API** – FastAPI web service (uvicorn)
- **Worker** – ARQ background worker for audit jobs
- **PostgreSQL** – Database (RDS / Azure Database for PostgreSQL)
- **Redis** – Job queue (ElastiCache / Azure Cache for Redis)
- **Container Registry** – ECR / ACR for Docker images

## Prerequisites

- AWS CLI or Azure CLI
- Docker (for building and pushing images)
- OpenAI API key (required)
- Anthropic API key (optional)

## Quick Start

See `COST_ESTIMATE.md` for deployment commands.

## Security Notes

- Use strong passwords for database credentials
- Store API keys in AWS Secrets Manager or Azure Key Vault for production
- Restrict PostgreSQL/Redis to VPC/private subnets in production
- Enable HTTPS/TLS for the API in production
