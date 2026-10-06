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

def get_iam_client(endpoint_url: str = LOCALSTACK_ENDPOINT):
    return boto3.client(
        "iam",
        endpoint_url=endpoint_url,
        aws_access_key_id="test",
        aws_secret_access_key="test",
        region_name="us-east-1",
    )

def check_role_has_wildcard_policy(iam_client, role_name: str) -> bool:
    policy_names = iam_client.list_role_policies(RoleName=role_name)["PolicyNames"]

    for policy_name in policy_names:
        policy = iam_client.get_role_policy(RoleName=role_name, PolicyName=policy_name)
        statements = policy["PolicyDocument"]["Statement"]

        if not isinstance(statements, list):
            statements = [statements]

        for statement in statements:
            action = statement.get("Action")
            resource = statement.get("Resource")
            if action == "*" and resource == "*":
                return True

    return False

def scan_all_roles(iam_client):
    findings = []
    response = iam_client.list_roles()

    for role in response["Roles"]:
        name = role["RoleName"]
        has_wildcard = check_role_has_wildcard_policy(iam_client, name)
        findings.append({"role": name, "has_wildcard_policy": has_wildcard})

    return findings

def get_mongo_collection():
    uri = os.getenv("MONGODB_URI")
    client = MongoClient(uri)
    db = client["cloudguard"]
    return db["incidents"]


def log_incident(collection, finding: dict) -> None:
    if "bucket" in finding:
        resource_id = finding["bucket"]
        rule = "s3_kms_encryption"
        status = (
            "fixed" if finding["remediated"] else
            "error" if finding.get("remediation_error") else
            "compliant" if finding["uses_kms_before"] else
            "flagged"
        )
    elif "role" in finding:
        resource_id = finding["role"]
        rule = "iam_wildcard_policy"
        status = "flagged" if finding["has_wildcard_policy"] else "compliant"
    elif "bucket_for_tagging" in finding:
        resource_id = finding["bucket_for_tagging"]
        rule = "s3_required_tag"
        status = "compliant" if finding["has_required_tag"] else "flagged"
    else:
        raise ValueError(f"Unknown finding shape: {finding}")

    incident = {
        "resource": resource_id,
        "rule": rule,
        "status": status,
        "raw_finding": finding,
        "timestamp": datetime.now(timezone.utc),
    }

    try:
        collection.insert_one(incident)
    except Exception as e:
        print(f"[ERROR] Failed to log incident for {resource_id}: {e}")

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


def print_role_findings(findings):
    print(f"\nScanning {len(findings)} IAM role(s)...\n")
    for f in findings:
        if f["has_wildcard_policy"]:
            print(f"[FINDING]   {f['role']} — has wildcard (Action:*, Resource:*) policy, flagged for review")
        else:
            print(f"[OK]        {f['role']} — policies properly scoped")

def check_bucket_has_required_tag(s3_client, bucket_name: str, required_tag: str = "Environment") -> bool:
    
    try:
        response = s3_client.get_bucket_tagging(Bucket=bucket_name)
        tag_keys = [tag["Key"] for tag in response["TagSet"]]
        return required_tag in tag_keys
    except s3_client.exceptions.ClientError:
        return False

def scan_all_buckets_for_tags(s3_client, required_tag: str = "Environment"):
    
    findings = []
    response = s3_client.list_buckets()

    for bucket in response["Buckets"]:
        name = bucket["Name"]
        has_tag = check_bucket_has_required_tag(s3_client, name, required_tag)
        findings.append({"bucket_for_tagging": name, "has_required_tag": has_tag})

    return findings

def print_tag_findings(findings):
    print(f"\nScanning {len(findings)} bucket(s) for required tags...\n")
    for f in findings:
        if f["has_required_tag"]:
            print(f"[OK]        {f['bucket_for_tagging']} — has required 'Environment' tag")
        else:
            print(f"[FINDING]   {f['bucket_for_tagging']} — missing required 'Environment' tag")


if __name__ == "__main__":
    s3_client = get_s3_client()
    iam_client = get_iam_client()
    mongo_collection = get_mongo_collection()

    bucket_results = scan_all_buckets(s3_client, auto_remediate=True)
    role_results = scan_all_roles(iam_client)
    tag_results = scan_all_buckets_for_tags(s3_client)

    all_results = bucket_results + role_results + tag_results

    for finding in all_results:
        log_incident(mongo_collection, finding)

    print_findings(bucket_results)
    print_role_findings(role_results)
    print_tag_findings(tag_results)