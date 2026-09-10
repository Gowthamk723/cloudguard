# CloudGuard

Automated cloud security & cost governance scanner. Detects misconfigurations
(unencrypted S3 buckets, public access, overly permissive IAM policies) and
untagged/idle resources; auto-remediates safe issues, flags risky ones via
Discord, and logs everything to a persistent, publicly viewable audit trail.

Built and tested end-to-end against **LocalStack** (a local AWS emulator) —
zero cloud cost, zero card required, fully reproducible via Terraform.

## Status
🚧 In development — building in public, one phase at a time.

## Architecture
_(coming soon)_

## Stack
Python · boto3 · Terraform · LocalStack · MongoDB Atlas · GitHub Actions ·
React · Vercel · Discord

## Design Notes & Discoveries

**S3 default encryption (Jan 2023 AWS change):** Initial plan was to detect
buckets with no server-side encryption at all. During development, discovered
that AWS enables SSE-S3 encryption by default on all new buckets since
January 2023 (LocalStack correctly emulates this). Adjusted the rule to
instead detect buckets using AWS-managed keys (SSE-S3) when the required
standard is customer-managed KMS keys (SSE-KMS) — a compliance gap that
still commonly exists in real environments, unlike "no encryption at all."