
output "api_endpoint" {
    value = aws_apigatewayv2_api.incidents_api.api_endpoint
}

output "lambda_function_name" {
    value = aws_lambda_function.incident_processor.function_name
}

output "dynamodb_table_name" {
    value = aws_dynamodb_table.incidentiq_table.name
}