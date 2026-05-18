"""LLM diagnosis agent that produces structured incident summaries."""

import json
import re
from llm_client import chat


class DiagnosisAgent:
    """Wraps prompt construction and JSON extraction for diagnosis."""

    def __init__(self):
        pass

    def build_prompt(self, incident_window, retrieved_docs):
        """Create a diagnosis prompt from a log window and supporting documents."""

        docs_text = ""
        for doc in retrieved_docs:
            docs_text += f"\n[Source: {doc['metadata']['source']} | {doc['metadata']['filename']}]\n"
            docs_text += doc["content"]
            docs_text += "\n---\n"

        return f"""
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
- Respond ONLY in valid JSON format with the following fields:
{{
    "incident_type": "...",
    "root_cause": "...",
    "severity": "Low | Medium | High | Critical",
    "confidence": 0.0
}}
"""

    def _extract_json(self, text):
        """Extract the first JSON object from text."""

        match = re.search(r"\{.*\}", text, re.DOTALL)
        if not match:
            return None

        try:
            return json.loads(match.group())
        except json.JSONDecodeError:
            return None

    def diagnose(self, incident_window, retrieved_docs):
        """Run diagnosis against a log window and supporting knowledge.

        Returns a dictionary with incident diagnosis fields.
        """

        prompt = self.build_prompt(incident_window, retrieved_docs)
        content = chat([{"role": "user", "content": prompt}])
        parsed = self._extract_json(content)
        if parsed is None:
            return {"error": "Invalid JSON", "raw_output": content}
        return parsed
