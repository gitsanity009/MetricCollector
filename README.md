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

# 2. Configure credentials
cp .env.example .env
# Edit .env with connection details and app login credentials
# Service credentials in `.env` are optional fallback values; admins can enter one domain credential set in the UI for AD, vCenter, Jira, and Confluence collection

# 3. Run
python run.py
```

Open `http://localhost:8000` in your browser. Log in with the app admin account from `.env` (default: `admin` / `changeme123`).

When collecting metrics, enter domain credentials once in the dashboard. The same credentials are used for **Active Directory**, **vCenter**, **Jira**, and **Confluence** requests instead of requiring service credentials in `.env`.

## API Endpoints

All `/api/metrics/*` endpoints require a Bearer token obtained from login.

| Method | Path | Description |
|--------|------|-------------|
| POST | `/api/auth/login` | Get JWT token (OAuth2 password flow) |
| GET | `/api/metrics/sources` | List available metric sources |
| GET | `/api/metrics/{source}` | Fetch metrics as JSON |
| GET | `/api/metrics/{source}/csv` | Export flat CSV |
| GET | `/api/metrics/{source}/tableau` | Export Tableau-optimized CSV (detail rows) |

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
  auth.py              # JWT authentication
  collectors/
    ad_collector.py    # Active Directory via LDAP
    vcenter_collector.py  # vCenter via pyVmomi
    jira_collector.py  # Jira via jira-python
    confluence_collector.py  # Confluence via atlassian-python-api
  routes/
    auth_routes.py     # Login endpoint
    metrics_routes.py  # Metrics + export endpoints
  templates/           # Jinja2 HTML templates
  static/css/          # Dashboard styles
```
