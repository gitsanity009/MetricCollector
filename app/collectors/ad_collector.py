"""Active Directory metrics collector using LDAP."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from ldap3 import ALL, BASE, Connection, Server
from ldap3.core.exceptions import LDAPException
from ldap3.utils.conv import escape_filter_chars

from app.config import settings


def _connect(bind_user: str | None = None, bind_password: str | None = None) -> Connection:
    server = Server(settings.ad_server, get_info=ALL)
    user = bind_user or settings.ad_user
    password = bind_password or settings.ad_password
    conn = Connection(server, user=user, password=password, auto_bind=True)
    return conn


def validate_credentials(username: str, password: str) -> bool:
    """Validate user-provided domain credentials by attempting LDAP bind."""
    try:
        conn = _connect(bind_user=username, bind_password=password)
        conn.unbind()
        return True
    except LDAPException:
        return False


def _count_users_in_group(conn: Connection, base_dn: str, group_cn: str) -> int:
    """Count direct user members of an AD group by CN.

    Returns 0 when the group does not exist or has no members.
    """
    group_filter = f"(&(objectClass=group)(cn={escape_filter_chars(group_cn)}))"
    conn.search(base_dn, group_filter, attributes=["member"])
    if not conn.entries:
        return 0

    members = conn.entries[0].member.values if "member" in conn.entries[0] else []
    if not members:
        return 0

    count = 0
    for member_dn in members:
        conn.search(member_dn, "(objectClass=user)", search_scope=BASE, attributes=["distinguishedName"])
        if conn.entries:
            count += 1
    return count


def collect(bind_user: str | None = None, bind_password: str | None = None) -> dict[str, Any]:
    """Return AD metrics: user counts, group counts, locked/disabled accounts, recent changes."""
    metrics: dict[str, Any] = {"source": "active_directory", "collected_at": datetime.now(timezone.utc).isoformat()}

    try:
        conn = _connect(bind_user=bind_user, bind_password=bind_password)
    except LDAPException as exc:
        metrics["error"] = f"AD bind failed: {exc}"
        return metrics

    base = settings.ad_base_dn

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

        # Platform/group-specific user counts
        metrics["batts_users"] = _count_users_in_group(conn, base, settings.ad_batts_group_cn)
        metrics["linux_users"] = _count_users_in_group(conn, base, settings.ad_unixusers_group_cn)

    except LDAPException as exc:
        metrics["error"] = str(exc)
    finally:
        conn.unbind()

    return metrics
