from unittest.mock import MagicMock

from src.consumer import parse_dsn, process_batch


# --- parse_dsn ---

def test_parse_dsn_full():
    result = parse_dsn("postgresql://user:pass@localhost:5432/mydb")
    assert result == {"host": "localhost", "port": 5432, "dbname": "mydb", "user": "user", "password": "pass"}


def test_parse_dsn_default_port():
    result = parse_dsn("postgresql://user:pass@localhost/mydb")
    assert result["port"] == 5432


def test_parse_dsn_custom_port():
    result = parse_dsn("postgresql://user:pass@db:5433/mydb")
    assert result["port"] == 5433


# --- process_batch helpers ---

def make_conn(already_processed=None):
    already_processed = already_processed or []
    conn = MagicMock()
    cur = MagicMock()
    cur.__enter__ = MagicMock(return_value=cur)
    cur.__exit__ = MagicMock(return_value=False)
    cur.fetchall.return_value = [(k,) for k in already_processed]
    conn.cursor.return_value = cur
    return conn, cur


def get_update_calls(cur):
    return [c for c in cur.execute.call_args_list if "UPDATE" in str(c)]


def get_insert_calls(cur):
    return [c for c in cur.execute.call_args_list if "INSERT" in str(c)]


# --- process_batch ---

def test_process_batch_empty_does_nothing():
    conn, cur = make_conn()
    process_batch([], conn)
    cur.execute.assert_not_called()
    conn.commit.assert_not_called()


def test_process_batch_single_event():
    conn, cur = make_conn()
    process_batch([{"paste_uid": "abc", "idempotency_key": "key1"}], conn)
    updates = get_update_calls(cur)
    assert len(updates) == 1
    assert updates[0].args[1] == (1, "abc")


def test_process_batch_deduplicates_same_key():
    conn, cur = make_conn()
    batch = [
        {"paste_uid": "abc", "idempotency_key": "key1"},
        {"paste_uid": "abc", "idempotency_key": "key1"},
    ]
    process_batch(batch, conn)
    updates = get_update_calls(cur)
    assert len(updates) == 1
    assert updates[0].args[1] == (1, "abc")


def test_process_batch_skips_already_processed():
    conn, cur = make_conn(already_processed=["key1"])
    process_batch([{"paste_uid": "abc", "idempotency_key": "key1"}], conn)
    updates = get_update_calls(cur)
    assert len(updates) == 0


def test_process_batch_multiple_pastes():
    conn, cur = make_conn()
    batch = [
        {"paste_uid": "abc", "idempotency_key": "key1"},
        {"paste_uid": "def", "idempotency_key": "key2"},
        {"paste_uid": "abc", "idempotency_key": "key3"},
    ]
    process_batch(batch, conn)
    updates = get_update_calls(cur)
    assert len(updates) == 2
    # each update call: execute(sql, (count, paste_uid))
    counts = {c.args[1][1]: c.args[1][0] for c in updates}
    assert counts["abc"] == 2
    assert counts["def"] == 1


def test_process_batch_stores_new_keys():
    conn, cur = make_conn()
    batch = [
        {"paste_uid": "abc", "idempotency_key": "key1"},
        {"paste_uid": "abc", "idempotency_key": "key2"},
    ]
    process_batch(batch, conn)
    inserts = get_insert_calls(cur)
    inserted_keys = {c.args[1][0] for c in inserts}
    assert inserted_keys == {"key1", "key2"}


def test_process_batch_skips_malformed_events():
    conn, cur = make_conn()
    batch = [
        {"paste_uid": "abc"},
        {"idempotency_key": "key1"},
        {},
        {"paste_uid": "abc", "idempotency_key": "key2"},
    ]
    process_batch(batch, conn)
    updates = get_update_calls(cur)
    assert len(updates) == 1
    assert updates[0].args[1] == (1, "abc")


def test_process_batch_partial_already_processed():
    conn, cur = make_conn(already_processed=["key1"])
    batch = [
        {"paste_uid": "abc", "idempotency_key": "key1"},
        {"paste_uid": "abc", "idempotency_key": "key2"},
    ]
    process_batch(batch, conn)
    updates = get_update_calls(cur)
    assert len(updates) == 1
    assert updates[0].args[1] == (1, "abc")


def test_process_batch_commits():
    conn, cur = make_conn()
    process_batch([{"paste_uid": "abc", "idempotency_key": "key1"}], conn)
    conn.commit.assert_called()
