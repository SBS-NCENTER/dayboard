"""요청당 access log 1줄 stdout emit (NCCP: `<ip> "<method> <path>" <status>`)."""


class AccessLog:
    def __init__(self, app):
        self.app = app

    def __call__(self, environ, start_response):
        ip = environ.get("REMOTE_ADDR", "-")
        method = environ.get("REQUEST_METHOD", "-")
        path = environ.get("PATH_INFO", "-")

        def _sr(status, headers, exc_info=None):
            print(f'{ip} "{method} {path}" {status.split(" ", 1)[0]}', flush=True)
            return start_response(status, headers, exc_info)

        return self.app(environ, _sr)
