"""Azure OpenAI chat client wrapper for managed deployments."""

import os
from dotenv import load_dotenv
from openai import AzureOpenAI
from keyvault_client import KeyVaultClient

load_dotenv()


class AzureOpenAIClient:
    """Azure OpenAI client used for chat completions."""

    def __init__(self):
        endpoint = KeyVaultClient.get_secret("aoai-endpoint")
        api_key = KeyVaultClient.get_secret("aoai-api-key")
        self.deployment = KeyVaultClient.get_secret("aoai-chat-deployment")
        self.client = AzureOpenAI(
            api_key=api_key,
            api_version=os.getenv("AZURE_OPENAI_API_VERSION", "2025-01-01-preview"),
            azure_endpoint=endpoint,
        )

    def azure_chat(self, prompt):
        """Send a prompt to Azure OpenAI and return the assistant content."""

        response = self.client.chat.completions.create(
            model=self.deployment,
            messages=[{"role": "user", "content": prompt}],
            temperature=0,
        )
        return response.choices[0].message.content
