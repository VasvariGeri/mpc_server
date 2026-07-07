import os

import pytest

from mek_mcp.client import MekClient
from mek_mcp.parsers import (
    parse_full_text_results,
    parse_index_browse_results,
    parse_record,
    parse_simple_results,
)
from mek_mcp.schemas import (
    AdvancedField,
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


def test_live_record_round_trip() -> None:
    with MekClient() as client:
        page = client.fetch_record(RecordQuery(identifier="05500/05585"))

    response = parse_record(page)

    assert response.mek_id == "05500/05585"
    assert response.url.startswith("https://mek.oszk.hu/")
