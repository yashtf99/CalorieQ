import os
from dotenv import load_dotenv
from langchain_aws import ChatBedrockConverse

load_dotenv()

aws_token = os.getenv("AWS_BEARER_TOKEN_BEDROCK")
if not aws_token:
    raise ValueError("AWS_BEARER_TOKEN_BEDROCK not found in .env file")

llm = ChatBedrockConverse(
    model="global.amazon.nova-2-lite-v1:0",
    region_name="us-east-1"
)

response = llm.invoke("Explain RAG in one sentence.")

print(response.content)