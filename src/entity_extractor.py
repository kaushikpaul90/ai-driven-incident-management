import re
from collections import Counter

class EntityExtractor:

    def extract_nodes(self, text):
        patterns = [
            r'R\d{2}-M\d-[A-Z0-9\-]+',          # Full node IDs
            r'R\d{2}-M\d-L\d-U\d-C',            # Specific format
            r'R\d{2}-M\d-N\d-C:J\d{2}-U\d{2}',  # Extended format
        ]

        nodes = set()

        for pattern in patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            nodes.update([m.lower() for m in matches])

        return sorted(nodes)

    def extract_services(self, text, kb_entry):
        services = set()

        # 1. From KB category (PRIMARY SOURCE)
        category = kb_entry.get("category", "").lower()

        if "memory" in category:
            services.add("memory")
        if "cpu" in category:
            services.add("cpu")
        if "network" in category:
            services.add("io")
        if "interconnect" in category:
            services.add("interconnect")
        if "disk" in category:
            services.add("disk")
        if "filesystem" in category:
            services.add("filesystem")

        # 2. From KB error_type (fallback)
        error_type = kb_entry.get("error_type", "").lower()

        if "cache" in error_type:
            services.add("cache")
        if "ecc" in error_type:
            services.add("memory")

        # 3. From actual log text (last fallback)
        text_lower = text.lower()

        if "ciostream" in text_lower or "socket" in text_lower:
            services.add("io")
        if "linkcard" in text_lower:
            services.add("interconnect")

        return list(services)