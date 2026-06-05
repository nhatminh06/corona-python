from flask import Flask, jsonify
import os
import time
import uuid
import requests

app = Flask(__name__)

START_TIME = time.time()
VERSION = os.getenv("APP_VERSION", "dev")


@app.route("/")
def hello():
    return jsonify({
        "service": "corona-python",
        "requestID": str(uuid.uuid4()),
        "message": "hello from the Python service",
        "requestsVersion": requests.__version__
    })


@app.route("/version")
def version():
    return jsonify({
        "version": VERSION,
        "uptimeSec": int(time.time() - START_TIME)
    })


@app.route("/health")
def health():
    return "ok\n", 200


if __name__ == "__main__":
    port = int(os.getenv("PORT", "8080"))
    app.run(host="0.0.0.0", port=port)
