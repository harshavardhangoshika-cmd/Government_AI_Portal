"""
app/database/dns_patch.py
=========================
Resilient DNS resolution hook for Supabase cloud endpoints.
Addresses POSIX [Errno -2] Name or service not known (EAI_NONAME) on containerized Linux runtimes
(Streamlit Community Cloud, Docker, Kubernetes).

Background:
Supabase project hostnames (e.g. uusnnqbutovbnjqzyhmx.supabase.co) only publish IPv4 (A) records.
They do NOT publish IPv6 (AAAA) records.
When HTTP libraries (httpx, urllib3, requests) call socket.getaddrinfo(host, port, family=0),
glibc on container environments attempts IPv6 (AAAA) resolution first. If the container lacks an IPv6
default gateway or the DNS resolver times out on AAAA queries, glibc raises EAI_NONAME ([Errno -2]).

This patch intercepts socket.getaddrinfo calls for *.supabase.co when family==0 (AF_UNSPEC) and
attempts socket.AF_INET (IPv4) resolution first. If AF_INET resolution fails or for any other host,
it delegates directly to the standard socket.getaddrinfo.

Security & Integrity Guarantee:
- Never hardcodes IP addresses.
- Dynamic DNS lookup is fully preserved.
- Full TLS/SSL SNI and hostname certificate validation are strictly maintained.
"""

import socket
import logging

logger = logging.getLogger(__name__)

_ORIGINAL_GETADDRINFO = socket.getaddrinfo
_PATCH_INSTALLED = False


def install_dns_patch():
    """Install the IPv4-preferring resolver hook for Supabase domains."""
    global _PATCH_INSTALLED, _ORIGINAL_GETADDRINFO
    if _PATCH_INSTALLED:
        return

    def _resilient_getaddrinfo(host, port, family=0, type=0, proto=0, flags=0):
        # Only intervene for supabase.co domains when family is unconstrained (family==0 / AF_UNSPEC)
        if family == 0 and isinstance(host, str) and "supabase.co" in host.lower():
            try:
                # Query IPv4 specifically to prevent [Errno -2] Name or service not known
                return _ORIGINAL_GETADDRINFO(host, port, socket.AF_INET, type, proto, flags)
            except (socket.gaierror, OSError):
                # Fall back to original resolution if AF_INET attempt failed
                pass
        return _ORIGINAL_GETADDRINFO(host, port, family, type, proto, flags)

    socket.getaddrinfo = _resilient_getaddrinfo
    _PATCH_INSTALLED = True
    logger.info("[OK] Resilient Supabase IPv4 DNS resolver hook installed.")
