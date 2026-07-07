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
- `mek_full_text_search`, an MCP tool for MEK's full text search
- `mek_advanced_search`, an MCP tool for MEK's fielded catalog search

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

### `mek_advanced_search`

Searches MEK bibliographic metadata with up to five fielded catalog
conditions. Use it for role-aware searches such as author vs. contributor,
controlled subject, geographic subject, document type, format, and language.

Arguments:

- `conditions`: list of 1-5 condition objects
- `sort`: one of `szerzosz`, `cimsz`, `idorend`, or `idsz`
- `accentless`: set to `true` to use MEK's accentless search option
- `include_in_progress`: include documents still under processing

Each condition has:

- `field`: MEK catalog field, for example:
  - `dc_title main`
  - `dc_creator_o FamilyGivenName`
  - `dc_contributor_o FamilyGivenName`
  - `dc_subject keyword`
  - `dc_subject geographic`
  - `dc_type dc_type`
  - `dc_format format_name`
  - `dc_language m_lang`
- `value`: search value; trailing `*` truncation is supported by MEK
- `operator_after`: optional `and`, `or`, or `not` join to the next condition

Example:

```json
{
  "conditions": [
    {
      "field": "dc_creator_o FamilyGivenName",
      "value": "Jókai",
      "operator_after": "and"
    },
    {
      "field": "dc_title main",
      "value": "arany*"
    }
  ],
  "accentless": true
}
```

### `mek_full_text_search`

Searches inside MEK document full text. MEK searches HTML and PDF texts,
automatically stems Hungarian inflected forms, and returns snippets plus direct
hit locations when available.

Arguments:

- `query`: full text search query
- `broadtopic`: optional collection filter; use one of:
  - empty string for the full collection
  - `természettudományok és matematika`
  - `műszaki tudományok, gazdasági ágazatok`
  - `társadalomtudományok`
  - `humán területek, kultúra, irodalom`
  - `kézikönyvek és egyéb műfajok`
- `limit`: results per page, one of `10`, `50`, or `100`
- `offset`: pagination offset

Additional MCP search tools will be added incrementally in later commits.
