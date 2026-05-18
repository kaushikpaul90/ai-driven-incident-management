"""Azure Key Vault helper for retrieving secret values."""

import os
from dotenv import load_dotenv
from azure.identity import DefaultAzureCredential
from azure.keyvault.secrets import SecretClient

load_dotenv()


class KeyVaultClient:
    """Singleton wrapper around Azure Key Vault secret retrieval."""

    _client = None

    @classmethod
    def get_client(cls):
        """Create or return an existing SecretClient."""

        if cls._client is None:
            vault_url = os.getenv("AZURE_KEYVAULT_URL")
            cls._client = SecretClient(vault_url=vault_url, credential=DefaultAzureCredential())
        return cls._client

    @classmethod
    def get_secret(cls, secret_name):
        """Retrieve a secret value by name."""

        client = cls.get_client()
        secret = client.get_secret(secret_name)
        return secret.value
