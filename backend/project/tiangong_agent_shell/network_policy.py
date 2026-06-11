from __future__ import annotations

"""L6.72.18 network policy for model-provider HTTPS and loopback Runtime traffic.

This module centralizes the boundary rules that were previously scattered around
urllib.request.urlopen calls:

* remote network traffic must use HTTPS;
* localhost / loopback HTTP is allowed only when the caller explicitly asks for it;
* TLS certificate validation uses Python's default verified SSL context;
* optional certificate SHA256 pinning can be enabled with
  LINYUANZHE_TLS_CERT_SHA256. The value may be a raw hex digest for all hosts or
  comma-separated host=hex entries.
"""

import hashlib
import os
import socket
import ssl
import urllib.parse
import urllib.request
from typing import Any


class NetworkPolicyError(RuntimeError):
    """Raised when a URL violates the Linyuanzhe network boundary policy."""


_LOOPBACK_HOSTS = {"localhost", "127.0.0.1", "::1", "0.0.0.0"}


def _hostname(url: str) -> str:
    parsed = urllib.parse.urlparse(str(url or ""))
    return (parsed.hostname or "").strip().lower()


def is_loopback_url(url: str) -> bool:
    host = _hostname(url)
    if not host:
        return False
    if host in _LOOPBACK_HOSTS:
        return True
    try:
        return socket.gethostbyname(host).startswith("127.")
    except Exception:
        return False


def _request_url(req_or_url: Any) -> str:
    return str(getattr(req_or_url, "full_url", req_or_url) or "")


def validate_url(url: str, *, allow_loopback_http: bool = False, purpose: str = "network") -> None:
    parsed = urllib.parse.urlparse(str(url or ""))
    scheme = (parsed.scheme or "").lower()
    host = (parsed.hostname or "").strip().lower()
    if not scheme or not host:
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


def _configured_pin_for_host(host: str) -> str:
    raw = os.environ.get("LINYUANZHE_TLS_CERT_SHA256", "").strip()
    if not raw:
        return ""
    host = (host or "").lower()
    for item in [x.strip() for x in raw.split(",") if x.strip()]:
        if "=" in item:
            key, val = item.split("=", 1)
            if key.strip().lower() == host:
                return val.strip().lower().replace(":", "")
        elif len(item.replace(":", "")) >= 32:
            return item.lower().replace(":", "")
    return ""


def _peer_cert_digest(response: Any) -> str:
    # urllib/http.client internals differ by Python version. Keep this best-effort
    # but fail closed when pinning was explicitly configured.
    candidates = []
    fp = getattr(response, "fp", None)
    if fp is not None:
        candidates.append(fp)
        raw = getattr(fp, "raw", None)
        if raw is not None:
            candidates.append(raw)
            sock = getattr(raw, "_sock", None)
            if sock is not None:
                candidates.append(sock)
    candidates.append(getattr(response, "sock", None))
    for obj in candidates:
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


def _verify_optional_pin(response: Any, url: str) -> None:
    host = _hostname(url)
    expected = _configured_pin_for_host(host)
    if not expected:
        return
    actual = _peer_cert_digest(response)
    if not actual:
        try:
            response.close()
        except Exception:
            pass
        raise NetworkPolicyError(f"tls pinning requested for {host}, but peer certificate is unavailable")
    if actual.lower() != expected.lower():
        try:
            response.close()
        except Exception:
            pass
        raise NetworkPolicyError(f"tls certificate pin mismatch for {host}")


def urlopen_with_policy(req_or_url: Any, *, timeout: float, allow_loopback_http: bool = False, purpose: str = "network") -> Any:
    url = _request_url(req_or_url)
    validate_url(url, allow_loopback_http=allow_loopback_http, purpose=purpose)
    scheme = urllib.parse.urlparse(url).scheme.lower()
    if scheme == "https":
        response = urllib.request.urlopen(req_or_url, timeout=timeout, context=_ssl_context())  # nosec B310: guarded by NetworkPolicy
        _verify_optional_pin(response, url)
        return response
    return urllib.request.urlopen(req_or_url, timeout=timeout)  # nosec B310: loopback HTTP only by policy
