# IncidentIQ - AI-Powered Incident Response Platform

An end-to-end serverless incident response platform that automatically detects cloud infrastructure issues, uses AI to perform root cause analysis, and provides a dashboard for incident management.

## Architecture

```
                    AUTOMATIC DETECTION
                    ───────────────────
    CloudWatch Alarm ──▶ SNS ──▶ Lambda ──▶ CloudWatch Logs
                                   │              │
                                   │     (fetch error details)
                                   │
                                   ▼
                              Bedrock AI ──▶ Root Cause Analysis
                                   │
                                   ▼
                              DynamoDB ──▶ Store Incident

                    MANUAL REPORTING
                    ────────────────
    User ──▶ S3 Dashboard ──▶ API Gateway ──▶ Lambda ──▶ Bedrock AI
                                                │              │
                                                │    (AI analysis)
                                                ▼
                                           DynamoDB

                    INCIDENT VIEWING
                    ────────────────
    User ──▶ S3 Dashboard ──▶ API Gateway ──▶ Lambda ──▶ DynamoDB
                                                │
                                                ▼
                                         Return Incidents
```

## AWS Services

| Service | Purpose |
|---------|---------|
| **AWS Lambda** | Core processing - handles incident creation, AI analysis, and retrieval |
| **Amazon API Gateway v2** | HTTP API with POST/GET routes for incident management |
| **Amazon DynamoDB** | NoSQL database for incident storage (PAY_PER_REQUEST) |
| **Amazon Bedrock** | AI-powered root cause analysis using Amazon Nova Micro |
| **Amazon SNS** | Fan-out notifications - routes CloudWatch alarms to Lambda + email |
| **Amazon CloudWatch** | 3 metric alarms monitoring Lambda errors, throttles, and duration |
| **Amazon S3** | Static website hosting for the frontend dashboard |
| **AWS IAM** | Least-privilege roles and policies for all service interactions |

## DevOps Pipeline

```
    Push to main
         │
         ▼
  ┌─────────────┐     ┌──────────────┐     ┌─────────────────┐
  │  LINT & TEST │────▶│ PACKAGE      │────▶│ TERRAFORM       │
  │  pytest      │     │ zip Lambda   │     │ init/plan/apply  │
  │  moto mocks  │     │ upload artifact    │ S3 remote state  │
  └─────────────┘     └──────────────┘     └─────────────────┘
        │                                          │
   PRs: stop here                          Only on main branch
```

- **CI**: Automated testing with pytest and moto (AWS mocking library)
- **CD**: GitHub Actions deploys infrastructure via Terraform on every push to main
- **State**: Terraform state stored in S3 with versioning enabled
- **PRs**: Only run test + package stages (no deployment)

## Monitoring & Alerting

Three CloudWatch alarms monitor the Lambda function:

| Alarm | Metric | Threshold | Purpose |
|-------|--------|-----------|---------|
| Lambda Errors | `Errors` | > 1 in 5 min | Detects function failures |
| Lambda Throttles | `Throttles` | > 0 in 5 min | Detects capacity issues |
| Lambda Duration | `Duration` | > 15s avg in 10 min | Detects performance degradation |

When alarms fire, SNS simultaneously:
1. Sends email notification to the on-call engineer
2. Triggers Lambda to auto-create an incident with AI analysis

## Project Structure

```
incidentiq/
├── .github/
│   └── workflows/
│       └── deploy.yml          # CI/CD pipeline
├── frontend/
│   └── index.html              # Dashboard UI
├── src/
│   └── lambdas/
│       └── handler.py          # Lambda function code
├── terraform/
│   ├── provider.tf             # AWS provider + S3 backend
│   ├── lambda.tf               # Lambda function + IAM role
│   ├── dynamodb.tf             # Incidents table
│   ├── apigateway.tf           # HTTP API + routes + CORS
│   ├── sns.tf                  # Alert topic + subscriptions
│   ├── iam.tf                  # Permissions (least-privilege)
│   ├── monitoring.tf           # CloudWatch alarms + email alerts
│   ├── frontend.tf             # S3 static website hosting
│   └── outputs.tf              # API endpoint, function name, table name
├── tests/
│   └── test_handler.py         # Unit tests with moto
└── README.md
```

## API Endpoints

### POST /incidents
Create a new incident with AI-powered analysis.

```bash
curl -X POST https://<api-id>.execute-api.ap-south-1.amazonaws.com/incidents \
  -H "Content-Type: application/json" \
  -d '{"title": "High CPU usage", "details": "CPU at 95% on prod-web-01"}'
```

**Response:**
```json
{
  "incident_id": "uuid",
  "title": "High CPU usage",
  "details": "CPU at 95% on prod-web-01",
  "source": "manual",
  "status": "open",
  "ai_analysis": "Probable Root Cause: ...\nSeverity: High\nRecommended Actions: ...",
  "created_at": "2026-03-26T14:29:30+00:00"
}
```

### GET /incidents
Retrieve all incidents sorted by most recent.

```bash
curl https://<api-id>.execute-api.ap-south-1.amazonaws.com/incidents
```

## Security

- **IAM Least Privilege**: Lambda role only has permissions for specific DynamoDB actions (PutItem, GetItem, Query, Scan), Bedrock InvokeModel, and CloudWatch Logs read
- **No hardcoded credentials**: AWS credentials managed via GitHub Secrets and IAM roles
- **Input validation**: API validates required fields before processing
- **CORS configured**: API Gateway restricts allowed methods and headers

## Cost

Designed to run within AWS free tier / minimal cost:

| Service | Monthly Cost |
|---------|-------------|
| Lambda | Free (1M requests/month) |
| API Gateway | Free (1M calls/month) |
| DynamoDB | Free (25GB, PAY_PER_REQUEST) |
| Bedrock Nova Micro | ~$0.01-0.05 |
| S3 | ~$0.00 |
| SNS | Free (1M publishes) |
| CloudWatch | Free (basic metrics) |
| **Total** | **< $0.10/month** |

## Tech Stack

- **Language**: Python 3.12
- **IaC**: Terraform
- **CI/CD**: GitHub Actions
- **Testing**: pytest + moto
- **AI Model**: Amazon Nova Micro (via Bedrock)
- **Frontend**: Vanilla HTML/CSS/JS
