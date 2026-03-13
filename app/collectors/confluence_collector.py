"""Confluence metrics collector."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from atlassian import Confluence

from app.config import settings


def _connect(username: str | None = None, password: str | None = None) -> Confluence:
    return Confluence(
        url=settings.confluence_url,
        username=username or settings.confluence_user,
        password=password or settings.confluence_api_token,
        cloud=True,
    )


def collect(space_key: str | None = None, username: str | None = None, password: str | None = None) -> dict[str, Any]:
    """Return Confluence metrics for all spaces or a specific space."""
    metrics: dict[str, Any] = {"source": "confluence", "collected_at": datetime.now(timezone.utc).isoformat()}

    try:
        client = _connect(username=username, password=password)
    except Exception as exc:
        metrics["error"] = f"Confluence authentication failed: {exc}"
        return metrics

    try:
        spaces = client.get_all_spaces(start=0, limit=500, expand="description.plain")
        space_list = spaces.get("results", [])
        metrics["total_spaces"] = len(space_list)
        metrics["spaces"] = [{"key": s["key"], "name": s["name"], "type": s["type"]} for s in space_list]

        space_metrics = []
        target_spaces = [s for s in space_list if s["key"] == space_key] if space_key else space_list
        for space in target_spaces:
            cql = f'space = "{space["key"]}" AND type = page'
            result = client.cql(cql, limit=0)
            page_count = result.get("totalSize", 0)

            cql_blog = f'space = "{space["key"]}" AND type = blogpost'
            blog_result = client.cql(cql_blog, limit=0)
            blog_count = blog_result.get("totalSize", 0)

            space_metrics.append(
                {
                    "space_key": space["key"],
                    "space_name": space["name"],
                    "pages": page_count,
                    "blog_posts": blog_count,
                }
            )
        metrics["space_details"] = space_metrics

        metrics["total_pages"] = sum(s["pages"] for s in space_metrics)
        metrics["total_blog_posts"] = sum(s["blog_posts"] for s in space_metrics)

        cql_recent = 'lastModified >= now("-30d")'
        if space_key:
            cql_recent = f'space = "{space_key}" AND {cql_recent}'
        recent = client.cql(cql_recent, limit=0)
        metrics["content_modified_last_30d"] = recent.get("totalSize", 0)

    except Exception as exc:
        metrics["error"] = str(exc)

    return metrics
