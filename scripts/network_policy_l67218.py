from __future__ import annotations

"""Standalone NetworkPolicy for DataUp and release scripts."""

import hashlib
import os
import ssl
import urllib.parse
import urllib.request
from typing import Any


class NetworkPolicyError(RuntimeError):
    pass


def _url(req_or_url: Any) -> str:
    return str(getattr(req_or_url, "full_url", req_or_url) or "")


def _host(url: str) -> str:
    return (urllib.parse.urlparse(str(url or "")).hostname or "").lower()


def validate_url(url: str, *, allow_loopback_http: bool = False, purpose: str = "dataup") -> None:
    parsed = urllib.parse.urlparse(str(url or ""))
    scheme = (parsed.scheme or "").lower()
    host = (parsed.hostname or "").lower()
    if not scheme or not host:
        raise NetworkPolicyError(f"{purpose}: invalid URL")
    if scheme == "http" and allow_loopback_http and host in {"localhost", "127.0.0.1", "::1"}:
        return
    if scheme != "https":
        raise NetworkPolicyError(f"{purpose}: remote URL must use HTTPS")


def _context() -> ssl.SSLContext:
    cafile = os.environ.get("LINYUANZHE_CA_BUNDLE", "").strip() or None
    return ssl.create_default_context(cafile=cafile)


def _pin_for_host(host: str) -> str:
    raw = os.environ.get("LINYUANZHE_TLS_CERT_SHA256", "").strip()
    if not raw:
        return ""
    for item in [x.strip() for x in raw.split(",") if x.strip()]:
        if "=" in item:
            key, val = item.split("=", 1)
            if key.strip().lower() == host:
                return val.strip().lower().replace(":", "")
        else:
            return item.lower().replace(":", "")
    return ""


def _peer_cert_digest(response: Any) -> str:
    fp = getattr(response, "fp", None)
    raw = getattr(fp, "raw", None) if fp is not None else None
    sock = getattr(raw, "_sock", None) if raw is not None else None
    getpeercert = getattr(sock, "getpeercert", None)
    if callable(getpeercert):
        try:
            cert = getpeercert(binary_form=True)
            if cert:
                return hashlib.sha256(cert).hexdigest()
        except Exception:
            return ""
    return ""


def _verify_pin(response: Any, url: str) -> None:
    host = _host(url)
    expected = _pin_for_host(host)
    if not expected:
        return
    actual = _peer_cert_digest(response)
    if not actual:
        response.close()
        raise NetworkPolicyError(f"tls pinning requested for {host}, but peer certificate is unavailable")
    if actual.lower() != expected.lower():
        response.close()
        raise NetworkPolicyError(f"tls certificate pin mismatch for {host}")


def urlopen_with_policy(req_or_url: Any, *, timeout: float, allow_loopback_http: bool = False, purpose: str = "dataup") -> Any:
    url = _url(req_or_url)
    validate_url(url, allow_loopback_http=allow_loopback_http, purpose=purpose)
    response = urllib.request.urlopen(req_or_url, timeout=timeout, context=_context())  # nosec B310: guarded by NetworkPolicy
    _verify_pin(response, url)
    return response
