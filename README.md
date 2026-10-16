# CloudGuard

**Automated Cloud Security & Cost Governance Scanner**

CloudGuard is an automated cloud security and cost governance scanner that detects common AWS misconfigurations, automatically remediates safe issues, flags risky configurations through Discord alerts, and records every scan result in a persistent MongoDB Atlas audit trail.

Built and tested end-to-end against **LocalStack**, a local AWS emulator, with a fully reproducible test environment provisioned using Terraform.

---

## Status

| Phase | Status |
| --- | --- |
| Scanner rules (S3 encryption, IAM wildcard, missing tags) | Done |
| Auto-remediation and MongoDB audit logging | Done |
| Discord alerts with severity-ranked summaries | Done |
| Unit and integration tests | Done |
| Terraform test environment | Done |
| GitHub Actions scheduled scans and CI | Planned |
| Dashboard (React + Vercel) | Planned |

---

## Detection Rules

| Rule | Resource | Action |
| --- | --- | --- |
| S3 bucket not using KMS encryption | S3 | Auto-remediated by applying `aws:kms` encryption |
| IAM role with `Action: "*"` on `Resource: "*"` | IAM | Flag only; no remediation code exists by design |
| S3 bucket missing the `Environment` tag | S3 | Flag only |

> **Design Philosophy:** Reversible, low-risk fixes are automated. Anything affecting permissions or ownership labels requires human judgment and is strictly flagged for review.

---

## Tech Stack

- **Languages & Core:** Python, `boto3`
- **Testing:** `pytest`, `moto`, Terraform, LocalStack
- **Infrastructure & Storage:** MongoDB Atlas, Docker
- **Notifications:** Discord webhooks
- **Infrastructure as Code:** Terraform

---

## Project Structure

```
cloudguard/
├── scanner/
│   ├── scan.py
│   └── requirements.txt
├── tests/
│   ├── unit/
│   └── integration/
├── infra/
├── docs/
│   └── PRD.md
├── .env.example
└── README.md
```

---

## Prerequisites

Install or configure the following before getting started:

- Docker Desktop
- Python 3.10+
- Terraform 1.5+
- Git
- LocalStack account
- MongoDB Atlas cluster
- Discord webhook URL

---

## Setup

### 1\. Clone the Repository

Replace `<your-username>` with your GitHub username.

```
git clone https://github.com/<your-username>/cloudguard.git
cd cloudguard
```

### 2\. Create a Virtual Environment

```
python -m venv venv
venv\Scripts\Activate.ps1
```

Install the project dependencies:

```
pip install -r scanner/requirements.txt
```

### 3\. Configure Environment Variables

Copy `.env.example` to `.env` and fill in the required values.

Example configuration:

```
LOCALSTACK_ENDPOINT=http://localhost:4566
MONGODB_URI=mongodb+srv://<username>:<password>@<cluster-url>/?appName=Cluster0
DISCORD_WEBHOOK_URL=https://discord.com/api/webhooks/<id>/<token>
```

Replace the placeholders with your actual MongoDB Atlas connection string and Discord webhook URL.


---

## Local Test Environment (Terraform + LocalStack)

All test resources are defined in the `infra/` directory and provisioned against LocalStack.

### 1\. Start Docker Desktop

Ensure Docker Desktop is running before starting LocalStack.

### 2\. Start LocalStack

Open PowerShell and run:

```
localstack start -d
```

Verify that LocalStack is running before continuing.

### 3\. Configure Terraform

Navigate to the infrastructure directory:

```
cd infra
```

Copy the example Terraform variables file:

```
Copy-Item terraform.tfvars.example terraform.tfvars
```

Edit `terraform.tfvars` if any configuration values need to be adjusted.

### 4\. Initialize Terraform

Run this command the first time you provision the environment:

```
terraform init
```

### 5\. Provision the Test Resources

```
terraform apply
```

Review the execution plan and confirm the changes when prompted.

Terraform creates deliberately misconfigured resources to give CloudGuard real findings to detect, including:

- An S3 bucket using AES256 encryption instead of customer-managed KMS encryption.
- An S3 bucket without the required `Environment` tag.
- An over-permissive IAM role with wildcard permissions.

These resources provide a repeatable test environment for validating detection, remediation, alerting, and audit logging.

### Resetting the Lab

CloudGuard modifies resources when it automatically remediates issues. Because the scanner operates on Terraform-managed resources, the infrastructure may drift from the Terraform configuration after a scan.

Run the following command to restore the lab to its configured state:

```
terraform apply
```

Review the proposed changes before confirming them.

Run this reset step at the beginning of each test session if resources have been modified or LocalStack has restarted. Verify the actual state after a restart, since persistence behavior depends on the LocalStack configuration and deployment.

---

## Running the Scanner

