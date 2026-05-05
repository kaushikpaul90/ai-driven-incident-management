import json
import os

class RAGEngine:
    def __init__(self, kb_path):
        self.kb = []
        self.load_json(kb_path)

    def load_json(self, kb_path):
        json_file = os.path.join(kb_path, "knowledge_base.json")

        if not os.path.exists(json_file):
            raise ValueError("knowledge_base.json not found!")

        with open(json_file, "r") as f:
            self.kb = json.load(f)

    def retrieve(self, query, top_k=3):
        query = query.lower()
        matches = []

        for entry in self.kb:
            patterns = entry.get("log_patterns", [])
            score = 0

            for p in patterns:
                if p.lower() in query:
                    score += 1

            if score > 0:
                matches.append((score, entry))

        # sort by score
        matches = sorted(matches, key=lambda x: x[0], reverse=True)

        results = []

        for _, entry in matches[:top_k]:
            content = f"""
                        Incident Type: {entry.get("error_type")}
                        Category: {entry.get("category")}

                        Log Patterns: {entry.get("log_patterns")}

                        Disambiguation Rules:
                        {entry.get("disambiguation")}

                        Root Cause:
                        {entry.get("root_cause")}

                        Resolution:
                        {entry.get("resolution_hint")}
                    """

            results.append({
                "content": content,
                "metadata": {
                    "source": "json_kb",
                    "filename": "knowledge_base.json"
                }
            })

        return results
    
    def match_kb_entry(self, text):
        text = text.lower()

        best_match = None
        best_score = 0

        for entry in self.kb:
            score = 0

            for pattern in entry.get("log_patterns", []):
                if pattern.lower() in text:
                    score += 1

            if score > best_score:
                best_score = score
                best_match = entry

        return best_match