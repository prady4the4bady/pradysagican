"""Unified enterprise application entrypoint."""

from __future__ import annotations

from fastapi import FastAPI

from pradysagican.api.enterprise_server import EnterpriseAPIServer


def create_unified_app() -> FastAPI:
    """Create the complete application API surface."""
    server = EnterpriseAPIServer(version="2.0.0")
    return server.get_app()

