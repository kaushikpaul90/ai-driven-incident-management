import json
import ollama


class EventClassifier:
    def __init__(self, model="llama3"):
        self.model = model

    def build_prompt(self, text):
        return f"""
                You are an expert SRE (Site Reliability Engineer).

                Classify the system state based on the logs.

                Categories:
                1. corrected_event → errors detected but corrected automatically (NO ACTION needed)
                2. warning → potential issue, needs monitoring
                3. failure → real failure, requires diagnosis and remediation

                Rules:
                - "corrected", "CE", "bit sparing" → corrected_event
                - repeated minor errors → warning
                - "failed", "fatal", "unable" → failure

                Logs:
                {text}

                Return ONLY valid JSON:
                {{
                "state": "corrected_event" OR "warning" OR "failure",
                "confidence": 0.0-1.0
                }}
            """

    def classify(self, text):
        response = ollama.chat(
            model=self.model,
            messages=[{"role": "user", "content": self.build_prompt(text)}]
        )

        try:
            return json.loads(response["message"]["content"])
        except:
            return {"state": "failure", "confidence": 0.5}  # safe fallback