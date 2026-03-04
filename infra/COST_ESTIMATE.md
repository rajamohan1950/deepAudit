# DeepAudit Infrastructure — Cost Estimate

Estimated monthly costs for running DeepAudit on AWS and Azure (US regions).  
Prices are approximate and may vary by region and over time.

---

## AWS (CloudFormation)

| Component | Sizing | Unit Price | Monthly (730 hrs) |
|----------|--------|------------|-------------------|
| **ECS Fargate – API** | 0.25 vCPU, 512 MB | ~$0.012/hr | ~$8.76 |
| **ECS Fargate – Worker** | 0.5 vCPU, 1 GB | ~$0.024/hr | ~$17.52 |
| **RDS PostgreSQL** | db.t3.micro, 20 GB | ~$0.017/hr | ~$12.41 |
| **ElastiCache Redis** | cache.t3.micro | ~$0.017/hr | ~$12.41 |
| **Application Load Balancer** | 1 ALB + LCU | ~$0.0225/hr + LCU | ~$16–22 |
| **ECR** | 10 images stored | ~$0.10/GB/mo | ~$1 |
| **CloudWatch Logs** | 5 GB ingestion | $0.50/GB | ~$2.50 |
| **Data transfer** | Outbound (estimate) | $0.09/GB | ~$5–15 |

### AWS Total (baseline)

| Tier | Monthly estimate |
|------|------------------|
| **Minimum** | **~$70–75** |
| **Typical** | **~$85–100** |

### AWS cost notes

- Fargate: $0.04048/vCPU-hr + $0.004445/GB-hr (us-east-1)
- RDS db.t3.micro: single-AZ, 20 GB
- ElastiCache cache.t3.micro: 256 MB
- Savings: Fargate Spot (~70% off) or Reserved Capacity

---

## Azure (ARM Template)

| Component | Sizing | Unit Price | Monthly |
|----------|--------|------------|---------|
| **Container Apps – API** | 0.5 vCPU, 1 GB | ~$0.000024/vCPU-s, $0.000003/GB-s | ~$15–25 |
| **Container Apps – Worker** | 0.5 vCPU, 1 GB | Same | ~$15–25 |
| **PostgreSQL Flexible** | B_Standard_B1ms, 32 GB | ~$0.0208/hr | ~$15.18 |
| **Azure Cache for Redis** | Basic C0 (250 MB) | ~$16/mo flat | ~$16 |
| **Container Registry** | Basic | ~$5/mo | ~$5 |
| **Log Analytics** | 5 GB ingestion | $0.50/GB (first 5 GB) | ~$2.50 |
| **Virtual Network** | VNet + subnets | Free | $0 |
| **Data transfer** | Outbound | $0.087/GB | ~$5–15 |

### Azure Total (baseline)

| Tier | Monthly estimate |
|------|------------------|
| **Minimum** | **~$70–80** |
| **Typical** | **~$85–100** |

### Azure cost notes

- Container Apps: consumption billing (vCPU-s, GB-s)
- PostgreSQL Burstable B1ms: 1 vCore, 2 GB RAM
- Redis Basic C0: 250 MB, non-HA

---

## Cost comparison summary

| | AWS | Azure |
|---|-----|-------|
| **Baseline monthly** | ~$75–100 | ~$75–100 |
| **Dev / low usage** | ~$70 | ~$70 |
| **Production (scaled)** | ~$150–250 | ~$150–250 |

---

## Cost optimization

### Both clouds

1. **LLM usage** – Largest variable cost; OpenAI/Anthropic billed separately.
2. **Scale to zero** – Use serverless/consumption plans where possible.
3. **Reserved / Savings Plans** – 1–3 year commitments for 30–50% savings.
4. **Right-sizing** – Start with smallest instances and scale up as needed.

### AWS

- Use **Fargate Spot** for worker (up to ~70% off).
- Use **RDS Reserved Instances** for predictable workloads.
- Use **ElastiCache Reserved Nodes** for steady Redis usage.

### Azure

- Use **Container Apps consumption plan** with scale-to-zero.
- Use **PostgreSQL Burstable** tier for dev/test.
- Use **Azure Hybrid Benefit** if you have existing licenses.

---

## Excluded costs

- **OpenAI / Anthropic** – Per-token; depends on audit volume.
- **GitHub API** – Free tier usually sufficient.
- **Custom domain / TLS** – Certificate and DNS costs if used.
- **Backup / DR** – Extra storage and replication if enabled.

---

## Deployment steps

### AWS

```bash
# 1. Create stack (provide parameters)
aws cloudformation create-stack \
  --stack-name deepaudit-prod \
  --template-body file://infra/aws/cloudformation.yaml \
  --parameters \
    ParameterKey=DbMasterPassword,ParameterValue=YOUR_SECURE_PASSWORD \
    ParameterKey=OpenAiApiKey,ParameterValue=YOUR_OPENAI_KEY \
  --capabilities CAPABILITY_NAMED_IAM

# 2. Build and push image
aws ecr get-login-password --region us-east-1 | docker login --username AWS --password-stdin ACCOUNT.dkr.ecr.us-east-1.amazonaws.com
docker build -t deepaudit .
docker tag deepaudit:latest ACCOUNT.dkr.ecr.us-east-1.amazonaws.com/deepaudit:latest
docker push ACCOUNT.dkr.ecr.us-east-1.amazonaws.com/deepaudit:latest
```

### Azure

```bash
# 1. Create resource group
az group create --name deepaudit-rg --location eastus

# 2. Deploy template
az deployment group create \
  --resource-group deepaudit-rg \
  --template-file infra/azure/deploy.json \
  --parameters dbAdminPassword=YOUR_PASSWORD openAiApiKey=YOUR_OPENAI_KEY

# 3. Build and push image
az acr login --name ENVACRNAME
docker build -t deepaudit .
docker tag deepaudit:latest ENVACRNAME.azurecr.io/deepaudit:latest
docker push ENVACRNAME.azurecr.io/deepaudit:latest
```

---

*Prices as of March 2025. Verify with [AWS Pricing Calculator](https://calculator.aws/) and [Azure Pricing Calculator](https://azure.microsoft.com/pricing/calculator/).*
