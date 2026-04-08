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
import json

from preprocessing import load_bgl, create_windows
from detection import IncidentDetector
from rag import RAGEngine
from diagnosis_agent import DiagnosisAgent
from remediation_agent import RemediationAgent
from environment import SystemEnvironment
from evaluation import evaluate_remediation

# -----------------------------
# STEP 1: Load Logs
# -----------------------------
print("Loading logs...")
# contents, labels = load_bgl("data/BGL.log")
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
log_path = os.path.join(BASE_DIR, "data", "BGL.log")

contents, labels = load_bgl(log_path)

# -----------------------------
# STEP 2: Create Windows
# -----------------------------
print("Creating windows...")
window_texts, window_labels = create_windows(
    contents,
    labels,
    window_size=50,
    stride=50
)

print("Total windows:", len(window_texts))


# -----------------------------
# STEP 3: Train Detection Model
# -----------------------------
print("Training detection model...")
detector = IncidentDetector()
X_test, y_test = detector.train(window_texts, window_labels)


# -----------------------------
# STEP 4: Initialize Components
# -----------------------------
print("Initializing RAG + Agents...")

kb_path = os.path.join(BASE_DIR, "knowledge_base")
rag = RAGEngine(kb_path)
diagnosis_agent = DiagnosisAgent(model="llama3")

env = SystemEnvironment()
remediation_agent = RemediationAgent(env)


# -----------------------------
# STEP 5: Process Incidents
# -----------------------------
incident_count = 0
all_metrics = []

for text, label in zip(window_texts, window_labels):

    if label == 1:
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

        remediation_result = remediation_agent.remediate(clean_diagnosis)

        print("\n⚙️ Remediation Result:")
        print(remediation_result)

        # 🔹 Evaluation
        metrics = evaluate_remediation(diagnosis, remediation_result)

        print("\n📊 Evaluation Metrics:")
        print(metrics)

        # 🔹 Environment State
        print("\n🌐 Updated Environment State:")
        print(env.get_environment_status())

        all_metrics.append(metrics)

        incident_count += 1

        if incident_count == 3:
            break

print("\n==========================")
print("📈 FINAL EVALUATION")
print("==========================")

if len(all_metrics) == 0:
    print("No metrics collected!")
else:
    avg_action = sum(m["action_correctness"] for m in all_metrics) / len(all_metrics)
    avg_success = sum(m["resolution_success"] for m in all_metrics) / len(all_metrics)
    avg_steps = sum(m["steps_taken"] for m in all_metrics) / len(all_metrics)
    avg_reasoning = sum(m["reasoning_quality"] for m in all_metrics) / len(all_metrics)

    print(f"Action Accuracy: {avg_action:.2f}")
    print(f"Resolution Success: {avg_success:.2f}")
    print(f"Avg Steps: {avg_steps:.2f}")
    print(f"Reasoning Quality: {avg_reasoning:.2f}")
