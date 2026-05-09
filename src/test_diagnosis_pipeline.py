import os
import re
import sys
import json
import logging
import warnings
import time

from rag import RAGEngine
from detection import IncidentDetector
from environment import SystemEnvironment
from diagnosis_agent import DiagnosisAgent
from evaluation import evaluate_remediation
from langchain_community.llms import Ollama
from remediation_engine import RemediationEngine
from preprocessing import load_bgl, create_windows

os.environ["TRANSFORMERS_NO_ADVISORY_WARNINGS"] = "1"
os.environ["TRANSFORMERS_VERBOSITY"] = "error"
os.environ["TOKENIZERS_PARALLELISM"] = "false"
os.environ["TRANSFORMERS_NO_TORCHVISION"] = "1"
logging.getLogger("transformers").setLevel(logging.ERROR)
logging.getLogger("torch").setLevel(logging.ERROR)
warnings.filterwarnings("ignore")

# -----------------------------
# LOGGING SETUP
# -----------------------------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(message)s"
)

logger = logging.getLogger()

# -----------------------------
# LIVE LOGGER HELPER
# -----------------------------
def live_log(message, logger_callback=None):

    logger.info(message)

    if logger_callback:
        logger_callback(message)

# -----------------------------
# HELPERS
# -----------------------------
def extract_nodes(log_text: str):
    patterns = [
        r'R\d+-M\d+-N\w+-I:J\d+-U\d+',
        r'R\d+-M\d+-L\d+-U\d+-C',
        r'R\d+-M\d+-N\d+',
        r'R\d+-M\d+-N\d+-C\d+-J\d+',
        r'R\d+-M\d+\b',
        r'R\d+-M\d+-N\d+-U\d+',
        r'\bR\d{1,2}-[A-Z0-9][\w-]+\b',
    ]

    nodes = set()
    for pattern in patterns:
        matches = re.findall(pattern, log_text, re.IGNORECASE)
        nodes.update(m.lower() for m in matches)

    return list(nodes)


def extract_services_from_logs(log_lines):
    services = set()
    keywords = ["cache", "memory", "disk", "io", "network", "filesystem", "cpu"]

    for line in log_lines:
        line = line.lower()
        for keyword in keywords:
            if keyword in line:
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


