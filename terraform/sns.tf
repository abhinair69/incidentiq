resource "aws_sns_topic" "incident_alerts" {
    name = "incidentiq-alerts"

}

resource "aws_sns_topic_subscription" "lambda_trigger" {
    topic_arn = aws_sns_topic.incident_alerts.arn
    protocol = "lambda"
    endpoint = aws_lambda_function.incident_processor.arn
}