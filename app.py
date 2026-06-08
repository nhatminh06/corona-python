import os
import time
import uuid
import threading
import logging
from collections import deque
from fastapi import FastAPI

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI()
VERSION = os.getenv("APP_VERSION", "dev")
START_TIME = time.time()

events = deque(maxlen=100)
event_count = 0
events_lock = threading.Lock()


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


def start_kafka_consumer():
    global event_count
    broker = os.getenv("KAFKA_BROKER", "kafka-external.messaging.svc.cluster.local:9092")
    topic = os.getenv("KAFKA_TOPIC", "corona-events")

    try:
        from kafka import KafkaConsumer
        consumer = KafkaConsumer(
            topic,
            bootstrap_servers=[broker],
            group_id="corona-python-group",
            auto_offset_reset="earliest",
            value_deserializer=lambda m: m.decode("utf-8"),
        )
        logger.info(f"Kafka consumer started: broker={broker} topic={topic}")
        for message in consumer:
            msg = f"[{time.strftime('%Y-%m-%dT%H:%M:%S')}] {message.value}"
            logger.info(f"Kafka event received: {msg}")
            with events_lock:
                events.appendleft(msg)
                event_count += 1
    except Exception as e:
        logger.warning(f"Kafka consumer error: {e} — running without Kafka")


def start_redis_listener():
    addr = os.getenv("REDIS_ADDR", "redis.messaging.svc.cluster.local:6379")
    try:
        import redis
        r = redis.Redis.from_url(f"redis://{addr}")
        r.ping()
        logger.info(f"Redis connected: {addr}")
        pubsub = r.pubsub()
        pubsub.subscribe("corona-notifications")
        for message in pubsub.listen():
            if message["type"] == "message":
                msg = f"[redis] {message['data'].decode()}"
                logger.info(msg)
                with events_lock:
                    events.appendleft(msg)
    except Exception as e:
        logger.warning(f"Redis listener error: {e} — running without Redis")


@app.on_event("startup")
async def startup():
    threading.Thread(target=start_kafka_consumer, daemon=True).start()
    threading.Thread(target=start_redis_listener, daemon=True).start()


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


@app.get("/events")
def get_events():
    with events_lock:
        return {
            "service": "corona-python",
            "eventCount": event_count,
            "recentEvents": list(events),
        }


@app.get("/events/count")
def get_event_count():
    with events_lock:
        return {
            "service": "corona-python",
            "count": event_count,
        }
