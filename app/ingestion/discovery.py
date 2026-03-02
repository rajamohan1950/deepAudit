import logging
import os
from pathlib import Path

logger = logging.getLogger(__name__)

DEFAULT_IGNORE = {
    ".git",
    "node_modules",
    "__pycache__",
    ".pytest_cache",
    ".mypy_cache",
    ".ruff_cache",
    "vendor",
    "dist",
    "build",
    ".next",
    ".nuxt",
    "target",
    "bin",
    "obj",
    ".venv",
    "venv",
    "env",
    ".tox",
    ".eggs",
    "*.egg-info",
    ".terraform",
    ".gradle",
}

BINARY_EXTENSIONS = {
    ".png", ".jpg", ".jpeg", ".gif", ".ico", ".svg", ".bmp", ".webp",
    ".mp3", ".mp4", ".wav", ".avi", ".mov", ".mkv",
    ".zip", ".tar", ".gz", ".bz2", ".rar", ".7z",
    ".exe", ".dll", ".so", ".dylib", ".o", ".a",
    ".woff", ".woff2", ".ttf", ".eot", ".otf",
    ".pyc", ".pyo", ".class", ".jar",
    ".db", ".sqlite", ".sqlite3",
    ".pdf", ".doc", ".docx", ".xls", ".xlsx",
}

MAX_FILE_SIZE_BYTES = 1_000_000  # 1MB


class FileDiscovery:
    """Recursively discover and filter files in a cloned repository."""

    def __init__(
        self,
        paths_include: list[str] | None = None,
        paths_exclude: list[str] | None = None,
    ):
        self.paths_include = paths_include or []
        self.paths_exclude = set(paths_exclude or [])
        self.ignore_dirs = DEFAULT_IGNORE | self.paths_exclude

    def discover(self, repo_path: str) -> list[dict]:
        root = Path(repo_path)
        if not root.exists():
            raise FileNotFoundError(f"Repo path not found: {repo_path}")

        files = []
        for file_path in root.rglob("*"):
            if not file_path.is_file():
                continue

            rel_path = str(file_path.relative_to(root))

            if self._should_skip(rel_path, file_path):
                continue

            if self.paths_include:
                if not any(rel_path.startswith(p) for p in self.paths_include):
                    continue

            try:
                size = file_path.stat().st_size
            except OSError:
                continue

            if size > MAX_FILE_SIZE_BYTES:
                logger.debug(f"Skipping large file: {rel_path} ({size} bytes)")
                continue

            files.append({
                "path": rel_path,
                "absolute_path": str(file_path),
                "size_bytes": size,
                "extension": file_path.suffix.lower(),
            })

        logger.info(f"Discovered {len(files)} files in {repo_path}")
        return files

    def _should_skip(self, rel_path: str, file_path: Path) -> bool:
        parts = Path(rel_path).parts
        for part in parts:
            if part in self.ignore_dirs:
                return True

        ext = file_path.suffix.lower()
        if ext in BINARY_EXTENSIONS:
            return True

        if file_path.name.startswith(".") and file_path.name not in (
            ".env", ".env.example", ".gitignore", ".dockerignore",
            ".eslintrc", ".prettierrc", ".editorconfig",
            ".gitlab-ci.yml", ".travis.yml",
        ):
            return True

        return False
