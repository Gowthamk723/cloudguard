import boto3
from moto import mock_aws
from unittest.mock import patch
import json
from scanner.scan import (
    check_bucket_uses_kms,
    scan_all_buckets,
    check_role_has_wildcard_policy,
    scan_all_roles,
    check_bucket_has_required_tag,
    scan_all_buckets_for_tags,
)

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
    
    client = boto3.client("s3", region_name="us-east-1")
    client.create_bucket(Bucket="bucket-to-fix")
    client.put_bucket_encryption(
        Bucket="bucket-to-fix",
        ServerSideEncryptionConfiguration={
            "Rules": [{"ApplyServerSideEncryptionByDefault": {"SSEAlgorithm": "AES256"}}]
        },
    )

    findings = scan_all_buckets(client, auto_remediate=True)


    result = findings[0]
    assert result["uses_kms_before"] is False
    assert result["remediated"] is True


    response = client.get_bucket_encryption(Bucket="bucket-to-fix")
    algorithm = response["ServerSideEncryptionConfiguration"]["Rules"][0][
        "ApplyServerSideEncryptionByDefault"
    ]["SSEAlgorithm"]
    assert algorithm == "aws:kms"


@mock_aws
def test_auto_remediate_false_only_detects():
    
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

    response = client.get_bucket_encryption(Bucket="bucket-detect-only")
    algorithm = response["ServerSideEncryptionConfiguration"]["Rules"][0][
        "ApplyServerSideEncryptionByDefault"
    ]["SSEAlgorithm"]
    assert algorithm == "AES256"

@mock_aws
def test_remediation_failure_does_not_crash_scan():
    
    client = boto3.client("s3", region_name="us-east-1")
    client.create_bucket(Bucket="bucket-remediation-fails")
    client.put_bucket_encryption(
        Bucket="bucket-remediation-fails",
        ServerSideEncryptionConfiguration={
            "Rules": [{"ApplyServerSideEncryptionByDefault": {"SSEAlgorithm": "AES256"}}]
        },
    )

    with patch(
        "scanner.scan.remediate_bucket_encryption",
        side_effect=Exception("simulated AWS failure"),
    ):
        findings = scan_all_buckets(client, auto_remediate=True)

    result = findings[0]
    assert result["remediated"] is False
    assert result["remediation_error"] == "simulated AWS failure"


@mock_aws
def test_wildcard_policy_is_flagged():
    client = boto3.client("iam", region_name="us-east-1")
    client.create_role(
        RoleName="role-with-wildcard",
        AssumeRolePolicyDocument=json.dumps({
            "Version": "2012-10-17",
            "Statement": [{"Effect": "Allow", "Principal": {"Service": "lambda.amazonaws.com"}, "Action": "sts:AssumeRole"}]
        }),
    )
    client.put_role_policy(
        RoleName="role-with-wildcard",
        PolicyName="wildcard-policy",
        PolicyDocument=json.dumps({
            "Version": "2012-10-17",
            "Statement": [{"Effect": "Allow", "Action": "*", "Resource": "*"}]
        }),
    )

    result = check_role_has_wildcard_policy(client, "role-with-wildcard")

    assert result is True


@mock_aws
def test_scoped_policy_is_not_flagged():
    
    client = boto3.client("iam", region_name="us-east-1")
    client.create_role(
        RoleName="role-with-scoped-policy",
        AssumeRolePolicyDocument=json.dumps({
            "Version": "2012-10-17",
            "Statement": [{"Effect": "Allow", "Principal": {"Service": "lambda.amazonaws.com"}, "Action": "sts:AssumeRole"}]
        }),
    )
    client.put_role_policy(
        RoleName="role-with-scoped-policy",
        PolicyName="scoped-policy",
        PolicyDocument=json.dumps({
            "Version": "2012-10-17",
            "Statement": [{"Effect": "Allow", "Action": "s3:GetObject", "Resource": "arn:aws:s3:::my-specific-bucket/*"}]
        }),
    )

    result = check_role_has_wildcard_policy(client, "role-with-scoped-policy")

    assert result is False


@mock_aws
def test_scan_all_roles_distinguishes_wildcard_from_scoped():
    client = boto3.client("iam", region_name="us-east-1")

    for role_name, action, resource in [
        ("bad-role", "*", "*"),
        ("good-role", "s3:GetObject", "arn:aws:s3:::my-bucket/*"),
    ]:
        client.create_role(
            RoleName=role_name,
            AssumeRolePolicyDocument=json.dumps({
                "Version": "2012-10-17",
                "Statement": [{"Effect": "Allow", "Principal": {"Service": "lambda.amazonaws.com"}, "Action": "sts:AssumeRole"}]
            }),
        )
        client.put_role_policy(
            RoleName=role_name,
            PolicyName="policy",
            PolicyDocument=json.dumps({
                "Version": "2012-10-17",
                "Statement": [{"Effect": "Allow", "Action": action, "Resource": resource}]
            }),
        )

    findings = scan_all_roles(client)
    results = {f["role"]: f["has_wildcard_policy"] for f in findings}

    assert results["bad-role"] is True
    assert results["good-role"] is False

@mock_aws
def test_bucket_without_tag_is_flagged():
    client = boto3.client("s3", region_name="us-east-1")
    client.create_bucket(Bucket="untagged-bucket")

    result = check_bucket_has_required_tag(client, "untagged-bucket")

    assert result is False

@mock_aws
def test_bucket_with_required_tag_is_not_flagged():
    client = boto3.client("s3", region_name="us-east-1")
    client.create_bucket(Bucket="tagged-bucket")
    client.put_bucket_tagging(
        Bucket="tagged-bucket",
        Tagging={"TagSet": [{"Key": "Environment", "Value": "production"}]},
    )

    result = check_bucket_has_required_tag(client, "tagged-bucket")

    assert result is True

@mock_aws
def test_scan_all_buckets_for_tags_distinguishes_tagged_from_untagged():
    client = boto3.client("s3", region_name="us-east-1")
    client.create_bucket(Bucket="bucket-no-tag")
    client.create_bucket(Bucket="bucket-with-tag")
    client.put_bucket_tagging(
        Bucket="bucket-with-tag",
        Tagging={"TagSet": [{"Key": "Environment", "Value": "staging"}]},
    )

    findings = scan_all_buckets_for_tags(client)
    results = {f["bucket_for_tagging"]: f["has_required_tag"] for f in findings}

    assert results["bucket-no-tag"] is False
    assert results["bucket-with-tag"] is True