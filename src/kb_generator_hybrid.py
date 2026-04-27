import os
import json
import requests
import time
from collections import defaultdict

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE_DIR, "data")

# ==============================
# CONFIG
# ==============================

OLLAMA_URL = "http://localhost:11434/api/generate"
MODEL = "mistral"

INPUT_FILE = os.path.join(DATA_DIR, "final_structured_output.json")
TEMPLATE_FILE = os.path.join(DATA_DIR, "error_analysis.json")
OUTPUT_FILE = os.path.join(DATA_DIR, "knowledge_base.json")

MAX_RETRIES = 3

LOW_CONFIDENCE_CATEGORIES = [
    "Runtime Failure",
    "Filesystem Error",
    "Network - Timeout",
    "System - Interrupt (Generic)"
]

# ==============================
# LOAD DATA
# ==============================

with open(INPUT_FILE, "r") as f:
    structured_data = json.load(f)

with open(TEMPLATE_FILE, "r") as f:
    template_data = json.load(f)

categories = structured_data["categories"]
templates = template_data["templates"]

# ==============================
# TEMPLATE → CATEGORY MAP
# ==============================

def classify_template(template):
    t = template.lower()

    if "tlb" in t:
        return "Memory - TLB Error"
    if "alignment exception" in t:
        return "CPU - Alignment Error"
    if "floating point" in t:
        return "CPU - Floating Point Error"
    if "cache" in t:
        return "CPU - Cache Error"
    if "ciod" in t or "socket" in t:
        return "IO - Communication Failure"
    if "ddr" in t or "edram" in t:
        return "Memory - Hardware Error"
    if "machine check" in t:
        return "Hardware - Machine Check"
    if "assert" in t:
        return "Software Assertion Failure"
    if "lustre" in t:
        return "Filesystem Error"
    if "timeout" in t:
        return "Network - Timeout"

    return None


def build_examples():
    example_map = defaultdict(list)

    for template, _ in templates:
        cat = classify_template(template)
        if cat:
            example_map[cat].append(template)

    return example_map


example_map = build_examples()

# ==============================
# SEVERITY & CONFIDENCE
# ==============================

def get_severity(error_type):
    if any(x in error_type for x in ["Hardware", "Storage"]):
        return "HIGH"
    if any(x in error_type for x in ["Memory", "Alignment"]):
        return "HIGH"
    if "IO" in error_type or "Network" in error_type:
        return "MEDIUM"
    if "CPU" in error_type:
        return "MEDIUM"
    return "LOW"


def get_confidence(error_type):
    if error_type in LOW_CONFIDENCE_CATEGORIES:
        return "LOW"
    if "Hardware" in error_type or "Memory" in error_type:
        return "HIGH"
    if "CPU" in error_type:
        return "MEDIUM"
    return "LOW"

# ==============================
# PROMPT
# ==============================

def build_prompt(error_type, frequency, examples):
    return f"""
You are an expert in HPC systems and distributed infrastructure.

Error Type: {error_type}
Frequency: {frequency}

Example logs:
{examples}

Rules:
- Avoid textbook explanations
- Avoid hardware redesign suggestions
- Prefer operational fixes

Return STRICT JSON:
{{
  "description": "...",
  "root_cause": ["...", "...", "..."],
  "impact": ["...", "...", "..."],
  "resolution": ["...", "...", "..."]
}}
"""

# ==============================
# OLLAMA CALL
# ==============================

def call_ollama(prompt):
    response = requests.post(
        OLLAMA_URL,
        json={"model": MODEL, "prompt": prompt, "stream": False}
    )
    return response.json()["response"]

# ==============================
# VALIDATION
# ==============================

def validate_output(text):
    try:
        start = text.find("{")
        end = text.rfind("}") + 1
        parsed = json.loads(text[start:end])

        if not isinstance(parsed.get("root_cause"), list):
            return None
        if not isinstance(parsed.get("resolution"), list):
            return None

        return parsed
    except:
        return None

# ==============================
# SANITIZATION
# ==============================

def sanitize_resolution(resolutions):
    cleaned = []
    for r in resolutions:
        r_lower = r.lower()

        if any(x in r_lower for x in [
            "increase tlb",
            "replace cpu",
            "increase cache size"
        ]):
            continue

        cleaned.append(r)

    return cleaned


def enforce_operational_resolution(resolutions):
    cleaned = []

    for r in resolutions:
        if "replace" in r.lower() and "cpu" in r.lower():
            continue
        cleaned.append(r)

    cleaned.append("Restart affected node and monitor for recurrence")

    return cleaned[:3]

# ==============================
# TAGS
# ==============================

def enrich_tags(entry):
    tags = set(entry["tags"])

    if "memory" in entry["error_type"].lower():
        tags.add("memory")

    if entry["severity"] == "HIGH":
        tags.add("critical")

    return list(tags)

# ==============================
# REFINEMENT
# ==============================

def refine_entry(entry):
    error = entry["error_type"]

    # Fix severity
    if "Alignment" in error:
        entry["severity"] = "HIGH"

    if "Assertion" in error:
        entry["severity"] = "HIGH"
        entry["confidence"] = "HIGH"

    # ECC correction
    if "ECC" in error:
        entry["root_cause"] = [
            "Correctable memory bit errors",
            "Degrading memory module",
            "Transient hardware fault"
        ]

    # TLB correction
    if "TLB" in error:
        entry["root_cause"] = [
            "Invalid memory mapping",
            "Application memory access issue",
            "Transient memory subsystem fault"
        ]

    # Clean resolutions
    entry["resolution"] = sanitize_resolution(entry["resolution"])
    entry["resolution"] = enforce_operational_resolution(entry["resolution"])

    # Add frequency context
    entry["description"] += f" Observed {entry['frequency']} times."

    # Root cause flag
    entry["is_root_cause"] = error not in LOW_CONFIDENCE_CATEGORIES

    # Improve tags
    entry["tags"] = enrich_tags(entry)

    return entry

# ==============================
# MAIN PIPELINE
# ==============================

knowledge_base = []

for error_type, freq in categories.items():

    print(f"Processing: {error_type}")

    examples = example_map.get(error_type, [])[:3]
    if not examples:
        examples = [f"generic log for {error_type}"]

    prompt = build_prompt(error_type, freq, examples)

    parsed = None

    for _ in range(MAX_RETRIES):
        raw = call_ollama(prompt)
        parsed = validate_output(raw)
        if parsed:
            break
        time.sleep(1)

    if not parsed:
        print(f"Skipping {error_type}")
        continue

    entry = {
        "error_type": error_type,
        "category": error_type.split(" - ")[0],
        "frequency": freq,
        "description": parsed["description"],
        "root_cause": parsed["root_cause"],
        "impact": parsed["impact"],
        "resolution": parsed["resolution"],
        "severity": get_severity(error_type),
        "confidence": get_confidence(error_type),
        "examples": examples,
        "tags": error_type.lower().replace("-", "").split(),
        "priority": freq * (3 if get_severity(error_type) == "HIGH" else 1)
    }

    entry = refine_entry(entry)

    if error_type in LOW_CONFIDENCE_CATEGORIES:
        entry["note"] = "Generic category – requires deeper log correlation"

    knowledge_base.append(entry)

# ==============================
# SAVE OUTPUT
# ==============================

with open(OUTPUT_FILE, "w") as f:
    json.dump(knowledge_base, f, indent=4)

print("\n✅ knowledge_base.json generated")