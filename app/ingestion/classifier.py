import logging
from pathlib import Path

logger = logging.getLogger(__name__)


class FileType:
    SOURCE_CODE = "source_code"
    CONFIG = "config"
    IAC = "iac"
    K8S = "kubernetes"
    DOCKER = "docker"
    CICD = "cicd"
    DB_MIGRATION = "db_migration"
    DEPENDENCY = "dependency"
    TEST = "test"
    API_SPEC = "api_spec"
    AI_ML = "ai_ml"
    SECURITY = "security"
    DOCUMENTATION = "documentation"
    BUILD = "build"
    LOCKFILE = "lockfile"


LANGUAGE_MAP = {
    ".py": "python",
    ".js": "javascript",
    ".ts": "typescript",
    ".tsx": "typescript",
    ".jsx": "javascript",
    ".go": "go",
    ".java": "java",
    ".rs": "rust",
    ".rb": "ruby",
    ".php": "php",
    ".cs": "csharp",
    ".cpp": "cpp",
    ".c": "c",
    ".swift": "swift",
    ".kt": "kotlin",
    ".scala": "scala",
    ".r": "r",
    ".sql": "sql",
    ".sh": "shell",
    ".bash": "shell",
    ".zsh": "shell",
    ".ps1": "powershell",
}

DEPENDENCY_FILES = {
    "package.json", "requirements.txt", "Pipfile", "pyproject.toml",
    "setup.py", "setup.cfg", "go.mod", "Cargo.toml", "Gemfile",
    "pom.xml", "build.gradle", "build.gradle.kts", "composer.json",
    "mix.exs", "Package.swift", "pubspec.yaml",
}

LOCKFILE_FILES = {
    "package-lock.json", "yarn.lock", "pnpm-lock.yaml", "Pipfile.lock",
    "poetry.lock", "go.sum", "Cargo.lock", "Gemfile.lock",
    "composer.lock", "mix.lock",
}

CICD_FILES = {
    "Jenkinsfile", ".travis.yml", "appveyor.yml", "azure-pipelines.yml",
    "bitbucket-pipelines.yml", ".circleci/config.yml", "cloudbuild.yaml",
}

API_SPEC_FILES = {
    "openapi.yaml", "openapi.json", "swagger.yaml", "swagger.json",
    "api.yaml", "api.json",
}


class FileClassifier:
    """Classify discovered files into 15 audit-relevant types."""

    def classify(self, files: list[dict]) -> list[dict]:
        classified = []
        for f in files:
            file_type, language = self._classify_one(f["path"], f["extension"])
            f["file_type"] = file_type
            f["language"] = language
            classified.append(f)

        type_counts = {}
        for f in classified:
            type_counts[f["file_type"]] = type_counts.get(f["file_type"], 0) + 1
        logger.info(f"Classification breakdown: {type_counts}")

        return classified

    def _classify_one(self, path: str, ext: str) -> tuple[str, str | None]:
        name = Path(path).name
        parts = Path(path).parts

        # Security files
        if name in (".env", ".env.example", ".env.local", ".env.production"):
            return FileType.SECURITY, None
        if any(kw in name.lower() for kw in ("secret", "credential", "cert", "key.pem", "private")):
            return FileType.SECURITY, None

        # Docker
        if name in ("Dockerfile", ".dockerignore") or name.startswith("Dockerfile."):
            return FileType.DOCKER, None
        if name in ("docker-compose.yml", "docker-compose.yaml", "compose.yml", "compose.yaml"):
            return FileType.DOCKER, None

        # Kubernetes
        if any(d in parts for d in ("k8s", "kubernetes", "kube", "helm", "charts")):
            return FileType.K8S, None
        if ext in (".yaml", ".yml") and any(
            kw in path.lower()
            for kw in ("deployment", "service", "ingress", "configmap",
                       "secret", "hpa", "pdb", "networkpolicy", "rbac",
                       "serviceaccount", "cronjob", "statefulset", "daemonset")
        ):
            return FileType.K8S, None

        # IaC (Terraform, Pulumi, CloudFormation)
        if ext in (".tf", ".tfvars"):
            return FileType.IAC, "terraform"
        if any(d in parts for d in ("terraform", "pulumi", "cloudformation", "cdk")):
            return FileType.IAC, None

        # CI/CD
        if ".github" in parts and "workflows" in parts:
            return FileType.CICD, None
        if ".gitlab-ci.yml" == name:
            return FileType.CICD, None
        if name in CICD_FILES:
            return FileType.CICD, None

        # DB Migrations
        if any(d in parts for d in ("migrations", "migrate", "alembic", "flyway", "liquibase")):
            return FileType.DB_MIGRATION, LANGUAGE_MAP.get(ext)

        # Dependencies
        if name in DEPENDENCY_FILES:
            return FileType.DEPENDENCY, None

        # Lockfiles
        if name in LOCKFILE_FILES:
            return FileType.LOCKFILE, None

        # API specs
        if name in API_SPEC_FILES:
            return FileType.API_SPEC, None
        if ext in (".proto", ".graphql", ".gql"):
            return FileType.API_SPEC, LANGUAGE_MAP.get(ext)

        # AI/ML
        if any(kw in path.lower() for kw in (
            "prompt", "llm", "embedding", "model", "ai_", "ml_",
            "guardrail", "rag", "vector", "fine_tun", "finetun",
        )):
            lang = LANGUAGE_MAP.get(ext)
            if lang:
                return FileType.AI_ML, lang

        # Tests
        if any(d in parts for d in ("test", "tests", "spec", "specs", "__tests__")):
            return FileType.TEST, LANGUAGE_MAP.get(ext)
        if name.startswith("test_") or name.endswith("_test.py") or name.endswith(".test.ts"):
            return FileType.TEST, LANGUAGE_MAP.get(ext)
        if name.endswith("_spec.rb") or name.endswith(".spec.js") or name.endswith(".spec.ts"):
            return FileType.TEST, LANGUAGE_MAP.get(ext)

        # Documentation
        if name.lower() in (
            "readme.md", "changelog.md", "contributing.md",
            "license", "license.md", "code_of_conduct.md",
        ):
            return FileType.DOCUMENTATION, None
        if any(d in parts for d in ("docs", "doc", "adr", "adrs", "runbooks")):
            return FileType.DOCUMENTATION, None

        # Build files
        if name in ("Makefile", "CMakeLists.txt", "Rakefile", "Taskfile.yml"):
            return FileType.BUILD, None
        if ext in (".cmake",):
            return FileType.BUILD, None

        # Config files
        if ext in (".yaml", ".yml", ".json", ".toml", ".ini", ".cfg", ".conf"):
            return FileType.CONFIG, None
        if name in (".eslintrc", ".prettierrc", ".editorconfig", ".gitignore"):
            return FileType.CONFIG, None

        # Source code (default for known languages)
        lang = LANGUAGE_MAP.get(ext)
        if lang:
            return FileType.SOURCE_CODE, lang

        return FileType.CONFIG, None
