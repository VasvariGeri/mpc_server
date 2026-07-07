import os

import pytest

from mek_mcp.client import MekClient
from mek_mcp.parsers import (
    parse_advanced_results,
    parse_full_text_results,
    parse_index_browse_results,
    parse_record,
    parse_simple_results,
)
from mek_mcp.schemas import (
    AdvancedCondition,
    AdvancedField,
    AdvancedSearchQuery,
    FullTextSearchQuery,
    IndexBrowseQuery,
    RecordQuery,
    SimpleSearchQuery,
)

pytestmark = pytest.mark.skipif(
    os.environ.get("MEK_LIVE_TESTS") != "1",
    reason="Set MEK_LIVE_TESTS=1 to run live MEK integration tests.",
)


def test_live_simple_search_round_trip() -> None:
    with MekClient() as client:
        page = client.fetch_simple_search(SimpleSearchQuery(title="arany*", limit=10))

    response = parse_simple_results(page, limit=10)

    assert response.source_url.startswith("https://mek.oszk.hu/")
    assert response.total_results is None or response.total_results >= 0


def test_live_full_text_search_round_trip() -> None:
    with MekClient() as client:
        page = client.fetch_full_text_search(
            FullTextSearchQuery(query="Duna", limit=10)
        )

    response = parse_full_text_results(page, limit=10)

    assert response.source_url.startswith("https://mek.oszk.hu/")
    assert response.total_results is None or response.total_results >= 0


def test_live_index_browse_round_trip() -> None:
    with MekClient() as client:
        page = client.fetch_index_browse(
            IndexBrowseQuery(field=AdvancedField.SUBJECT_KEYWORD, prefix="nep")
        )

    response = parse_index_browse_results(
        page,
        field=AdvancedField.SUBJECT_KEYWORD,
        prefix="nep",
        limit=10,
    )

    assert response.source_url.startswith("https://mek.oszk.hu/")
    assert response.total_results is None or response.total_results >= 0


def test_live_advanced_search_pagination_round_trip() -> None:
    first_query = AdvancedSearchQuery(
        conditions=[
            AdvancedCondition(field=AdvancedField.TITLE_MAIN, value="arany*")
        ],
        accentless=True,
    )

    with MekClient() as client:
        first_page = client.fetch_advanced_search(first_query)

    first_response = parse_advanced_results(first_page)

    assert first_response.source_url.startswith("https://mek.oszk.hu/")
    assert first_response.total_results is None or first_response.total_results >= 0

    if first_response.next_offset is None or first_response.next_page_state is None:
        return

    next_query = AdvancedSearchQuery(
        conditions=[
            AdvancedCondition(field=AdvancedField.TITLE_MAIN, value="arany*")
        ],
        accentless=True,
        offset=first_response.next_offset,
        page_state=first_response.next_page_state,
    )

    with MekClient() as client:
        next_page = client.fetch_advanced_search(next_query)

    next_response = parse_advanced_results(next_page, offset=next_query.offset)

    assert next_response.offset == first_response.next_offset
    assert next_response.source_url.startswith("https://mek.oszk.hu/")


def test_live_record_round_trip() -> None:
    with MekClient() as client:
        page = client.fetch_record(RecordQuery(identifier="05500/05585"))

    response = parse_record(page)

    assert response.mek_id == "05500/05585"
    assert response.url.startswith("https://mek.oszk.hu/")
