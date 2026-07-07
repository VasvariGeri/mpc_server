from mek_mcp.server import SERVER_NAME, create_server


def test_create_server_has_expected_name() -> None:
    server = create_server()

    assert server.name == SERVER_NAME
