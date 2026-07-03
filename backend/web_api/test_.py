from datetime import datetime, timedelta, timezone
from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session, sessionmaker

from src.config import DATABASE_URL
from src.database import get_db
from src.main import app
from src.models import Category, Paste


@pytest.fixture(scope="session")
def engine():
    return create_engine(DATABASE_URL)


@pytest.fixture(autouse=True)
def clean_tables(engine):
    with engine.connect() as conn:
        conn.execute(text("TRUNCATE pastes_visitcount, pastes_paste, pastes_category RESTART IDENTITY CASCADE"))
        conn.commit()


@pytest.fixture
def db(engine):
    session = Session(engine)
    try:
        yield session
    finally:
        session.close()


@pytest.fixture
def client(db):
    def override_get_db():
        yield db

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()


@pytest.fixture
def category(db):
    cat = Category(name="Python", created_at=datetime.now(timezone.utc))
    db.add(cat)
    db.commit()
    db.refresh(cat)
    return cat


def make_paste(client, category_id, **kwargs):
    payload = {"title": "Test", "category_id": category_id, "raw_data": "content", **kwargs}
    return client.post("/pastes", json=payload)


# --- GET /categories ---

def test_list_categories_empty(client):
    response = client.get("/categories")
    assert response.status_code == 200
    assert response.json() == []


def test_list_categories(client, category):
    response = client.get("/categories")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["name"] == "Python"


# --- POST /pastes ---

@patch("src.main.publish_view_event")
@patch("src.main.redis_client")
def test_create_paste_returns_uid(mock_redis, mock_kafka, client, category):
    response = make_paste(client, category.id)
    assert response.status_code == 201
    data = response.json()
    assert "uid" in data
    assert len(data["uid"]) == 21


@patch("src.main.publish_view_event")
@patch("src.main.redis_client")
def test_create_paste_invalid_category(mock_redis, mock_kafka, client):
    response = make_paste(client, 9999)
    assert response.status_code == 404


# --- GET /pastes/{uid} ---

@patch("src.main.publish_view_event")
@patch("src.main.redis_client")
def test_get_paste_success(mock_redis, mock_kafka, client, category):
    mock_redis.set.return_value = True
    uid = make_paste(client, category.id, title="Hello", raw_data="world").json()["uid"]

    response = client.get(f"/pastes/{uid}")
    assert response.status_code == 200
    data = response.json()
    assert data["title"] == "Hello"
    assert data["raw_data"] == "world"


@patch("src.main.publish_view_event")
@patch("src.main.redis_client")
def test_get_paste_publishes_kafka_event(mock_redis, mock_kafka, client, category):
    mock_redis.set.return_value = True
    uid = make_paste(client, category.id).json()["uid"]

    client.get(f"/pastes/{uid}")
    mock_kafka.assert_called_once()


@patch("src.main.publish_view_event")
@patch("src.main.redis_client")
def test_get_paste_skips_kafka_on_duplicate_key(mock_redis, mock_kafka, client, category):
    mock_redis.set.return_value = None
    uid = make_paste(client, category.id).json()["uid"]

    client.get(f"/pastes/{uid}")
    mock_kafka.assert_not_called()


def test_get_paste_not_found(client):
    response = client.get("/pastes/doesnotexist1234567")
    assert response.status_code == 404


@patch("src.main.publish_view_event")
@patch("src.main.redis_client")
def test_get_paste_wrong_password(mock_redis, mock_kafka, client, category):
    uid = make_paste(client, category.id, password="secret").json()["uid"]
    response = client.get(f"/pastes/{uid}?password=wrong")
    assert response.status_code == 403


@patch("src.main.publish_view_event")
@patch("src.main.redis_client")
def test_get_paste_missing_password(mock_redis, mock_kafka, client, category):
    uid = make_paste(client, category.id, password="secret").json()["uid"]
    response = client.get(f"/pastes/{uid}")
    assert response.status_code == 403


@patch("src.main.publish_view_event")
@patch("src.main.redis_client")
def test_get_paste_correct_password(mock_redis, mock_kafka, client, category):
    mock_redis.set.return_value = True
    uid = make_paste(client, category.id, password="secret").json()["uid"]
    response = client.get(f"/pastes/{uid}?password=secret")
    assert response.status_code == 200


@patch("src.main.publish_view_event")
@patch("src.main.redis_client")
def test_burn_after_read(mock_redis, mock_kafka, client, category):
    mock_redis.set.return_value = True
    uid = make_paste(client, category.id, burn_after_read=True).json()["uid"]

    assert client.get(f"/pastes/{uid}").status_code == 200
    assert client.get(f"/pastes/{uid}").status_code == 404


@patch("src.main.publish_view_event")
@patch("src.main.redis_client")
def test_expired_paste_returns_404(mock_redis, mock_kafka, client, category):
    past = (datetime.now(timezone.utc) - timedelta(hours=1)).isoformat()
    uid = make_paste(client, category.id, expiration_datetime=past).json()["uid"]
    assert client.get(f"/pastes/{uid}").status_code == 404


@patch("src.main.publish_view_event")
@patch("src.main.redis_client")
def test_not_expired_paste_returns_200(mock_redis, mock_kafka, client, category):
    mock_redis.set.return_value = True
    future = (datetime.now(timezone.utc) + timedelta(hours=1)).isoformat()
    uid = make_paste(client, category.id, expiration_datetime=future).json()["uid"]
    assert client.get(f"/pastes/{uid}").status_code == 200
