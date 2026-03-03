"""Instant static analysis — produces real findings in <100ms with zero LLM calls.

Scans file structure, configs, dependencies, and code patterns using regex/AST
to generate the first batch of signals before LLM even starts.
"""

import re
import os
import logging
from dataclasses import dataclass, field
from pathlib import Path

logger = logging.getLogger(__name__)


@dataclass
class InstantSignal:
    category_id: int
    signal_text: str
    severity: str
    score: float
    evidence: str
    failure_scenario: str
    remediation: str
    effort: str
    confidence: float = 0.85


SECRETS_PATTERNS = [
    (r'(?i)(api[_-]?key|apikey)\s*[=:]\s*["\']?[A-Za-z0-9_\-]{20,}', "API key hardcoded"),
    (r'(?i)(secret|password|passwd|pwd)\s*[=:]\s*["\'][^"\']{8,}', "Secret/password hardcoded"),
    (r'(?i)bearer\s+[A-Za-z0-9_\-\.]{20,}', "Bearer token in code"),
    (r'AKIA[0-9A-Z]{16}', "AWS Access Key ID"),
    (r'(?i)-----BEGIN\s+(RSA\s+)?PRIVATE\s+KEY-----', "Private key in source"),
    (r'sk-[A-Za-z0-9]{32,}', "OpenAI API key"),
    (r'sk-ant-api\d+-[A-Za-z0-9_\-]{40,}', "Anthropic API key"),
    (r'ghp_[A-Za-z0-9]{36}', "GitHub personal access token"),
    (r'xoxb-[0-9]{10,}-[A-Za-z0-9]{20,}', "Slack bot token"),
]

SECURITY_PATTERNS = [
    (r'eval\s*\(', 3, "eval() usage — code injection risk", "P0", 9.5, "RCE via eval injection"),
    (r'exec\s*\(', 3, "exec() usage — code injection risk", "P0", 9.0, "RCE via exec injection"),
    (r'subprocess\.call.*shell\s*=\s*True', 3, "subprocess with shell=True — command injection", "P0", 9.5, "OS command injection"),
    (r'os\.system\s*\(', 3, "os.system() — command injection risk", "P0", 9.0, "OS command injection"),
    (r'pickle\.loads?\s*\(', 3, "Pickle deserialization — arbitrary code execution", "P0", 9.5, "Deserialization RCE"),
    (r'yaml\.load\s*\([^)]*\)(?!.*Loader)', 3, "YAML.load without safe Loader — code execution", "P0", 9.0, "Deserialization RCE"),
    (r'(?i)md5\s*\(', 5, "MD5 hash usage — cryptographically broken", "P1", 6.0, "Hash collision attack"),
    (r'(?i)sha1\s*\(', 5, "SHA-1 hash usage — cryptographically weak", "P2", 5.0, "Hash collision feasible"),
    (r'Math\.random\(\)', 5, "Math.random() for security — not cryptographically secure", "P1", 7.0, "Predictable token generation"),
    (r'random\.random\(\)|random\.randint\(', 5, "Python random module for security — use secrets module", "P1", 7.0, "Predictable token generation"),
    (r'(?i)cors.*\*|allow_origins.*\[.*\*.*\]', 3, "CORS wildcard origin — any site can make requests", "P1", 6.5, "Cross-origin data theft"),
    (r'(?i)(verify\s*=\s*False|ssl\s*=\s*False|check_hostname\s*=\s*False)', 5, "SSL verification disabled", "P1", 7.5, "Man-in-the-middle attack"),
    (r'DEBUG\s*=\s*True', 4, "Debug mode enabled — exposes stack traces and internals", "P1", 6.0, "Information disclosure"),
    (r'(?i)jwt\.decode.*verify\s*=\s*False', 1, "JWT verification disabled — token forgery", "P0", 9.5, "Authentication bypass"),
    (r'(?i)password.*=\s*["\'][^"\']{1,20}["\']', 1, "Short/hardcoded password", "P1", 7.0, "Credential compromise"),
]

SQL_INJECTION_PATTERNS = [
    (r'f["\'].*(?:SELECT|INSERT|UPDATE|DELETE|FROM|WHERE).*\{', "f-string SQL query — SQL injection risk"),
    (r'%s.*%.*(?:SELECT|INSERT|UPDATE|DELETE)', "String format SQL — SQL injection risk"),
    (r'\.format\(.*\).*(?:SELECT|INSERT|UPDATE|DELETE)', ".format() SQL — SQL injection risk"),
    (r'\+\s*.*(?:SELECT|INSERT|UPDATE|DELETE)', "String concatenation SQL — SQL injection risk"),
]

