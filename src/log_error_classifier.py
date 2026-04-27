import os
import json
from collections import defaultdict

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE_DIR, "data")

# ==============================
# STEP 1: Load input
# ==============================

input_path = os.path.join(DATA_DIR, "error_analysis.json")
with open(input_path, "r") as f:
    data = json.load(f)

templates = data["templates"]

# ==============================
# STEP 2: Noise filter
# ==============================

def is_noise(template):
    t = template.lower()

    noise_patterns = [
        "generating core",
        "microseconds spent",
        "total interrupts",
        "wait state enable",
        "debug wait",
        "debug interrupt",
        "instruction address space",
        "data address space",
        "core configuration register",
        "problem state",
        "disable store gathering",
    ]

    return any(p in t for p in noise_patterns)

# ==============================
# STEP 3: Classification
# ==============================

def classify_template(template):
    t = template.lower()

    # ---- DIAGNOSTIC ----
    if "iar" in t and "dear" in t:
        return "Diagnostic - Register Dump"

    # ---- MEMORY ----
    if "tlb" in t:
        return "Memory - TLB Error"

    if "ddr" in t or "edram" in t:
        return "Memory - Hardware Error"

    if "ce sym" in t:
        return "Memory - ECC Error"

    if "data address" in t:
        return "Memory Address Error"

    # ---- STORAGE ----
    if "data storage interrupt" in t:
        return "Storage Failure"

    # ---- CPU ----
    if "alignment exception" in t:
        return "CPU - Alignment Error"

    if "floating point" in t or "floating pt ex mode" in t:
        return "CPU - Floating Point Error"

    # MERGED INSTRUCTION CATEGORY
    if ("illegal instruction" in t or
        "privileged instruction" in t or
        "trap instruction" in t):
        return "CPU - Instruction Error"

    if "imprecise exception" in t:
        return "CPU - Exception"

    if "store operation" in t:
        return "CPU - Memory Operation Error"

    if "byte ordering exception" in t:
        return "CPU - Byte Order Error"

    # ---- HARDWARE ----
    if "machine check" in t:
        return "Hardware - Machine Check"

    if "exception syndrome register" in t:
        return "Hardware - Exception Register"

    if "machine state register" in t:
        return "Hardware - Machine State"

    if "node card is not fully functional" in t:
        return "Hardware - Node Failure"

    if "node card status" in t:
        return "Hardware - Status"

    if "auxiliary processor" in t:
        return "Hardware - Processor Subsystem"

    if "invalid node ecid" in t:
        return "Hardware - Configuration Error"

    # ---- CACHE ----
    if "cache" in t:
        return "CPU - Cache Error"

    # ---- IO / NETWORK ----
    if "ciod" in t or "socket" in t:
        return "IO - Communication Failure"

    if "packet timeout" in t:
        return "Network - Timeout"

    if "tree network" in t or "tree receiver" in t:
        return "Network - Error"

    if "lustre" in t:
        return "Filesystem Error"

    # ---- RUNTIME ----
    if "rts" in t or "kernel terminated" in t:
        return "Runtime Failure"

    if "assert condition" in t:
        return "Software Assertion Failure"

    # ---- INTERRUPT (ONLY if generic) ----
    if "interrupt" in t:
        return "System - Interrupt (Generic)"

    return "Unmapped"

# ==============================
# STEP 4: Process templates
# ==============================

category_counts = defaultdict(int)
diagnostics = defaultdict(int)
unmapped = []

for template, count in templates:

    if is_noise(template):
        continue

    category = classify_template(template)

    # Separate diagnostics (not for KB)
    if category.startswith("Diagnostic"):
        diagnostics[category] += count
        continue

    category_counts[category] += count

    if category == "Unmapped":
        unmapped.append((template, count))

# ==============================
# STEP 5: Print results
# ==============================

print("\n===== FINAL CATEGORY DISTRIBUTION =====\n")

for cat, count in sorted(category_counts.items(), key=lambda x: x[1], reverse=True):
    print(f"{cat}: {count}")

print("\n===== DIAGNOSTIC (EXCLUDED FROM KB) =====\n")
for cat, count in diagnostics.items():
    print(f"{cat}: {count}")

print("\n===== REMAINING UNMAPPED =====\n")
for t, c in sorted(unmapped, key=lambda x: x[1], reverse=True)[:20]:
    print(f"{c} --> {t}")

# ==============================
# STEP 6: Save final structured output
# ==============================

output = {
    "categories": dict(category_counts),
    "diagnostics": dict(diagnostics),
    "unmapped": unmapped
}

output_path = os.path.join(DATA_DIR, "final_structured_output.json")
with open(output_path, "w") as f:
    json.dump(output, f, indent=4)

print(f"\nSaved to {output_path}")