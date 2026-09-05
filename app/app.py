import os

from flask import Flask

app = Flask(__name__)


@app.route("/")
def home():
    return "DevSecOps application is running!"


@app.route("/health")
def health():
    return {"status": "healthy"}


if __name__ == "__main__":
    host = os.getenv("HOST", "0.0.0.0")  # nosec B104
    app.run(host=host, port=5001)