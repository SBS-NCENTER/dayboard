# ARCHITECTURE.md — the codemap

What is where, and what may depend on what. A map of the present: a change
rewrites the cell it touches.

```text
a browser on the office network ──► http://ts5-server:20000/   (waitress, ncenter)
                                            │
ts5-server, /opt/dayboard                   ▼
┌───────────────────────────────────────────────────────────────────────────┐
│ src/dayboard/                                                             │
│   serve.py          the entry point: server.toml → host, port; waitress   │
│   server/           Flask: routes (api, views), the page's templates and  │
│                     static files                                          │
│   config.py         the settings SSOT (config.toml, server.toml, paths)   │
│   calendar_data.py  the month grid and Korean holidays (offline)          │
│   astro.py          sun, moon and curated sky events (astral, offline)    │
│   weather.py        Open-Meteo, the one place the network is reached, TTL │
│                     cache                                                 │
│   hidden_events.py  the hidden sky events, persisted in data/             │
└───────────────────────────────────────────────────────────────────────────┘
```

| Directory | Holds | Depends on |
| --- | --- | --- |
| `src/dayboard/` | the package above, its unit tests under `tests/` | flask, waitress, requests, astral, holidays |
| `setup/` | `run.sh` (the entry point), `install.sh` (`uv sync`), `firewall.sh`, the systemd unit | ts5-server |
| `config.toml`, `server.toml` | the runtime settings and the server-manager manifest | — |
| `data/` | runtime files: the pid, the hidden events; never tracked | — |
| `doc/` | the designs in force, the plans | — |
| `scripts/`, `.claude/`, `roles/`, `git-hooks/` | the harness and the check | `chun-harness`, their source |
