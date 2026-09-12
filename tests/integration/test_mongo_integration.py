import pytest
from datetime import datetime, timezone
from scanner.scan import get_mongo_collection, log_incident


@pytest.fixture
def collection():
    """Real connection to your actual Atlas cluster — not mocked.
    Requires MONGODB_URI to be set in .env, same as scan.py uses."""
    return get_mongo_collection()


def test_log_incident_writes_all_status_types(collection):
    """Exercises every branch of log_incident's status logic against
    the REAL database — proves the write actually succeeds and the
    document shape is correct for each of the 4 possible outcomes."""

    test_findings = [
        {"bucket": "test-compliant-bucket", "uses_kms_before": True, "remediated": False, "remediation_error": None},
        {"bucket": "test-fixed-bucket", "uses_kms_before": False, "remediated": True, "remediation_error": None},
        {"bucket": "test-flagged-bucket", "uses_kms_before": False, "remediated": False, "remediation_error": None},
        {"bucket": "test-error-bucket", "uses_kms_before": False, "remediated": False, "remediation_error": "simulated failure"},
    ]

    for finding in test_findings:
        log_incident(collection, finding)

    written = list(collection.find({"bucket": {"$in": [f["bucket"] for f in test_findings]}}))

    assert len(written) == 4

    statuses = {doc["bucket"]: doc["status"] for doc in written}
    assert statuses["test-compliant-bucket"] == "compliant"
    assert statuses["test-fixed-bucket"] == "fixed"
    assert statuses["test-flagged-bucket"] == "flagged"
    assert statuses["test-error-bucket"] == "error"

    for doc in written:
        assert isinstance(doc["timestamp"], datetime)

    collection.delete_many({"bucket": {"$in": [f["bucket"] for f in test_findings]}})