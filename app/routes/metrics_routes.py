"""API routes for pulling and exporting metrics."""

from __future__ import annotations

import csv
import io
from typing import Any

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
    # Jira Cloud — requires an Atlassian API token, not an account password
    jira_url: str = ""
    jira_user: str = ""
    jira_api_token: str = ""
    # Confluence Cloud — requires an Atlassian API token, not an account password
    confluence_url: str = ""
    confluence_user: str = ""
    confluence_api_token: str = ""


def _require_credentials(source: str, creds: Credentials) -> str | None:
    """Return an error message when required credentials are missing."""
    requirements = {
        "ad": [
            ("ad_server", creds.ad_server),
            ("ad_user", creds.ad_user),
            ("ad_password", creds.ad_password),
            ("ad_base_dn", creds.ad_base_dn),
        ],
        "vcenter": [
            ("vcenter_host", creds.vcenter_host),
            ("vcenter_user", creds.vcenter_user),
            ("vcenter_password", creds.vcenter_password),
        ],
        "jira": [
            ("jira_url", creds.jira_url),
            ("jira_user", creds.jira_user),
            ("jira_api_token", creds.jira_api_token),
        ],
        "confluence": [
            ("confluence_url", creds.confluence_url),
            ("confluence_user", creds.confluence_user),
            ("confluence_api_token", creds.confluence_api_token),
        ],
    }
    missing = [name for name, value in requirements.get(source, []) if not value]
    if missing:
        return f"Missing required credentials: {', '.join(missing)}"
    return None


def _collect(source: str, creds: Credentials, project: str | None = None, space: str | None = None) -> dict[str, Any]:
    """Dispatch to the correct collector with request-supplied credentials only."""
    if source == "ad":
        return ad_collector.collect(
            server_url=creds.ad_server,
            user=creds.ad_user,
            password=creds.ad_password,
            base_dn=creds.ad_base_dn,
            batts_group_cn=creds.ad_batts_group_cn or settings.ad_batts_group_cn,
            unixusers_group_cn=creds.ad_unixusers_group_cn or settings.ad_unixusers_group_cn,
        )
    elif source == "vcenter":
        return vcenter_collector.collect(
            host=creds.vcenter_host,
            user=creds.vcenter_user,
            password=creds.vcenter_password,
            disable_ssl=creds.vcenter_disable_ssl,
        )
    elif source == "jira":
        return jira_collector.collect(
            url=creds.jira_url,
            user=creds.jira_user,
            api_token=creds.jira_api_token,
            project_key=project,
        )
    elif source == "confluence":
        return confluence_collector.collect(
            url=creds.confluence_url,
            user=creds.confluence_user,
            api_token=creds.confluence_api_token,
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
):
    if source not in SOURCES:
        return Response(status_code=404, content=f"Unknown source: {source}")
    missing_creds_error = _require_credentials(source, creds)
    if missing_creds_error:
        return Response(status_code=400, content=missing_creds_error)
    data = _collect(source, creds, project=project, space=space)
    return data


# ---- CSV export ----

@router.post("/{source}/csv")
async def export_csv(
    source: str,
    creds: Credentials,
    project: str | None = Query(None),
    space: str | None = Query(None),
):
    if source not in SOURCES:
        return Response(status_code=404, content=f"Unknown source: {source}")
    missing_creds_error = _require_credentials(source, creds)
    if missing_creds_error:
        return Response(status_code=400, content=missing_creds_error)

    data = _collect(source, creds, project=project, space=space)
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


# ---- Tableau-friendly export (flat detail rows) ----

@router.post("/{source}/tableau")
async def export_tableau(
    source: str,
    creds: Credentials,
    project: str | None = Query(None),
    space: str | None = Query(None),
):
    """Export detail-level rows as CSV, ideal for Tableau import."""
    if source not in SOURCES:
        return Response(status_code=404, content=f"Unknown source: {source}")
    missing_creds_error = _require_credentials(source, creds)
    if missing_creds_error:
        return Response(status_code=400, content=missing_creds_error)

    data = _collect(source, creds, project=project, space=space)

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
