"""Fail-closed model for future customer access via Home Assistant Ingress.

Never trust identity headers from a direct client: only the Supervisor ingress
proxy address is eligible to supply them. Customer access is DISABLED until
all entity-scoped reads/actions can be independently enforced and tested.
"""
from __future__ import annotations
from dataclasses import dataclass
from ipaddress import ip_address
import re

INGRESS_PROXY = "172.30.32.2"
USER_PATTERN = re.compile(r"^[a-f0-9]{32}$", re.IGNORECASE)
ADMIN_GROUP = "system-admin"


@dataclass(frozen=True)
class AccessContext:
    role: str
    user_id: str | None
    verified_ingress: bool
    reason: str


def trusted_source(remote: str | None, *, proxy: str = INGRESS_PROXY) -> bool:
    if not remote:
        return False
    try:
        return ip_address(remote) == ip_address(proxy)
    except ValueError:
        return False


def identity_from_ingress(remote, headers, *, proxy: str = INGRESS_PROXY) -> AccessContext:
    """Supervisor-origin request with an authenticated HA user or deny.

    These headers cannot be accepted from callers reaching the container
    directly. A future customer mode also needs native per-entity policies.
    """
    if not trusted_source(remote, proxy=proxy):
        return AccessContext("denied", None, False, "untrusted_source")
    raw_id = headers.get("X-Remote-User-Id", "")
    groups = headers.get("X-Remote-User-Groups", "")
    if not USER_PATTERN.fullmatch(raw_id):
        return AccessContext("denied", None, True, "user_unverified")
    group_names = {part.strip() for part in groups.split(",") if part.strip()}
    if ADMIN_GROUP in group_names:
        return AccessContext("installer", raw_id, True, "admin_group")
    return AccessContext("denied", raw_id, True, "customer_disabled")


def may_access(ctx: AccessContext, operation: str) -> bool:
    """No client access until a user-scoped HA permissions API exists."""
    return ctx.verified_ingress and ctx.role == "installer" and operation in {
        "read", "control", "installer"
    }


def access_summary(ctx: AccessContext) -> dict:
    """No identifiers or raw request headers are exposed to the frontend."""
    return {
        "role": ctx.role,
        "verified_ingress": ctx.verified_ingress,
        "customer_enabled": False,
        "installer_allowed": may_access(ctx, "installer"),
        "reason": ctx.reason,
    }
