"""Incident pipeline orchestrator for log ingestion, detection, diagnosis, and remediation."""

import json
import logging
import os
import re
import sys
import time
import warnings
from datetime import datetime

from detection import IncidentDetector
from diagnosis_agent import DiagnosisAgent
from environment import SystemEnvironment
from evaluation import evaluate_remediation
from llm_client import chat
from preprocessing import create_windows, load_bgl
from rag import RAGEngine
from remediation_engine import RemediationEngine
from opentelemetry import trace
from sklearn.metrics import accuracy_score, f1_score, precision_score, recall_score

os.environ["TRANSFORMERS_NO_ADVISORY_WARNINGS"] = "1"
os.environ["TRANSFORMERS_VERBOSITY"] = "error"
os.environ["TOKENIZERS_PARALLELISM"] = "false"
os.environ["TRANSFORMERS_NO_TORCHVISION"] = "1"
logging.getLogger("transformers").setLevel(logging.ERROR)
logging.getLogger("torch").setLevel(logging.ERROR)
warnings.filterwarnings("ignore")

logger = logging.getLogger("incident_pipeline")
_log_file_path = None
_tracer = trace.get_tracer(__name__)


class UnifiedLLM:
    """Adapter that forwards prompts to the configured chat provider."""

    def invoke(self, prompt):
        """Send a prompt to the configured LLM provider and return the text response."""
        return chat([{"role": "user", "content": prompt}])


def initialize_logger():
    """Initialize the incident pipeline logger and file handlers."""

    global _log_file_path
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    log_dir = os.path.join(base_dir, "logs")
    os.makedirs(log_dir, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    _log_file_path = os.path.join(log_dir, f"incident_pipeline_{timestamp}.log")

    logger.handlers.clear()
    logger.setLevel(logging.INFO)
    logger.propagate = False

    formatter = logging.Formatter("%(asctime)s | %(levelname)s | %(message)s")
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    file_handler = logging.FileHandler(_log_file_path, mode="w", encoding="utf-8")
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)

    logger.info("========== INCIDENT PIPELINE STARTED ==========")
    logger.info("Log file created at: %s", _log_file_path)


initialize_logger()


def live_log(message, logger_callback=None):
    """Log a message and optionally send it to the UI callback."""

    logger.info(message)
    if logger_callback:
        timestamp = datetime.now().strftime("%H:%M:%S")
        logger_callback(f"[{timestamp}] {message}")


def extract_nodes(log_text: str):
    """Extract normalized node identifiers from a BGL log window."""

    log_text = log_text.upper()
    pattern = (
        r"\bR\d{2}-M\d-"
        r"(?:N\d|NC|NA|NB|NF)"
        r"(?:-[A-Z])"
        r"(?::J\d{2}-U\d{2})?\b"
    )
    matches = re.findall(pattern, log_text)
    return sorted({node.split(":")[0] for node in matches})


def extract_affected_components(log_text: str):
    """Return a sorted list of unique affected components found in log text."""

    patterns = [
        r"\bTLB\b",
        r"\bECC\b",
        r"\bCioStream\b",
        r"\bcache\b",
        r"\bkernel\b",
        r"\bciod\b",
        r"\bASSERT\b",
        r"\bmachine check\b",
        r"\balignment exceptions\b",
    ]
    components = set()
    for pattern in patterns:
        for match in re.findall(pattern, log_text, re.IGNORECASE):
            components.add(match.lower())
    return sorted(components)


def prepare_training_texts(window_texts):
    """Flatten window records into a list of text blocks for training."""

    return ["\n".join(record["text"] for record in window) for window in window_texts]


def train_or_load_model(detector, training_texts, window_labels, logger_callback=None):
    """Load a pretrained detector if available or train a new one."""

    if detector.model_exists():
        live_log("STEP 3: Loading Detection Model", logger_callback)
        live_log("Loading pretrained ML model...", logger_callback)
        detector.load_model()
        live_log("Pretrained ML model loaded successfully", logger_callback)
        return {
            "accuracy": "Pretrained",
            "precision": "Pretrained",
            "recall": "Pretrained",
            "f1_score": "Pretrained",
        }

    live_log("STEP 3: Training Detection Model", logger_callback)
    live_log("Training ML model on generated windows...", logger_callback)
    X_test, y_test = detector.train(training_texts, window_labels)
    live_log("Evaluating model performance metrics...", logger_callback)
    detector.evaluate(X_test, y_test)
    predictions_eval = detector.predict(X_test)
    return {
        "accuracy": round(float(accuracy_score(y_test, predictions_eval)), 2),
        "precision": round(float(precision_score(y_test, predictions_eval, zero_division=0)), 2),
        "recall": round(float(recall_score(y_test, predictions_eval, zero_division=0)), 2),
        "f1_score": round(float(f1_score(y_test, predictions_eval, zero_division=0)), 2),
    }


