resource "aws_lambda_permission" "sns_invoke" {
    statement_id  = "AllowSNSInvoke"
    action        = "lambda:InvokeFunction"
    function_name = aws_lambda_function.incident_processor.function_name
    principal     = "sns.amazonaws.com"
    source_arn    = aws_sns_topic.incident_alerts.arn
}

resource "aws_iam_role_policy" "lambda_permissions" {
    name = "incidentiq-lambda-permissions"
    role = aws_iam_role.lambda_role.id

    policy = jsonencode({
        Version = "2012-10-17"
        Statement = [
            {
                Effect   = "Allow"
                Action   = [
                    "dynamodb:PutItem",
                    "dynamodb:GetItem",
                    "dynamodb:Query",
                    "dynamodb:Scan"
                ]
                Resource = aws_dynamodb_table.incidentiq_table.arn
            },
            {
                Effect   = "Allow"
                Action   = ["bedrock:InvokeModel"]
                Resource = "*"
            },
            {
                Effect   = "Allow"
                Action   = [
                    "logs:GetLogEvents",
                    "logs:FilterLogEvents"
                ]
                Resource = "*"
            }
        ]
    })
}
