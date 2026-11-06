import json
from datetime import datetime, timezone
from unittest.mock import MagicMock
from dashboard.api.incidents import get_incidents, serialize_incident


def make_collection(docs):
    collection = MagicMock()
    collection.find.return_value.sort.return_value.limit.return_value = docs
    return collection


def good_doc(**overrides):
    doc = {
        "_id": "abc123",
        "resource": "bucket-1",
        "rule": "s3_kms_encryption",
        "status": "fixed",
        "timestamp": datetime(2026, 11, 3, tzinfo=timezone.utc),
    }
    doc.update(overrides)
    return doc


def test_empty_collection_returns_empty_list():
    result = get_incidents(make_collection([]))
    assert result == {"incidents": [], "count": 0, "skipped": 0}


def test_normal_document_has_expected_shape():
    result = get_incidents(make_collection([good_doc()]))
    item = result["incidents"][0]
    assert set(item) == {"id", "resource", "rule", "status", "source", "timestamp"}
    assert item["source"] == "local"          
    assert item["timestamp"].startswith("2026-11-03")


def test_malformed_document_is_skipped_not_fatal():
    bad = {"_id": "x", "rule": "s3_required_tag"}   
    result = get_incidents(make_collection([good_doc(), bad]))
    assert result["count"] == 1
    assert result["skipped"] == 1


def test_legacy_document_with_bucket_field_still_works():
    legacy = good_doc()
    del legacy["resource"]
    legacy["bucket"] = "old-bucket"
    assert serialize_incident(legacy)["resource"] == "old-bucket"


def test_limit_is_clamped():
    collection = make_collection([])
    get_incidents(collection, limit=10_000)
    collection.find.return_value.sort.return_value.limit.assert_called_with(500)

def test_local_source_includes_legacy_documents():
    collection = make_collection([])
    get_incidents(collection, source="local")
    collection.find.assert_called_with({"source": {"$ne": "ci"}})

def test_naive_timestamp_is_treated_as_utc():
    item = serialize_incident(good_doc(timestamp=datetime(2026, 11, 3, 10, 0, 0)))
    assert item["timestamp"].endswith("+00:00")