def detect_incidents(detector, window_texts, logger_callback=None):
    """Run prediction across all windows and return counts."""

    live_log("STEP 4: Detecting Incidents", logger_callback)
    live_log("Running anomaly prediction on all windows...", logger_callback)
    prediction_texts = prepare_training_texts(window_texts)
    predictions = detector.predict(prediction_texts)
    anomalous_windows = int(sum(predictions))
    correct_windows = len(predictions) - anomalous_windows
    logger.info(
        "Window statistics calculated",
        extra={
            "custom_dimensions": {
                "total_windows": len(predictions),
                "correct_windows": correct_windows,
                "anomalous_windows": anomalous_windows,
            }
        },
    )
    live_log(f"Detected {anomalous_windows} anomalous windows", logger_callback)
    live_log(f"Detected {correct_windows} normal windows", logger_callback)
    return predictions, anomalous_windows, correct_windows


def initialize_ai_components(base_dir=None, logger_callback=None):
    """Create RAG, diagnosis, and remediation objects for incident processing."""

    if base_dir is None:
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    kb_path = os.path.join(base_dir, "knowledge_base")
    live_log("STEP 5: Initializing AI Components", logger_callback)
    live_log("Initializing embedding provider...", logger_callback)
    rag = RAGEngine(kb_path)
    live_log("Initializing diagnosis agent...", logger_callback)
    diagnosis_agent = DiagnosisAgent()
    live_log("Initializing remediation engine...", logger_callback)
    llm = UnifiedLLM()
    remediation_engine = RemediationEngine(llm)
    live_log("AI components initialized successfully", logger_callback)
    return rag, diagnosis_agent, remediation_engine


def build_incident_text(window):
    """Return the most relevant incident text for RAG and diagnosis."""

    filtered_lines = [record["text"] for record in window if record["label"] == 1]
    return "\n".join(filtered_lines or [record["text"] for record in window])


def build_incident_output(incident_count, filtered_text, diagnosis, nodes, affected_components, remediation_result, metrics):
    """Package a single incident record for the return payload."""

    return {
        "incident_id": incident_count,
        "log": filtered_text,
        "diagnosis": diagnosis,
        "nodes": nodes,
        "affected_components": affected_components,
        "action": remediation_result.get("action"),
        "result": remediation_result.get("result"),
        "metrics": metrics,
    }


def build_incident_visualization(incident_count, diagnosis_time, diagnosis, remediation_time, nodes, anomalous_windows_count, metrics):
    """Build one row of performance telemetry for incident visualization."""

    return {
        "incident_id": incident_count,
        "diagnosis_time_sec": round(float(diagnosis_time), 2),
        "remediation_time_sec": round(remediation_time, 2),
        "confidence": round(float(diagnosis.get("confidence", 0)), 2),
        "node_count": len(nodes),
        "anomalous_windows": anomalous_windows_count,
        "action_correctness": metrics.get("action_correctness", 0),
        "resolution_success": metrics.get("resolution_success", 0),
        "reasoning_quality": metrics.get("reasoning_quality", 0),
    }


