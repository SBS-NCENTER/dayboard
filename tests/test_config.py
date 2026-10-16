from dayboard import config


def test_load_defaults_when_missing(tmp_path, monkeypatch):
    monkeypatch.setattr(config, "CONFIG_TOML", tmp_path / "nope.toml")
    c = config.load()
    assert c.lat == 37.57 and c.lon == 126.98 and c.label == "서울"
    assert c.tz == "Asia/Seoul" and c.port == 20000 and c.cache_ttl == 600


def test_load_from_file(tmp_path, monkeypatch):
    p = tmp_path / "config.toml"
    p.write_text(
        '[location]\nlat=35.1\nlon=129.0\nlabel="부산"\ntz="Asia/Seoul"\n'
        "[server]\nport=20001\n[weather]\ncache_ttl=30\n",
        encoding="utf-8",
    )
    monkeypatch.setattr(config, "CONFIG_TOML", p)
    c = config.load()
    assert c.lat == 35.1 and c.label == "부산" and c.port == 20001 and c.cache_ttl == 30
    assert c.lon == 129.0 and c.tz == "Asia/Seoul"
