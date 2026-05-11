import os

from openai import AzureOpenAI
from azure.identity import DefaultAzureCredential
from azure.keyvault.secrets import SecretClient
from dotenv import load_dotenv

load_dotenv()

credential = DefaultAzureCredential()
kv_url = os.getenv("AZURE_KEYVAULT_URL")

kv = SecretClient(
    vault_url=kv_url,
    credential=credential
)

endpoint = kv.get_secret("aoai-endpoint").value
api_key = kv.get_secret("aoai-api-key").value
deployment = kv.get_secret("aoai-deployment").value

client = AzureOpenAI(
    api_key=api_key,
    api_version="2025-01-01-preview",
    azure_endpoint=endpoint
)

response = client.chat.completions.create(
    model=deployment,
    messages=[
        {"role": "user", "content": "What's the time now?"}
    ]
)

print(response.choices[0].message.content)