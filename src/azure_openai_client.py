import os
from openai import AzureOpenAI
from dotenv import load_dotenv
from keyvault_client import KeyVaultClient

load_dotenv()

# endpoint = os.getenv("AZURE_OPENAI_ENDPOINT")
# deployment = os.getenv("AZURE_OPENAI_DEPLOYMENT")
# api_version = os.getenv("AZURE_OPENAI_API_VERSION")

# api_key = os.getenv("AZURE_OPENAI_API_KEY")

# client = AzureOpenAI(
#     api_key=api_key,
#     api_version=api_version,
#     azure_endpoint=endpoint
# )


# def azure_chat(messages):

#     response = client.chat.completions.create(
#         model=deployment,
#         messages=messages,
#         temperature=0
#     )

#     return response.choices[0].message.content

class AzureOpenAIClient:

    def __init__(self):

        endpoint = KeyVaultClient.get_secret(
            "aoai-endpoint"
        )

        api_key = KeyVaultClient.get_secret(
            "aoai-api-key"
        )

        self.deployment = KeyVaultClient.get_secret(
            "aoai-chat-deployment"
        )

        self.client = AzureOpenAI(
            api_key=api_key,
            api_version=os.getenv(
                "AZURE_OPENAI_API_VERSION",
                "2025-01-01-preview"
            ),
            azure_endpoint=endpoint
        )


    def azure_chat(self, prompt):

        response = self.client.chat.completions.create(
            model=self.deployment,
            messages=[
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            temperature=0
        )

        return response.choices[0].message.content