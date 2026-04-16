"""Thin wrapper around the GitHub REST API.

Handles URL parsing, pagination via the Link header, and shapes
responses into plain Python lists so the analysis layer doesn't
need to know anything about HTTP.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Iterator, Optional

import requests


GITHUB_API = "https://api.github.com"
DEFAULT_PER_PAGE = 100


@dataclass(frozen=True)
class RepoRef:
    """A parsed owner/name pair from a GitHub URL."""

    owner: str
    name: str

    @property
    def slug(self) -> str:
        return f"{self.owner}/{self.name}"


_URL_PATTERNS = (
    # https://github.com/owner/name(/...|.git|?...|#...)?
    re.compile(r"^https?://(?:www\.)?github\.com/([^/\s]+)/([^/\s?#.]+)"),
    # git@github.com:owner/name.git
    re.compile(r"^git@github\.com:([^/\s]+)/([^/\s.]+)"),
    # owner/name shorthand
    re.compile(r"^([^/\s]+)/([^/\s]+)$"),
)


def parse_repo_url(raw: str) -> Optional[RepoRef]:
    """Best-effort parse of a repo identifier.

    Accepts full GitHub URLs (with or without .git), SSH-style URLs,
    and the ``owner/name`` shorthand. Returns ``None`` if nothing
    matches so callers can show a helpful error.
    """
    raw = (raw or "").strip()
    if not raw:
        return None
    for pattern in _URL_PATTERNS:
        match = pattern.match(raw)
        if match:
            owner, name = match.group(1), match.group(2)
            name = name.removesuffix(".git")
            return RepoRef(owner=owner, name=name)
    return None


class GitHubClient:
    """Authenticated-or-anonymous GitHub REST client."""

    def __init__(self, token: Optional[str] = None, timeout: float = 15.0) -> None:
        self.session = requests.Session()
        self.session.headers.update(
            {
                "Accept": "application/vnd.github+json",
                "X-GitHub-Api-Version": "2022-11-28",
                "User-Agent": "GitPulse/0.1",
            }
        )
        if token:
            self.session.headers["Authorization"] = f"Bearer {token}"
        self.timeout = timeout

    # ---- single-resource endpoints -------------------------------------

    def get_repo(self, ref: RepoRef) -> dict:
        return self._get_json(f"/repos/{ref.slug}")

    def get_languages(self, ref: RepoRef) -> dict[str, int]:
        return self._get_json(f"/repos/{ref.slug}/languages")

    def get_contributors(self, ref: RepoRef, limit: int = 30) -> list[dict]:
        # /contributors is already sorted by contribution count desc.
        return list(self._paginate(f"/repos/{ref.slug}/contributors", limit=limit))

    # ---- paginated endpoints -------------------------------------------

    def get_commits(self, ref: RepoRef, limit: int = 500) -> list[dict]:
        return list(self._paginate(f"/repos/{ref.slug}/commits", limit=limit))

    def get_issues(self, ref: RepoRef, state: str = "all", limit: int = 500) -> list[dict]:
        return list(
            self._paginate(
                f"/repos/{ref.slug}/issues",
                params={"state": state},
                limit=limit,
            )
        )

    # ---- plumbing ------------------------------------------------------

    def _get_json(self, path: str, params: Optional[dict] = None) -> dict:
        resp = self.session.get(
            f"{GITHUB_API}{path}",
            params=params,
            timeout=self.timeout,
        )
        resp.raise_for_status()
        return resp.json()

    def _paginate(
        self,
        path: str,
        params: Optional[dict] = None,
        limit: int = 500,
    ) -> Iterator[dict]:
        """Walk GitHub's page-based pagination.

        Stops when either ``limit`` items have been yielded or the
        server runs out of ``next`` Link-header entries.
        """
        url: Optional[str] = f"{GITHUB_API}{path}"
        merged = {"per_page": DEFAULT_PER_PAGE, **(params or {})}
        seen = 0
        while url and seen < limit:
            resp = self.session.get(url, params=merged, timeout=self.timeout)
            resp.raise_for_status()
            batch = resp.json()
            if not isinstance(batch, list):
                return
            for item in batch:
                yield item
                seen += 1
                if seen >= limit:
                    return
            url = _next_link(resp.headers.get("Link"))
            # After the first request the full next URL already has params.
            merged = {}


_LINK_NEXT = re.compile(r'<([^>]+)>;\s*rel="next"')


def _next_link(header: Optional[str]) -> Optional[str]:
    """Extract the ``rel=next`` URL from a GitHub Link header."""
    if not header:
        return None
    match = _LINK_NEXT.search(header)
    return match.group(1) if match else None
