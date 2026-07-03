import json
import logging

from confluent_kafka import Producer

from .config import KAFKA_BOOTSTRAP_SERVERS, KAFKA_TOPIC_PASTE_VIEWS


logger = logging.getLogger(__name__)

_producer: Producer | None = None


def get_producer() -> Producer:
    global _producer
    if _producer is None:
        _producer = Producer({"bootstrap.servers": KAFKA_BOOTSTRAP_SERVERS})
    return _producer


def publish_view_event(paste_uid: str, idempotency_key: str) -> None:
    producer = get_producer()
    message = json.dumps({"paste_uid": paste_uid, "idempotency_key": idempotency_key})
    producer.produce(KAFKA_TOPIC_PASTE_VIEWS, value=message.encode())
    producer.flush()
