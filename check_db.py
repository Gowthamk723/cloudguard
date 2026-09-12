import os
from dotenv import load_dotenv
from pymongo import MongoClient
import pprint

load_dotenv()
uri = os.getenv("MONGODB_URI")

client = MongoClient(uri)
db = client["cloudguard"]
incidents = db["incidents"].find()

print("\n--- MONGODB RECORDS ---")
for incident in incidents:
    incident.pop('_id', None) 
    pprint.pprint(incident)