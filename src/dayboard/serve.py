"""웹 서버 진입점: server.toml에서 host/port 읽고 waitress로 서빙."""

import argparse
import os
import tomllib

import waitress

from . import config
from .server.access_log import AccessLog
from .server.app import create_app


def _load_web_service():
    c = config.load()
    host, port = "0.0.0.0", c.port
    pidfile = config.DATA_DIR / "dayboard.pid"
    server_toml = config.PROJECT_ROOT / "server.toml"
    if server_toml.exists():
        data = tomllib.loads(server_toml.read_text(encoding="utf-8"))
        for svc in data.get("service", []):
            if svc.get("type") == "web":
                host = svc.get("host", host)
                port = int(svc.get("port", port))
                pidfile = config.PROJECT_ROOT / svc.get("pidfile", "data/dayboard.pid")
                break
    return host, port, pidfile


def main(argv=None):
    h, p, pidfile = _load_web_service()
    ap = argparse.ArgumentParser()
    ap.add_argument("--host", default=h)
    ap.add_argument("--port", type=int, default=p)
    args = ap.parse_args(argv)

    config.ensure_runtime_dirs()
    pidfile.write_text(str(os.getpid()), encoding="utf-8")
    app = create_app()
    print(f"dayboard serving on http://{args.host}:{args.port}", flush=True)
    waitress.serve(AccessLog(app), host=args.host, port=args.port)


if __name__ == "__main__":
    main()
