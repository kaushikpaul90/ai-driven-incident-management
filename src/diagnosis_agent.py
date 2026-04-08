import ollama
import json
import re

class DiagnosisAgent:

    def __init__(self, model="llama3"):
        self.model = model
    
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

        response = ollama.chat(
            model=self.model,
            messages=[{"role": "user", "content": prompt}],
            options={"temperature": 0}
        )

        content = response["message"]["content"]

        # Extract JSON block safely
        try:
            json_match = re.search(r'\{.*\}', content, re.DOTALL)
            if json_match:
                return json.loads(json_match.group())
            else:
                return {"error": "No JSON found", "raw_output": content}
        except:
            return {"error": "Invalid JSON", "raw_output": content}