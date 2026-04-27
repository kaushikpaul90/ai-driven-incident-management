import os
import re
import json
from collections import Counter, defaultdict

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE_DIR, "data")

# Step 1: Read file
log_file = os.path.join(DATA_DIR, "BGL.log")
with open(log_file, "r") as f:
    lines = f.readlines()

# Step 2: Extract message part
def extract_message(line):
    parts = line.strip().split()

    # Find "INFO", "FATAL", etc.
    for i, p in enumerate(parts):
        if p in ["INFO", "FATAL", "WARNING", "ERROR"]:
            return " ".join(parts[i+1:])
    return ""

messages = [extract_message(line) for line in lines if line.strip()]

# Step 3: Normalize (basic template extraction)
def normalize(msg):
    msg = re.sub(r'0x[0-9a-fA-F]+', '<HEX>', msg)   # hex values
    msg = re.sub(r'\d+', '<NUM>', msg)              # numbers
    msg = re.sub(r'\(.*?\)', '<VAR>', msg)          # brackets
    msg = re.sub(r'\s+', ' ', msg)                  # clean spaces
    return msg.strip()

normalized_msgs = [normalize(m) for m in messages if m]

# Step 4: Count unique templates
template_counts = Counter(normalized_msgs)

print("\nTop Error Templates:\n")
for template, count in template_counts.most_common(20):
    print(f"{count} --> {template}")

# Step 5: Categorize based on keywords
categories = defaultdict(list)

def categorize(msg):
    msg_lower = msg.lower()

    if "tlb" in msg_lower:
        return "Memory / TLB Errors"
    elif "storage" in msg_lower:
        return "Storage Errors"
    elif "cache" in msg_lower:
        return "Cache Errors"
    elif "alignment" in msg_lower:
        return "Alignment Errors"
    elif "ciod" in msg_lower:
        return "IO / Communication Errors"
    elif "core" in msg_lower:
        return "Core Dump / Crash"
    elif "interrupt" in msg_lower:
        return "Interrupt Errors"
    else:
        return "Other"

for msg in normalized_msgs:
    cat = categorize(msg)
    categories[cat].append(msg)

# Step 6: Print summary
print("\n\nError Categories Summary:\n")

for cat, msgs in categories.items():
    print(f"{cat}: {len(msgs)} occurrences")

# Step 7: Save results for KB creation
output = {
    "templates": template_counts.most_common(100),
    "categories": {k: len(v) for k, v in categories.items()}
}

output_path = os.path.join(DATA_DIR, "error_analysis.json")
with open(output_path, "w") as f:
    json.dump(output, f, indent=4)

print(f"\nResults saved to {output_path}")