def process_incidents(window_texts, window_labels, predictions, diagnosis_agent, rag, remediation_engine, logger_callback, max_incidents):
    """Process predicted anomaly windows and return incident summaries."""

    incidents_output = []
    all_metrics = []
    incident_count = 0
    total_predicted = int(sum(predictions))
    live_log(f"Beginning processing for {total_predicted} incidents", logger_callback)

    for window, pred, _ in zip(window_texts, predictions, window_labels):
        if pred != 1:
            continue

        incident_count += 1
        env = SystemEnvironment()
        live_log("=================================", logger_callback)
        live_log(f"INCIDENT #{incident_count}", logger_callback)
        live_log("=================================", logger_callback)
        live_log(f"Processing incident {incident_count} of approximately {min(total_predicted, max_incidents)}", logger_callback)

        filtered_text = build_incident_text(window)
        logger.info("🔹 Full Incident Window:")
        logger.info(filtered_text)

        with _tracer.start_as_current_span("rag_retrieval"):
            retrieved_docs = rag.retrieve(filtered_text, top_k=5)

        live_log(f"Retrieved {len(retrieved_docs)} relevant knowledge documents", logger_callback)

        with _tracer.start_as_current_span("llm_diagnosis"):
            diagnosis_start = time.time()
            diagnosis = diagnosis_agent.diagnose(filtered_text, retrieved_docs)
            diagnosis_time = time.time() - diagnosis_start

        live_log(f"Diagnosis completed: {diagnosis.get('incident_type', 'Unknown Incident')}", logger_callback)

        nodes = extract_nodes(filtered_text)
        env.register_nodes(nodes)
        live_log(f"Detected {len(nodes)} impacted nodes", logger_callback)

        affected_components = extract_affected_components(filtered_text)
        env.register_services(affected_components)
        live_log(f"Detected impacted services: {affected_components}", logger_callback)

        with _tracer.start_as_current_span("remediation_engine"):
            remediation_start = time.time()
            remediation_result = remediation_engine.run(diagnosis, env, nodes)
            remediation_time = time.time() - remediation_start

        metrics = evaluate_remediation(diagnosis, remediation_result)
        live_log(f"Incident #{incident_count} processing completed", logger_callback)

        incidents_output.append(build_incident_output(incident_count, filtered_text, diagnosis, nodes, affected_components, remediation_result, metrics))
        all_metrics.append(build_incident_visualization(incident_count, diagnosis_time, diagnosis, remediation_time, nodes, int(sum(predictions)), metrics))

        if incident_count >= max_incidents:
            live_log(f"Reached configured max incident limit ({max_incidents})", logger_callback)
            break

    return incidents_output, all_metrics, incident_count


def run_pipeline(logs, labels=None, max_incidents=20, logger_callback=None):
    """Execute the full incident detection and remediation pipeline."""

    with _tracer.start_as_current_span("incident_pipeline"):
        pipeline_start = time.time()
        live_log("STEP 1: Loading Logs", logger_callback)
        contents = logs
        live_log(f"Loaded {len(contents)} total log lines", logger_callback)
        logger.info("Logs loaded", extra={"custom_dimensions": {"total_logs": len(contents)}})

        labels = labels if labels is not None else [0] * len(contents)
        live_log("STEP 2: Creating Windows", logger_callback)
        window_texts, window_labels = create_windows(contents=contents, labels=labels, window_size=100, stride=100)
        live_log(f"Total Windows: {len(window_texts)}", logger_callback)

        detector = IncidentDetector()
        training_texts = prepare_training_texts(window_texts)
        ml_metrics = train_or_load_model(detector, training_texts, window_labels, logger_callback)

        predictions, anomalous_count, correct_count = detect_incidents(detector, window_texts, logger_callback)
        rag, diagnosis_agent, remediation_engine = initialize_ai_components(logger_callback=logger_callback)
        incidents_output, all_metrics, incident_count = process_incidents(window_texts, window_labels, predictions, diagnosis_agent, rag, remediation_engine, logger_callback, max_incidents)

        avg_action_accuracy = round(sum(metric["action_correctness"] for metric in all_metrics) / len(all_metrics), 2) if all_metrics else 0
        avg_resolution_success = round(sum(metric["resolution_success"] for metric in all_metrics) / len(all_metrics), 2) if all_metrics else 0

        live_log("Pipeline execution completed successfully", logger_callback)
        live_log(f"Average Action Accuracy: {avg_action_accuracy}", logger_callback)
        live_log(f"Average Resolution Success: {avg_resolution_success}", logger_callback)

        total_duration = time.time() - pipeline_start
        logger.info(
            "Pipeline execution completed",
            extra={
                "custom_dimensions": {
                    "processed_incidents": incident_count,
                    "total_anomalies": anomalous_count,
                    "pipeline_time_sec": round(total_duration, 2),
                    "avg_action_accuracy": avg_action_accuracy,
                    "avg_resolution_success": avg_resolution_success,
                }
            },
        )

        return {
            "total_windows": len(window_texts),
            "correct_windows": correct_count,
            "anomalous_windows": anomalous_count,
            "total_anomalies": anomalous_count,
            "processed_incidents": incident_count,
            "avg_action_accuracy": avg_action_accuracy,
            "avg_resolution_success": avg_resolution_success,
            "incidents": incidents_output,
            "performance_metrics": all_metrics,
            "ml_metrics": ml_metrics,
        }


if __name__ == "__main__":
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    log_path = os.path.join(base_dir, "data", "BGL.log")
    contents, labels = load_bgl(log_path)
    output = run_pipeline(logs=contents, labels=labels, max_incidents=5)
    print("\nFINAL OUTPUT SUMMARY:")
    print(json.dumps(output, indent=2))
