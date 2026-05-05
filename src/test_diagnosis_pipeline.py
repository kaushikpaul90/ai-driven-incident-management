import os
import re
import sys
import json
import logging
from rag import RAGEngine
from detection import IncidentDetector
from environment import SystemEnvironment
from diagnosis_agent import DiagnosisAgent
from evaluation import evaluate_remediation
from langchain_community.llms import Ollama
from remediation_engine import RemediationEngine
from preprocessing import load_bgl, create_windows

# -----------------------------
# 🔥 LOGGING SETUP
# -----------------------------
LOG_FILE = "incident_pipeline.log"

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
    handlers=[
        logging.FileHandler(LOG_FILE, mode="w"),
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger()

# -----------------------------
# 🔥 REDIRECT PRINT → LOGGER
# -----------------------------
class StreamToLogger:
    def __init__(self, logger, level):
        self.logger = logger
        self.level = level
        self.linebuf = ""

    def write(self, buf):
        for line in buf.splitlines():
            clean_line = line.strip()

            # 🚫 Ignore empty lines completely
            if not clean_line:
                continue

            # 🔥 Handle tqdm progress bars
            if re.search(r"\d+it\s*\[", clean_line) or "it/s" in clean_line:
                self.logger.info(clean_line)
                continue

            # 🔥 Handle model loading progress
            if "Loading weights" in clean_line:
                self.logger.info(clean_line)
                continue

            # 🔥 Handle sklearn warnings (downgrade)
            if "RuntimeWarning" in clean_line or "warning" in clean_line.lower():
                self.logger.warning(clean_line)
                continue

            # Default behavior
            self.logger.log(self.level, clean_line)

    def flush(self):
        for handler in self.logger.handlers:
            handler.flush()

    def isatty(self):
        return False

# 🚨 Redirect ALL prints globally
sys.stdout = StreamToLogger(logger, logging.INFO)
# sys.stderr = StreamToLogger(logger, logging.ERROR)

def extract_nodes(log_text: str):
    patterns = [
        # Full BlueGene/L node format: R##-M#-N###-I:J#-U##
        r'R\d+-M\d+-N\w+-I:J\d+-U\d+',
        # Midplane format: R##-M#-L#-U##-C
        r'R\d+-M\d+-L\d+-U\d+-C',
        # Short rack-midplane-node: R##-M#-N##
        r'R\d+-M\d+-N\d+',
        # FIX: Extended rack format with board/chip: R##-M#-N##-C#-J##
        r'R\d+-M\d+-N\d+-C\d+-J\d+',
        # FIX: Rack-only node references: R##-M#
        r'R\d+-M\d+\b',
        # FIX: BGL style with U-suffix only: R##-M#-N##-U##
        r'R\d+-M\d+-N\d+-U\d+',
        # FIX: Any node-like token starting with R followed by numbers and dashes
        # Catches BGL variations not covered above (broad fallback)
        r'\bR\d{1,2}-[A-Z0-9][\w-]+\b',
    ]
 
    nodes = set()
    for pattern in patterns:
        matches = re.findall(pattern, log_text, re.IGNORECASE)
        nodes.update(m.lower() for m in matches)

    return list(nodes)

def extract_services_from_logs(log_lines):
    services = set()

    keywords = [
        "cache",
        "memory",
        "disk",
        "io",
        "network",
        "filesystem",
        "cpu"
    ]

    for line in log_lines:
        line_lower = line.lower()

        for keyword in keywords:
            if keyword in line_lower:
                services.add(keyword)

    return list(services)

def extract_services_from_diagnosis(diagnosis):
    services = set()

    text = (
        diagnosis.get("incident_type", "") +
        " " +
        diagnosis.get("root_cause", "")
    ).lower()

    if "cache" in text:
        services.add("cache")

    if "memory" in text:
        services.add("memory")

    if "disk" in text or "io" in text:
        services.add("disk_io")

    if "network" in text:
        services.add("network")

    return list(services)

# -----------------------------
# STEP 1: Load Logs
# -----------------------------
print("\nLoading logs...")
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
log_path = os.path.join(BASE_DIR, "data", "BGL.log")

contents, labels = load_bgl(log_path)

# -----------------------------
# STEP 2: Create Windows
# -----------------------------
print("\nCreating windows...")
window_texts, window_labels = create_windows(
    contents=contents,
    labels=labels,
    window_size=100,
    stride=50
)

print("\nTotal windows:", len(window_texts))

# -----------------------------
# STEP 3: Train Detection Model
# -----------------------------
print("\nTraining detection model...")
detector = IncidentDetector()
X_test, y_test = detector.train(window_texts, window_labels)

# Detection Evaluation
print("\n📊 Detection Model Evaluation:")
detector.evaluate(X_test, y_test)

# -----------------------------
# STEP 4: Predict Incidents
# -----------------------------
print("Running detection inference...")
predictions = detector.predict(window_texts)

# -----------------------------
# STEP 5: Initialize Components
# -----------------------------
print("\nInitializing RAG + Agents...")

kb_path = os.path.join(BASE_DIR, "knowledge_base")

rag = RAGEngine(kb_path)
diagnosis_agent = DiagnosisAgent(model="llama3")

# env = SystemEnvironment()
llm = Ollama(model="llama3")
remediation_engine = RemediationEngine(llm)

# ----------------------------------
# STEP 6: Process Detected Incidents
# ----------------------------------
incident_count = 0
all_metrics = []
detection_correct_count = 0
total_detected = 0

print(f"\nTotal anomalies detected: {sum(predictions)}")
for text, pred, true_label in zip(window_texts, predictions, window_labels):
    if pred == 1:
        print(f"\nProcessing anomaly index: {incident_count}")
        total_detected += 1

        if pred == true_label:
            detection_correct_count += 1

        print("\n==========================")
        print("🚨 Incident Detected")
        print("==========================")

        # Fresh environment per incident prevents state bleed-over
        env = SystemEnvironment()
        
        # 🔹 RAG Retrieval
        retrieved_docs = rag.retrieve(text, top_k=5)

        # 🔹 Diagnosis
        diagnosis = diagnosis_agent.diagnose(text, retrieved_docs)

        print("\n🧠 Diagnosis Output:")
        print(json.dumps(diagnosis, indent=2))

        # 🔹 Remediation (Agentic)
        clean_diagnosis = {
            "incident_type": diagnosis.get("incident_type"),
            "root_cause": diagnosis.get("root_cause"),
            "severity": diagnosis.get("severity")
        }

        nodes = [n.lower() for n in extract_nodes(text)]
        print("🔍 Extracted Nodes:", nodes)

        # Register nodes in environment
        env.register_nodes(nodes)
        if not nodes:
            print("⚠️ No nodes found in this incident window")

        services_from_logs = extract_services_from_logs([text])
        services_from_diag = extract_services_from_diagnosis(clean_diagnosis)
        services = list(set(services_from_logs + services_from_diag))
        if services:
            env.register_services(services)
        else:
            print("⚠️ No services detected — using environment baseline")
            # env.register_services(env.get_default_services())

        remediation_result = remediation_engine.run(
            clean_diagnosis,
            env,
            nodes
        )

        print("\n⚙️ Remediation Result:")
        print(remediation_result)

        # 🔹 Evaluation
        metrics = evaluate_remediation(diagnosis, remediation_result)

        # 🔹 Add detection correctness
        metrics["detection_correct"] = int(pred == true_label)

        print("\n📊 Evaluation Metrics:")
        print(metrics)

        # 🔹 Environment State
        print("\n🌐 Updated Environment State:")
        print(env.get_environment_status())

        all_metrics.append(metrics)

        incident_count += 1

        if incident_count == 100:
            break

print("\n🧾 Action History:")
print(env.to_dict().get("recent_actions", []))

# ----------------------------------
# STEP 7: Failure Analysis (Deep Dive)
# ----------------------------------
print("\n🔍 Analyzing Detection Blind Spots...")
# We use window_texts and window_labels from earlier in the script
missed_incidents = detector.get_failures(window_texts, window_labels)

if missed_incidents:
    print(f"Total Missed Incidents: {len(missed_incidents)}")
    print("Sample of missed logs:")
    for i, log in enumerate(missed_incidents[:5]):
        print(f"  [{i+1}] {log[:150]}...") # Print first 150 chars of the window
else:
    print("✅ No incidents were missed in this run.")

print("\n==========================")
print("📈 FINAL EVALUATION")
print("==========================")

if len(all_metrics) == 0:
    print("No incidents processed!")
else:
    avg_action = sum(m["action_correctness"] for m in all_metrics) / len(all_metrics)
    avg_success = sum(m["resolution_success"] for m in all_metrics) / len(all_metrics)
    avg_steps = sum(m["steps_taken"] for m in all_metrics) / len(all_metrics)
    avg_reasoning = sum(m["reasoning_quality"] for m in all_metrics) / len(all_metrics)
    avg_detection = sum(m["detection_correct"] for m in all_metrics) / len(all_metrics)

    print(f"Detection Accuracy (on processed incidents): {avg_detection:.2f}")
    print(f"Action Accuracy: {avg_action:.2f}")
    print(f"Resolution Success: {avg_success:.2f}")
    print(f"Avg Steps: {avg_steps:.2f}")
    print(f"Reasoning Quality: {avg_reasoning:.2f}")
