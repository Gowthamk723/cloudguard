# Product Requirements Document
## CloudGuard: Cloud Security & Cost Governance Scanner

**Author:** [Your Name]
**Status:** Draft — In Development
**Last Updated:** September 2026
**Build philosophy:** 100% free, no credit/debit card required anywhere, no student-pack dependency

---

## 0. Cost & Access Verification (read this first)

Every tool below was checked specifically for "free with no card required." This table is the source of truth for what you're actually signing up for — verify current terms yourself at signup, since pricing pages do change.

| Tool | Role in project | Cost | Card required? |
|---|---|---|---|
| **LocalStack (Hobby plan)** | Local AWS emulator — Lambda, S3, DynamoDB, IAM, SNS, SQS, STS, Secrets Manager, CloudWatch Logs | Free (non-commercial use) | **No** — free account signup only |
| **Terraform (CLI)** | Infrastructure as Code | Free, open-source | No — just a downloaded binary |
| **Docker Desktop / Docker Engine** | Runs LocalStack locally | Free | No |
| **GitHub Actions** | CI/CD pipeline | Free for public repositories | No |
| **Python 3 + boto3** | Lambda logic, AWS SDK | Free, open-source | No |
| **pytest + moto + pytest-cov** | Test framework, in-memory AWS mocking, coverage reporting | Free, open-source | No |
| **MongoDB Atlas (free M0 tier)** | Persistent incident log storage for the public dashboard | Free forever, 512MB | No |
| **Vercel (Hobby plan)** | Hosts the React dashboard + serverless API | Free | No |
| **Discord (webhook)** | Real-time alerts | Free, no limits relevant to this use case | No |
| **GitHub (public repo)** | Version control, portfolio visibility | Free | No |

**What's intentionally NOT in this stack:** a real AWS account (requires a card for identity verification even on the free plan), real DynamoDB (same reason), and Slack (works free too, but Discord is simpler for a solo project with no integration-count limits).

**Known limitation, stated honestly:** LocalStack's free tier doesn't guarantee state persistence between container restarts, and full IAM policy *enforcement* (vs. just writing policies) is a paid feature. The architecture below is designed around these limits rather than fighting them — see Section 3.

---

## 1. Overview

### 1.1 Problem Statement
Organizations running cloud infrastructure face two chronic, expensive problems:

1. **Security drift** — resources get misconfigured (public S3 buckets, unencrypted storage, overly permissive IAM policies) faster than human teams can review them manually.
2. **Cost waste** — forgotten or untagged resources (idle compute, orphaned storage, non-production resources left running) silently inflate cloud bills.

Both share the same root cause: nobody is watching continuously. Manual audits happen weekly or monthly, by which point damage is already done.

### 1.2 Solution
CloudGuard is a scheduled, automated scanner that:
- **Scans** cloud resources on a regular interval for known misconfiguration patterns
- **Auto-remediates** safe, well-defined issues (e.g., re-encrypts an unencrypted S3 bucket)
- **Flags** issues requiring human judgment via a Discord alert
- **Enforces cost discipline** by scanning for untagged/idle resources and flagging or stopping non-production waste
- **Logs everything** to a persistent, queryable audit trail (MongoDB Atlas) with a public dashboard for visibility

