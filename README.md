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

Live MEK integration tests are skipped by default. Run them explicitly with
network access:

```bash
MEK_LIVE_TESTS=1 python3 -m pytest tests/test_live_mek.py
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

Tool errors are returned as structured payloads instead of raw tracebacks:

```json
{
  "error": {
    "type": "validation_error",
    "message": "...",
    "retryable": false
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
- `mek_browse_index`, an MCP tool for MEK's controlled index suggestions
- `mek_get_record`, an MCP tool for normalized MEK record details

See [Agent Workflows](docs/agent-workflows.md) for example multi-tool search
strategies and prompt-oriented usage patterns.

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
- `offset`: pagination offset; use `next_offset` from the previous response
- `page_state`: pagination state; use `next_page_state` from the previous
  response when requesting later advanced-search pages

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

### `mek_browse_index`

Browses MEK LISTA/index suggestions for an advanced-search field. Use it when
the exact controlled form is uncertain, then pass a returned `value` into
`mek_advanced_search`.

Arguments:

- `field`: one of the same MEK catalog fields accepted by `mek_advanced_search`
- `prefix`: one or more starting characters to browse from
- `limit`: maximum number of suggestions to return, from `1` to `200`

Example:

```json
{
  "field": "dc_subject keyword",
  "prefix": "nep",
  "limit": 20
}
```

### `mek_get_record`

Fetches a MEK record page and returns normalized bibliographic details. Use it
after a search result when the agent needs richer metadata, available formats,
stable identifiers, or related pages.

Arguments:

- `identifier`: a MEK ID such as `05500/05585`, or a full MEK record URL

Returned data includes title, authors, MEK ID, URL, URN, description, date,
topics, keywords, available files, related pages, cover URL, and raw page-level
metadata discovered in `meta` tags.

Example:

```json
{
  "identifier": "https://mek.oszk.hu/05500/05585"
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
