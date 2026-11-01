from __future__ import annotations

import json
import re
from urllib.error import HTTPError, URLError
from urllib.parse import quote
from urllib.request import Request, urlopen

from .models import WorkItem


REPO_PATTERN = re.compile(r"^[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+$")


class GitHubError(RuntimeError):
    """An API or repository input error safe to show in a CLI message."""


def validate_repo(repo: str) -> tuple[str, str]:
    if not REPO_PATTERN.fullmatch(repo):
        raise GitHubError("Repository must use the owner/name format, for example octo-org/example.")
    owner, name = repo.split("/", 1)
    return owner, name


def fetch_open_items(repo: str, token: str | None = None) -> list[WorkItem]:
    owner, name = validate_repo(repo)
    encoded_owner = quote(owner, safe="")
    encoded_name = quote(name, safe="")
    items: list[WorkItem] = []
    page = 1

    while True:
        url = (
            f"https://api.github.com/repos/{encoded_owner}/{encoded_name}/issues"
            f"?state=open&sort=updated&direction=asc&per_page=100&page={page}"
        )
        headers = {
            "Accept": "application/vnd.github+json",
            "User-Agent": "repo-triage-kit/0.1.0b1",
            "X-GitHub-Api-Version": "2022-11-28",
        }
        if token:
            headers["Authorization"] = f"Bearer {token}"
        request = Request(url, headers=headers)
        try:
            with urlopen(request, timeout=20) as response:
                payload = json.loads(response.read().decode("utf-8"))
        except HTTPError as error:
            if error.code == 404:
                raise GitHubError("Repository was not found or is not readable with the supplied token.") from error
            if error.code == 401 or error.code == 403:
                raise GitHubError("GitHub rejected the request. Check the token and its read access to issues and pull requests.") from error
            raise GitHubError(f"GitHub returned HTTP {error.code} while reading the repository.") from error
        except (TimeoutError, URLError, json.JSONDecodeError) as error:
            raise GitHubError(f"Could not read GitHub data: {error}") from error

        if not isinstance(payload, list):
            raise GitHubError("GitHub returned an unexpected response while listing issues.")
        items.extend(WorkItem.from_github(record) for record in payload if isinstance(record, dict))
        if len(payload) < 100:
            break
        page += 1
    return items
