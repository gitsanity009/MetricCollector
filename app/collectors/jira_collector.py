"""Jira metrics collector."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from jira import JIRA


def _connect(url: str, user: str, api_token: str) -> JIRA:
    return JIRA(
        server=url,
        basic_auth=(user, api_token),
    )


def collect(url: str, user: str, api_token: str, project_key: str | None = None) -> dict[str, Any]:
    """Return Jira metrics for all projects or a specific project."""
    client = _connect(url, user, api_token)
    metrics: dict[str, Any] = {"source": "jira", "collected_at": datetime.now(timezone.utc).isoformat()}

    try:
        projects = client.projects()
        metrics["total_projects"] = len(projects)
        metrics["projects"] = [{"key": p.key, "name": p.name} for p in projects]

        # If a specific project is requested, scope queries to it
        scope = f"project = {project_key}" if project_key else ""

        # Issue counts by status category
        for status_name in ["To Do", "In Progress", "Done"]:
            jql = f'statusCategory = "{status_name}"'
            if scope:
                jql = f"{scope} AND {jql}"
            metrics[f"issues_{status_name.lower().replace(' ', '_')}"] = client.search_issues(jql, maxResults=0).total

        # Total issues
        jql = scope if scope else "order by created DESC"
        metrics["total_issues"] = client.search_issues(jql if scope else jql, maxResults=0).total

        # Issues created last 30 days
        recent_jql = 'created >= -30d'
        if scope:
            recent_jql = f"{scope} AND {recent_jql}"
        metrics["issues_created_last_30d"] = client.search_issues(recent_jql, maxResults=0).total

        # Issues resolved last 30 days
        resolved_jql = 'resolved >= -30d'
        if scope:
            resolved_jql = f"{scope} AND {resolved_jql}"
        metrics["issues_resolved_last_30d"] = client.search_issues(resolved_jql, maxResults=0).total

        # Unresolved by priority
        priority_metrics = []
        for priority in ["Highest", "High", "Medium", "Low", "Lowest"]:
            pjql = f'priority = {priority} AND resolution = Unresolved'
            if scope:
                pjql = f"{scope} AND {pjql}"
            count = client.search_issues(pjql, maxResults=0).total
            priority_metrics.append({"priority": priority, "count": count})
        metrics["unresolved_by_priority"] = priority_metrics

        # Issue types breakdown
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
