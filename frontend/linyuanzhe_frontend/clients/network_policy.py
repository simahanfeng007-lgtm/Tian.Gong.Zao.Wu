from __future__ import annotations

"""Frontend Runtime network policy for L6.72.18.

The desktop frontend may use HTTP only for localhost/loopback Runtime bridge.
Remote Runtime URLs must use HTTPS. TLS verification uses Python's default SSL
context, with optional certificate SHA256 pinning through
LINYUANZHE_TLS_CERT_SHA256.
"""

import hashlib
import os
import socket
import ssl
import urllib.parse
import urllib.request
from typing import Any


class NetworkPolicyError(RuntimeError):
    pass


_LOOPBACK_HOSTS = {"localhost", "127.0.0.1", "::1", "0.0.0.0"}


def _request_url(req_or_url: Any) -> str:
    return str(getattr(req_or_url, "full_url", req_or_url) or "")


def _host(url: str) -> str:
    return (urllib.parse.urlparse(str(url or "")).hostname or "").lower()


def is_loopback_url(url: str) -> bool:
    host = _host(url)
    if host in _LOOPBACK_HOSTS:
        return True
    try:
        return socket.gethostbyname(host).startswith("127.")
    except Exception:
        return False


def validate_url(url: str, *, allow_loopback_http: bool = True, purpose: str = "runtime") -> None:
    parsed = urllib.parse.urlparse(str(url or ""))
    scheme = (parsed.scheme or "").lower()
    if not scheme or not parsed.hostname:
        raise NetworkPolicyError(f"{purpose}: invalid URL")
    if scheme == "http":
        if allow_loopback_http and is_loopback_url(url):
            return
        raise NetworkPolicyError(f"{purpose}: remote HTTP is forbidden; use HTTPS")
    if scheme != "https":
        raise NetworkPolicyError(f"{purpose}: unsupported URL scheme {scheme!r}")


def _ssl_context() -> ssl.SSLContext:
    cafile = os.environ.get("LINYUANZHE_CA_BUNDLE", "").strip() or None
    return ssl.create_default_context(cafile=cafile)


def _pin_for_host(host: str) -> str:
    raw = os.environ.get("LINYUANZHE_TLS_CERT_SHA256", "").strip()
    if not raw:
        return ""
    for item in [x.strip() for x in raw.split(",") if x.strip()]:
        if "=" in item:
            key, val = item.split("=", 1)
            if key.strip().lower() == host.lower():
                return val.strip().lower().replace(":", "")
        else:
            return item.lower().replace(":", "")
    return ""


def _peer_cert_digest(response: Any) -> str:
    fp = getattr(response, "fp", None)
    raw = getattr(fp, "raw", None) if fp is not None else None
    for obj in (getattr(raw, "_sock", None), getattr(response, "sock", None)):
        if obj is None:
            continue
        getpeercert = getattr(obj, "getpeercert", None)
        if callable(getpeercert):
            try:
                cert = getpeercert(binary_form=True)
                if cert:
                    return hashlib.sha256(cert).hexdigest()
            except Exception:
                continue
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


def urlopen_with_policy(req_or_url: Any, *, timeout: float, allow_loopback_http: bool = True, purpose: str = "runtime") -> Any:
    url = _request_url(req_or_url)
    validate_url(url, allow_loopback_http=allow_loopback_http, purpose=purpose)
    scheme = urllib.parse.urlparse(url).scheme.lower()
    if scheme == "https":
        response = urllib.request.urlopen(req_or_url, timeout=timeout, context=_ssl_context())  # nosec B310: guarded by NetworkPolicy
        _verify_pin(response, url)
        return response
    return urllib.request.urlopen(req_or_url, timeout=timeout)  # nosec B310: loopback HTTP only
