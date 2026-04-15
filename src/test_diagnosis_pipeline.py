# from preprocessing import load_bgl, create_windows
# from detection import IncidentDetector
# from rag import RAGEngine
# from diagnosis_agent import DiagnosisAgent


# # Load logs
# contents, labels = load_bgl("../data/BGL.log")

# # Create windows
# window_texts, window_labels = create_windows(
#     contents,
#     labels,
#     window_size=50,
#     stride=50
# )

# print("Total windows:", len(window_texts))

# # Train detector (quick training for test)
# detector = IncidentDetector()
# X_test, y_test = detector.train(window_texts, window_labels)

# # Initialize RAG
# rag = RAGEngine("../knowledge_base")

# # Initialize Diagnosis Agent
# diagnosis_agent = DiagnosisAgent(model="llama3")

# # Find first 3 incident windows
# incident_count = 0

# for text, label in zip(window_texts, window_labels):
#     if label == 1:
#         print("\n==========================")
#         print("Incident Detected")
#         print("==========================")

#         # Retrieve knowledge
#         retrieved_docs = rag.retrieve(text, top_k=3)

#         # Diagnose
#         diagnosis = diagnosis_agent.diagnose(text, retrieved_docs)

#         print("Diagnosis Output:")
#         print(diagnosis)

#         incident_count += 1

#         if incident_count == 3:
#             break

import os
import re
import json

from preprocessing import load_bgl, create_windows
from detection import IncidentDetector
from rag import RAGEngine
from diagnosis_agent import DiagnosisAgent
from remediation_engine import RemediationEngine
from environment import SystemEnvironment
from evaluation import evaluate_remediation
from langchain_community.llms import Ollama

def extract_nodes(log_text: str):
    patterns = [
        r'R\d+-M\d+-N\w+-I:J\d+-U\d+',   # Full format
        r'R\d+-M\d+-L\d+-U\d+-C',        # Midplane format
        r'R\d+-M\d+-N\d+'                # Short format
    ]

    nodes = set()

    for pattern in patterns:
        matches = re.findall(pattern, log_text)
        nodes.update(matches)

    return list(nodes)

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

env = SystemEnvironment()
llm = Ollama(model="llama3")
remediation_engine = RemediationEngine(llm)

# ----------------------------------
# STEP 6: Process Detected Incidents
# ----------------------------------
incident_count = 0
all_metrics = []
detection_correct_count = 0
total_detected = 0

for text, pred, true_label in zip(window_texts, predictions, window_labels):
    if pred == 1:
        total_detected += 1

        if pred == true_label:
            detection_correct_count += 1

        print("\n==========================")
        print("🚨 Incident Detected")
        print("==========================")

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

        # remediation_result = remediation_agent.remediate(clean_diagnosis)
        nodes = extract_nodes(text)
        print("🔍 Extracted Nodes:", nodes)

        # Register nodes in environment
        env.register_nodes(nodes)
        if not nodes:
            print("⚠️ No nodes found in this incident window")

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

        # if incident_count == 3:
        #     break

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
