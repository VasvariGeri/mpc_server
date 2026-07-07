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

Example MCP server configuration:

```json
{
  "mcpServers": {
    "mek": {
      "command": "mek-mcp"
    }
  }
}
```

## Current scope

The project currently contains:

- a minimal MCP server entry point
- typed request/response schemas for MEK searches
- an HTTP client for MEK simple, advanced, and full text search endpoints
- offline-tested HTML parsers for MEK search result pages
- `mek_simple_search`, an MCP tool for MEK's simple bibliographic search

## Tools

### `mek_simple_search`

Searches MEK bibliographic metadata by title, subject, creator, or MEK ID.
When multiple fields are provided, MEK combines them with logical AND.

Arguments:

- `title`: title words
- `subject`: subject, subtopic, keyword, or type words
- `creator`: author, editor, or translator name
- `mek_id`: MEK document identifier
- `limit`: results per page, one of `10`, `50`, or `100`
- `offset`: pagination offset

Additional MCP search tools will be added incrementally in later commits.