### 1.3 Why polling/scheduled scanning instead of real-time event triggers
The original design used AWS CloudTrail + EventBridge for instant, real-time detection. That's the "correct" production pattern, but it depends on services whose free-tier local emulation isn't guaranteed. A **scheduled scanner** (runs every N minutes) is:
- Fully buildable on confirmed-free tools (Lambda + S3 + IAM, all in LocalStack's Hobby tier)
- A legitimate, widely-used real-world pattern in its own right (many company security tools poll rather than stream)
- Easier to reason about and debug while you're still learning

The README will document the **event-driven upgrade path** (CloudTrail + EventBridge) as a "Future Enhancement" — this is a great interview talking point ("I built the polling version first because it was verifiable on free tooling, and I designed the event-driven version as the natural next step") that shows engineering judgment, not a limitation you're hiding.

### 1.4 Goals
| Goal | Success Metric |
|---|---|
| Reliable misconfiguration detection | Scanner correctly identifies at least 3 distinct misconfiguration types on a test AWS environment (via LocalStack) |
| Safe auto-remediation | At least 2 remediation types fully automated end-to-end |
| Cost governance | Scan identifies untagged/non-prod resources and flags or stops them |
| Auditability | Every action (detected, remediated, or flagged) is logged with timestamp, resource, and outcome |
| Visibility | A public dashboard shows incident history and estimated cost savings over time |
| Zero cost, zero card | Entire build and running demo cost $0 with no payment method entered anywhere |

### 1.5 Non-Goals (v1)
- Multi-cloud support (AWS emulation only)
- Real-time event-driven detection (documented as future work, not built now)
- Every possible misconfiguration type (start with 3-4 well-understood ones)
- Machine-learning-based anomaly detection (rule-based only)
- Real production AWS deployment (this is a portfolio/learning project — see Section 9 for the honest framing)

---

## 2. Users & Use Cases

**Primary user:** You, building this as a portfolio project. In interviews, you present it as: "I built and fully tested this against a local AWS emulation environment to avoid cloud costs while learning; the architecture is designed to deploy against real AWS with minimal changes."

**Use cases:**
1. Scanner runs → finds an S3 bucket without encryption → auto-applies default encryption → logs the fix → posts a Discord notification.
2. Scanner finds a security group open to `0.0.0.0/0` on port 22 → too risky to auto-close (could break legitimate access) → flags it with a Discord alert for human review instead of auto-fixing.
3. Scanner finds a compute instance without an `Environment` tag → flags it (or stops it, depending on configured aggressiveness) → logs the action and estimated dollars saved.
4. You open the public dashboard → see a timeline of all incidents, auto-fixed vs. flagged counts, and running total of estimated savings.

---

## 3. System Architecture

```
┌───────────────────────────────────────────────────────────┐
│              LocalStack (local AWS emulation)               │
│                                                               │
│   ┌─────────┐   ┌──────────┐   ┌─────────┐   ┌───────────┐ │
│   │   S3     │   │   IAM     │   │  Lambda  │   │  Secrets   │ │
│   │(buckets) │   │(policies) │   │(scanner) │   │  Manager   │ │
│   └─────────┘   └──────────┘   └────┬────┘   └───────────┘ │
│                                       │                       │
└───────────────────────────────────────┼───────────────────────┘
                                         │
                    triggered on a schedule by:
                    GitHub Actions (cron) OR local cron/Task Scheduler
                                         │
                                         ▼
                          ┌──────────────────────┐
                          │  Python Scanner Logic  │
                          │  (boto3, pointed at     │
                          │   LocalStack endpoint)  │
                          └──────┬───────────┬────┘
                                 │           │
                    safe issue?  │           │  risky issue?
                      auto-fix   │           │  flag only
                                 ▼           ▼
                    ┌──────────────┐  ┌──────────────┐
                    │ Remediation   │  │   Discord      │
                    │  Action       │  │   Webhook       │
                    │ (via boto3)   │  │   Alert         │
                    └──────────────┘  └──────────────┘
                                 │
                                 ▼
                    ┌───────────────────────┐
                    │   MongoDB Atlas         │
                    │   (persistent incident   │
                    │    log — free M0 tier)   │
                    └──────────┬────────────┘
                               │
                               ▼
                    ┌───────────────────────┐
                    │  Vercel Serverless API  │
                    │  (reads incident log)   │
                    └──────────┬────────────┘
                               │
                               ▼
                    ┌───────────────────────┐
                    │  React Dashboard         │
                    │  (hosted on Vercel)      │
                    └───────────────────────┘

All infrastructure (S3 buckets, IAM policies, Lambda function
definitions) is defined in Terraform, applied against the
LocalStack endpoint — same HCL syntax as real AWS, swappable
to a real AWS provider later by changing the endpoint config.
```

### 3.1 Component Breakdown

| Component | Purpose | Tool |
|---|---|---|
| Local cloud environment | Emulates AWS services for free, no card | LocalStack (Hobby plan) |
| Test resources | S3 buckets, IAM roles/policies you create to scan against | LocalStack S3 + IAM |
| Scanner logic | Core detection + remediation rules | Python + boto3 |
| Scheduler | Triggers the scanner periodically | GitHub Actions (cron schedule) |
| Persistent incident log | Stores every detected/remediated/flagged event — chosen over DynamoDB specifically because it's genuinely free and persistent, sidestepping LocalStack's free-tier state-persistence limitation | MongoDB Atlas (M0 free tier) |
| Real-time alerting | Notifies you instantly | Discord webhook (HTTP POST from Python) |
| API layer | Serves incident data to frontend | Vercel serverless function (Python or Node) |
| Dashboard | Visualizes incidents & savings | React, hosted on Vercel |
| Infrastructure definition | Version-controlled, reproducible setup | Terraform (targeting LocalStack endpoint) |
| CI | Runs scanner logic + tests automatically | GitHub Actions |

---

## 4. Detection & Remediation Rules (v1 scope)

| # | Misconfiguration | Auto-Remediate? | Action |
|---|---|---|---|
| 1 | S3 bucket without default encryption | ✅ Yes | Apply AES-256 default encryption |
| 2 | S3 bucket with public access enabled | ✅ Yes | Re-apply public access block |
| 3 | IAM policy with wildcard (`"Action": "*"`, `"Resource": "*"`) attached to a role | ❌ No — flag only | Discord alert with role name + policy details |
| 4 | IAM user with no MFA / long-unused access key (simulated via metadata you set on test resources) | ❌ No — flag only | Discord alert for human review |
| 5 | Resource missing required tag (e.g., `Environment`) | ✅ Yes (configurable) | Flag by default; optionally auto-stop if you extend to compute resources |



---

## 5. Technical Requirements

### 5.1 Local Development Setup
- Docker installed (required to run LocalStack)
- LocalStack Hobby account (free signup, no card) — run via `docker run` or LocalStack CLI
- Point `boto3` and Terraform's AWS provider at the LocalStack endpoint (`http://localhost:4566`) using dummy credentials (LocalStack doesn't validate real AWS credentials)

