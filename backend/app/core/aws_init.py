import os
from config import settings


def ensure_aws_credentials() -> None:
    """Set AWS credentials from settings to environment."""
    if settings.AWS_BEARER_TOKEN_BEDROCK:
        os.environ["AWS_BEARER_TOKEN_BEDROCK"] = settings.AWS_BEARER_TOKEN_BEDROCK
