import os
from dotenv import load_dotenv

load_dotenv()

LLM_PROVIDER = os.getenv("LLM_PROVIDER", "ollama")

azure_client = None


def chat(prompt):

    global azure_client

    if LLM_PROVIDER == "azure":

        if azure_client is None:
            from azure_openai_client import AzureOpenAIClient
            azure_client = AzureOpenAIClient()

        prompt_text = prompt[0]["content"]

        return azure_client.azure_chat(prompt_text)

    elif LLM_PROVIDER == "ollama":

        from ollama_client import ollama_chat

        return ollama_chat(prompt)

    else:
        raise ValueError(
            f"Unsupported LLM provider: {LLM_PROVIDER}"
        )