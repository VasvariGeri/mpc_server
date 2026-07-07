"""MCP server entry point for MEK search tools."""

from __future__ import annotations

from mcp.server.fastmcp import FastMCP

SERVER_NAME = "mek-mcp"


def create_server() -> FastMCP:
    """Create the MEK MCP server instance.

    Search tools are added in later commits. Keeping construction in a separate
    function makes smoke tests and future integration tests straightforward.
    """
    return FastMCP(SERVER_NAME)


def main() -> None:
    """Run the MCP server over stdio."""
    create_server().run()


if __name__ == "__main__":
    main()
