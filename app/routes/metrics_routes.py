"""API routes for pulling and exporting metrics."""

from __future__ import annotations

import csv
import io
from typing import Any

from fastapi import APIRouter, Depends, Header, Query, Response

from app.auth import get_current_user
from app.collectors import ad_collector, confluence_collector, jira_collector, vcenter_collector

router = APIRouter(prefix="/api/metrics", tags=["metrics"])

COLLECTORS = {
    "ad": {
        "fn": lambda **kw: ad_collector.collect(bind_user=kw.get("username"), bind_password=kw.get("password")),
        "label": "Active Directory",
    },
    "vcenter": {
        "fn": lambda **kw: vcenter_collector.collect(username=kw.get("username"), password=kw.get("password")),
        "label": "vCenter",
    },
    "jira": {
        "fn": lambda **kw: jira_collector.collect(
            project_key=kw.get("project"),
            username=kw.get("username"),
            password=kw.get("password"),
        ),
        "label": "Jira",
    },
    "confluence": {
        "fn": lambda **kw: confluence_collector.collect(
            space_key=kw.get("space"),
            username=kw.get("username"),
            password=kw.get("password"),
        ),
        "label": "Confluence",
    },
}


def _flatten(data: dict, parent_key: str = "", sep: str = ".") -> dict[str, Any]:
    """Flatten nested dicts/lists into dot-separated keys for CSV export."""
    items: list[tuple[str, Any]] = []
    for k, v in data.items():
        new_key = f"{parent_key}{sep}{k}" if parent_key else k
        if isinstance(v, dict):
            items.extend(_flatten(v, new_key, sep).items())
        elif isinstance(v, list):
            if v and isinstance(v[0], dict):
                for i, item in enumerate(v):
                    items.extend(_flatten(item, f"{new_key}[{i}]", sep).items())
            else:
                items.append((new_key, "; ".join(str(x) for x in v)))
        else:
            items.append((new_key, v))
    return dict(items)


@router.get("/sources")
async def list_sources(_user: str = Depends(get_current_user)):
    return {"sources": [{"id": k, "label": v["label"]} for k, v in COLLECTORS.items()]}


@router.get("/{source}")
async def get_metrics(
    source: str,
    project: str | None = Query(None, description="Jira project key"),
    space: str | None = Query(None, description="Confluence space key"),
    x_domain_username: str | None = Header(default=None),
    x_domain_password: str | None = Header(default=None),
    _user: str = Depends(get_current_user),
):
    if source not in COLLECTORS:
        return Response(status_code=404, content=f"Unknown source: {source}")
    return COLLECTORS[source]["fn"](
        project=project,
        space=space,
        username=x_domain_username,
        password=x_domain_password,
    )


@router.get("/{source}/csv")
async def export_csv(
    source: str,
    project: str | None = Query(None),
    space: str | None = Query(None),
    x_domain_username: str | None = Header(default=None),
    x_domain_password: str | None = Header(default=None),
    _user: str = Depends(get_current_user),
):
    if source not in COLLECTORS:
        return Response(status_code=404, content=f"Unknown source: {source}")

    data = COLLECTORS[source]["fn"](
        project=project,
        space=space,
        username=x_domain_username,
        password=x_domain_password,
    )
    flat = _flatten(data)

    buf = io.StringIO()
    writer = csv.DictWriter(buf, fieldnames=flat.keys())
    writer.writeheader()
    writer.writerow(flat)

    return Response(
        content=buf.getvalue(),
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename={source}_metrics.csv"},
    )


@router.get("/{source}/tableau")
async def export_tableau(
    source: str,
    project: str | None = Query(None),
    space: str | None = Query(None),
    x_domain_username: str | None = Header(default=None),
    x_domain_password: str | None = Header(default=None),
    _user: str = Depends(get_current_user),
):
    """Export detail-level rows as CSV, ideal for Tableau import."""
    if source not in COLLECTORS:
        return Response(status_code=404, content=f"Unknown source: {source}")

    data = COLLECTORS[source]["fn"](
        project=project,
        space=space,
        username=x_domain_username,
        password=x_domain_password,
    )

    detail_keys = [k for k, v in data.items() if isinstance(v, list) and v and isinstance(v[0], dict)]
    summary = {k: v for k, v in data.items() if not isinstance(v, (list, dict))}

    rows: list[dict] = []
    if detail_keys:
        primary = detail_keys[0]
        for item in data[primary]:
            row = {**summary, "detail_type": primary}
            row.update(item)
            rows.append(row)
    else:
        rows.append(summary)

    if not rows:
        return Response(content="No data", status_code=204)

    buf = io.StringIO()
    writer = csv.DictWriter(buf, fieldnames=list(rows[0].keys()), extrasaction="ignore")
    writer.writeheader()
    writer.writerows(rows)

    return Response(
        content=buf.getvalue(),
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename={source}_tableau.csv"},
    )
