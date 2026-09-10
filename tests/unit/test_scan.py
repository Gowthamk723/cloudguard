import boto3
from moto import mock_aws
from scanner.scan import check_bucket_uses_kms, scan_all_buckets


@mock_aws
def test_sse_s3_bucket_is_flagged():
    
    client = boto3.client("s3", region_name="us-east-1")
    client.create_bucket(Bucket="test-bucket-sse-s3")
    
    client.put_bucket_encryption(
        Bucket="test-bucket-sse-s3",
        ServerSideEncryptionConfiguration={
            "Rules": [
                {"ApplyServerSideEncryptionByDefault": {"SSEAlgorithm": "AES256"}}
            ]
        },
    )

    result = check_bucket_uses_kms(client, "test-bucket-sse-s3")

    assert result is False


@mock_aws
def test_kms_bucket_is_not_flagged():
    """A bucket explicitly configured with KMS should pass."""
    client = boto3.client("s3", region_name="us-east-1")
    client.create_bucket(Bucket="test-bucket-kms")
    client.put_bucket_encryption(
        Bucket="test-bucket-kms",
        ServerSideEncryptionConfiguration={
            "Rules": [
                {"ApplyServerSideEncryptionByDefault": {"SSEAlgorithm": "aws:kms"}}
            ]
        },
    )

    result = check_bucket_uses_kms(client, "test-bucket-kms")

    assert result is True


@mock_aws
def test_scan_all_buckets_distinguishes_kms_from_sse_s3():
    """Mixed scenario — proves the scan correctly separates both cases
    in a single pass, not just in isolation."""
    client = boto3.client("s3", region_name="us-east-1")

    client.create_bucket(Bucket="bucket-sse-s3")
    client.put_bucket_encryption(
        Bucket="bucket-sse-s3",
        ServerSideEncryptionConfiguration={
            "Rules": [{"ApplyServerSideEncryptionByDefault": {"SSEAlgorithm": "AES256"}}]
        },
    )

    client.create_bucket(Bucket="bucket-kms")
    client.put_bucket_encryption(
        Bucket="bucket-kms",
        ServerSideEncryptionConfiguration={
            "Rules": [{"ApplyServerSideEncryptionByDefault": {"SSEAlgorithm": "aws:kms"}}]
        },
    )

    findings = scan_all_buckets(client)
    results = {f["bucket"]: f["uses_kms"] for f in findings}

    assert results["bucket-sse-s3"] is False
    assert results["bucket-kms"] is True