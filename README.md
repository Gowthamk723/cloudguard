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