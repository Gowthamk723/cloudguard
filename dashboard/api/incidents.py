import json
import os
from http.server import BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs
from datetime import timezone

REQUIRED_FIELDS = ("rule", "status", "timestamp")


def serialize_incident(doc: dict) -> dict | None:
    resource = doc.get("resource") or doc.get("bucket")
    if not resource or any(doc.get(f) is None for f in REQUIRED_FIELDS):
        return None

    timestamp = doc["timestamp"]
    if hasattr(timestamp, "isoformat"):
        if timestamp.tzinfo is None:
            timestamp = timestamp.replace(tzinfo=timezone.utc)
        timestamp = timestamp.isoformat()
    else:
        timestamp = str(timestamp)

    return {
        "id": str(doc["_id"]),
        "resource": resource,
        "rule": doc["rule"],
        "status": doc["status"],
        "source": doc.get("source", "local"),
        "timestamp": timestamp,
    }


def get_incidents(collection, limit: int = 100, source: str | None = None) -> dict:
    
    limit = max(1, min(limit, 500))
    if source == "ci":
        query = {"source": "ci"}
    elif source == "local":
        query = {"source": {"$ne": "ci"}}   
    else:
        query = {}

    incidents, skipped = [], 0
    for doc in collection.find(query).sort("timestamp", -1).limit(limit):
        item = serialize_incident(doc)
        if item is None:
            skipped += 1
        else:
            incidents.append(item)

    return {"incidents": incidents, "count": len(incidents), "skipped": skipped}

_client = None


def _get_collection():
    
    global _client
    if _client is None:
        from pymongo import MongoClient
        _client = MongoClient(os.environ["MONGODB_URI"], serverSelectionTimeoutMS=5000)
    return _client["cloudguard"]["incidents"]


class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        params = parse_qs(urlparse(self.path).query)

        try:
            limit = int(params.get("limit", ["100"])[0])
        except ValueError:
            return self._send(400, {"error": "limit must be an integer"})

        source = params.get("source", [None])[0]
        if source not in (None, "ci", "local"):
            return self._send(400, {"error": "source must be 'ci' or 'local'"})

        try:
            body = get_incidents(_get_collection(), limit, source)
        except Exception:
            traceback.print_exc()
            return self._send(503, {"error": "database unavailable"})

        self._send(200, body)

    def _send(self, status: int, payload: dict):
        data = json.dumps(payload).encode()
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Cache-Control", "s-maxage=60, stale-while-revalidate")
        self.end_headers()
        self.wfile.write(data)