### 5.2 Handling the state-persistence limitation
Since free-tier LocalStack may not persist state across restarts:
- Keep the LocalStack container running for the duration of a work session (state persists as long as the container is alive)
- Use a Terraform script to **quickly recreate test resources** (buckets, IAM roles) at the start of each session if the container was restarted — this is good practice anyway ("infrastructure should be reproducible from code, not hand-clicked")
- The MongoDB Atlas incident log is genuinely persistent regardless of LocalStack restarts, so your historical data/dashboard is never lost even if local test resources are recreated

### 5.3 Security of the tool itself
- Terraform-defined IAM roles for the scanner follow least-privilege even in the local/emulated environment — document this explicitly, since it's a strong practice to demonstrate even where enforcement isn't guaranteed by the free tier
- Discord webhook URL and MongoDB connection string stored as GitHub Actions encrypted secrets, never hardcoded

---

## 6. Build Plan — Week by Week

| Week | Milestone | Details |
|---|---|---|
| **1** | Environment setup | Install Docker, sign up for LocalStack Hobby (free), run your first `docker run localstack/localstack`, verify `awslocal s3 ls` works |
| **2** | First detection rule (manual script, no IaC yet) | Python script using boto3 pointed at LocalStack; detect an unencrypted test bucket you create manually; just print/log the finding. Write the matching `moto`-based unit test alongside it (see Section 8) |
| **3** | Add remediation logic + MongoDB logging | Implement rules #1 and #2 (auto-remediation); set up free MongoDB Atlas cluster; write incident records to it; unit tests for both rules |
| **4** | Add flagging rules + Discord alerting | Implement rules #3 and #5 (flag-only); wire up Discord webhook, test end-to-end alert; unit tests including the "flag-only, never auto-remediate" boundary check |
| **5** | Rewrite test infrastructure as Terraform | Codify your test S3 buckets/IAM roles as Terraform, applied against LocalStack — this is where you actually learn Terraform, since you already understand what each resource does |
| **6** | GitHub Actions automation | Pipeline that runs the scanner on a schedule (cron) in CI, using LocalStack-in-CI (LocalStack has an official GitHub Action for this); CI test job (pytest unit + integration) runs before the scan job |
| **7** | Dashboard backend | Vercel serverless function reading from MongoDB Atlas, returning incident JSON; API tests for empty-state and malformed-data cases |
| **8** | Dashboard frontend | React app on Vercel — incident timeline, auto-fixed vs. flagged counts, estimated savings total |
| **9** | Documentation + polish | README with architecture diagram, demo GIF, design-decision write-up (why polling not events, why MongoDB not DynamoDB, why some issues auto-fix and others don't), test coverage report — and a clearly labeled "Future Enhancements" section covering the real-time CloudTrail+EventBridge upgrade path |

*Buffer note: if you fall behind, weeks 7-8 (dashboard) are the most compressible — a working scanner with logged results in MongoDB (even viewed via a simple script rather than a polished dashboard) is still a strong, demonstrable project.*

---

## 7. Success Criteria (definition of "done")

- [ ] At least 4 detection rules working end-to-end against LocalStack (2+ auto-remediated, 2+ flagged)
- [ ] All test infrastructure defined in Terraform, reproducible with `terraform apply`
- [ ] GitHub Actions runs the scanner automatically on a schedule
- [ ] Discord receives real alerts for flagged issues
- [ ] MongoDB Atlas persistently stores incident history
- [ ] Public dashboard (Vercel) displays real incident data
- [ ] README documents architecture, setup, design rationale, and the honest scope/limitations (local emulation vs. real AWS)
- [ ] You can verbally explain, unprompted: why polling instead of events, why MongoDB instead of DynamoDB, what would change to deploy this against real AWS, and what happens on failure (script crashes mid-remediation, MongoDB write fails, etc.)
- [ ] Unit tests exist for all 4+ detection/remediation rules, including negative (no false-positive) cases
- [ ] At least one integration test runs the scanner end-to-end against LocalStack in CI
- [ ] At least one test covers a failure mode (DB write failure or remediation exception) without crashing the scan
- [ ] API layer has tests for empty-state and malformed-data cases
- [ ] CI fails the pipeline if tests fail — scanning doesn't run on broken code

---

## 8. Testing & QA Strategy

Why this section exists: Section 7's commitment to explaining failure handling ("script crashes mid-remediation, MongoDB write fails") is only a credible interview claim if it's backed by actual tests. This section makes it real — it's what turns "I built a scanner" into "I built and tested a scanner," the exact language a test-automation-focused JD is looking for.

**Stack (all free, no new tools/cards):**

| Layer | Framework | Why |
|---|---|---|
| Scanner logic (detection/remediation rules) | pytest | Industry-standard |
| AWS mocking (unit tests) | moto | Mocks S3/IAM/Lambda in-memory — faster than hitting LocalStack, no container needed for pure logic tests |
| AWS integration tests | pytest + boto3 pointed at LocalStack | Verifies real request/response shape against the emulator, not just mocked behavior |
| API layer (Vercel serverless) | pytest + requests | Hits the deployed/local endpoint, asserts on JSON shape and status codes |
| CI enforcement | GitHub Actions | Test job runs on every push; scanner job only runs after tests pass |

### 8.1 Unit tests — scanner rules (moto, no LocalStack needed)

Test each detection/remediation rule from Section 4 in isolation, with mocked AWS state:

- Rule #1 (unencrypted bucket): create a mocked bucket with no encryption → assert detector flags it → assert remediation applies AES-256 → assert re-scan shows it as fixed
- Rule #2 (public bucket): mocked bucket with public access → assert detection + assert public access block gets reapplied
- Rule #3 (wildcard IAM policy): mocked role with `"Action":"*"` → assert it's flagged, and explicitly assert no remediation is attempted (this is your "flag-only" safety boundary — test that it stays that way)
- Rule #5 (missing tag): mocked resource with no `Environment` tag → assert flagged/stopped per configured aggressiveness
- Negative cases for every rule: a correctly-configured resource should produce zero findings — this catches false positives, which matter more than false negatives in a security tool

### 8.2 Integration tests — against LocalStack

A smaller set of tests that run the same scanner code against a live LocalStack container (via the LocalStack GitHub Action, same one used for the scheduled scan job):

- End-to-end: create real (emulated) misconfigured resources via Terraform → run the actual scanner entrypoint → assert MongoDB received the expected incident record → assert Discord webhook was called with expected payload (mock the webhook call itself here — don't spam real Discord in CI)
- Idempotency check: run the scanner twice against the same resource → assert the second run doesn't create a duplicate incident or re-apply remediation unnecessarily

### 8.3 API tests — dashboard backend

- Empty state: MongoDB has zero incidents → API returns 200 with an empty array, not an error
- Malformed/partial document: insert a record missing an expected field → assert the API doesn't 500, either sanitizes or returns a clear error
- Normal case: seeded incident data → assert response shape matches what the React dashboard expects (field names, types, pagination if used)

### 8.4 Failure-mode tests

Directly covers the Section 7 commitment to explain failure handling:

- Simulate a MongoDB write failure (e.g., bad connection string in test config) → assert the scanner logs the failure locally and doesn't crash the whole run — one bad write shouldn't lose all other incidents from that scan
- Simulate a remediation call raising an exception mid-fix → assert it's caught, logged as a failed remediation (not silently swallowed), and doesn't block remaining resources from being scanned

### 8.5 CI wiring

Add a test job in GitHub Actions that runs before the scheduled scan job:

```yaml
- name: Run unit tests
  run: pytest tests/unit --cov=scanner
- name: Run integration tests (LocalStack)
  run: pytest tests/integration
```

Track coverage with `pytest-cov` — you don't need a high number, but "here's my coverage report" is a strong interview artifact on its own.

---



## 9. Future Enhancements (post-v1, don't build now)
- Real-time detection via CloudTrail + EventBridge (once you're comfortable spending on a real AWS account, or once budget allows)
- Deploy against a real AWS free-tier account (still requires a card for AWS's identity verification, but $0 actual charges within limits) to get a genuinely live demo
- Multi-cloud support (Azure via Azure for Students, which is confirmed card-free for eligible students)
- Slack as an alternate alerting channel (confirmed free-tier capable, if you want both)
