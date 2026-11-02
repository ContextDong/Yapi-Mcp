from yapi_mcp.url_parser import parse_yapi_url


def test_project_list_url():
    parts = parse_yapi_url("https://yapi.example.com/project/123/interface/api/")
    assert parts.base_url == "https://yapi.example.com"
    assert parts.project_id == 123
    assert parts.interface_id is None


def test_interface_detail_url():
    parts = parse_yapi_url("https://yapi.example.com/project/123/interface/api/456")
    assert parts.project_id == 123
    assert parts.interface_id == 456


def test_base_only():
    parts = parse_yapi_url("https://yapi.example.com")
    assert parts.base_url == "https://yapi.example.com"
    assert parts.project_id is None
