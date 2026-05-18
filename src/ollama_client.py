"""Ollama client wrapper for LLM chat integration."""

import os
import ollama
from dotenv import load_dotenv

load_dotenv()

MODEL = os.getenv("OLLAMA_MODEL", "llama3")


def ollama_chat(messages):
    """Send chat messages to an Ollama model and return the response text."""

    response = ollama.chat(model=MODEL, messages=messages)
    return response["message"]["content"]
