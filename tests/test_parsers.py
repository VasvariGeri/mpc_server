from pathlib import Path

from mek_mcp.parsers import (
    parse_advanced_results,
    parse_full_text_results,
    parse_index_browse_results,
    parse_record,
    parse_simple_results,
)
from mek_mcp.schemas import AdvancedField, MekPage

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


def test_parse_advanced_results_old_catalog_format() -> None:
    response = parse_advanced_results(load_page("advanced_results.html"))

    assert response.kind == "advanced"
    assert response.total_results == 165
    assert response.next_offset == 100
    assert response.next_page_state == "5919:13081:8173"
    assert len(response.results) == 2
    assert response.results[0].title == "II. Endre Aranybullája"
    assert response.results[0].url == "https://mek.oszk.hu/05900/05919"
    assert response.results[0].mek_id == "05900/05919"
    assert response.results[1].title == "Az arany ember"
    assert response.results[1].authors == ["Jókai Mór"]
    assert response.results[1].url == "https://mek.oszk.hu/00700/00798"


def test_parse_old_catalog_authors_keeps_hyphenated_names() -> None:
    page = MekPage(
        url="https://mek.oszk.hu/katalog/kataluj.php3",
        status_code=200,
        html="""
            <html><body>
              <div class="hit">
                <b>Szalay-Bobrovniczky Vince - Kovács Pál; Nagy Anna: Példa cím</b>
                <form action="/12300/12345/index.phtml"></form>
              </div>
            </body></html>
        """,
    )

    response = parse_advanced_results(page)

    assert response.results[0].title == "Példa cím"
    assert response.results[0].authors == [
        "Szalay-Bobrovniczky Vince",
        "Kovács Pál",
        "Nagy Anna",
    ]


def test_parse_index_browse_results() -> None:
    response = parse_index_browse_results(
        load_page("index_browse_results.html"),
        field=AdvancedField.SUBJECT_KEYWORD,
        prefix="nep",
        limit=3,
    )

    assert response.kind == "index"
    assert response.field == "dc_subject keyword"
    assert response.prefix == "nep"
    assert response.total_results == 177
    assert response.limit == 3
    assert [entry.value for entry in response.entries] == [
        "magyar néprajz",
        "néprajz",
        "néprajzi kutatás",
    ]


def test_parse_record_page() -> None:
    response = parse_record(load_page("record_page.html"))

    assert response.kind == "record"
    assert response.title == "A kőszívű ember fiai"
    assert response.authors == ["Jókai Mór"]
    assert response.mek_id == "05500/05585"
    assert response.url == "https://mek.oszk.hu/05500/05585"
    assert response.urn == "http://nbn.urn.hu/N2L?urn:nbn:hu-8131"
    assert response.description == "Rövid leírás a rekordhoz."
    assert response.date == "2008-01-15"
    assert response.topics == [
        "Szépirodalom, népköltészet",
        "Klasszikus magyar irodalom",
    ]
    assert response.keywords == ["magyar irodalom"]
    assert response.cover_url == "https://mek.oszk.hu/05500/05585/borito.jpg"
    assert [(file.label, file.file_type) for file in response.files] == [
        ("ZIP", "zip"),
        ("HTML", "htm"),
    ]
    assert [page.label for page in response.related_pages] == [
        "Katalóguscédula",
        "Fülszöveg",
    ]
    assert response.metadata["dc.title"] == ["A kőszívű ember fiai"]


def test_parse_record_cover_prefers_record_image_container() -> None:
    page = MekPage(
        url="https://mek.oszk.hu/05500/05585",
        status_code=200,
        html="""
            <html>
              <head>
                <meta property="og:image" content="https://mek.oszk.hu/05500/05585/meta.jpg">
              </head>
              <body>
                <img src="/logo.png">
                <div class="ipic"><img src="/05500/05585/borito.jpg"></div>
                <a class="itemurl">URL: https://mek.oszk.hu/05500/05585</a>
              </body>
            </html>
        """,
    )

    response = parse_record(page)

    assert response.cover_url == "https://mek.oszk.hu/05500/05585/borito.jpg"


def test_parse_record_cover_falls_back_to_meta_image() -> None:
    page = MekPage(
        url="https://mek.oszk.hu/05500/05585",
        status_code=200,
        html="""
            <html>
              <head>
                <meta property="og:image" content="https://mek.oszk.hu/05500/05585/meta.jpg">
              </head>
              <body>
                <img src="/logo.png">
                <a class="itemurl">URL: https://mek.oszk.hu/05500/05585</a>
              </body>
            </html>
        """,
    )

    response = parse_record(page)

    assert response.cover_url == "https://mek.oszk.hu/05500/05585/meta.jpg"
