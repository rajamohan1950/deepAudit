import logging
from pathlib import Path

import yaml
from jinja2 import Environment, FileSystemLoader

logger = logging.getLogger(__name__)

PROMPTS_DIR = Path(__file__).parent.parent.parent.parent / "prompts"


class PromptBuilder:
    """Assembles LLM prompts from Jinja2 YAML templates."""

    def __init__(self, prompts_dir: str | None = None):
        self.prompts_dir = Path(prompts_dir) if prompts_dir else PROMPTS_DIR
        self.env = Environment(
            loader=FileSystemLoader(str(self.prompts_dir)),
            trim_blocks=True,
            lstrip_blocks=True,
        )

    def build_system_prompt(self) -> str:
        template = self._load_yaml("system_role.yaml")
        return template.get("content", "")

    def build_phase_prompt(
        self,
        phase_number: int,
        category_ids: list[int],
        system_context: dict,
        code_context: str,
        git_insights: dict | None = None,
    ) -> str:
        phase_file = f"phase_{phase_number:02d}.yaml"
        template_data = self._load_yaml(phase_file)

        signal_format = self._load_yaml("signal_format.yaml")

        context_summary = self._format_system_context(system_context)
        git_summary = self._format_git_insights(git_insights) if git_insights else ""

        prompt_parts = [
            template_data.get("preamble", ""),
            f"\n## System Under Audit\n{context_summary}",
        ]

        if git_summary:
            prompt_parts.append(f"\n## Git History Insights\n{git_summary}")

        prompt_parts.append(f"\n## Signal Output Format\n{signal_format.get('content', '')}")

        for cat_id in category_ids:
            cat_section = template_data.get("categories", {}).get(str(cat_id), "")
            if cat_section:
                prompt_parts.append(f"\n{cat_section}")

        prompt_parts.append(
            f"\n## Code and Configuration to Analyze\n"
            f"```\n{code_context}\n```"
        )

        prompt_parts.append(template_data.get("closing", ""))

        return "\n".join(prompt_parts)

    def _load_yaml(self, filename: str) -> dict:
        filepath = self.prompts_dir / filename
        if not filepath.exists():
            logger.warning(f"Prompt template not found: {filepath}")
            return {}
        try:
            with open(filepath) as f:
                return yaml.safe_load(f) or {}
        except Exception as e:
            logger.error(f"Error loading prompt {filename}: {e}")
            return {}

    def _format_system_context(self, ctx: dict) -> str:
        lines = []
        field_map = {
            "tech_stack": "Tech Stack",
            "architecture": "Architecture",
            "cloud_provider": "Cloud Provider",
            "container_orchestration": "Container Orchestration",
            "databases": "Databases",
            "message_queues": "Message Queues",
            "ai_ml_components": "AI/ML Components",
            "scale": "Scale",
            "team_size": "Team Size",
            "compliance_requirements": "Compliance",
            "external_dependencies": "External Dependencies",
            "current_state": "Current State",
            "os_runtime": "OS/Runtime",
            "multi_tenancy": "Multi-tenancy",
            "geographic_scope": "Geographic Scope",
        }
        for key, label in field_map.items():
            val = ctx.get(key, "")
            if val:
                if isinstance(val, list):
                    val = ", ".join(str(v) for v in val)
                lines.append(f"- **{label}**: {val}")
        return "\n".join(lines)

    def _format_git_insights(self, insights: dict) -> str:
        lines = []
        if insights.get("bus_factor"):
            lines.append(f"- Bus Factor: {insights['bus_factor']}")
        if insights.get("secrets_found_count"):
            lines.append(
                f"- Potential secrets found in repo: {insights['secrets_found_count']}"
            )
        churn = insights.get("high_churn_files", [])
        if churn:
            files = ", ".join(f["path"] for f in churn[:5])
            lines.append(f"- High-churn files: {files}")
        return "\n".join(lines)
