"""
GitHub integration logic — pure functions, no route decorators.

Uses httpx async client for REST API calls.
"""

from __future__ import annotations

from typing import Any

import httpx
from fastapi import HTTPException

from .models import _get_config_key


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

GITHUB_API_BASE = "https://api.github.com"


# ---------------------------------------------------------------------------
# Auth helper
# ---------------------------------------------------------------------------

async def get_github_headers() -> dict[str, str]:
    """Returnează header-ele de autorizare pentru GitHub API."""
    token = await _get_config_key("github_token")
    if not token:
        raise HTTPException(400, "GitHub nu este configurat. Adaugă github_token în Setări AI.")
    return {
        "Authorization": f"Bearer {token}",
        "Accept": "application/vnd.github.v3+json",
    }


# ---------------------------------------------------------------------------
# Logic functions
# ---------------------------------------------------------------------------

async def check_github_status() -> dict:
    """Verifică dacă token-ul GitHub e valid, returnează status dict."""
    token = await _get_config_key("github_token")
    configured = bool(token)

    if configured:
        try:
            async with httpx.AsyncClient(timeout=10) as client:
                resp = await client.get(
                    f"{GITHUB_API_BASE}/user",
                    headers={
                        "Authorization": f"Bearer {token}",
                        "Accept": "application/vnd.github.v3+json",
                    },
                )
                if resp.status_code == 200:
                    user = resp.json()
                    return {
                        "provider": "github",
                        "configured": True,
                        "connected": True,
                        "user": user.get("login", ""),
                        "name": user.get("name", ""),
                        "repos": user.get("public_repos", 0),
                        "message": "GitHub conectat.",
                    }
                else:
                    return {
                        "provider": "github",
                        "configured": True,
                        "connected": False,
                        "message": "Token GitHub invalid sau expirat.",
                    }
        except Exception:
            return {
                "provider": "github",
                "configured": True,
                "connected": False,
                "message": "Nu s-a putut verifica conexiunea GitHub.",
            }

    return {
        "provider": "github",
        "configured": False,
        "connected": False,
        "message": "Lipsește github_token din Setări AI.",
    }


async def list_github_repos(headers: dict[str, str], max_results: int) -> list[dict]:
    """Listează repo-urile utilizatorului GitHub."""
    async with httpx.AsyncClient(timeout=15) as client:
        resp = await client.get(
            f"{GITHUB_API_BASE}/user/repos",
            headers=headers,
            params={
                "sort": "updated",
                "direction": "desc",
                "per_page": max_results,
            },
        )

    if resp.status_code == 401:
        raise HTTPException(401, "Token GitHub invalid.")
    if resp.status_code != 200:
        raise HTTPException(resp.status_code, f"Eroare GitHub API: {resp.text}")

    repos = []
    for repo in resp.json():
        repos.append({
            "id": repo.get("id"),
            "name": repo.get("name"),
            "full_name": repo.get("full_name"),
            "description": repo.get("description", ""),
            "private": repo.get("private", False),
            "language": repo.get("language", ""),
            "stars": repo.get("stargazers_count", 0),
            "updated_at": repo.get("updated_at", ""),
            "html_url": repo.get("html_url", ""),
        })

    return repos


async def list_github_commits(
    headers: dict[str, str],
    owner: str,
    repo: str,
    max_results: int,
    branch: str,
) -> list[dict]:
    """Listează ultimele commit-uri dintr-un repo GitHub."""
    async with httpx.AsyncClient(timeout=15) as client:
        resp = await client.get(
            f"{GITHUB_API_BASE}/repos/{owner}/{repo}/commits",
            headers=headers,
            params={"per_page": max_results, "sha": branch},
        )

    if resp.status_code == 401:
        raise HTTPException(401, "Token GitHub invalid.")
    if resp.status_code == 404:
        raise HTTPException(404, f"Repo {owner}/{repo} negăsit.")
    if resp.status_code == 409:
        raise HTTPException(404, f"Branch-ul '{branch}' nu există în {owner}/{repo}.")
    if resp.status_code != 200:
        raise HTTPException(resp.status_code, f"Eroare GitHub API: {resp.text}")

    commits = []
    for c in resp.json():
        commit_info = c.get("commit", {})
        author_info = commit_info.get("author", {})
        commits.append({
            "sha": c.get("sha", "")[:8],
            "message": commit_info.get("message", ""),
            "author": author_info.get("name", ""),
            "date": author_info.get("date", ""),
            "html_url": c.get("html_url", ""),
        })

    return commits


async def create_github_issue(
    headers: dict[str, str],
    owner: str,
    repo: str,
    title: str,
    body: str,
    labels: list[str],
) -> dict:
    """Creează un issue nou într-un repo GitHub. Returns created issue dict."""
    issue_body: dict[str, Any] = {
        "title": title,
        "body": body,
    }
    if labels:
        issue_body["labels"] = labels

    async with httpx.AsyncClient(timeout=15) as client:
        resp = await client.post(
            f"{GITHUB_API_BASE}/repos/{owner}/{repo}/issues",
            headers={**headers, "Content-Type": "application/json"},
            json=issue_body,
        )

    if resp.status_code == 401:
        raise HTTPException(401, "Token GitHub invalid.")
    if resp.status_code == 404:
        raise HTTPException(404, f"Repo {owner}/{repo} negăsit.")
    if resp.status_code not in (200, 201):
        raise HTTPException(resp.status_code, f"Eroare creare issue: {resp.text}")

    return resp.json()
