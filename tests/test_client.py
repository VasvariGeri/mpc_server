import httpx
import pytest

from mek_mcp.client import MekClient, MekClientError
from mek_mcp.schemas import (
    AdvancedCondition,
    AdvancedField,
    AdvancedOperator,
    AdvancedSearchQuery,
    FullTextBroadTopic,
    FullTextSearchQuery,
    IndexBrowseQuery,
    RecordQuery,
    SimpleSearchQuery,
)


def test_fetch_simple_search_posts_expected_form_fields() -> None:
    captured: dict[str, str] = {}

    def handler(request: httpx.Request) -> httpx.Response:
        captured.update(dict(httpx.QueryParams(request.content.decode())))
        return httpx.Response(200, text="<html>ok</html>", request=request)

    client = MekClient(transport=httpx.MockTransport(handler))

    page = client.fetch_simple_search(
        SimpleSearchQuery(title="Duna", subject="tortenelem", limit=50, offset=10)
    )

    assert page.status_code == 200
    assert page.html == "<html>ok</html>"
    assert captured["dc_title"] == "Duna"
    assert captured["dc_subject"] == "tortenelem"
    assert captured["dc_creator"] == ""
    assert captured["id"] == ""
    assert captured["size"] == "50"
    assert captured["from"] == "10"


def test_fetch_full_text_search_posts_expected_form_fields() -> None:
    captured: dict[str, str] = {}

    def handler(request: httpx.Request) -> httpx.Response:
        captured.update(dict(httpx.QueryParams(request.content.decode())))
        return httpx.Response(200, text="<html>ok</html>", request=request)

    client = MekClient(transport=httpx.MockTransport(handler))

    client.fetch_full_text_search(
        FullTextSearchQuery(
            query="mesterséges intelligencia",
            broadtopic=FullTextBroadTopic.TECHNICAL_SCIENCES,
            limit=100,
        )
    )

    assert captured["body"] == "mesterséges intelligencia"
    assert captured["broadtopic"] == "műszaki tudományok, gazdasági ágazatok"
    assert captured["size"] == "100"


def test_fetch_advanced_search_posts_conditions_and_options() -> None:
    captured: dict[str, str] = {}
    captured_params: dict[str, str] = {}

    def handler(request: httpx.Request) -> httpx.Response:
        captured.update(dict(httpx.QueryParams(request.content.decode())))
        captured_params.update(dict(request.url.params))
        return httpx.Response(200, text="<html>ok</html>", request=request)

    client = MekClient(transport=httpx.MockTransport(handler))

    client.fetch_advanced_search(
        AdvancedSearchQuery(
            conditions=[
                AdvancedCondition(
                    field=AdvancedField.CREATOR,
                    value="Petőfi",
                    operator_after=AdvancedOperator.OR,
                ),
                AdvancedCondition(
                    field=AdvancedField.SUBJECT_KEYWORD,
                    value="Petőfi",
                ),
            ],
            accentless=True,
            include_in_progress=True,
        )
    )

    assert captured["s1"] == "dc_creator_o FamilyGivenName"
    assert captured["m1"] == "Petőfi"
    assert captured["muv1"] == "or"
    assert captured["s2"] == "dc_subject keyword"
    assert captured["m2"] == "Petőfi"
    assert captured["ekezet"] == "ektelen"
    assert captured["subid"] == "on"
    assert captured_params["sind1"] == "7"
    assert captured_params["sind2"] == "13"
    assert captured_params["muv1index"] == "1"


def test_fetch_index_browse_posts_expected_params_and_form_fields() -> None:
    captured: dict[str, str] = {}
    captured_params: dict[str, str] = {}

    def handler(request: httpx.Request) -> httpx.Response:
        captured.update(dict(httpx.QueryParams(request.content.decode())))
        captured_params.update(dict(request.url.params))
        return httpx.Response(200, text="<html>ok</html>", request=request)

    client = MekClient(transport=httpx.MockTransport(handler))

    client.fetch_index_browse(
        IndexBrowseQuery(field=AdvancedField.SUBJECT_KEYWORD, prefix="nep")
    )

    assert captured_params["tablefield"] == "dc_subject keyword"
    assert captured_params["par"] == "0"
    assert captured_params["indindex"] == "13"
    assert captured["s1"] == "dc_subject keyword"
    assert captured["m1"] == "nep"


def test_fetch_record_accepts_id_or_url() -> None:
    requested_paths: list[str] = []

    def handler(request: httpx.Request) -> httpx.Response:
        requested_paths.append(request.url.path)
        return httpx.Response(200, text="<html>ok</html>", request=request)

    client = MekClient(transport=httpx.MockTransport(handler))

    client.fetch_record(RecordQuery(identifier="05500/05585"))
    client.fetch_record(RecordQuery(identifier="https://mek.oszk.hu/05500/05585"))

    assert requested_paths == ["/05500/05585", "/05500/05585"]


def test_fetch_record_rejects_non_mek_urls() -> None:
    transport = httpx.MockTransport(lambda request: httpx.Response(200))
    client = MekClient(transport=transport)

    with pytest.raises(MekClientError, match="MEK ID or MEK URL"):
        client.fetch_record(RecordQuery(identifier="https://example.com/05500/05585"))


def test_decodes_iso_8859_2_html() -> None:
    body = (
        '<html><head><meta charset="iso-8859-2"></head>'
        "<body>Magyar Elektronikus Könyvtár</body></html>"
    ).encode("iso-8859-2")

    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, content=body, request=request)

    client = MekClient(transport=httpx.MockTransport(handler))

    page = client.get("/hu/search/detailed/")

    assert "Könyvtár" in page.html


def test_http_errors_are_wrapped() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(503, text="unavailable", request=request)

    client = MekClient(transport=httpx.MockTransport(handler))

    with pytest.raises(MekClientError):
        client.get("/hu/search/elfull/")


def test_simple_search_requires_at_least_one_field() -> None:
    with pytest.raises(ValueError, match="At least one"):
        SimpleSearchQuery()
