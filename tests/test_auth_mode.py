from yapi_mcp.client import detect_auth_mode


def test_session_jwt():
    # Synthetic JWT payload only — not a real credential.
    token = (
        "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9."
        "eyJ1aWQiOjQyLCJpYXQiOjEsImV4cCI6Mn0."
        "sig"
    )
    mode, uid = detect_auth_mode(token)
    assert mode == "session"
    assert uid == 42


def test_open_token():
    mode, uid = detect_auth_mode("plain-project-token")
    assert mode == "open"
    assert uid is None
