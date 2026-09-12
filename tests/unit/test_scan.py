import boto3
from moto import mock_aws
from scanner.scan import check_bucket_uses_kms, scan_all_buckets


@mock_aws
def test_sse_s3_bucket_is_flagged():
    """A bucket explicitly configured with AES256 should fail."""
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
    results = {f["bucket"]: f["uses_kms_before"] for f in findings}

    assert results["bucket-sse-s3"] is False
    assert results["bucket-kms"] is True

@mock_aws
def test_non_kms_bucket_gets_remediated():
    """The core Week 3 behavior: a non-compliant bucket should be
    fixed automatically when auto_remediate=True."""
    client = boto3.client("s3", region_name="us-east-1")
    client.create_bucket(Bucket="bucket-to-fix")
    client.put_bucket_encryption(
        Bucket="bucket-to-fix",
        ServerSideEncryptionConfiguration={
            "Rules": [{"ApplyServerSideEncryptionByDefault": {"SSEAlgorithm": "AES256"}}]
        },
    )

    findings = scan_all_buckets(client, auto_remediate=True)

    # Check what the function reported...
    result = findings[0]
    assert result["uses_kms_before"] is False
    assert result["remediated"] is True

    # ...AND independently verify the actual AWS state changed,
    # not just that our function claims it did.
    response = client.get_bucket_encryption(Bucket="bucket-to-fix")
    algorithm = response["ServerSideEncryptionConfiguration"]["Rules"][0][
        "ApplyServerSideEncryptionByDefault"
    ]["SSEAlgorithm"]
    assert algorithm == "aws:kms"


@mock_aws
def test_auto_remediate_false_only_detects():
    """When auto_remediate=False, a non-compliant bucket should be
    flagged but NOT actually fixed — detection and remediation must
    stay independently controllable."""
    client = boto3.client("s3", region_name="us-east-1")
    client.create_bucket(Bucket="bucket-detect-only")
    client.put_bucket_encryption(
        Bucket="bucket-detect-only",
        ServerSideEncryptionConfiguration={
            "Rules": [{"ApplyServerSideEncryptionByDefault": {"SSEAlgorithm": "AES256"}}]
        },
    )

    findings = scan_all_buckets(client, auto_remediate=False)

    result = findings[0]
    assert result["uses_kms_before"] is False
    assert result["remediated"] is False

    # Verify the bucket was genuinely left untouched
    response = client.get_bucket_encryption(Bucket="bucket-detect-only")
    algorithm = response["ServerSideEncryptionConfiguration"]["Rules"][0][
        "ApplyServerSideEncryptionByDefault"
    ]["SSEAlgorithm"]
    assert algorithm == "AES256"