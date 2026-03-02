import logging
import re
from collections import Counter
from pathlib import Path

from git import Repo

logger = logging.getLogger(__name__)

SECRET_PATTERNS = [
    (r"(?i)(api[_-]?key|apikey)\s*[:=]\s*['\"]?[a-zA-Z0-9_\-]{20,}", "API key"),
    (r"(?i)(secret|password|passwd|pwd)\s*[:=]\s*['\"]?[^\s'\"]{8,}", "Secret/Password"),
    (r"(?i)aws[_-]?(access|secret)[_-]?key[_-]?id?\s*[:=]\s*['\"]?[A-Z0-9]{16,}", "AWS key"),
    (r"ghp_[a-zA-Z0-9]{36}", "GitHub PAT"),
    (r"sk-[a-zA-Z0-9]{32,}", "OpenAI/Stripe key"),
    (r"sk-ant-[a-zA-Z0-9\-]{40,}", "Anthropic key"),
    (r"-----BEGIN (RSA |EC |DSA )?PRIVATE KEY-----", "Private key"),
    (r"(?i)bearer\s+[a-zA-Z0-9_\-\.]{20,}", "Bearer token"),
    (r"(?i)(jdbc|mongodb|postgres|mysql|redis)://[^\s]{10,}", "Connection string"),
]


class GitAnalyzer:
    """Analyze git history for security signals, code churn, and bus factor."""

    def analyze(self, repo_path: str, max_commits: int = 200) -> dict:
        try:
            repo = Repo(repo_path)
        except Exception as e:
            logger.warning(f"Could not open git repo at {repo_path}: {e}")
            return self._empty_result()

        result = {
            "secrets_found": [],
            "bus_factor": 0,
            "author_distribution": {},
            "high_churn_files": [],
            "recent_changes": [],
            "commit_count": 0,
            "total_authors": 0,
        }

        try:
            commits = list(repo.iter_commits(max_count=max_commits))
            result["commit_count"] = len(commits)
        except Exception:
            return result

        author_counts = Counter()
        file_change_counts = Counter()

        for commit in commits:
            author = commit.author.name or commit.author.email
            author_counts[author] += 1

            try:
                for diff in commit.diff(commit.parents[0] if commit.parents else None):
                    if diff.a_path:
                        file_change_counts[diff.a_path] += 1
            except Exception:
                continue

        result["author_distribution"] = dict(author_counts.most_common(20))
        result["total_authors"] = len(author_counts)

        if author_counts:
            total_commits = sum(author_counts.values())
            cumulative = 0
            bus_factor = 0
            for _author, count in author_counts.most_common():
                cumulative += count
                bus_factor += 1
                if cumulative >= total_commits * 0.5:
                    break
            result["bus_factor"] = bus_factor

        result["high_churn_files"] = [
            {"path": path, "changes": count}
            for path, count in file_change_counts.most_common(20)
            if count >= 5
        ]

        if commits:
            recent = commits[:10]
            result["recent_changes"] = [
                {
                    "sha": c.hexsha[:8],
                    "message": c.message.strip()[:200],
                    "author": c.author.name,
                    "date": c.committed_datetime.isoformat(),
                }
                for c in recent
            ]

        result["secrets_found"] = self._scan_for_secrets(repo_path)

        return result

    def _scan_for_secrets(self, repo_path: str) -> list[dict]:
        findings = []
        root = Path(repo_path)

        skip_dirs = {".git", "node_modules", "__pycache__", "vendor", ".venv"}
        skip_exts = {".png", ".jpg", ".gif", ".ico", ".woff", ".ttf", ".lock"}

        for file_path in root.rglob("*"):
            if not file_path.is_file():
                continue
            if any(d in file_path.parts for d in skip_dirs):
                continue
            if file_path.suffix.lower() in skip_exts:
                continue
            if file_path.stat().st_size > 500_000:
                continue

            try:
                content = file_path.read_text(encoding="utf-8", errors="ignore")
            except Exception:
                continue

            rel_path = str(file_path.relative_to(root))
            for line_num, line in enumerate(content.splitlines(), 1):
                for pattern, secret_type in SECRET_PATTERNS:
                    if re.search(pattern, line):
                        findings.append({
                            "file": rel_path,
                            "line": line_num,
                            "type": secret_type,
                            "snippet": line.strip()[:100],
                        })
                        break

        logger.info(f"Secret scan found {len(findings)} potential secrets")
        return findings

    def _empty_result(self) -> dict:
        return {
            "secrets_found": [],
            "bus_factor": 0,
            "author_distribution": {},
            "high_churn_files": [],
            "recent_changes": [],
            "commit_count": 0,
            "total_authors": 0,
        }