# =========================================================
# 🚀 MAIN PIPELINE FUNCTION (USED BY UI)
# =========================================================
def run_pipeline(logs, labels=None, max_incidents=20, logger_callback=None):

    live_log("STEP 1: Loading Logs", logger_callback)

    # BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    # log_path = os.path.join(BASE_DIR, "data", "BGL.log")

    # contents, labels = load_bgl(log_path)

    # Use logs coming from UI
    contents = logs

    live_log(f"Loaded {len(contents)} total log lines", logger_callback)

    # Since uploaded logs don’t have labels → assume normal (0)
    if labels is None:
        labels = [0] * len(contents)

    # -----------------------------
    live_log("STEP 2: Creating Windows", logger_callback)

    live_log("Creating sliding log windows...", logger_callback)

    window_texts, window_labels = create_windows(
        contents=contents,
        labels=labels,
        window_size=100,
        stride=50
    )

    live_log(f"Total Windows: {len(window_texts)}", logger_callback)

    # -----------------------------
    live_log("STEP 3: Training Detection Model", logger_callback)

    detector = IncidentDetector()

    live_log(
        "Initializing anomaly detection model...",
        logger_callback
    )

    live_log(
        "Training ML model on generated windows...",
        logger_callback
    )

    X_test, y_test = detector.train(window_texts, window_labels)

    live_log(
        "Model training completed successfully",
        logger_callback
    )

    logger.info("STEP 3.1: Evaluating Model")

    live_log(
        "Evaluating model performance metrics...",
        logger_callback
    )

    detector.evaluate(X_test, y_test)

    live_log(
        "Model evaluation completed",
        logger_callback
    )

    # -----------------------------
    live_log("STEP 4: Detecting Incidents", logger_callback)

    live_log(
        "Running anomaly prediction on all windows...",
        logger_callback
    )

    predictions = detector.predict(window_texts)

    live_log(
        f"Detected {int(sum(predictions))} anomalous windows",
        logger_callback
    )

    # -----------------------------
    live_log("STEP 5: Initializing AI Components", logger_callback)

    live_log(
        "Loading SentenceTransformer embeddings...",
        logger_callback
    )

    BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    kb_path = os.path.join(BASE_DIR, "knowledge_base")

    rag = RAGEngine(kb_path)

    live_log(
        "Initializing diagnosis agent...",
        logger_callback
    )

    diagnosis_agent = DiagnosisAgent(model="llama3")

    live_log(
        "Connecting to Ollama LLM...",
        logger_callback
    )

    llm = Ollama(model="llama3")

    live_log(
        "Initializing remediation engine...",
        logger_callback
    )

    remediation_engine = RemediationEngine(llm)

    live_log(
        "AI components initialized successfully",
        logger_callback
    )

    # -----------------------------
    incidents_output = []
    all_metrics = []

    incident_count = 0

    total_predicted_incidents = int(sum(predictions))

    live_log(
        f"Beginning processing for {total_predicted_incidents} incidents",
        logger_callback
    )

    # =====================================================
    # MAIN LOOP
    # =====================================================
    for text, pred, true_label in zip(window_texts, predictions, window_labels):

        if pred != 1:
            continue

        live_log("===================================", logger_callback)
        live_log(f"INCIDENT #{incident_count + 1}", logger_callback)
        live_log("===================================", logger_callback)

        live_log(
            f"Processing incident {incident_count + 1} "
            f"of approximately {min(total_predicted_incidents, max_incidents)}",
            logger_callback
        )

        env = SystemEnvironment()

        logger.info("🔹 Incident Sample:")
        logger.info(text[:300])

        live_log(
            "Extracting incident sample logs...",
            logger_callback
        )

        # -----------------------------
        logger.info("🔹 Retrieving Knowledge")

        live_log(
            "Querying RAG knowledge base...",
            logger_callback
        )

        retrieved_docs = rag.retrieve(text, top_k=5)

        live_log(
            f"Retrieved {len(retrieved_docs)} relevant knowledge documents",
            logger_callback
        )

        # -----------------------------
        logger.info("🔹 Running Diagnosis")

        live_log(
            "Running LLM diagnosis engine...",
            logger_callback
        )

        diagnosis = diagnosis_agent.diagnose(text, retrieved_docs)

        logger.info("🧠 Diagnosis:")
        logger.info(json.dumps(diagnosis, indent=2))

        live_log(
            f"Diagnosis completed: "
            f"{diagnosis.get('incident_type', 'Unknown Incident')}",
            logger_callback
        )

        # -----------------------------
        nodes = extract_nodes(text)
        env.register_nodes(nodes)

        logger.info(f"🔍 Nodes: {nodes}")

        live_log(
            f"Detected {len(nodes)} impacted nodes",
            logger_callback
        )

        services_logs = extract_services_from_logs([text])
        services_diag = extract_services_from_diagnosis(diagnosis)
        services = list(set(services_logs + services_diag))

        env.register_services(services)

        logger.info(f"🔍 Services: {services}")

        live_log(
            f"Detected impacted services: {services}",
            logger_callback
        )

        # -----------------------------
        logger.info("⚙️ Running Remediation")

        live_log(
            "Executing remediation engine...",
            logger_callback
        )

        remediation_result = remediation_engine.run(
            diagnosis,
            env,
            nodes
        )

        logger.info("⚙️ Action Taken:")
        logger.info(remediation_result.get("action"))

        logger.info("⚙️ Result:")
        logger.info(remediation_result.get("result"))

        live_log(
            f"Remediation Action: "
            f"{remediation_result.get('action')}",
            logger_callback
        )

        # -----------------------------
        metrics = evaluate_remediation(diagnosis, remediation_result)

        logger.info("📊 Metrics:")
        logger.info(metrics)

        live_log(
            f"Incident #{incident_count + 1} processing completed",
            logger_callback
        )

        # -----------------------------
        # STORE FOR UI
        incidents_output.append({
            "incident_id": incident_count + 1,
            "log": text[:300],
            "diagnosis": diagnosis,
            "nodes": nodes,
            "services": services,
            "action": remediation_result.get("action"),
            "result": remediation_result.get("result"),
            "metrics": metrics
        })

        all_metrics.append(metrics)

        incident_count += 1

        if incident_count >= max_incidents:

            live_log(
                f"Reached configured max incident limit "
                f"({max_incidents})",
                logger_callback
            )

            break

    # =====================================================
    # FINAL METRICS
    # =====================================================
    logger.info("===================================")
    logger.info("DEMO COMPLETE")
    logger.info("===================================")

    live_log(
        "Pipeline execution completed successfully",
        logger_callback
    )

    if len(all_metrics) > 0:
        avg_action = sum(m["action_correctness"] for m in all_metrics) / len(all_metrics)
        avg_success = sum(m["resolution_success"] for m in all_metrics) / len(all_metrics)
    else:
        avg_action = avg_success = 0

    live_log(
        f"Average Action Accuracy: {round(avg_action, 2)}",
        logger_callback
    )

    live_log(
        f"Average Resolution Success: {round(avg_success, 2)}",
        logger_callback
    )

    return {
        "total_windows": len(window_texts),
        "total_anomalies": int(sum(predictions)),
        "processed_incidents": incident_count,
        "avg_action_accuracy": avg_action,
        "avg_resolution_success": avg_success,
        "incidents": incidents_output
    }


# =========================================================
# RUN DIRECTLY (CLI MODE)
# =========================================================
if __name__ == "__main__":

    BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    log_path = os.path.join(BASE_DIR, "data", "BGL.log")

    contents, labels = load_bgl(log_path)

    output = run_pipeline(logs=contents, labels=labels, max_incidents=5)

    print("\nFINAL OUTPUT SUMMARY:")
    print(json.dumps(output, indent=2))