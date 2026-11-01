"""Ingress identity diagnostics and fail-closed customer authorization.

Supervisor provides X-Remote-User-Id (not a trusted HA role/group header).
Only the Supervisor ingress gateway can supply trustworthy identity.
The existing panel_admin=true remains the CURRENT administrator access gate.
No client permission can be inferred from an ingress user ID alone.
"""
from __future__ import annotations
from dataclasses import dataclass
from ipaddress import ip_address
import re

INGRESS_PROXY = "172.30.32.2"
USER_PATTERN = re.compile(r"^[a-f0-9]{32}$", re.IGNORECASE)


@dataclass(frozen=True)
class AccessContext:
    user_id: str | None
    ingress_verified: bool
    reason: str


def trusted_source(remote: str | None, *, proxy: str = INGRESS_PROXY) -> bool:
    if not remote:
        return False
    try:
        return ip_address(remote) == ip_address(proxy)
    except ValueError:
        return False


def identity_from_ingress(remote, headers, *, proxy: str = INGRESS_PROXY) -> AccessContext:
    if not trusted_source(remote, proxy=proxy):
        return AccessContext(None, False, "untrusted_source")
    raw_id = headers.get("X-Remote-User-Id", "")
    if not isinstance(raw_id, str) or not USER_PATTERN.fullmatch(raw_id):
        return AccessContext(None, False, "user_unverified")
    return AccessContext(raw_id, True, "ingress_authenticated")


def may_access_customer(ctx: AccessContext, entity_id: str, action: str) -> bool:
    """Until per-user HA permission checks exist, all customer data/control denied."""
    return False


def access_summary(ctx: AccessContext) -> dict:
    # Do not return user IDs, cookies, group information or remote address.
    return {
        "ingress_verified": ctx.ingress_verified,
        "identity_available": ctx.user_id is not None,
        "customer_enabled": False,
        "role": "admin_panel_only" if ctx.ingress_verified else "unverified",
        "role_verification": "not_available",
        "reason": ctx.reason,
    }
