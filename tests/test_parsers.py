from pathlib import Path

from mek_mcp.parsers import parse_full_text_results, parse_simple_results
from mek_mcp.schemas import MekPage

FIXTURE_DIR = Path(__file__).parent / "fixtures"


def load_page(name: str) -> MekPage:
    return MekPage(
        url="https://mek.oszk.hu/hu/search/elfull/",
        status_code=200,
        html=(FIXTURE_DIR / name).read_text(encoding="utf-8"),
    )


def test_parse_simple_results() -> None:
    response = parse_simple_results(load_page("simple_results.html"), limit=10)

    assert response.kind == "simple"
    assert response.total_results == 2
    assert response.limit == 10
    assert response.offset == 0
    assert response.next_offset == 10
    assert len(response.results) == 2
    assert response.results[0].title == "Petőfi Sándor összes költeményei"
    assert response.results[0].authors == ["Petőfi Sándor"]
    assert response.results[0].mek_id == "01000/01006"
    assert response.results[1].authors == ["Ferenczi Zoltán", "Hatvany Lajos"]
    assert response.results[1].url == "https://mek.oszk.hu/01100/01122/"


def test_parse_full_text_results_with_snippets_and_found_urls() -> None:
    response = parse_full_text_results(load_page("full_text_results.html"), limit=10)

    assert response.kind == "full_text"
    assert response.total_results == 13175
    assert response.next_offset == 10
    assert len(response.results) == 2
    assert response.results[0].title == "A kőszívű ember fiai"
    assert response.results[0].authors == ["Jókai Mór"]
    assert response.results[0].snippet == "Duna folyama (K: Duna <vize> folyama)"
    assert (
        response.results[0].found_url
        == "https://mek.oszk.hu/05500/05585/html/jokaikoszivu0017/footnoteS01939.html"
    )
    assert (
        response.results[1].snippet
        == "Duna Földvár D Duoviri TARTALOM → D Duna Pentele"
    )


def test_parse_no_results_page() -> None:
    response = parse_simple_results(load_page("no_results.html"), limit=10)

    assert response.total_results == 0
    assert response.next_offset is None
    assert response.results == []
