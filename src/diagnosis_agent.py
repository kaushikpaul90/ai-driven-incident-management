import ollama
import json
import re

class DiagnosisAgent:

    def __init__(self, model="llama3"):
        self.model = model
    
    def build_prompt(self, incident_window, retrieved_docs):
        docs_text = ""

        for doc in retrieved_docs:
            source = doc.get("metadata", {}).get("source", doc.get("error_type", "knowledge_base"))
            filename = doc.get("metadata", {}).get("filename", "N/A")

            docs_text += f"\n[Source: {source} | {filename}]\n"
            content = doc.get("content") or doc.get("page_content") or doc.get("description", "")
            docs_text += content

            docs_text += "\n---\n"

        prompt = f"""
                    You are a distributed systems diagnosis expert.

                    Use ONLY the provided context.
                    Use disambiguation rules strictly before classifying.

                    Incident log window:
                    --------------------
                    {incident_window}
                    --------------------

                    Knowledge base:
                    --------------------
                    {docs_text}
                    --------------------

                    Analyze the incident and provide a structured diagnosis.

                    CLASSIFICATION RULES (apply strictly):
                    - If the log contains "TLB" or "cache parity" or "ECC" or "hardware"
                      → incident_type must reflect the hardware fault (e.g. "TLB Error",
                        "Cache Parity Error"). root_cause must describe the hardware issue.
                    - If the log contains "CioStream" or "socket" or "failed to read message
                      prefix" WITHOUT any hardware fault keywords
                      → incident_type should be "Network Connectivity Issue". root_cause
                        should describe the socket/stream failure.
                    - Do NOT mix hardware incident_type with a network root_cause or vice versa.
                    - You must not return generic labels like "Hardware Fault". Use the pre-classified incident type as primary context.

                    IMPORTANT:
                    - If the log contains words like "corrected", "recovered", "handled", "no error",
                    then it is NOT a failure.
                    - Only classify as FAILURE if the issue is unresolved or causing disruption.

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

        try:
            json_match = re.search(r'\{.*\}', content, re.DOTALL)
            if json_match:
                return json.loads(json_match.group())
            return {"error": "No JSON found"}
        except:
            return {"error": "Invalid JSON"}