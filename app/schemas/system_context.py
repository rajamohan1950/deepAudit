from pydantic import BaseModel, Field


class SystemContext(BaseModel):
    """User-provided metadata about the system being audited.
    The LLM uses this alongside code artifacts to produce relevant signals.
    """

    tech_stack: list[str] = Field(
        ...,
        description="e.g. ['Python 3.11', 'FastAPI', 'React 18']",
        min_length=1,
    )
    languages_versions: list[str] = Field(
        default=[],
        description="e.g. ['Python 3.11', 'Node 20', 'Go 1.22']",
    )
    architecture: str = Field(
        ...,
        description="e.g. 'Microservices', 'Monolith', 'Event-driven', 'CQRS'",
    )
    cloud_provider: str = Field(
        default="Unknown",
        description="e.g. 'AWS', 'Azure', 'GCP', 'Multi-cloud'",
    )
    container_orchestration: str = Field(
        default="Unknown",
        description="e.g. 'Kubernetes 1.29', 'ECS', 'Cloud Run', 'None'",
    )
    databases: list[str] = Field(
        default=[],
        description="e.g. ['PostgreSQL 16', 'Redis 7', 'MongoDB 7']",
    )
    message_queues: list[str] = Field(
        default=[],
        description="e.g. ['Kafka', 'RabbitMQ', 'SQS']",
    )
    ai_ml_components: list[str] = Field(
        default=[],
        description="e.g. ['GPT-4o', 'Claude', 'embeddings', 'fine-tuned models']",
    )
    scale: str = Field(
        default="Unknown",
        description="e.g. '10K RPM, 5TB data, 50 microservices'",
    )
    team_size: str = Field(
        default="Unknown",
        description="e.g. '25 engineers'",
    )
    compliance_requirements: list[str] = Field(
        default=[],
        description="e.g. ['SOC2', 'HIPAA', 'GDPR', 'PCI-DSS']",
    )
    external_dependencies: list[str] = Field(
        default=[],
        description="e.g. ['Stripe', 'Twilio', 'OpenAI API']",
    )
    current_state: str = Field(
        default="Production",
        description="e.g. 'Production 2 years', 'Pre-launch', 'Migration in progress'",
    )
    os_runtime: str = Field(
        default="Unknown",
        description="e.g. 'Ubuntu 22.04', 'Alpine 3.19', 'Amazon Linux 2023'",
    )
    multi_tenancy: str = Field(
        default="None",
        description="e.g. 'Shared infra', 'DB-per-tenant', 'Schema-per-tenant'",
    )
    geographic_scope: str = Field(
        default="Unknown",
        description="e.g. 'US-only', 'Global', 'EU + US'",
    )
    additional_context: str = Field(
        default="",
        description="Any other relevant context about the system",
    )
