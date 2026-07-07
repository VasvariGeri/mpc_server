import pytest
from mcp.server.fastmcp import FastMCP

from mek_mcp.schemas import FullTextSearchQuery, MekPage, SimpleSearchQuery
from mek_mcp.tools import register_tools


class FakeMekClient:
    last_query: SimpleSearchQuery | None = None
    last_full_text_query: FullTextSearchQuery | None = None

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
async def test_registered_server_lists_search_tools() -> None:
    server = FastMCP("test")
    register_tools(server, client_factory=FakeMekClient)

    tools = await server.list_tools()
    tool_names = [tool.name for tool in tools]

    assert tool_names == ["mek_simple_search", "mek_full_text_search"]

    simple_tool = tools[0]
    assert "title" in simple_tool.inputSchema["properties"]
    assert "subject" in simple_tool.inputSchema["properties"]
    assert "creator" in simple_tool.inputSchema["properties"]
    assert "mek_id" in simple_tool.inputSchema["properties"]

    full_text_tool = tools[1]
    assert "query" in full_text_tool.inputSchema["properties"]
    assert "broadtopic" in full_text_tool.inputSchema["properties"]
