"""Network policy for everything the scanner fetches (SSRF protection).

One decision function, used for: the URL of POST /api/scans, EVERY browser
request (navigation, sub-resources, iframes, pasted HTML, each redirect hop —
see capture/browser.py), and the 2.4.4 destination-title fetch.

Defaults
  * schemes: http and https (file: only when an operator scans a local file
    from the CLI; data:, blob: and about: never reach the network);
  * always blocked: link-local and cloud metadata (169.254.0.0/16, fe80::/10),
    0.0.0.0/8, multicast, reserved and unspecified addresses;
  * loopback blocked, except explicitly allowed origins: the app's own /demo/
    and the local servers of the evaluation;
  * private networks (RFC 1918, fc00::/7, 100.64.0.0/10) blocked unless
    KLAR_ALLOW_PRIVATE_NETWORKS=1 (intranet deployments).

Host names are resolved and every resolved address is checked. Residual risk
(documented): DNS rebinding between our check and the browser's own lookup.
"""

from __future__ import annotations

import ipaddress
import socket
import threading
from dataclasses import dataclass, field
from urllib.parse import urlparse

PASSIVE_SCHEMES = {"data", "blob", "about"}


@dataclass(frozen=True)
class Verdict:
    ok: bool
    reason: str = ""
    # which rule fired: blocked_metadata | blocked_localhost | blocked_private | dns | blocked_scheme
    code: str = ""


def _origin(scheme: str, host: str, port: int | None) -> str:
    default = {"http": 80, "https": 443}.get(scheme)
    h = f"[{host}]" if ":" in host else host
    return f"{scheme}://{h}" + ("" if port in (None, default) else f":{port}")


def origin_of(url: str) -> str:
    u = urlparse(url)
    return _origin((u.scheme or "").lower(), (u.hostname or "").lower(), u.port)


def classify_ip(ip: ipaddress._BaseAddress) -> str:
    """'blocked' (never), 'loopback', 'private' or 'public'."""
    if isinstance(ip, ipaddress.IPv6Address) and ip.ipv4_mapped:
        ip = ip.ipv4_mapped
    if ip.is_link_local or ip.is_multicast or ip.is_unspecified or ip.is_reserved:
        return "blocked"
    if isinstance(ip, ipaddress.IPv4Address) and ip in ipaddress.ip_network("0.0.0.0/8"):
        return "blocked"
    if ip.is_loopback:
        return "loopback"
    if ip.is_private or (isinstance(ip, ipaddress.IPv4Address) and ip in ipaddress.ip_network("100.64.0.0/10")):
        return "private"
    return "public"


@dataclass
class NetPolicy:
    allow_private: bool = False
    allow_file: bool = False
    # (origin, path prefix) pairs that bypass the address checks: own /demo/, eval servers
    allowed: tuple[tuple[str, str], ...] = ()
    _dns: dict[str, list[str]] = field(default_factory=dict, repr=False)
    _lock: threading.Lock = field(default_factory=threading.Lock, repr=False)
    blocked_log: list[str] = field(default_factory=list, repr=False)
    # url → error code of a failed or refused request (keeps the real cause for the scan error)
    errors: dict[str, str] = field(default_factory=dict, repr=False)

    def with_allowed(self, *entries: tuple[str, str]) -> "NetPolicy":
        return NetPolicy(self.allow_private, self.allow_file, self.allowed + tuple(entries))

    def _resolve(self, host: str) -> list[str]:
        with self._lock:
            if host in self._dns:
                return self._dns[host]
        try:
            infos = socket.getaddrinfo(host, None, proto=socket.IPPROTO_TCP)
            addrs = sorted({i[4][0].split("%")[0] for i in infos})
        except OSError:
            addrs = []
        with self._lock:
            self._dns[host] = addrs
        return addrs

    def check(self, url: str) -> Verdict:
        u = urlparse(url)
        scheme = (u.scheme or "").lower()
        if scheme in PASSIVE_SCHEMES:
            return Verdict(True)
        if scheme == "file":
            return Verdict(self.allow_file, "" if self.allow_file else "file: URLs are not allowed",
                           "" if self.allow_file else "blocked_scheme")
        if scheme not in ("http", "https"):
            return Verdict(False, f"scheme {scheme or '(none)'!r} is not allowed", "blocked_scheme")
        host = (u.hostname or "").lower().rstrip(".")
        if not host:
            return Verdict(False, "no host", "dns")
        try:
            port = u.port
        except ValueError:
            return Verdict(False, "invalid port", "dns")
        origin = _origin(scheme, host, port)
        path = u.path or "/"
        for allowed_origin, prefix in self.allowed:
            if origin == allowed_origin and path.startswith(prefix):
                return Verdict(True)
        try:
            addrs = [host] if ipaddress.ip_address(host) else []
        except ValueError:
            addrs = self._resolve(host)
        if not addrs:
            return Verdict(False, f"host {host!r} does not resolve", "dns")
        for a in addrs:
            kind = classify_ip(ipaddress.ip_address(a))
            if kind == "blocked":
                return Verdict(False, f"{host} resolves to a link-local or metadata address ({a})", "blocked_metadata")
            if kind == "loopback":
                return Verdict(False, f"{host} is a loopback address ({a})", "blocked_localhost")
            if kind == "private" and not self.allow_private:
                return Verdict(False, f"{host} is a private address ({a}); set KLAR_ALLOW_PRIVATE_NETWORKS=1 to allow",
                               "blocked_private")
        return Verdict(True)

    @staticmethod
    def check_endpoint(url: str) -> Verdict:
        """The configured LLM endpoint (LLM_BASE_URL) is NOT a scan target: its host is
        always allowed, including loopback, private addresses and compose service names
        (llm-gpu, llm-cpu, host.docker.internal), without KLAR_ALLOW_PRIVATE_NETWORKS.
        Link-local / cloud-metadata addresses stay blocked. Scan targets never inherit
        this exemption."""
        u = urlparse(url or "")
        if u.scheme not in ("http", "https") or not u.hostname:
            return Verdict(False, "LLM_BASE_URL must be an http(s) URL with a host")
        host = u.hostname.lower().rstrip(".")
        try:
            addrs = [str(ipaddress.ip_address(host))]
        except ValueError:
            try:
                addrs = sorted({i[4][0].split("%")[0] for i in socket.getaddrinfo(host, None, proto=socket.IPPROTO_TCP)})
            except OSError:
                return Verdict(True)  # not resolvable yet (container starting): allowed, the request will tell
        for a in addrs:
            if classify_ip(ipaddress.ip_address(a)) == "blocked":
                return Verdict(False, f"LLM endpoint {host} resolves to a blocked address ({a})")
        return Verdict(True)

    def log_block(self, url: str, reason: str, code: str = "") -> None:
        with self._lock:
            if len(self.blocked_log) < 200:
                self.blocked_log.append(f"{url[:200]} — {reason}")
            if code:
                self.errors.setdefault(url, code)

    def note_error(self, url: str, code: str) -> None:
        with self._lock:
            self.errors.setdefault(url, code)
