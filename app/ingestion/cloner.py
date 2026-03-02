import logging
import os
import shutil
import uuid
from pathlib import Path

from git import Repo
from git.exc import GitCommandError

from app.config import settings

logger = logging.getLogger(__name__)


class RepoCloner:
    """Clones git repositories for audit ingestion."""

    def __init__(self, storage_path: str | None = None):
        self.storage_path = Path(storage_path or settings.repo_storage_path)
        self.storage_path.mkdir(parents=True, exist_ok=True)

    async def clone(
        self,
        repo_url: str,
        branch: str | None = None,
        access_token: str | None = None,
        audit_id: str | None = None,
    ) -> dict:
        clone_dir = self.storage_path / (audit_id or str(uuid.uuid4()))
        if clone_dir.exists():
            shutil.rmtree(clone_dir)

        auth_url = self._inject_token(repo_url, access_token)

        clone_args = {
            "depth": 1,
            "single_branch": True,
        }
        if branch:
            clone_args["branch"] = branch

        logger.info(f"Cloning {repo_url} (branch={branch}) to {clone_dir}")
        try:
            repo = Repo.clone_from(auth_url, str(clone_dir), **clone_args)
        except GitCommandError as e:
            logger.error(f"Git clone failed: {e}")
            raise RuntimeError(f"Failed to clone repository: {e.stderr or str(e)}")

        commit_sha = repo.head.commit.hexsha
        actual_branch = str(repo.active_branch) if not repo.head.is_detached else branch or "HEAD"

        repo_size_mb = self._dir_size_mb(clone_dir)
        if repo_size_mb > settings.max_repo_size_mb:
            shutil.rmtree(clone_dir)
            raise RuntimeError(
                f"Repository too large: {repo_size_mb:.1f}MB "
                f"(max {settings.max_repo_size_mb}MB)"
            )

        logger.info(
            f"Cloned successfully: sha={commit_sha[:8]} "
            f"branch={actual_branch} size={repo_size_mb:.1f}MB"
        )

        return {
            "local_path": str(clone_dir),
            "commit_sha": commit_sha,
            "branch": actual_branch,
            "size_mb": repo_size_mb,
        }

    def cleanup(self, local_path: str) -> None:
        path = Path(local_path)
        if path.exists():
            shutil.rmtree(path)
            logger.info(f"Cleaned up repo at {local_path}")

    def _inject_token(self, repo_url: str, token: str | None) -> str:
        if not token:
            return repo_url
        if "github.com" in repo_url:
            return repo_url.replace(
                "https://github.com",
                f"https://{token}@github.com",
            )
        if "gitlab.com" in repo_url:
            return repo_url.replace(
                "https://gitlab.com",
                f"https://oauth2:{token}@gitlab.com",
            )
        return repo_url

    def _dir_size_mb(self, path: Path) -> float:
        total = sum(f.stat().st_size for f in path.rglob("*") if f.is_file())
        return total / (1024 * 1024)
