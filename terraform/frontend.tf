resource "aws_s3_bucket" "frontend" {
    bucket = "incidentiq-frontend-036639178555"
}

resource "aws_s3_bucket_website_configuration" "frontend" {
    bucket = aws_s3_bucket.frontend.id

    index_document {
        suffix = "index.html"
    }
}

resource "aws_s3_bucket_public_access_block" "frontend" {
    bucket = aws_s3_bucket.frontend.id

    block_public_acls       = false
    block_public_policy     = false
    ignore_public_acls      = false
    restrict_public_buckets = false
}

resource "aws_s3_bucket_policy" "frontend" {
    bucket     = aws_s3_bucket.frontend.id
    depends_on = [aws_s3_bucket_public_access_block.frontend]

    policy = jsonencode({
        Version = "2012-10-17"
        Statement = [{
            Sid       = "PublicReadGetObject"
            Effect    = "Allow"
            Principal = "*"
            Action    = "s3:GetObject"
            Resource  = "${aws_s3_bucket.frontend.arn}/*"
        }]
    })
}

resource "aws_s3_object" "index_html" {
    bucket       = aws_s3_bucket.frontend.id
    key          = "index.html"
    source       = "../frontend/index.html"
    content_type = "text/html"
    etag         = filemd5("../frontend/index.html")
}

output "frontend_url" {
    value = "http://${aws_s3_bucket_website_configuration.frontend.website_endpoint}"
}
