import os
import sys
import traceback

# Ensure root directory is on Python path
root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if root_dir not in sys.path:
    sys.path.insert(0, root_dir)

app_import_error = None
try:
    from app.main import app as fastapi_app
except Exception:
    app_import_error = traceback.format_exc()
    fastapi_app = None


async def app(scope, receive, send):
    if app_import_error:
        if scope.get("type") == "http":
            body = (
                f"<html><body style='font-family:sans-serif;padding:40px;background:#111;color:#eee;'>"
                f"<h2 style='color:#f87171;'>FastAPI Startup Import Error:</h2>"
                f"<pre style='background:#222;padding:20px;border-radius:8px;overflow:auto;color:#fca5a5;'>{app_import_error}</pre>"
                f"</body></html>"
            ).encode("utf-8")
            await send({
                "type": "http.response.start",
                "status": 500,
                "headers": [
                    (b"content-type", b"text/html; charset=utf-8"),
                    (b"content-length", str(len(body)).encode("ascii")),
                ],
            })
            await send({
                "type": "http.response.body",
                "body": body,
            })
        return

    try:
        await fastapi_app(scope, receive, send)
    except Exception:
        err = traceback.format_exc()
        if scope.get("type") == "http":
            body = (
                f"<html><body style='font-family:sans-serif;padding:40px;background:#111;color:#eee;'>"
                f"<h2 style='color:#f87171;'>FastAPI Request Error:</h2>"
                f"<pre style='background:#222;padding:20px;border-radius:8px;overflow:auto;color:#fca5a5;'>{err}</pre>"
                f"</body></html>"
            ).encode("utf-8")
            await send({
                "type": "http.response.start",
                "status": 500,
                "headers": [
                    (b"content-type", b"text/html; charset=utf-8"),
                    (b"content-length", str(len(body)).encode("ascii")),
                ],
            })
            await send({
                "type": "http.response.body",
                "body": body,
            })
