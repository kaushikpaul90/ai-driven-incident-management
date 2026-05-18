"""Utility for categorizing BGL error logs and printing a summary."""

import re
from collections import Counter, defaultdict

LOG_FILE = "BGL.log"
ERROR_PATTERNS = {
    "network": [r"socket", r"control stream", r"connection", r"network", r"CioStream"],
    "hardware": [r"TLB", r"cache parity", r"ECC", r"hardware", r"machine check"],
    "memory": [r"memory", r"RAM", r"segmentation fault", r"malloc"],
    "filesystem": [r"filesystem", r"disk", r"I/O error", r"storage", r"block device"],
    "kernel": [r"kernel", r"panic", r"syscall"],
    "scheduler": [r"scheduler", r"job", r"queue"],
    "daemon": [r"daemon", r"service", r"process"],
}


def categorize_log_line(line):
    """Return the matching error category for a line."""

    text = line.lower()
    for category, patterns in ERROR_PATTERNS.items():
        for pattern in patterns:
            if re.search(pattern.lower(), text):
                return category
    return "unknown"


def main():
    """Read the BGL log and print category statistics with examples."""

    error_counts = Counter()
    sample_logs = defaultdict(list)

    with open(LOG_FILE, "r", errors="ignore") as stream:
        for line in stream:
            category = categorize_log_line(line)
            error_counts[category] += 1
            if len(sample_logs[category]) < 5:
                sample_logs[category].append(line.strip())

    print("\n===== ERROR CATEGORY SUMMARY =====\n")
    for category, count in error_counts.most_common():
        print(f"{category.upper()} : {count}")

    print("\n===== SAMPLE LOGS =====\n")
    for category, logs in sample_logs.items():
        print(f"\n--- {category.upper()} ---")
        for entry in logs:
            print(entry)


if __name__ == "__main__":
    main()
