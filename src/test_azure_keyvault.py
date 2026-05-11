import os

from azure.identity import DefaultAzureCredential
from azure.keyvault.secrets import SecretClient
from dotenv import load_dotenv

load_dotenv()

credential = DefaultAzureCredential()
kv_url = os.getenv("AZURE_KEYVAULT_URL")

client = SecretClient(
    vault_url=kv_url,
    credential=credential
)

secret = client.get_secret("aoai-endpoint")

print(secret.value)