import hashlib
import hmac
import logging

from fastapi import APIRouter, Header, HTTPException, Request, status

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post("/github")
async def github_webhook(
    request: Request,
    x_hub_signature_256: str | None = Header(None),
    x_github_event: str | None = Header(None),
):
    """Receive GitHub push events to trigger auto-audits on configured repos."""
    body = await request.body()

    payload = await request.json()
    event = x_github_event or "unknown"

    if event == "push":
        repo_url = payload.get("repository", {}).get("html_url", "")
        branch_ref = payload.get("ref", "")
        branch = branch_ref.replace("refs/heads/", "")
        commit_sha = payload.get("after", "")

        logger.info(
            f"GitHub push webhook: repo={repo_url} branch={branch} sha={commit_sha}"
        )

        return {
            "status": "received",
            "event": event,
            "repo": repo_url,
            "branch": branch,
            "message": "Auto-audit webhook support is configured. "
                       "Set up webhook-to-audit mapping via tenant settings.",
        }
    elif event == "ping":
        return {"status": "pong"}
    else:
        return {"status": "ignored", "event": event}