PERF_PATTERNS = [
    (r'SELECT\s+\*', 9, "SELECT * query — over-fetching columns", "P2", 5.0, "SELECT specific columns only"),
    (r'time\.sleep\s*\(', 7, "Blocking sleep in application code", "P2", 5.0, "Use async sleep or remove"),
    (r'\.readlines\(\)', 7, "readlines() loads entire file into memory", "P2", 4.0, "Use line-by-line iterator"),
    (r'json\.dumps.*json\.loads', 7, "Redundant JSON serialize/deserialize cycle", "P2", 4.0, "Pass object directly"),
]

RELIABILITY_PATTERNS = [
    (r'except\s*:', 14, "Bare except — swallows all errors including SystemExit", "P1", 6.0, "Catch specific exceptions"),
    (r'except\s+Exception\s*:', 14, "Broad Exception catch — masks real errors", "P2", 5.0, "Catch specific exceptions"),
    (r'pass\s*$', 14, "Empty except/pass — silently ignores errors", "P2", 5.0, "Log or handle the error"),
    (r'TODO|FIXME|HACK|XXX|TEMP', 30, "Code marker indicates known issue", "P3", 3.0, "Address the TODO/FIXME"),
]


class InstantScanner:
    """Produces findings in <100ms using pure static analysis."""

    def scan(self, repo_path: str, classified_files: list[dict]) -> list[InstantSignal]:
        signals: list[InstantSignal] = []

        signals.extend(self._scan_structure(repo_path))
        signals.extend(self._scan_dependencies(repo_path))
        signals.extend(self._scan_configs(repo_path, classified_files))
        signals.extend(self._scan_code_patterns(classified_files))
        signals.extend(self._scan_docker(repo_path))
        signals.extend(self._scan_ci_cd(repo_path))

        return signals

    def _scan_structure(self, repo_path: str) -> list[InstantSignal]:
        signals = []
        root = Path(repo_path)

        if not (root / ".gitignore").exists():
            signals.append(InstantSignal(
                category_id=30, signal_text="No .gitignore file — risk of committing secrets, build artifacts, and IDE files",
                severity="P1", score=6.0, evidence=f"{repo_path}/.gitignore (missing)",
                failure_scenario="Secrets, node_modules, .env files committed to git history",
                remediation="Create .gitignore with standard patterns for your language/framework", effort="S",
            ))

        if not any((root / f).exists() for f in ["README.md", "README.rst", "README"]):
            signals.append(InstantSignal(
                category_id=40, signal_text="No README — knowledge silo risk, no onboarding documentation",
                severity="P3", score=3.0, evidence=f"{repo_path}/README.md (missing)",
                failure_scenario="New team members can't understand the project without tribal knowledge",
                remediation="Create README with setup instructions, architecture overview, and contributing guide", effort="S",
            ))

        env_files = list(root.glob("**/.env")) + list(root.glob("**/.env.*"))
        env_files = [f for f in env_files if ".env.example" not in f.name and ".env.sample" not in f.name]
        if env_files:
            signals.append(InstantSignal(
                category_id=4, signal_text=f".env file(s) in repository — {len(env_files)} file(s) may contain secrets",
                severity="P0", score=9.0, evidence=", ".join(str(f.relative_to(root)) for f in env_files[:5]),
                failure_scenario="API keys, database passwords, and secrets exposed in version control",
                remediation="Add .env to .gitignore, rotate all exposed secrets, use vault/secrets manager", effort="S",
            ))

        test_dirs = [d for d in ["tests", "test", "spec", "__tests__"] if (root / d).exists()]
        if not test_dirs:
            signals.append(InstantSignal(
                category_id=29, signal_text="No test directory found — zero automated test coverage",
                severity="P1", score=7.0, evidence=f"{repo_path} (no tests/, test/, spec/, __tests__/)",
                failure_scenario="Bugs ship to production undetected, regressions go unnoticed",
                remediation="Create test suite with unit tests for critical business logic at minimum", effort="L",
            ))

        if not any((root / f).exists() for f in [".github/workflows", "Jenkinsfile", ".gitlab-ci.yml", ".circleci", "azure-pipelines.yml"]):
            signals.append(InstantSignal(
                category_id=21, signal_text="No CI/CD pipeline detected — manual deployment risk",
                severity="P1", score=6.5, evidence=f"{repo_path} (no .github/workflows, Jenkinsfile, etc.)",
                failure_scenario="Manual deployments are error-prone, no automated testing gate",
                remediation="Set up CI/CD pipeline with at minimum: lint, test, build, deploy stages", effort="M",
            ))

        return signals

    def _scan_dependencies(self, repo_path: str) -> list[InstantSignal]:
        signals = []
        root = Path(repo_path)

        for dep_file in ["requirements.txt", "Pipfile", "pyproject.toml"]:
            path = root / dep_file
            if path.exists():
                content = path.read_text(errors="ignore")
                unpinned = []
                for line in content.splitlines():
                    line = line.strip()
                    if line and not line.startswith("#") and not line.startswith("["):
                        if ">=" in line and "==" not in line:
                            unpinned.append(line.split(">=")[0].strip())
                        elif "==" not in line and "@" not in line and line.isalpha():
                            unpinned.append(line)
                if unpinned:
                    signals.append(InstantSignal(
                        category_id=22, signal_text=f"{len(unpinned)} Python dependencies not pinned to exact version — build not reproducible",
                        severity="P2", score=5.0, evidence=f"{dep_file}: {', '.join(unpinned[:5])}{'...' if len(unpinned) > 5 else ''}",
                        failure_scenario="pip install resolves different version tomorrow, introduces breaking change or vulnerability",
                        remediation="Pin all dependencies with == in requirements.txt, use pip-compile or poetry.lock", effort="S",
                    ))

        for lock_file, ecosystem in [("package-lock.json", "npm"), ("yarn.lock", "yarn"), ("poetry.lock", "Python"), ("Pipfile.lock", "Python"), ("go.sum", "Go"), ("Cargo.lock", "Rust")]:
            pkg_files = {"package-lock.json": "package.json", "yarn.lock": "package.json", "poetry.lock": "pyproject.toml", "Pipfile.lock": "Pipfile", "go.sum": "go.mod", "Cargo.lock": "Cargo.toml"}
            pkg = pkg_files.get(lock_file, "")
            if (root / pkg).exists() if pkg else False:
                if not (root / lock_file).exists():
                    signals.append(InstantSignal(
                        category_id=22, signal_text=f"{ecosystem} lockfile ({lock_file}) missing — dependency resolution non-deterministic",
                        severity="P1", score=6.5, evidence=f"{pkg} exists but {lock_file} missing",
                        failure_scenario="Different environments install different dependency versions — works on my machine, fails in prod",
                        remediation=f"Generate and commit {lock_file} to ensure deterministic builds", effort="S",
                    ))

        return signals

    def _scan_configs(self, repo_path: str, classified_files: list[dict]) -> list[InstantSignal]:
        signals = []
        root = Path(repo_path)

        for f_info in classified_files:
            if f_info.get("file_type") != "config":
                continue
            path = Path(f_info["absolute_path"])
            try:
                content = path.read_text(errors="ignore")
            except Exception:
                continue

            for pattern, desc in SECRETS_PATTERNS:
                matches = re.findall(pattern, content)
                if matches:
                    signals.append(InstantSignal(
                        category_id=4, signal_text=f"{desc} found in {f_info['path']}",
                        severity="P0", score=9.0, evidence=f"{f_info['path']}",
                        failure_scenario="Secret exposed — attacker gains access to external service or database",
                        remediation="Remove secret from code, rotate it, use environment variables or secrets manager", effort="S",
                    ))
                    break

        return signals

    def _scan_code_patterns(self, classified_files: list[dict]) -> list[InstantSignal]:
        signals = []
        code_files = [f for f in classified_files if f.get("file_type") == "source"]

        for f_info in code_files[:200]:
            try:
                content = open(f_info["absolute_path"], "r", errors="ignore").read()
            except Exception:
                continue

            for pattern, cat_id, desc, sev, score, scenario in SECURITY_PATTERNS:
                matches = list(re.finditer(pattern, content))
                if matches:
                    line_no = content[:matches[0].start()].count('\n') + 1
                    signals.append(InstantSignal(
                        category_id=cat_id, signal_text=f"{desc} in {f_info['path']}:{line_no}",
                        severity=sev, score=score, evidence=f"{f_info['path']}:L{line_no} — {matches[0].group()[:80]}",
                        failure_scenario=scenario,
                        remediation=f"Remove or replace the unsafe pattern in {f_info['path']}", effort="S",
                    ))

            for pattern, desc in SQL_INJECTION_PATTERNS:
                matches = list(re.finditer(pattern, content, re.IGNORECASE))
                if matches:
                    line_no = content[:matches[0].start()].count('\n') + 1
                    signals.append(InstantSignal(
                        category_id=3, signal_text=f"{desc} in {f_info['path']}:{line_no}",
                        severity="P0", score=9.5, evidence=f"{f_info['path']}:L{line_no}",
                        failure_scenario="SQL injection allows attacker to read/modify/delete all database records",
                        remediation="Use parameterized queries or ORM query builder instead of string interpolation", effort="S",
                    ))

            for pattern, cat_id, desc, sev, score, fix in PERF_PATTERNS:
                matches = list(re.finditer(pattern, content, re.IGNORECASE))
                if matches:
                    line_no = content[:matches[0].start()].count('\n') + 1
                    signals.append(InstantSignal(
                        category_id=cat_id, signal_text=f"{desc} in {f_info['path']}:{line_no}",
                        severity=sev, score=score, evidence=f"{f_info['path']}:L{line_no}",
                        failure_scenario="Performance degradation under load",
                        remediation=fix, effort="S",
                    ))

            for pattern, cat_id, desc, sev, score, fix in RELIABILITY_PATTERNS:
                matches = list(re.finditer(pattern, content))
                if matches and len(matches) > 2:
                    signals.append(InstantSignal(
                        category_id=cat_id, signal_text=f"{len(matches)}x {desc} across {f_info['path']}",
                        severity=sev, score=score, evidence=f"{f_info['path']} — {len(matches)} occurrences",
                        failure_scenario="Errors silently swallowed, debugging impossible",
                        remediation=fix, effort="M",
                    ))

        return signals

    def _scan_docker(self, repo_path: str) -> list[InstantSignal]:
        signals = []
        root = Path(repo_path)

        for df in root.glob("**/Dockerfile*"):
            try:
                content = df.read_text(errors="ignore")
            except Exception:
                continue
            rel = str(df.relative_to(root))

            if re.search(r'FROM\s+\S+:latest', content):
                signals.append(InstantSignal(
                    category_id=21, signal_text=f"Dockerfile uses :latest tag — non-reproducible builds",
                    severity="P2", score=5.0, evidence=f"{rel}",
                    failure_scenario="Deploying today gives different image than yesterday, introduces unknown changes",
                    remediation="Pin base image to specific version tag or SHA digest", effort="S",
                ))

            if not re.search(r'USER\s+\S+', content) or re.search(r'USER\s+root', content):
                signals.append(InstantSignal(
                    category_id=19, signal_text=f"Container runs as root — container escape = host root",
                    severity="P1", score=7.5, evidence=f"{rel}",
                    failure_scenario="Container vulnerability + root = full host compromise",
                    remediation="Add USER nonroot directive, run as non-root user", effort="S",
                ))

            if re.search(r'COPY\s+\.\s', content) and not any(
                (root / f).exists() for f in [".dockerignore"]
            ):
                signals.append(InstantSignal(
                    category_id=19, signal_text=f"COPY . without .dockerignore — secrets/artifacts may be copied into image",
                    severity="P1", score=6.5, evidence=f"{rel}",
                    failure_scenario=".env, .git, node_modules copied into image, secrets exposed",
                    remediation="Create .dockerignore excluding .env, .git, node_modules, etc.", effort="S",
                ))

        return signals

    def _scan_ci_cd(self, repo_path: str) -> list[InstantSignal]:
        signals = []
        root = Path(repo_path)

        workflows = list(root.glob(".github/workflows/*.yml")) + list(root.glob(".github/workflows/*.yaml"))
        for wf in workflows:
            try:
                content = wf.read_text(errors="ignore")
            except Exception:
                continue
            rel = str(wf.relative_to(root))

            if re.search(r'actions/checkout@v[12](?!\d)', content):
                signals.append(InstantSignal(
                    category_id=22, signal_text=f"GitHub Action uses outdated checkout version in {rel}",
                    severity="P2", score=4.0, evidence=rel,
                    failure_scenario="Outdated action version may have known vulnerabilities",
                    remediation="Update to actions/checkout@v4 or pin to specific SHA", effort="S",
                ))

        return signals
