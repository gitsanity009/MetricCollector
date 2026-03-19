# MetricCollector

Admin dashboard for pulling metrics from enterprise applications and exporting them to JSON, CSV, or Tableau-ready formats.

## Supported Sources

| Source | Metrics |
|--------|---------|
| **Active Directory** | User/group/computer counts, locked/disabled accounts, recent account creation, BATTS/Linux user counts by AD group membership |
| **vCenter** | VM inventory, host details, datastore capacity/usage, cluster counts |
| **Jira** | Issue counts by status/priority, project listing, recent activity |
| **Confluence** | Space listing, page/blog counts, recently modified content |

## Quick Start

```bash
# 1. Clone and install
pip install -r requirements.txt

# 2. (Optional) Pre-fill default credentials
cp .env.example .env
# Edit .env with your AD, vCenter, Jira, and Confluence credentials

# 3. Run
python run.py
```

Open `http://localhost:8000` in your browser. No login is required — the dashboard loads directly and prompts you to enter your service credentials (vCenter, Jira, Confluence, Active Directory) on first visit.

## API Endpoints

All `/api/metrics/*` endpoints accept service credentials in the POST request body. No authentication token is required.

| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/metrics/sources` | List available metric sources |
| POST | `/api/metrics/{source}` | Fetch metrics as JSON |
| POST | `/api/metrics/{source}/csv` | Export flat CSV |
| POST | `/api/metrics/{source}/tableau` | Export Tableau-optimized CSV (detail rows) |

Query parameters: `?project=KEY` (Jira), `?space=KEY` (Confluence)

## Export Formats

- **JSON** — Full nested data, downloaded from the browser
- **CSV** — Flattened key-value pairs, one row per collection
- **Tableau CSV** — Detail-level rows (e.g., one row per VM or per Jira issue type) with summary metrics repeated, ideal for direct Tableau import

## Architecture

```
app/
  main.py              # FastAPI app, routes, static files
  config.py            # Pydantic settings (.env loader)
  collectors/
    ad_collector.py    # Active Directory via LDAP
    vcenter_collector.py  # vCenter via pyVmomi
    jira_collector.py  # Jira via jira-python
    confluence_collector.py  # Confluence via atlassian-python-api
  routes/
    metrics_routes.py  # Metrics + export endpoints
  templates/           # Jinja2 HTML templates
  static/css/          # Dashboard styles
```
