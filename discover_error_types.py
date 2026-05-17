import re
from collections import Counter

LOG_FILE = "data/BGL.log"

template_counter = Counter()

with open(LOG_FILE, "r", errors="ignore") as f:

    for line in f:

        # ------------------------------------------------
        # NORMALIZATION
        # ------------------------------------------------

        normalized = line.strip()

        # Remove timestamps
        normalized = re.sub(
            r"\d{4}\.\d{2}\.\d{2}",
            "<DATE>",
            normalized
        )

        normalized = re.sub(
            r"\d{4}-\d{2}-\d{2}-[\d\.]+",
            "<TIMESTAMP>",
            normalized
        )

        # Remove IP addresses
        normalized = re.sub(
            r"\b\d+\.\d+\.\d+\.\d+\b",
            "<IP>",
            normalized
        )

        # Remove node identifiers
        normalized = re.sub(
            r"R\d+-M\d+-N\w+-[A-Z]",
            "<NODE>",
            normalized
        )

        # Remove numbers
        normalized = re.sub(
            r"\b\d+\b",
            "<NUM>",
            normalized
        )

        # Collapse spaces
        normalized = re.sub(
            r"\s+",
            " ",
            normalized
        )

        template_counter[normalized] += 1

# ------------------------------------------------
# SHOW MOST COMMON ERROR TYPES
# ------------------------------------------------

print("\n===== DISCOVERED ERROR TYPES =====\n")

for template, count in template_counter.most_common(50):

    print(f"\nCOUNT: {count}")
    print(template)