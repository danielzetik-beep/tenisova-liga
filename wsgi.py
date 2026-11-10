import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import init_db, route

init_db()


def application(environ, start_response):
    method = environ.get("REQUEST_METHOD", "GET")
    path = environ.get("PATH_INFO", "/") or "/"
    data = {}
    if method == "POST":
        try:
            length = int(environ.get("CONTENT_LENGTH") or 0)
        except ValueError:
            length = 0
        raw = environ["wsgi.input"].read(length) if length else b""
        try:
            data = json.loads(raw.decode("utf-8")) if raw else {}
        except Exception:
            status, payload, ct = 400, {"error": "Špatný požadavek"}, None
            body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
            start_response("400 Bad Request", [
                ("Content-Type", "application/json; charset=utf-8"),
                ("Content-Length", str(len(body))),
            ])
            return [body]
    status, payload, ct = route(method, path, data)
    if ct is None:
        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        ct = "application/json; charset=utf-8"
    else:
        body = payload
    reasons = {200: "OK", 400: "Bad Request", 403: "Forbidden", 404: "Not Found"}
    start_response(f"{status} {reasons.get(status, 'OK')}", [
        ("Content-Type", ct),
        ("Content-Length", str(len(body))),
    ])
    return [body]
