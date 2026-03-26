resource "aws_cloudwatch_metric_alarm" "lambda_errors" {
    alarm_name          = "incidentiq-lambda-errors"
    alarm_description   = "Triggers when Lambda errors exceed threshold"
    comparison_operator = "GreaterThanThreshold"
    evaluation_periods  = 1
    metric_name         = "Errors"
    namespace           = "AWS/Lambda"
    period              = 300
    statistic           = "Sum"
    threshold           = 1
    alarm_actions       = [aws_sns_topic.incident_alerts.arn]

    dimensions = {
        FunctionName = aws_lambda_function.incident_processor.function_name
    }
}

resource "aws_cloudwatch_metric_alarm" "lambda_throttles" {
    alarm_name          = "incidentiq-lambda-throttles"
    alarm_description   = "Triggers when Lambda is being throttled"
    comparison_operator = "GreaterThanThreshold"
    evaluation_periods  = 1
    metric_name         = "Throttles"
    namespace           = "AWS/Lambda"
    period              = 300
    statistic           = "Sum"
    threshold           = 0
    alarm_actions       = [aws_sns_topic.incident_alerts.arn]

    dimensions = {
        FunctionName = aws_lambda_function.incident_processor.function_name
    }
}

resource "aws_cloudwatch_metric_alarm" "lambda_duration" {
    alarm_name          = "incidentiq-lambda-high-duration"
    alarm_description   = "Triggers when Lambda execution time is too high"
    comparison_operator = "GreaterThanThreshold"
    evaluation_periods  = 2
    metric_name         = "Duration"
    namespace           = "AWS/Lambda"
    period              = 300
    statistic           = "Average"
    threshold           = 15000
    alarm_actions       = [aws_sns_topic.incident_alerts.arn]

    dimensions = {
        FunctionName = aws_lambda_function.incident_processor.function_name
    }
}

resource "aws_sns_topic_subscription" "email_alert" {
    topic_arn = aws_sns_topic.incident_alerts.arn
    protocol  = "email"
    endpoint  = "nairabhijith984@gmail.com"
}
