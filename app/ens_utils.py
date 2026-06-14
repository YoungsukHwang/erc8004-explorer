"""Cached ENS reverse lookup.

ENS Integrate-pool integration: take an Ethereum address, return the ENS name
the owner has set as their primary reverse record (or `None` if they haven't
claimed one). This turns the dashboard's anonymous `0x…` columns into
human-readable identities for the wallets that bothered to set one up.

Auth: none — uses a public RPC. No GCP credentials, no API key.
Cache: streamlit `cache_data` per instance, TTL one day.
"""
from __future__ import annotations

from typing import Iterable

try:
    import streamlit as st
    _HAS_STREAMLIT = True
except ImportError:
    _HAS_STREAMLIT = False

try:
    from web3 import Web3
    from ens import ENS
    _HAS_WEB3 = True
except ImportError:
    _HAS_WEB3 = False


# Public RPCs tried in order. The first one that answers wins.
_RPC_CANDIDATES = [
    "https://ethereum-rpc.publicnode.com",
    "https://cloudflare-eth.com",
    "https://rpc.ankr.com/eth",
    "https://eth.merkle.io",
]


_ens_singleton: ENS | None = None


def _get_ens() -> ENS | None:
    """Build a single ENS client lazily. Tries each RPC until one connects."""
    global _ens_singleton
    if _ens_singleton is not None:
        return _ens_singleton
    if not _HAS_WEB3:
        return None
    for rpc in _RPC_CANDIDATES:
        try:
            w3 = Web3(Web3.HTTPProvider(rpc, request_kwargs={"timeout": 8}))
            if w3.is_connected():
                _ens_singleton = ENS.from_web3(w3)
                return _ens_singleton
        except Exception:
            continue
    return None


def _resolve(address: str) -> str | None:
    if not address:
        return None
    ens = _get_ens()
    if ens is None:
        return None
    try:
        return ens.name(Web3.to_checksum_address(address))
    except Exception:
        return None


if _HAS_STREAMLIT:
    @st.cache_data(ttl=86400, show_spinner=False)
    def reverse_lookup(address: str) -> str | None:
        return _resolve(address)
else:
    def reverse_lookup(address: str) -> str | None:
        return _resolve(address)


def reverse_lookup_many(addresses: Iterable[str]) -> dict[str, str | None]:
    """Convenience: resolve a list. Each address is cached individually so
    repeated calls with overlapping lists reuse work."""
    return {a: reverse_lookup(a) for a in addresses}
