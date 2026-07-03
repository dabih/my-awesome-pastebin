import json
import logging
import os

import psycopg2
from confluent_kafka import Consumer, KafkaError


logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)

DATABASE_URL = os.environ.get("DATABASE_URL", "postgresql://pastebin:pastebin@localhost:5432/pastebin")
KAFKA_BOOTSTRAP_SERVERS = os.environ.get("KAFKA_BOOTSTRAP_SERVERS", "localhost:9092")
KAFKA_GROUP_ID = os.environ.get("KAFKA_GROUP_ID", "pastebin-consumer-group")
KAFKA_TOPIC = os.environ.get("KAFKA_TOPIC_PASTE_VIEWS", "paste_views")
BATCH_SIZE = int(os.environ.get("CONSUMER_BATCH_SIZE", "100"))
POLL_TIMEOUT = float(os.environ.get("CONSUMER_POLL_TIMEOUT", "1.0"))


def parse_dsn(url: str) -> dict:
    from urllib.parse import urlparse

    parsed = urlparse(url)
    return {
        "host": parsed.hostname,
        "port": parsed.port or 5432,
        "dbname": parsed.path.lstrip("/"),
        "user": parsed.username,
        "password": parsed.password,
    }


def ensure_idempotency_table(conn) -> None:
    with conn.cursor() as cur:
        cur.execute(
            "CREATE TABLE IF NOT EXISTS processed_idempotency_keys (key VARCHAR(36) PRIMARY KEY, created_at TIMESTAMP DEFAULT NOW())"
        )
    conn.commit()


def process_batch(batch: list[dict], conn) -> None:
    if not batch:
        return

    events_by_key: dict[str, str] = {}
    for event in batch:
        key = event.get("idempotency_key")
        paste_uid = event.get("paste_uid")
        if key and paste_uid and key not in events_by_key:
            events_by_key[key] = paste_uid

    if not events_by_key:
        return

    with conn.cursor() as cur:
        all_keys = list(events_by_key.keys())
        cur.execute("SELECT key FROM processed_idempotency_keys WHERE key = ANY(%s)", (all_keys,))
        already_processed = {row[0] for row in cur.fetchall()}

        new_events = {k: uid for k, uid in events_by_key.items() if k not in already_processed}
        if not new_events:
            conn.commit()
            return

        increments: dict[str, int] = {}
        for paste_uid in new_events.values():
            increments[paste_uid] = increments.get(paste_uid, 0) + 1

        for paste_uid, count in increments.items():
            cur.execute(
                "UPDATE pastes_visitcount SET count = count + %s, last_updated = NOW() "
                "FROM pastes_paste WHERE pastes_visitcount.paste_id = pastes_paste.id "
                "AND pastes_paste.uid = %s",
                (count, paste_uid),
            )

        for key in new_events:
            cur.execute(
                "INSERT INTO processed_idempotency_keys (key) VALUES (%s) ON CONFLICT DO NOTHING",
                (key,),
            )

    conn.commit()
    logger.info("Processed batch: %d events, %d new, %d unique pastes", len(batch), len(new_events), len(increments))


def main() -> None:
    consumer = Consumer(
        {
            "bootstrap.servers": KAFKA_BOOTSTRAP_SERVERS,
            "group.id": KAFKA_GROUP_ID,
            "auto.offset.reset": "earliest",
            "enable.auto.commit": False,
        }
    )
    consumer.subscribe([KAFKA_TOPIC])

    dsn = parse_dsn(DATABASE_URL)
    conn = psycopg2.connect(**dsn)
    conn.autocommit = False
    ensure_idempotency_table(conn)

    logger.info("Consumer started, listening on topic '%s'", KAFKA_TOPIC)

    try:
        batch: list[dict] = []
        while True:
            msg = consumer.poll(POLL_TIMEOUT)
            if msg is None:
                if batch:
                    process_batch(batch, conn)
                    consumer.commit()
                    batch = []
                continue

            if msg.error():
                if msg.error().code() == KafkaError._PARTITION_EOF:  # pylint: disable=protected-access
                    continue
                logger.error("Kafka error: %s", msg.error())
                continue

            try:
                event = json.loads(msg.value().decode())
                batch.append(event)
            except (json.JSONDecodeError, UnicodeDecodeError):
                logger.warning("Skipping malformed message")
                continue

            if len(batch) >= BATCH_SIZE:
                process_batch(batch, conn)
                consumer.commit()
                batch = []
    except KeyboardInterrupt:
        logger.info("Shutting down")
    finally:
        if batch:
            try:
                process_batch(batch, conn)
                consumer.commit()
            except (psycopg2.Error, OSError):
                logger.exception("Failed to process final batch")
        consumer.close()
        conn.close()


if __name__ == "__main__":
    main()
