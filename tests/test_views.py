from dayboard.server.app import create_app


def test_health_ok():
    c = create_app().test_client()
    r = c.get("/health")
    assert r.status_code == 200 and r.get_json() == {"status": "ok"}


def test_index_served():
    c = create_app().test_client()
    r = c.get("/")
    assert r.status_code == 200
    assert b"dayboard" in r.data.lower()   # index.html에 마커
