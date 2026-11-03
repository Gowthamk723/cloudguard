import json
import os
from http.server import BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs

REQUIRED_FIELDS = ("rule", "status", "timestamp")


def serialize_incident(doc: dict) -> dict | None:
    resource = doc.get("resource") or doc.get("bucket")
    if not resource or any(doc.get(f) is None for f in REQUIRED_FIELDS):
        return None

    timestamp = doc["timestamp"]
    return {
        "id": str(doc["_id"]),
        "resource": resource,
        "rule": doc["rule"],
        "status": doc["status"],
        "source": doc.get("source", "local"),
        "timestamp": timestamp.isoformat() if hasattr(timestamp, "isoformat") else str(timestamp),
    }


def get_incidents(collection, limit: int = 100, source: str | None = None) -> dict:
    
    limit = max(1, min(limit, 500))
    query = {"source": source} if source else {}

    incidents, skipped = [], 0
    for doc in collection.find(query).sort("timestamp", -1).limit(limit):
        item = serialize_incident(doc)
        if item is None:
            skipped += 1
        else:
            incidents.append(item)

    return {"incidents": incidents, "count": len(incidents), "skipped": skipped}