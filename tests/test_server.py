import pytest

from mek_mcp.server import SERVER_NAME, create_server


def test_create_server_has_expected_name() -> None:
    server = create_server()

    assert server.name == SERVER_NAME


@pytest.mark.anyio
async def test_create_server_registers_tools() -> None:
    server = create_server()

    tools = await server.list_tools()
    tool_names = {tool.name for tool in tools}

    assert "mek_simple_search" in tool_names
    assert "mek_full_text_search" in tool_names
    assert "mek_advanced_search" in tool_names
    assert "mek_browse_index" in tool_names
    assert "mek_get_record" in tool_names
