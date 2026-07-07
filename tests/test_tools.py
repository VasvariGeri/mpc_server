import pytest
from mcp.server.fastmcp import FastMCP

from mek_mcp.schemas import (
    AdvancedSearchQuery,
    FullTextSearchQuery,
    IndexBrowseQuery,
    MekPage,
    SimpleSearchQuery,
)
from mek_mcp.tools import register_tools


class FakeMekClient:
    last_query: SimpleSearchQuery | None = None
    last_full_text_query: FullTextSearchQuery | None = None
    last_advanced_query: AdvancedSearchQuery | None = None
    last_index_query: IndexBrowseQuery | None = None

    def __enter__(self) -> "FakeMekClient":
        return self

    def __exit__(self, *args: object) -> None:
        return None

    def fetch_simple_search(self, query: SimpleSearchQuery) -> MekPage:
        self.last_query = query
        return MekPage(
            url="https://mek.oszk.hu/hu/search/elfull/",
            status_code=200,
            html="""
            <html>
              <body>
                <h4 class="numberofhits">Találatok száma: 1</h4>
                <div class="hit">
                  <a class="etitem" href="https://mek.oszk.hu/01000/01006">
                    <div class="dcauthor">Petőfi Sándor</div>
                    <div class="dctitle">Petőfi Sándor összes költeményei</div>
                  </a>
                </div>
              </body>
            </html>
            """,
        )

    def fetch_full_text_search(self, query: FullTextSearchQuery) -> MekPage:
        self.last_full_text_query = query
        return MekPage(
            url="https://mek.oszk.hu/hu/search/elfulltext/",
            status_code=200,
            html="""
            <html>
              <body>
                <h4 class="numberofhits">Találatok száma 13175</h4>
                <div class="hit">
                  <a class="etitem" href="https://mek.oszk.hu/05500/05585">
                    <div class="dcauthor">Jókai Mór</div>
                    <div class="dctitle">A kőszívű ember fiai</div>
                    <div class="foundtext">
                      <span class="marked">Duna</span> folyama
                    </div>
                  </a>
                  <a class="mekfound" href="/05500/05585/html/hit.html">
                    Találat helye
                  </a>
                </div>
              </body>
            </html>
            """,
        )

    def fetch_advanced_search(self, query: AdvancedSearchQuery) -> MekPage:
        self.last_advanced_query = query
        return MekPage(
            url="https://mek.oszk.hu/katalog/kataluj.php3",
            status_code=200,
            html="""
            <html>
              <body>
                <div class="numberofhits">A találatok száma: 165</div>
                <div class="hit">
                  <form action="/00700/00798/index.phtml">
                    <b>
                      <a href="Javascript:document.fn00095.submit();">
                        Jókai Mór:&nbsp;Az arany ember
                      </a>
                    </b>
                    <br>
                    <span class="allis">
                      <a href="Javascript:document.fn00095.submit();">
                        https://mek.oszk.hu/00700/00798
                      </a>
                    </span>
                  </form>
                </div>
              </body>
            </html>
            """,
        )

    def fetch_index_browse(self, query: IndexBrowseQuery) -> MekPage:
        self.last_index_query = query
        return MekPage(
            url="https://mek.oszk.hu/katalog/browsuj.php3",
            status_code=200,
            html="""
            <html>
              <body>
                <select name="indexv">
                  <font>
                    <b><a href="#">A találatok száma:</a>177</b>
                  </font>
                  <option value="magyar néprajz">magyar néprajz</option>
                  <option value="néprajz">néprajz</option>
                  <option value="néprajzi kutatás">néprajzi kutatás</option>
                </select>
              </body>
            </html>
            """,
        )


@pytest.mark.anyio
async def test_simple_search_tool_returns_parsed_results() -> None:
    server = FastMCP("test")
    fake_client = FakeMekClient()
    register_tools(server, client_factory=lambda: fake_client)

    _, structured = await server.call_tool(
        "mek_simple_search",
        {"creator": "Petőfi", "limit": 10},
    )

    assert fake_client.last_query is not None
    assert fake_client.last_query.creator == "Petőfi"
    assert structured["kind"] == "simple"
    assert structured["total_results"] == 1
    assert structured["results"][0]["title"] == "Petőfi Sándor összes költeményei"
    assert structured["results"][0]["authors"] == ["Petőfi Sándor"]


