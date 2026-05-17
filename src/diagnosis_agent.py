# import ollama
import json
import re
from llm_client import chat

class DiagnosisAgent:

    # def __init__(self, model="llama3"):
    #     self.model = model

    def __init__(self):
        pass
    
    def build_prompt(self, incident_window, retrieved_docs):
        docs_text = ""

        for doc in retrieved_docs:
            source = doc["metadata"]["source"]
            filename = doc["metadata"]["filename"]

            docs_text += f"\n[Source: {source} | {filename}]\n"
            docs_text += doc["content"]
            docs_text += "\n---\n"

        prompt = f"""
                    You are a distributed systems diagnosis expert.

                    Use ONLY the provided context.

                    Incident log window:
                    --------------------
                    {incident_window}
                    --------------------

                    Knowledge base:
                    --------------------
                    {docs_text}
                    --------------------

                    Analyze the incident and provide a structured diagnosis.

                    DIAGNOSIS INSTRUCTIONS:

                    Analyze the incident dynamically from the logs.

                    IMPORTANT:
                    - Do NOT force predefined categories.
                    - Preserve the exact technical terminology from the logs.
                    - The incident_type should reflect the dominant failure signature.
                    - Prefer specific incident names over generic categories.
                    - Root cause MUST ONLY be inferred from the provided logs.
                    - Do NOT introduce unrelated hardware or memory errors.
                    - Do NOT mention TLB/cache/ECC unless explicitly present in logs.
                    - If evidence is insufficient, keep root cause conservative.
                    - Prefer infrastructure-specific terminology from logs.
                    - Avoid overly generic root causes like "Network Issue".
                    - Summarize failures using actual daemon/component names where possible.

                    Examples:
                    - "data TLB error interrupt"
                    - "instruction cache parity error"
                    - "CioStream socket link severed"
                    - "machine check timeout"
                    - "application image loading failure"

                    Avoid oversimplified labels like:
                    - "Network Issue"
                    - "Hardware Failure"
                    unless the logs are too ambiguous.

                    Respond ONLY in valid JSON format with the following fields:
                    {{
                        "incident_type": "...",
                        "root_cause": "...",
                        "severity": "Low | Medium | High | Critical",
                        "confidence": 0.0
                    }}
                """

        return prompt

    def diagnose(self, incident_window, retrieved_docs):
        prompt = self.build_prompt(incident_window, retrieved_docs)

        content = chat([
            {
                "role": "user",
                "content": prompt
            }
        ])

        # Extract JSON block safely
        try:
            json_match = re.search(r'\{.*\}', content, re.DOTALL)
            if json_match:
                return json.loads(json_match.group())
            else:
                return {"error": "No JSON found", "raw_output": content}
        except:
            return {"error": "Invalid JSON", "raw_output": content}