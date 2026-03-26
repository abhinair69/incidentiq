import json
import boto3
import uuid
from datetime import datetime, timezone


dynamodb = boto3.resource("dynamodb")
table = dynamodb.Table("incidentiq-table")
bedrock = boto3.client("bedrock-runtime", region_name="us-east-1")


def lambda_handler(event, context):
    # SNS trigger (auto-detected incident from CloudWatch alarm)
    if "Records" in event and event["Records"][0].get("EventSource") == "aws:sns":
        return handle_sns_event(event)

    # API Gateway trigger
    method = event.get("requestContext", {}).get("http", {}).get("method")

    if method == "POST":
        return handle_manual_incident(event)
    elif method == "GET":
        return get_incidents(event)
    else:
        return response(400, {"error": "Unsupported method"})


def handle_sns_event(event):
    """Process auto-detected incident from CloudWatch alarm via SNS."""
    sns_message = json.loads(event["Records"][0]["Sns"]["Message"])

    alarm_name = sns_message.get("AlarmName", "Unknown")
    description = sns_message.get("AlarmDescription", "No description")
    reason = sns_message.get("NewStateReason", "No reason provided")

    incident_details = (
        f"CloudWatch Alarm: {alarm_name}\n"
        f"Description: {description}\n"
        f"Reason: {reason}"
    )

    ai_analysis = analyze_with_bedrock(incident_details)

    incident = save_incident(
        source="auto",
        title=f"Alarm: {alarm_name}",
        details=incident_details,
        ai_analysis=ai_analysis,
    )

    return response(200, incident)


def handle_manual_incident(event):
    """Process manually reported incident from API Gateway POST."""
    raw_body = event.get("body", "{}")
    try:
        body = json.loads(raw_body)
    except json.JSONDecodeError:
        body = json.loads(raw_body.replace("\r", "").replace("\n", " "))

    title = body.get("title")
    details = body.get("details")

    if not title or not details:
        return response(400, {"error": "title and details are required"})

    ai_analysis = analyze_with_bedrock(details)

    incident = save_incident(
        source="manual",
        title=title,
        details=details,
        ai_analysis=ai_analysis,
    )

    return response(201, incident)


def get_incidents(event):
    """Return all incidents, most recent first."""
    query_params = event.get("queryStringParameters") or {}
    limit = int(query_params.get("limit", 20))

    result = table.scan(Limit=limit)
    items = sorted(result.get("Items", []), key=lambda x: x["created_at"], reverse=True)

    return response(200, {"incidents": items, "count": len(items)})


def analyze_with_bedrock(incident_details):
    """Send incident details to Bedrock Nova Micro for root cause analysis."""
    prompt = (
        "You are an SRE incident analyst. Analyze the following incident and provide:\n"
        "1. Probable root cause\n"
        "2. Severity (critical/high/medium/low)\n"
        "3. Recommended immediate actions\n"
        "4. Preventive measures\n\n"
        "Keep it concise.\n\n"
        f"Incident:\n{incident_details}"
    )

    try:
        body = json.dumps({
            "inferenceConfig": {"maxTokens": 500},
            "messages": [{"role": "user", "content": [{"text": prompt}]}],
        })

        resp = bedrock.invoke_model(
            modelId="us.amazon.nova-micro-v1:0",
            contentType="application/json",
            accept="application/json",
            body=body,
        )

        result = json.loads(resp["body"].read())
        return result["output"]["message"]["content"][0]["text"]

    except Exception as e:
        return f"AI analysis unavailable: {str(e)}"


def save_incident(source, title, details, ai_analysis):
    """Save incident to DynamoDB and return the record."""
    incident = {
        "incident_id": str(uuid.uuid4()),
        "created_at": datetime.now(timezone.utc).isoformat(),
        "source": source,
        "title": title,
        "details": details,
        "ai_analysis": ai_analysis,
        "status": "open",
    }

    table.put_item(Item=incident)
    return incident


def response(status_code, body):
    """Return API Gateway compatible response."""
    return {
        "statusCode": status_code,
        "headers": {
            "Content-Type": "application/json",
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Methods": "GET, POST, OPTIONS",
            "Access-Control-Allow-Headers": "Content-Type",
        },
        "body": json.dumps(body, default=str),
    }
