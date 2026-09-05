import os

from flask import Flask

app = Flask(__name__)

@app.after_request
def add_security_headers(response):
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-Content-Type-Options"] = "nosniff"

    response.headers["Content-Security-Policy"] = (
        "default-src 'self'; "
        "script-src 'self'; "
        "style-src 'self' 'unsafe-inline'; "
        "img-src 'self' data:; "
        "font-src 'self' data:; "
        "connect-src 'self'; "
        "object-src 'none'; "
        "base-uri 'self'; "
        "form-action 'self'; "
        "frame-ancestors 'none'; "
        "media-src 'self'; "
        "manifest-src 'self'; "
        "worker-src 'self';"
    )

    response.headers["Permissions-Policy"] = (
        "camera=(), microphone=(), geolocation=(), "
        "payment=(), usb=()"
    )

    response.headers["Cross-Origin-Embedder-Policy"] = "require-corp"
    response.headers["Cross-Origin-Opener-Policy"] = "same-origin"
    response.headers["Cross-Origin-Resource-Policy"] = "same-origin"

    response.headers["Cache-Control"] = (
        "no-store, no-cache, must-revalidate, max-age=0"
    )
    response.headers["Pragma"] = "no-cache"
    response.headers["Expires"] = "0"

    response.headers.pop("Server", None)

    return response


@app.route("/")
def home():
    return "DevSecOps application is running!"


@app.route("/health")
def health():
    return {"status": "healthy"}


if __name__ == "__main__":
    host = os.getenv("HOST", "0.0.0.0")  # nosec B104
    app.run(host=host, port=5001)

