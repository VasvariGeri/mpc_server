"""MCP tool registration for MEK searches."""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

from mcp.server.fastmcp import FastMCP
from pydantic import ValidationError

from .client import MekClient, MekClientError
from .parsers import (
    parse_advanced_results,
    parse_full_text_results,
    parse_index_browse_results,
    parse_record,
    parse_simple_results,
)
from .schemas import (
    AdvancedCondition,
    AdvancedSearchQuery,
    FullTextSearchQuery,
    IndexBrowseQuery,
    RecordQuery,
    SimpleSearchQuery,
)


def register_tools(
    server: FastMCP,
    *,
    client_factory: Callable[[], MekClient] = MekClient,
) -> None:
    """Register all currently supported MEK MCP tools."""

    @server.tool(
        name="mek_simple_search",
        description=(
            "Search Magyar Elektronikus Konyvtar bibliographic records by title, "
            "subject, creator, or MEK identifier. Multiple populated fields are "
            "combined by MEK with logical AND. Hungarian accents may be omitted; "
            "MEK also supports trailing * truncation."
        ),
    )
    def mek_simple_search(
        title: str | None = None,
        subject: str | None = None,
        creator: str | None = None,
        mek_id: str | None = None,
        limit: int = 10,
        offset: int = 0,
    ) -> dict[str, Any]:
        """Run MEK's simple bibliographic search."""
        return _handle_tool_errors(
            lambda: _simple_search(
                client_factory,
                title=title,
                subject=subject,
                creator=creator,
                mek_id=mek_id,
                limit=limit,
                offset=offset,
            )
        )

    @server.tool(
        name="mek_advanced_search",
        description=(
            "Search MEK bibliographic records with up to five fielded catalog "
            "conditions joined by AND, OR, or NOT. Use this when a query needs "
            "specific roles such as creator, contributor, controlled subject, "
            "geographic subject, document type, format, or language. Conditions "
            "must contain field, value, and optionally operator_after."
        ),
    )
    def mek_advanced_search(
        conditions: list[dict[str, str]],
        sort: str = "szerzosz",
        accentless: bool = False,
        include_in_progress: bool = False,
    ) -> dict[str, Any]:
        """Run MEK's advanced bibliographic catalog search."""
        return _handle_tool_errors(
            lambda: _advanced_search(
                client_factory,
                conditions=conditions,
                sort=sort,
                accentless=accentless,
                include_in_progress=include_in_progress,
            )
        )

    @server.tool(
        name="mek_browse_index",
        description=(
            "Browse MEK catalog index values for a specific advanced-search "
            "field. Use this before targeted advanced searches when the exact "
            "controlled subject, author, language, document type, or other "
            "catalog value is uncertain."
        ),
    )
    def mek_browse_index(
        field: str,
        prefix: str,
        limit: int = 50,
    ) -> dict[str, Any]:
        """Browse MEK's LISTA/index suggestions for an advanced-search field."""
        return _handle_tool_errors(
            lambda: _browse_index(
                client_factory,
                field=field,
                prefix=prefix,
                limit=limit,
            )
        )

    @server.tool(
        name="mek_get_record",
        description=(
            "Fetch and normalize a MEK record page by MEK ID or record URL. "
            "Returns bibliographic metadata, topics, keywords, description, "
            "available file formats, related pages, and stable identifiers."
        ),
    )
    def mek_get_record(identifier: str) -> dict[str, Any]:
        """Fetch and parse a MEK record page."""
        return _handle_tool_errors(
            lambda: _get_record(client_factory, identifier=identifier)
        )

    @server.tool(
        name="mek_full_text_search",
        description=(
            "Search inside MEK document full text. MEK searches HTML and PDF "
            "texts, stems Hungarian inflected forms automatically, and ignores "
            "very common stop words. Results include snippets and direct hit "
            "locations when MEK provides them."
        ),
    )
    def mek_full_text_search(
        query: str,
        broadtopic: str = "",
        limit: int = 10,
        offset: int = 0,
    ) -> dict[str, Any]:
        """Run MEK's full text search."""
        return _handle_tool_errors(
            lambda: _full_text_search(
                client_factory,
                query=query,
                broadtopic=broadtopic,
                limit=limit,
                offset=offset,
            )
        )


def _simple_search(
    client_factory: Callable[[], MekClient],
    *,
    title: str | None,
    subject: str | None,
    creator: str | None,
    mek_id: str | None,
    limit: int,
    offset: int,
) -> dict[str, Any]:
    query = SimpleSearchQuery(
        title=title,
        subject=subject,
        creator=creator,
        mek_id=mek_id,
        limit=limit,
        offset=offset,
    )

    with client_factory() as client:
        page = client.fetch_simple_search(query)

    response = parse_simple_results(
        page,
        limit=int(query.limit),
        offset=query.offset,
    )
    return response.model_dump(mode="json")


def _advanced_search(
    client_factory: Callable[[], MekClient],
    *,
    conditions: list[dict[str, str]],
    sort: str,
    accentless: bool,
    include_in_progress: bool,
) -> dict[str, Any]:
    query = AdvancedSearchQuery(
        conditions=[
            AdvancedCondition.model_validate(condition)
            for condition in conditions
        ],
        sort=sort,
        accentless=accentless,
        include_in_progress=include_in_progress,
    )

    with client_factory() as client:
        page = client.fetch_advanced_search(query)

    response = parse_advanced_results(page)
    return response.model_dump(mode="json")


def _browse_index(
    client_factory: Callable[[], MekClient],
    *,
    field: str,
    prefix: str,
    limit: int,
) -> dict[str, Any]:
    query = IndexBrowseQuery(field=field, prefix=prefix, limit=limit)

    with client_factory() as client:
        page = client.fetch_index_browse(query)

    response = parse_index_browse_results(
        page,
        field=query.field,
        prefix=query.prefix,
        limit=query.limit,
    )
    return response.model_dump(mode="json")


def _get_record(
    client_factory: Callable[[], MekClient],
    *,
    identifier: str,
) -> dict[str, Any]:
    query = RecordQuery(identifier=identifier)

    with client_factory() as client:
        page = client.fetch_record(query)

    response = parse_record(page)
    return response.model_dump(mode="json")


def _full_text_search(
    client_factory: Callable[[], MekClient],
    *,
    query: str,
    broadtopic: str,
    limit: int,
    offset: int,
) -> dict[str, Any]:
    search_query = FullTextSearchQuery(
        query=query,
        broadtopic=broadtopic,
        limit=limit,
        offset=offset,
    )

    with client_factory() as client:
        page = client.fetch_full_text_search(search_query)

    response = parse_full_text_results(
        page,
        limit=int(search_query.limit),
        offset=search_query.offset,
    )
    return response.model_dump(mode="json")


def _handle_tool_errors(action: Callable[[], dict[str, Any]]) -> dict[str, Any]:
    try:
        return action()
    except ValidationError as exc:
        return _error_response("validation_error", str(exc), retryable=False)
    except ValueError as exc:
        return _error_response("validation_error", str(exc), retryable=False)
    except MekClientError as exc:
        return _error_response("mek_request_error", str(exc), retryable=True)


def _error_response(
    error_type: str,
    message: str,
    *,
    retryable: bool,
) -> dict[str, Any]:
    return {
        "error": {
            "type": error_type,
            "message": message,
            "retryable": retryable,
        }
    }
