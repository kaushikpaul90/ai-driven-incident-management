import os
from dotenv import load_dotenv

from azure.identity import DefaultAzureCredential
from azure.keyvault.secrets import SecretClient


load_dotenv()


class KeyVaultClient:

    _client = None

    @classmethod
    def get_client(cls):

        if cls._client is None:

            vault_url = os.getenv("AZURE_KEYVAULT_URL")

            credential = DefaultAzureCredential()

            cls._client = SecretClient(
                vault_url=vault_url,
                credential=credential
            )

        return cls._client


    @classmethod
    def get_secret(cls, secret_name):

        client = cls.get_client()

        secret = client.get_secret(secret_name)

        return secret.value