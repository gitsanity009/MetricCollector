"""Active Directory metrics collector using LDAP."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from ldap3 import ALL, Connection, Server
from ldap3.core.exceptions import LDAPException

from app.config import settings


def _connect() -> Connection:
    server = Server(settings.ad_server, get_info=ALL)
    conn = Connection(server, user=settings.ad_user, password=settings.ad_password, auto_bind=True)
    return conn


def collect() -> dict[str, Any]:
    """Return AD metrics: user counts, group counts, locked/disabled accounts, recent changes."""
    conn = _connect()
    base = settings.ad_base_dn
    metrics: dict[str, Any] = {"source": "active_directory", "collected_at": datetime.now(timezone.utc).isoformat()}

    try:
        # Total users
        conn.search(base, "(objectClass=user)", attributes=["sAMAccountName"])
        metrics["total_users"] = len(conn.entries)

        # Enabled users
        conn.search(base, "(&(objectClass=user)(!(userAccountControl:1.2.840.113556.1.4.803:=2)))")
        metrics["enabled_users"] = len(conn.entries)

        # Disabled users
        conn.search(base, "(&(objectClass=user)(userAccountControl:1.2.840.113556.1.4.803:=2))")
        metrics["disabled_users"] = len(conn.entries)

        # Locked-out users
        conn.search(base, "(&(objectClass=user)(lockoutTime>=1))")
        metrics["locked_users"] = len(conn.entries)

        # Groups
        conn.search(base, "(objectClass=group)", attributes=["cn"])
        metrics["total_groups"] = len(conn.entries)

        # Computers
        conn.search(base, "(objectClass=computer)", attributes=["cn"])
        metrics["total_computers"] = len(conn.entries)

        # OUs
        conn.search(base, "(objectClass=organizationalUnit)", attributes=["ou"])
        metrics["total_ous"] = len(conn.entries)

        # Users created in last 30 days
        thirty_days_ago = datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S.0Z")
        conn.search(base, f"(&(objectClass=user)(whenCreated>={thirty_days_ago}))")
        metrics["users_created_last_30d"] = len(conn.entries)

    except LDAPException as exc:
        metrics["error"] = str(exc)
    finally:
        conn.unbind()

    return metrics
