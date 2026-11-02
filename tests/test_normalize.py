from yapi_mcp.normalize import flatten_menu, normalize_interface, search_index


def test_flatten_and_search():
    menu = [
        {
            "_id": 1,
            "name": "用户",
            "list": [
                {
                    "_id": 10,
                    "title": "登录",
                    "path": "/api/user/login",
                    "method": "POST",
                    "project_id": 529,
                },
                {
                    "_id": 11,
                    "title": "资料",
                    "path": "/api/user/profile",
                    "method": "GET",
                    "project_id": 529,
                },
            ],
        }
    ]
    rows = flatten_menu(menu)
    assert len(rows) == 2
    hits = search_index(rows, keyword="login", method="POST")
    assert len(hits) == 1
    assert hits[0]["id"] == 10


def test_normalize_interface_json_bodies():
    raw = {
        "_id": 10,
        "project_id": 529,
        "title": "登录",
        "path": "/api/user/login",
        "method": "POST",
        "req_body_type": "json",
        "req_body_other": '{"type":"object","properties":{"username":{"type":"string"}}}',
        "res_body_type": "json",
        "res_body": '{"code":0,"data":{}}',
        "req_query": [{"name": "lang", "required": "0", "example": "zh", "desc": ""}],
        "req_headers": [],
        "req_params": [],
        "req_body_form": [],
    }
    doc = normalize_interface(raw)
    assert doc["method"] == "POST"
    assert doc["request"]["body"]["type"] == "object"
    assert doc["response"]["body"]["code"] == 0
