"""MCP server entry point for MEK search tools."""

from __future__ import annotations

from mcp.server.fastmcp import FastMCP

from .tools import register_tools

SERVER_NAME = "mek-mcp"


def create_server() -> FastMCP:
    """Create the MEK MCP server instance.

    Keeping construction in a separate function makes smoke tests and future
    integration tests straightforward.
    """
    server = FastMCP(SERVER_NAME)
    register_tools(server)
    return server


def main() -> None:
    """Run the MCP server over stdio."""
    create_server().run()


if __name__ == "__main__":
    main()
