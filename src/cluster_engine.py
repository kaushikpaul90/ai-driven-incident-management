import re
from collections import defaultdict
from venv import logger

class ClusterEngine:
    def __init__(self, kb):
        self.kb = kb

    def classify_line(self, line):
        line_lower = line.lower()

        for entry in self.kb:
            for pattern in entry.get("log_patterns", []):
                if pattern.lower() in line_lower:
                    return entry["error_type"]

        return "unknown"

    def normalize(self, text):
        # remove special characters and normalize
        return re.sub(r'[^a-zA-Z0-9\s]', ' ', text.lower())

    def cluster_window(self, text, kb):
        clusters = defaultdict(list)

        # Split into segments (better than words)
        segments = re.split(r'(?=R\d{2}-M\d|ciod:|total of)', text)

        for segment in segments:
            segment_norm = self.normalize(segment)
            # logger.info(f"DEBUG SEGMENT: {segment_norm[:100]}")
            matched = False

            for entry in kb:
                examples = entry.get("examples", [])

                for example in examples:
                    example_norm = self.normalize(example)

                    # use keyword overlap matching
                    words = example_norm.split()

                    match_count = sum(1 for w in words if w in segment_norm)

                    if match_count >= max(2, len(words) // 4):
                        clusters[entry["error_type"]].append(segment)
                        matched = True
                        break

                if matched:
                    break

            if not matched:
                clusters["unknown"].append(segment)

        return clusters