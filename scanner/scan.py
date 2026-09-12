import os
from dotenv import load_dotenv
import boto3

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
        if not uses_kms and auto_remediate:
            remediate_bucket_encryption(s3_client, name)
            remediated = True

        findings.append({
            "bucket": name,
            "uses_kms_before": uses_kms,
            "remediated": remediated,
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

def print_findings(findings):
    print(f"Scanning {len(findings)} bucket(s)...\n")
    for f in findings:
        if f["uses_kms_before"]:
            print(f"[OK]        {f['bucket']} — already using KMS encryption")
        elif f["remediated"]:
            print(f"[FIXED]     {f['bucket']} — was AWS-managed keys, now using KMS")
        else:
            print(f"[FINDING]   {f['bucket']} — using AWS-managed keys, not KMS (not remediated)")


if __name__ == "__main__":
    client = get_s3_client()
    results = scan_all_buckets(client,auto_remediate=True)
    print_findings(results)