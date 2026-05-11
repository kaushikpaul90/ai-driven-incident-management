import os
from sentence_transformers import SentenceTransformer
from openai import AzureOpenAI
from keyvault_client import KeyVaultClient
from dotenv import load_dotenv

load_dotenv()

class EmbeddingClient:

    def __init__(self):

        self.provider = os.getenv("EMBEDDING_PROVIDER", "local")

        # ------------------------------------------
        # LOCAL EMBEDDINGS
        # ------------------------------------------
        if self.provider == "local":

            self.model = SentenceTransformer(
                "all-MiniLM-L6-v2"
            )

        # ------------------------------------------
        # AZURE EMBEDDINGS
        # ------------------------------------------
        elif self.provider == "azure":

            endpoint = KeyVaultClient.get_secret(
                "aoai-endpoint"
            )

            api_key = KeyVaultClient.get_secret(
                "aoai-api-key"
            )

            self.deployment = KeyVaultClient.get_secret(
                "aoai-embedding-deployment"
            )

            self.client = AzureOpenAI(
                api_key=api_key,
                api_version=os.getenv(
                    "AZURE_OPENAI_API_VERSION",
                    "2025-01-01-preview"
                ),
                azure_endpoint=endpoint
            )

        else:
            raise ValueError(
                f"Unsupported embedding provider: {self.provider}"
            )

    # --------------------------------------------------
    # SINGLE TEXT
    # --------------------------------------------------
    def embed_text(self, text):

        if self.provider == "local":
            return self.model.encode(text).tolist()

        response = self.client.embeddings.create(
            model=self.deployment,
            input=text
        )

        return response.data[0].embedding

    # --------------------------------------------------
    # MULTIPLE TEXTS
    # --------------------------------------------------
    def embed_texts(self, texts):

        if self.provider == "local":
            return self.model.encode(texts).tolist()

        response = self.client.embeddings.create(
            model=self.deployment,
            input=texts
        )

        return [x.embedding for x in response.data]