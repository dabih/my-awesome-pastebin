import os


DATABASE_URL = os.environ.get("DATABASE_URL", "postgresql://pastebin:pastebin@localhost:5432/pastebin")
REDIS_URL = os.environ.get("REDIS_URL", "redis://localhost:6379/0")
KAFKA_BOOTSTRAP_SERVERS = os.environ.get("KAFKA_BOOTSTRAP_SERVERS", "localhost:9092")
KAFKA_TOPIC_PASTE_VIEWS = os.environ.get("KAFKA_TOPIC_PASTE_VIEWS", "paste_views")
IDEMPOTENCY_KEY_TTL_SECONDS = int(os.environ.get("IDEMPOTENCY_KEY_TTL_SECONDS", "300"))