@pytest.mark.anyio
async def test_full_text_search_tool_returns_snippets() -> None:
    server = FastMCP("test")
    fake_client = FakeMekClient()
    register_tools(server, client_factory=lambda: fake_client)

    _, structured = await server.call_tool(
        "mek_full_text_search",
        {
            "query": "Duna",
            "broadtopic": "humán területek, kultúra, irodalom",
            "limit": 10,
        },
    )

    assert fake_client.last_full_text_query is not None
    assert fake_client.last_full_text_query.query == "Duna"
    assert (
        fake_client.last_full_text_query.broadtopic
        == "humán területek, kultúra, irodalom"
    )
    assert structured["kind"] == "full_text"
    assert structured["total_results"] == 13175
    assert structured["results"][0]["title"] == "A kőszívű ember fiai"
    assert structured["results"][0]["snippet"] == "Duna folyama"
    assert (
        structured["results"][0]["found_url"]
        == "https://mek.oszk.hu/05500/05585/html/hit.html"
    )


@pytest.mark.anyio
async def test_advanced_search_tool_returns_old_catalog_results() -> None:
    server = FastMCP("test")
    fake_client = FakeMekClient()
    register_tools(server, client_factory=lambda: fake_client)

    _, structured = await server.call_tool(
        "mek_advanced_search",
        {
            "conditions": [
                {
                    "field": "dc_creator_o FamilyGivenName",
                    "value": "Jókai",
                    "operator_after": "and",
                },
                {
                    "field": "dc_title main",
                    "value": "arany*",
                },
            ],
            "accentless": True,
        },
    )

    assert fake_client.last_advanced_query is not None
    assert len(fake_client.last_advanced_query.conditions) == 2
    assert fake_client.last_advanced_query.accentless is True
    assert structured["kind"] == "advanced"
    assert structured["total_results"] == 165
    assert structured["results"][0]["title"] == "Az arany ember"
    assert structured["results"][0]["authors"] == ["Jókai Mór"]
    assert structured["results"][0]["url"] == "https://mek.oszk.hu/00700/00798"


@pytest.mark.anyio
async def test_browse_index_tool_returns_controlled_values() -> None:
    server = FastMCP("test")
    fake_client = FakeMekClient()
    register_tools(server, client_factory=lambda: fake_client)

    _, structured = await server.call_tool(
        "mek_browse_index",
        {
            "field": "dc_subject keyword",
            "prefix": "nep",
            "limit": 2,
        },
    )

    assert fake_client.last_index_query is not None
    assert fake_client.last_index_query.field == "dc_subject keyword"
    assert fake_client.last_index_query.prefix == "nep"
    assert structured["kind"] == "index"
    assert structured["total_results"] == 177
    assert [entry["value"] for entry in structured["entries"]] == [
        "magyar néprajz",
        "néprajz",
    ]


@pytest.mark.anyio
async def test_registered_server_lists_search_tools() -> None:
    server = FastMCP("test")
    register_tools(server, client_factory=FakeMekClient)

    tools = await server.list_tools()
    tools_by_name = {tool.name: tool for tool in tools}

    assert set(tools_by_name) == {
        "mek_simple_search",
        "mek_full_text_search",
        "mek_advanced_search",
        "mek_browse_index",
    }

    simple_tool = tools_by_name["mek_simple_search"]
    assert "title" in simple_tool.inputSchema["properties"]
    assert "subject" in simple_tool.inputSchema["properties"]
    assert "creator" in simple_tool.inputSchema["properties"]
    assert "mek_id" in simple_tool.inputSchema["properties"]

    full_text_tool = tools_by_name["mek_full_text_search"]
    assert "query" in full_text_tool.inputSchema["properties"]
    assert "broadtopic" in full_text_tool.inputSchema["properties"]

    advanced_tool = tools_by_name["mek_advanced_search"]
    assert "conditions" in advanced_tool.inputSchema["properties"]
    assert "sort" in advanced_tool.inputSchema["properties"]

    browse_tool = tools_by_name["mek_browse_index"]
    assert "field" in browse_tool.inputSchema["properties"]
    assert "prefix" in browse_tool.inputSchema["properties"]
