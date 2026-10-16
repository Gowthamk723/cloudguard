import os
from dotenv import load_dotenv
from pymongo import MongoClient

load_dotenv()
client = MongoClient(os.getenv("MONGODB_URI"))

print("databases:", client.list_database_names())
col = client["cloudguard"]["incidents"]
print("total documents:", col.count_documents({}))

print("\nnewest 5:")
for d in col.find().sort("timestamp", -1).limit(5):
    print(d["timestamp"], d.get("rule"), d.get("resource") or d.get("bucket"), d.get("status"))