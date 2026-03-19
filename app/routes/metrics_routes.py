"""API routes for pulling and exporting metrics."""

from __future__ import annotations

import csv
import io
from typing import Any

<<<<<<< HEAD
from fastapi import APIRouter, Query, Response
from pydantic import BaseModel

from app.collectors import ad_collector, vcenter_collector, jira_collector, confluence_collector
from app.config import settings

router = APIRouter(prefix="/api/metrics", tags=["metrics"])

SOURCES = {
    "ad": "Active Directory",
    "vcenter": "vCenter",
    "jira": "Jira",
    "confluence": "Confluence",
=======
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
>>>>>>> main
}


class Credentials(BaseModel):
    # Active Directory
    ad_server: str = ""
    ad_user: str = ""
    ad_password: str = ""
    ad_base_dn: str = ""
    ad_batts_group_cn: str = ""
    ad_unixusers_group_cn: str = ""
    # vCenter
    vcenter_host: str = ""
    vcenter_user: str = ""
    vcenter_password: str = ""
    vcenter_disable_ssl: bool = True
    # Jira
    jira_url: str = ""
    jira_user: str = ""
    jira_password: str = ""
    # Confluence
    confluence_url: str = ""
    confluence_user: str = ""
    confluence_password: str = ""


def _collect(source: str, creds: Credentials, project: str | None = None, space: str | None = None) -> dict[str, Any]:
    """Dispatch to the correct collector with user-supplied credentials."""
    if source == "ad":
        return ad_collector.collect(
            server_url=creds.ad_server or settings.ad_server,
            user=creds.ad_user or settings.ad_user,
            password=creds.ad_password or settings.ad_password,
            base_dn=creds.ad_base_dn or settings.ad_base_dn,
            batts_group_cn=creds.ad_batts_group_cn or settings.ad_batts_group_cn,
            unixusers_group_cn=creds.ad_unixusers_group_cn or settings.ad_unixusers_group_cn,
        )
    elif source == "vcenter":
        return vcenter_collector.collect(
            host=creds.vcenter_host or settings.vcenter_host,
            user=creds.vcenter_user or settings.vcenter_user,
            password=creds.vcenter_password or settings.vcenter_password,
            disable_ssl=creds.vcenter_disable_ssl,
        )
    elif source == "jira":
        return jira_collector.collect(
            url=creds.jira_url or settings.jira_url,
            user=creds.jira_user or settings.jira_user,
            password=creds.jira_password or settings.jira_password,
            project_key=project,
        )
    elif source == "confluence":
        return confluence_collector.collect(
            url=creds.confluence_url or settings.confluence_url,
            user=creds.confluence_user or settings.confluence_user,
            password=creds.confluence_password or settings.confluence_password,
            space_key=space,
        )
    return {}


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
async def list_sources():
    return {"sources": [{"id": k, "label": v} for k, v in SOURCES.items()]}


@router.post("/{source}")
async def get_metrics(
    source: str,
    creds: Credentials,
    project: str | None = Query(None, description="Jira project key"),
    space: str | None = Query(None, description="Confluence space key"),
<<<<<<< HEAD
=======
    x_domain_username: str | None = Header(default=None),
    x_domain_password: str | None = Header(default=None),
    _user: str = Depends(get_current_user),
>>>>>>> main
):
    if source not in SOURCES:
        return Response(status_code=404, content=f"Unknown source: {source}")
<<<<<<< HEAD
    data = _collect(source, creds, project=project, space=space)
    return data


# ---- CSV export ----

@router.post("/{source}/csv")
=======
    return COLLECTORS[source]["fn"](
        project=project,
        space=space,
        username=x_domain_username,
        password=x_domain_password,
    )


@router.get("/{source}/csv")
>>>>>>> main
async def export_csv(
    source: str,
    creds: Credentials,
    project: str | None = Query(None),
    space: str | None = Query(None),
<<<<<<< HEAD
=======
    x_domain_username: str | None = Header(default=None),
    x_domain_password: str | None = Header(default=None),
    _user: str = Depends(get_current_user),
>>>>>>> main
):
    if source not in SOURCES:
        return Response(status_code=404, content=f"Unknown source: {source}")

<<<<<<< HEAD
    data = _collect(source, creds, project=project, space=space)
=======
    data = COLLECTORS[source]["fn"](
        project=project,
        space=space,
        username=x_domain_username,
        password=x_domain_password,
    )
>>>>>>> main
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


<<<<<<< HEAD
# ---- Tableau-friendly export (flat detail rows) ----

@router.post("/{source}/tableau")
=======
@router.get("/{source}/tableau")
>>>>>>> main
async def export_tableau(
    source: str,
    creds: Credentials,
    project: str | None = Query(None),
    space: str | None = Query(None),
<<<<<<< HEAD
):
    """Export detail-level rows as CSV, ideal for Tableau import."""
    if source not in SOURCES:
        return Response(status_code=404, content=f"Unknown source: {source}")

    data = _collect(source, creds, project=project, space=space)
=======
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
>>>>>>> main

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
