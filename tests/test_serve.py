from dayboard import serve


def test_load_web_service_reads_server_toml():
    _host, port, pidfile = serve._load_web_service()
    assert port == 20000  # server.toml
    assert str(pidfile).endswith("data/dayboard.pid")