From the repository root, activate your virtual environment if necessary and run:

```
python scanner\scan.py
```

For each scan, CloudGuard:

1. Inspects the configured AWS resources.
2. Detects security misconfigurations.
3. Automatically remediates eligible low-risk issues.
4. Records scan results and findings in MongoDB Atlas.
5. Sends a single severity-ranked summary alert to Discord when issues are detected or remediated.

Clean scans do not send Discord alerts, helping reduce alert fatigue.

---

## Running the Tests

### Unit Tests

Unit tests use `moto` to mock AWS services in memory.

Run:

```
pytest tests\unit --cov=scanner -v
```

The unit tests cover the detection rules, negative cases, and failure scenarios, including:

- Remediation errors.
- Database write failures.
- Discord webhook outages.
- Compliant resources.
- Misconfigured resources.

### Integration Tests

Run:

```
pytest tests\integration -v
```

Integration tests validate behavior against the configured test environment and MongoDB Atlas.

**Note:** These tests write directly to the configured Atlas cluster and clean up after themselves. Ensure the integration-test database and credentials are configured correctly before running them.

---

## Design Notes

### 1\. Dependency Injection

AWS and database clients are passed into functions rather than created internally.

This approach improves testability, makes it easier to substitute mocked dependencies with `moto`, and separates business logic from infrastructure setup.

### 2\. Log Everything, Alert Selectively

Every scan result, including compliant resources, is recorded in MongoDB Atlas.

Discord alerts are reserved for security problems and automatic remediation events. This keeps the audit trail comprehensive without flooding the notification channel with routine success messages.

### 3\. Resilient Execution

Failures in remediation, database writes, or Discord webhook delivery are caught and reported without unnecessarily stopping the processing of remaining resources.

This allows the scanner to continue working through other resources when an individual operation fails.

### 4\. S3 Default Encryption Nuance

AWS enables server-side encryption with S3-managed keys (SSE-S3) by default for new S3 buckets. However, some compliance standards require server-side encryption with AWS KMS keys, potentially including customer-managed keys.

CloudGuard's encryption rule is designed to identify buckets that do not meet the configured KMS encryption requirement rather than treating default SSE-S3 encryption as sufficient.

The precise compliance requirement depends on the applicable policy. If customer-managed keys are mandatory, the scanner should validate the KMS key configuration rather than simply checking for the `aws:kms` encryption algorithm.

### 5\. Terraform Drift

CloudGuard actively modifies resources managed by Terraform, which can cause `terraform plan` to report drift after a scan.

For this test environment, `terraform apply` can restore the configured resources.

Potential production approaches include:

- Using Terraform lifecycle settings such as `ignore_changes` for carefully selected remediated attributes.
- Having the scanner open a pull request with the proposed infrastructure change instead of directly modifying resources.
- Integrating remediation with an approved infrastructure-as-code workflow.

Any drift-management strategy should be designed carefully to avoid concealing unintended infrastructure changes.

### 6\. Pointing CloudGuard at Real AWS

To run CloudGuard against a real AWS account:

1. Remove the LocalStack-specific endpoint configuration from the Terraform provider.
2. Remove LocalStack-specific `skip_*` settings where applicable.
3. Remove `endpoint_url` arguments from the scanner's AWS client configuration.
4. Configure real AWS credentials through environment variables, an AWS profile, or an appropriate IAM role.
5. Review the detection and remediation rules against your organization's security policies.
6. Run the scanner with least-privilege permissions and validate its behavior in a non-production environment first.

**Note:** Automatic remediation can change production resources. Test thoroughly and establish appropriate permissions, monitoring, and approval controls before enabling production remediation.

### 7\. MongoDB Atlas Network Access

The original test setup allows MongoDB Atlas connections from any IP address because home and CI runner addresses may change frequently.

This configuration increases exposure and should not be used as a production default.

For improved security:

- Restrict Atlas network access to known IP addresses or approved network paths.
- Use private connectivity where appropriate.
- Store database credentials in a secrets manager or CI secret store.
- Apply least-privilege database access.
- Rotate credentials regularly.

Database credentials should not be treated as the only security boundary.

---

## Future Improvements

The following features are planned:

- **GitHub Actions CI:** Run automated tests on pushes and pull requests.
- **Scheduled Scans:** Execute CloudGuard periodically through GitHub Actions.
- **React Dashboard:** Visualize scan history, findings, severity levels, and remediation status.
- **Vercel Deployment:** Host the dashboard.
- **Enhanced Remediation Workflows:** Add approval-based remediation and pull-request-based infrastructure fixes.
- **Expanded Detection Coverage:** Add more AWS security and cost governance rules.


**CloudGuard — Detect misconfigurations. Automate safe fixes. Maintain an auditable cloud security posture.**