import json
import os
import sys
import boto3
import pytest
from moto import mock_aws
from unittest.mock import patch, MagicMock

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src", "lambdas"))

os.environ["AWS_DEFAULT_REGION"] = "ap-south-1"
os.environ["AWS_ACCESS_KEY_ID"] = "testing"
os.environ["AWS_SECRET_ACCESS_KEY"] = "testing"


@pytest.fixture
def dynamodb_table():
    """Create a mock DynamoDB table for testing."""
    with mock_aws():
        dynamodb = boto3.resource("dynamodb", region_name="ap-south-1")
        table = dynamodb.create_table(
            TableName="incidentiq-table",
            KeySchema=[
                {"AttributeName": "incident_id", "KeyType": "HASH"},
                {"AttributeName": "created_at", "KeyType": "RANGE"},
            ],
            AttributeDefinitions=[
                {"AttributeName": "incident_id", "AttributeType": "S"},
                {"AttributeName": "created_at", "AttributeType": "S"},
            ],
            BillingMode="PAY_PER_REQUEST",
        )
        table.meta.client.get_waiter("table_exists").wait(TableName="incidentiq-table")
        yield table


@pytest.fixture
def mock_bedrock():
    """Mock the Bedrock API call."""
    mock_response = {
        "output": {"message": {"content": [{"text": "Root cause: High error rate detected. Severity: high. Action: Check logs."}]}}
    }
    mock_body = MagicMock()
    mock_body.read.return_value = json.dumps(mock_response).encode()

    with patch("handler.bedrock") as mock_client:
        mock_client.invoke_model.return_value = {"body": mock_body}
        yield mock_client


def test_manual_incident(dynamodb_table, mock_bedrock):
    """Test creating an incident via API Gateway POST."""
    with mock_aws():
        # Re-patch the table inside mock_aws context
        with patch("handler.table", dynamodb_table):
            from handler import lambda_handler

            event = {
                "requestContext": {"http": {"method": "POST"}},
                "body": json.dumps({
                    "title": "Database connection pool exhausted",
                    "details": "RDS connections maxed out at 100, app returning 503s",
                }),
            }

            result = lambda_handler(event, None)

            assert result["statusCode"] == 201
            body = json.loads(result["body"])
            assert body["title"] == "Database connection pool exhausted"
            assert body["source"] == "manual"
            assert body["status"] == "open"
            assert "ai_analysis" in body


def test_manual_incident_missing_fields(dynamodb_table, mock_bedrock):
    """Test that POST without required fields returns 400."""
    with patch("handler.table", dynamodb_table):
        from handler import lambda_handler

        event = {
            "requestContext": {"http": {"method": "POST"}},
            "body": json.dumps({"title": "Missing details field"}),
        }

        result = lambda_handler(event, None)
        assert result["statusCode"] == 400


def test_get_incidents(dynamodb_table, mock_bedrock):
    """Test retrieving incidents via API Gateway GET."""
    with mock_aws():
        with patch("handler.table", dynamodb_table):
            from handler import lambda_handler

            # Create an incident first
            post_event = {
                "requestContext": {"http": {"method": "POST"}},
                "body": json.dumps({
                    "title": "Test incident",
                    "details": "Something broke",
                }),
            }
            lambda_handler(post_event, None)

            # Now fetch
            get_event = {
                "requestContext": {"http": {"method": "GET"}},
                "queryStringParameters": {"limit": "10"},
            }

            result = lambda_handler(get_event, None)

            assert result["statusCode"] == 200
            body = json.loads(result["body"])
            assert body["count"] == 1
            assert body["incidents"][0]["title"] == "Test incident"


def test_sns_event(dynamodb_table, mock_bedrock):
    """Test processing an auto-detected incident from SNS."""
    with mock_aws():
        with patch("handler.table", dynamodb_table):
            from handler import lambda_handler

            event = {
                "Records": [{
                    "EventSource": "aws:sns",
                    "Sns": {
                        "Message": json.dumps({
                            "AlarmName": "HighErrorRate",
                            "AlarmDescription": "Lambda error rate > 5%",
                            "NewStateReason": "Threshold crossed: 3 datapoints > 5%",
                        })
                    }
                }]
            }

            result = lambda_handler(event, None)

            assert result["statusCode"] == 200
            body = json.loads(result["body"])
            assert body["source"] == "auto"
            assert "HighErrorRate" in body["title"]
