import os
from dotenv import load_dotenv
import boto3
from datetime import datetime, timezone
from pymongo import MongoClient

load_dotenv()

LOCALSTACK_ENDPOINT = os.getenv("LOCALSTACK_ENDPOINT")


def get_s3_client(endpoint_url: str = LOCALSTACK_ENDPOINT):
    return boto3.client(
        "s3",
        endpoint_url=endpoint_url,
        aws_access_key_id="test",
        aws_secret_access_key="test",
        region_name="us-east-1",
    )


def check_bucket_uses_kms(s3_client, bucket_name: str) -> bool:
    try:
        response = s3_client.get_bucket_encryption(Bucket=bucket_name)
        rules = response["ServerSideEncryptionConfiguration"]["Rules"]
        algorithm = rules[0]["ApplyServerSideEncryptionByDefault"]["SSEAlgorithm"]
        return algorithm == "aws:kms"
    except s3_client.exceptions.ClientError:
        return False


def scan_all_buckets(s3_client, auto_remediate: bool = True):
    findings = []
    response = s3_client.list_buckets()

    for bucket in response["Buckets"]:
        name = bucket["Name"]
        uses_kms = check_bucket_uses_kms(s3_client, name)

        remediated = False
        remediation_error = None

        if not uses_kms and auto_remediate:
            try:
                remediate_bucket_encryption(s3_client, name)
                remediated = True
            except Exception as e:
                remediation_error = str(e)
                print(f"[ERROR] Failed to remediate {name}: {e}")

        findings.append({
            "bucket": name,
            "uses_kms_before": uses_kms,
            "remediated": remediated,
            "remediation_error": remediation_error,
        })

    return findings

def remediate_bucket_encryption(s3_client, bucket_name: str) -> None:
    s3_client.put_bucket_encryption(
        Bucket=bucket_name,
        ServerSideEncryptionConfiguration={
            "Rules": [
                {"ApplyServerSideEncryptionByDefault": {"SSEAlgorithm": "aws:kms"}}
            ]
        },
    )

def get_mongo_collection():
    """Factory, same dependency-injection pattern as get_s3_client —
    keeps MongoDB access swappable/testable, not hardcoded inline."""
    uri = os.getenv("MONGODB_URI")
    client = MongoClient(uri)
    db = client["cloudguard"]
    return db["incidents"]


def log_incident(collection, finding: dict) -> None:
    """Writes a single scan result as an incident document."""
    incident = {
        "bucket": finding["bucket"],
        "rule": "s3_kms_encryption",
        "uses_kms_before": finding["uses_kms_before"],
        "remediated": finding["remediated"],
        "remediation_error": finding.get("remediation_error"),
        "status": (
            "fixed" if finding["remediated"] else
            "error" if finding.get("remediation_error") else
            "compliant" if finding["uses_kms_before"] else 
            "flagged"
        ),
        "timestamp": datetime.now(timezone.utc),
    }

    try:
        collection.insert_one(incident)
    except Exception as e:
        print(f"[ERROR] Failed to log incident for {finding['bucket']}: {e}")

def print_findings(findings):
    print(f"Scanning {len(findings)} bucket(s)...\n")
    for f in findings:
        if f["uses_kms_before"]:
            print(f"[OK]        {f['bucket']} — already using KMS encryption")
        elif f["remediated"]:
            print(f"[FIXED]     {f['bucket']} — was AWS-managed keys, now using KMS")
        elif f.get("remediation_error"):
            print(f"[FAILED]    {f['bucket']} — tried to fix, but got AWS error")
        else:
            print(f"[FINDING]   {f['bucket']} — using AWS-managed keys, not KMS (not remediated)")


if __name__ == "__main__":
    client = get_s3_client()
    mongo_collection = get_mongo_collection()

    results = scan_all_buckets(client, auto_remediate=False)

    for finding in results:
        log_incident(mongo_collection, finding)

    print_findings(results)