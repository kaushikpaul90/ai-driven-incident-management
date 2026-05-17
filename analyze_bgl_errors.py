import re
from collections import Counter, defaultdict

LOG_FILE = "BGL.log"

# Common error keywords/patterns
ERROR_PATTERNS = {
    "network": [
        r"socket",
        r"control stream",
        r"connection",
        r"network",
        r"CioStream"
    ],

    "hardware": [
        r"TLB",
        r"cache parity",
        r"ECC",
        r"hardware",
        r"machine check"
    ],

    "memory": [
        r"memory",
        r"RAM",
        r"segmentation fault",
        r"malloc"
    ],

    "filesystem": [
        r"filesystem",
        r"disk",
        r"I/O error",
        r"storage",
        r"block device"
    ],

    "kernel": [
        r"kernel",
        r"panic",
        r"syscall"
    ],

    "scheduler": [
        r"scheduler",
        r"job",
        r"queue"
    ],

    "daemon": [
        r"daemon",
        r"service",
        r"process"
    ]
}

error_counts = Counter()
sample_logs = defaultdict(list)

with open(LOG_FILE, "r", errors="ignore") as f:

    for line in f:

        line_lower = line.lower()

        matched = False

        for category, patterns in ERROR_PATTERNS.items():

            for pattern in patterns:

                if re.search(pattern.lower(), line_lower):

                    error_counts[category] += 1

                    if len(sample_logs[category]) < 5:
                        sample_logs[category].append(line.strip())

                    matched = True
                    break

        if not matched:
            error_counts["unknown"] += 1

            if len(sample_logs["unknown"]) < 5:
                sample_logs["unknown"].append(line.strip())

# -----------------------------
# RESULTS
# -----------------------------
print("\n===== ERROR CATEGORY SUMMARY =====\n")

for category, count in error_counts.most_common():

    print(f"{category.upper()} : {count}")

print("\n===== SAMPLE LOGS =====\n")

for category, logs in sample_logs.items():

    print(f"\n--- {category.upper()} ---")

    for log in logs:
        print(log)