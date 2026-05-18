"""Discover frequent error templates in a BGL dataset."""

import re
from collections import Counter

LOG_FILE = "data/BGL.log"


def normalize_log_line(line):
    """Normalize timestamps, node IDs, IPs, and numbers in a log line."""

    normalized = line.strip()
    normalized = re.sub(r"\d{4}\.\d{2}\.\d{2}", "<DATE>", normalized)
    normalized = re.sub(r"\d{4}-\d{2}-\d{2}-[\d\.]+", "<TIMESTAMP>", normalized)
    normalized = re.sub(r"\b\d+\.\d+\.\d+\.\d+\b", "<IP>", normalized)
    normalized = re.sub(r"R\d+-M\d+-N\w+-[A-Z]", "<NODE>", normalized)
    normalized = re.sub(r"\b\d+\b", "<NUM>", normalized)
    normalized = re.sub(r"\s+", " ", normalized)
    return normalized.strip()


def main():
    """Print the most common normalized error templates from the dataset."""

    template_counter = Counter()
    with open(LOG_FILE, "r", errors="ignore") as stream:
        for line in stream:
            template_counter[normalize_log_line(line)] += 1

    print("\n===== DISCOVERED ERROR TYPES =====\n")
    for template, count in template_counter.most_common(50):
        print(f"\nCOUNT: {count}")
        print(template)


if __name__ == "__main__":
    main()
