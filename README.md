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

### Jira & Confluence Cloud authentication

Atlassian Cloud basic auth requires `email` + **API token**, not your account
password. Generate a token at
<https://id.atlassian.com/manage-profile/security/api-tokens> and paste it into
the "API Token" field of the Jira and Confluence cards in the Credentials
panel. Using a regular Atlassian password will fail with HTTP 401, especially
on tenants that enforce 2FA or SAML SSO. See
<https://developer.atlassian.com/cloud/jira/platform/basic-auth-for-rest-apis/>
for details.

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


## Playwright / E2E Timeout Tips

If browser tests are timing out in CI or containerized environments, use this startup pattern:

```bash
# Start app in non-reload mode for deterministic startup
UVICORN_RELOAD=false UVICORN_HOST=0.0.0.0 UVICORN_PORT=8000 python run.py
```

Then have Playwright wait for a stable health endpoint before navigation:

- Base URL: `http://127.0.0.1:8000`
- Health check: `GET /health`
- Avoid using `reload=True` during E2E runs (auto-reload can restart workers mid-test)

Common timeout causes:

- App container not started before tests
- Wrong host/port (for example, `localhost` inside another container namespace)
- No port forwarding from app container to test runner
