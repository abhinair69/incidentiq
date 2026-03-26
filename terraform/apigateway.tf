resource "aws_apigatewayv2_api" "incidents_api" {
    name          = "incidentiq-api"
    protocol_type = "HTTP"

    cors_configuration {
        allow_origins = ["*"]
        allow_methods = ["GET", "POST", "OPTIONS"]
        allow_headers = ["Content-Type"]
        max_age       = 3600
    }
}

resource "aws_apigatewayv2_integration" "lambda_integration" {
    api_id                 = aws_apigatewayv2_api.incidents_api.id
    integration_type       = "AWS_PROXY"
    integration_uri        = aws_lambda_function.incident_processor.invoke_arn
    payload_format_version = "2.0"
}

resource "aws_apigatewayv2_stage" "default_stage" {
    api_id      = aws_apigatewayv2_api.incidents_api.id
    name        = "$default"
    auto_deploy = true
}

resource "aws_apigatewayv2_route" "post_incident" {
    api_id    = aws_apigatewayv2_api.incidents_api.id
    route_key = "POST /incidents"
    target    = "integrations/${aws_apigatewayv2_integration.lambda_integration.id}"
}

resource "aws_apigatewayv2_route" "get_incidents" {
    api_id    = aws_apigatewayv2_api.incidents_api.id
    route_key = "GET /incidents"
    target    = "integrations/${aws_apigatewayv2_integration.lambda_integration.id}"
}


resource "aws_lambda_permission" "apigw_invoke" {
    statement_id  = "AllowAPIGWInvoke"
    action        = "lambda:InvokeFunction"
    function_name = aws_lambda_function.incident_processor.function_name
    principal     = "apigateway.amazonaws.com"
    source_arn    = "${aws_apigatewayv2_api.incidents_api.execution_arn}/*/*"
}