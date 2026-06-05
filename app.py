import os
import time
import uuid
from fastapi import FastAPI

app = FastAPI()
VERSION = os.getenv("APP_VERSION", "dev")
START_TIME = time.time()


def read_secret_file(path: str) -> dict:
    secrets = {}
    try:
        with open(path) as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith("#"):
                    continue
                if "=" in line:
                    key, value = line.split("=", 1)
                    secrets[key.strip()] = value.strip()
    except FileNotFoundError:
        pass
    return secrets


@app.get("/")
def hello():
    secrets = read_secret_file("/vault/secrets/app-creds")
    return {
        "service": "corona-python",
        "requestID": str(uuid.uuid4()),
        "message": "hello from the Python service",
        "secretsLoaded": {
            "apiKey": bool(secrets.get("apiKey")),
            "externalToken": bool(secrets.get("externalServiceToken")),
        },
    }


@app.get("/version")
def version():
    return {
        "version": VERSION,
        "uptimeSec": int(time.time() - START_TIME),
    }


@app.get("/health")
def health():
    return "ok"
