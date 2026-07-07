# MEK MCP Server

Python MCP server for exposing Magyar Elektronikus Konyvtar (MEK) search
interfaces to agentic coding and chat tools.

## Development

Install the package with development dependencies:

```bash
python3 -m pip install ".[dev]"
```

Run the smoke test suite:

```bash
python3 -m pytest
```

Start the MCP server over stdio:

```bash
mek-mcp
```

## Current scope

The project currently contains:

- a minimal MCP server entry point
- typed request/response schemas for MEK searches
- an HTTP client for MEK simple, advanced, and full text search endpoints
- offline-tested HTML parsers for MEK search result pages

MCP search tools will be added incrementally in later commits.
