"""MCP tool registration for MEK searches."""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

from mcp.server.fastmcp import FastMCP

from .client import MekClient
from .parsers import parse_full_text_results, parse_simple_results
from .schemas import FullTextSearchQuery, SimpleSearchQuery


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
