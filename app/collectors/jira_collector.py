"""Jira metrics collector."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from jira import JIRA

from app.config import settings


def _connect(username: str | None = None, password: str | None = None) -> JIRA:
    return JIRA(
        server=settings.jira_url,
        basic_auth=(username or settings.jira_user, password or settings.jira_api_token),
    )


def collect(project_key: str | None = None, username: str | None = None, password: str | None = None) -> dict[str, Any]:
    """Return Jira metrics for all projects or a specific project."""
    metrics: dict[str, Any] = {"source": "jira", "collected_at": datetime.now(timezone.utc).isoformat()}

    try:
        client = _connect(username=username, password=password)
    except Exception as exc:
        metrics["error"] = f"Jira authentication failed: {exc}"
        return metrics

    try:
        projects = client.projects()
        metrics["total_projects"] = len(projects)
        metrics["projects"] = [{"key": p.key, "name": p.name} for p in projects]

        scope = f"project = {project_key}" if project_key else ""

        for status_name in ["To Do", "In Progress", "Done"]:
            jql = f'statusCategory = "{status_name}"'
            if scope:
                jql = f"{scope} AND {jql}"
            metrics[f"issues_{status_name.lower().replace(' ', '_')}"] = client.search_issues(jql, maxResults=0).total

        jql = scope if scope else "order by created DESC"
        metrics["total_issues"] = client.search_issues(jql if scope else jql, maxResults=0).total

        recent_jql = "created >= -30d"
        if scope:
            recent_jql = f"{scope} AND {recent_jql}"
        metrics["issues_created_last_30d"] = client.search_issues(recent_jql, maxResults=0).total

        resolved_jql = "resolved >= -30d"
        if scope:
            resolved_jql = f"{scope} AND {resolved_jql}"
        metrics["issues_resolved_last_30d"] = client.search_issues(resolved_jql, maxResults=0).total

        priority_metrics = []
        for priority in ["Highest", "High", "Medium", "Low", "Lowest"]:
            pjql = f"priority = {priority} AND resolution = Unresolved"
            if scope:
                pjql = f"{scope} AND {pjql}"
            count = client.search_issues(pjql, maxResults=0).total
            priority_metrics.append({"priority": priority, "count": count})
        metrics["unresolved_by_priority"] = priority_metrics

        type_jql = scope if scope else "created is not EMPTY"
        issues_sample = client.search_issues(type_jql, maxResults=100, fields="issuetype,assignee")
        type_counts: dict[str, int] = {}
        for issue in issues_sample:
            itype = issue.fields.issuetype.name
            type_counts[itype] = type_counts.get(itype, 0) + 1
        metrics["issue_types_sample"] = [{"type": k, "count": v} for k, v in type_counts.items()]

    except Exception as exc:
        metrics["error"] = str(exc)

    return metrics
