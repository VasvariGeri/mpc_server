import pytest
from mcp.server.fastmcp import FastMCP

from mek_mcp.schemas import MekPage, SimpleSearchQuery
from mek_mcp.tools import register_tools


class FakeMekClient:
    last_query: SimpleSearchQuery | None = None

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
async def test_registered_server_lists_simple_search_tool() -> None:
    server = FastMCP("test")
    register_tools(server, client_factory=FakeMekClient)

    tools = await server.list_tools()

    assert [tool.name for tool in tools] == ["mek_simple_search"]
    assert "title" in tools[0].inputSchema["properties"]
    assert "subject" in tools[0].inputSchema["properties"]
    assert "creator" in tools[0].inputSchema["properties"]
    assert "mek_id" in tools[0].inputSchema["properties"]
