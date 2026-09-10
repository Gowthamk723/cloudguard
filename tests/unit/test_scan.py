import boto3
from moto import mock_aws
from scanner.scan import check_bucket_encryption, scan_all_buckets


@mock_aws
def test_unencrypted_bucket_is_flagged():
    client = boto3.client("s3", region_name="us-east-1")
    client.create_bucket(Bucket="test-bucket-no-encryption")

    is_encrypted = check_bucket_encryption(client, "test-bucket-no-encryption")

    assert is_encrypted is False


@mock_aws
def test_encrypted_bucket_is_not_flagged():
    client = boto3.client("s3", region_name="us-east-1")
    client.create_bucket(Bucket="test-bucket-encrypted")
    client.put_bucket_encryption(
        Bucket="test-bucket-encrypted",
        ServerSideEncryptionConfiguration={
            "Rules": [
                {"ApplyServerSideEncryptionByDefault": {"SSEAlgorithm": "AES256"}}
            ]
        },
    )

    is_encrypted = check_bucket_encryption(client, "test-bucket-encrypted")

    assert is_encrypted is True


@mock_aws
def test_scan_all_buckets_returns_correct_findings():
    client = boto3.client("s3", region_name="us-east-1")
    client.create_bucket(Bucket="bucket-a-unencrypted")
    client.create_bucket(Bucket="bucket-b-encrypted")
    client.put_bucket_encryption(
        Bucket="bucket-b-encrypted",
        ServerSideEncryptionConfiguration={
            "Rules": [
                {"ApplyServerSideEncryptionByDefault": {"SSEAlgorithm": "AES256"}}
            ]
        },
    )

    findings = scan_all_buckets(client)

    results = {f["bucket"]: f["encrypted"] for f in findings}
    assert results["bucket-a-unencrypted"] is False
    assert results["bucket-b-encrypted"] is True