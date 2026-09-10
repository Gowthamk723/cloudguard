import os
from dotenv import load_dotenv

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


def check_bucket_encryption(s3_client, bucket_name: str) -> bool:
    try:
        s3_client.get_bucket_encryption(Bucket=bucket_name)
        return True
    except s3_client.exceptions.ClientError:
        return False


def scan_all_buckets(s3_client):
    findings = []
    response = s3_client.list_buckets()

    for bucket in response["Buckets"]:
        name = bucket["Name"]
        is_encrypted = check_bucket_encryption(s3_client, name)
        findings.append({"bucket": name, "encrypted": is_encrypted})

    return findings


def print_findings(findings):
    print(f"Scanning {len(findings)} bucket(s)...\n")
    for f in findings:
        if f["encrypted"]:
            print(f"[OK]      {f['bucket']} — default encryption enabled")
        else:
            print(f"[FINDING] {f['bucket']} — NO default encryption (misconfiguration)")


if __name__ == "__main__":
    client = get_s3_client()
    results = scan_all_buckets(client)
    print_findings(results)