"""MCP server entry point for MEK search tools."""

from __future__ import annotations

import os
from typing import Literal

from mcp.server.fastmcp import FastMCP

from .tools import register_tools

SERVER_NAME = "mek-mcp"
HttpTransport = Literal["sse", "streamable-http"]


def create_server(
    *,
    host: str = "127.0.0.1",
    port: int = 8000,
    stateless_http: bool = True,
) -> FastMCP:
    """Create the MEK MCP server instance.

    Keeping construction in a separate function makes smoke tests and future
    integration tests straightforward.
    """
    server = FastMCP(
        SERVER_NAME,
        host=host,
        port=port,
        stateless_http=stateless_http,
    )
    register_tools(server)
    return server


def main() -> None:
    """Run the MCP server over stdio."""
    create_server().run()


def main_http() -> None:
    """Run the MCP server over an HTTP transport for remote deployments."""
    host = os.getenv("MEK_MCP_HOST", "0.0.0.0")
    port = int(os.getenv("PORT", os.getenv("MEK_MCP_PORT", "8000")))
    transport: HttpTransport = _http_transport_from_env()

    create_server(host=host, port=port).run(transport=transport)


def _http_transport_from_env() -> HttpTransport:
    transport = os.getenv("MEK_MCP_TRANSPORT", "streamable-http")
    if transport not in {"sse", "streamable-http"}:
        raise ValueError("MEK_MCP_TRANSPORT must be 'sse' or 'streamable-http'")
    return transport  # type: ignore[return-value]


if __name__ == "__main__":
    main()
