from dayboard.server.access_log import AccessLog


def _run(environ, capsys):
    def inner(env, sr):
        sr("200 OK", [("Content-Type", "text/plain")])
        return [b"ok"]

    body = b"".join(AccessLog(inner)(environ, lambda *a, **k: None))
    assert body == b"ok"
    return capsys.readouterr().out.strip()


def test_logs_ip_method_path_status(capsys):
    env = {
        "REMOTE_ADDR": "10.10.204.211",
        "REQUEST_METHOD": "GET",
        "PATH_INFO": "/api/data",
    }
    assert _run(env, capsys) == '10.10.204.211 "GET /api/data" 200'


def test_missing_remote_addr_dash(capsys):
    env = {"REQUEST_METHOD": "GET", "PATH_INFO": "/health"}
    assert _run(env, capsys) == '- "GET /health" 200'
