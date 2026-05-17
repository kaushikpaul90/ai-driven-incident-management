import os
import re
import sys
import json
import logging
import warnings
import time
from datetime import datetime

from rag import RAGEngine
from detection import IncidentDetector
from environment import SystemEnvironment
from diagnosis_agent import DiagnosisAgent
from evaluation import evaluate_remediation
# from langchain_community.llms import Ollama
from llm_client import chat
from remediation_engine import RemediationEngine
from preprocessing import load_bgl, create_windows
from opentelemetry import trace
from sklearn.metrics import (
    accuracy_score,
    precision_score,
    recall_score,
    f1_score
)

os.environ["TRANSFORMERS_NO_ADVISORY_WARNINGS"] = "1"
os.environ["TRANSFORMERS_VERBOSITY"] = "error"
os.environ["TOKENIZERS_PARALLELISM"] = "false"
os.environ["TRANSFORMERS_NO_TORCHVISION"] = "1"
logging.getLogger("transformers").setLevel(logging.ERROR)
logging.getLogger("torch").setLevel(logging.ERROR)
warnings.filterwarnings("ignore")

# -----------------------------
# LOG FILE PATH SETUP
# -----------------------------
BASE_DIR = os.path.dirname(
    os.path.dirname(os.path.abspath(__file__))
)

LOG_DIR = os.path.join(BASE_DIR, "logs")

os.makedirs(LOG_DIR, exist_ok=True)

timestamp = datetime.now().strftime(
    "%Y%m%d_%H%M%S"
)

LOG_FILE = os.path.join(
    LOG_DIR,
    f"incident_pipeline_{timestamp}.log"
)

# -----------------------------
# CUSTOM LOGGER SETUP
# -----------------------------
logger = logging.getLogger("incident_pipeline")

# Prevent duplicate handlers
logger.handlers.clear()

logger.setLevel(logging.INFO)

# Prevent Streamlit root logger propagation
logger.propagate = False

# -----------------------------
# LOG FORMAT
# -----------------------------
formatter = logging.Formatter(
    "%(asctime)s | %(levelname)s | %(message)s"
)

# -----------------------------
# CONSOLE HANDLER
# -----------------------------
console_handler = logging.StreamHandler(sys.stdout)
console_handler.setFormatter(formatter)

# -----------------------------
# FILE HANDLER
# -----------------------------
file_handler = logging.FileHandler(
    LOG_FILE,
    mode="w",
    encoding="utf-8"
)

file_handler.setFormatter(formatter)

# -----------------------------
# REGISTER HANDLERS
# -----------------------------
logger.addHandler(console_handler)
logger.addHandler(file_handler)

logger.info("========== INCIDENT PIPELINE STARTED ==========")
logger.info(f"Log file created at: {LOG_FILE}")

# logger = logging.getLogger()
tracer = trace.get_tracer(__name__)

class UnifiedLLM:
    def invoke(self, prompt):
        return chat([
            {
                "role": "user",
                "content": prompt
            }
        ])

# -----------------------------
# LIVE LOGGER HELPER
# -----------------------------
def live_log(message, logger_callback=None):

    logger.info(message)

    if logger_callback:

        timestamp = datetime.now().strftime("%H:%M:%S")

        formatted_message = f"[{timestamp}] {message}"

        logger_callback(formatted_message)

# -----------------------------
# HELPERS
# -----------------------------
def extract_nodes(log_text: str):

    # Normalize log text to uppercase
    log_text = log_text.upper()

    # ---------------------------------------------------
    # STRICT BGL NODE REGEX
    # ---------------------------------------------------
    # Examples matched:
    # R03-M1-N9-C:J09-U11
    # R36-M0-N4-I:J18-U11
    # R24-M1-NC-I:J18-U01
    # R03-M1-N9-C
    # R24-M1-NC-I
    # ---------------------------------------------------
    pattern = (
        r"\bR\d{2}-M\d-"
        r"(?:N\d|NC|NA|NB|NF)"
        r"(?:-[A-Z])"
        r"(?::J\d{2}-U\d{2})?\b"
    )

    matches = re.findall(
        pattern,
        log_text
    )

    # ---------------------------------------------------
    # CLEAN SOCKET INFO
    # ---------------------------------------------------
    # Convert:
    # R03-M1-N9-C:J09-U11
    # → R03-M1-N9-C
    # ---------------------------------------------------
    clean_nodes = [
        node.split(":")[0]
        for node in matches
    ]

    return sorted(list(set(clean_nodes)))

def extract_affected_components(log_text):

    patterns = [
        r"\bTLB\b",
        r"\bECC\b",
        r"\bCioStream\b",
        r"\bcache\b",
        r"\bkernel\b",
        r"\bciod\b",
        r"\bASSERT\b",
        r"\bmachine check\b",
        r"\balignment exceptions\b"
    ]

    components = set()

    for pattern in patterns:

        matches = re.findall(
            pattern,
            log_text,
            re.IGNORECASE
        )

        for match in matches:
            components.add(match.lower())

    return sorted(list(components))

# =========================================================
# 🚀 MAIN PIPELINE FUNCTION (USED BY UI)
# =========================================================
def run_pipeline(logs, labels=None, max_incidents=20, logger_callback=None):

    with tracer.start_as_current_span("incident_pipeline"):
        pipeline_start_time = time.time()

        live_log("STEP 1: Loading Logs", logger_callback)

        # BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        # log_path = os.path.join(BASE_DIR, "data", "BGL.log")

        # contents, labels = load_bgl(log_path)

        # Use logs coming from UI
        contents = logs

        live_log(f"Loaded {len(contents)} total log lines", logger_callback)
        logger.info(
            "Logs loaded",
            extra={
                "custom_dimensions": {
                    "total_logs": len(contents)
                }
            }
        )

        # Since uploaded logs don’t have labels → assume normal (0)
        if labels is None:
            labels = [0] * len(contents)

        # -----------------------------
        live_log("STEP 2: Creating Windows", logger_callback)

        live_log("Creating sliding log windows...", logger_callback)

        with tracer.start_as_current_span("window_creation"):
            window_texts, window_labels = create_windows(
                contents=contents,
                labels=labels,
                window_size=100,
                stride=100
            )

        live_log(f"Total Windows: {len(window_texts)}", logger_callback)

        detector = IncidentDetector()

        # ---------------------------------------------------
        # STEP 3: MODEL INITIALIZATION
        # ---------------------------------------------------

        model_exists = detector.model_exists()

        training_texts = [
            "\n".join([r["text"] for r in window])
            for window in window_texts
        ]

        # ---------------------------------------------------
        # LOAD EXISTING MODEL
        # ---------------------------------------------------
        if model_exists:

            live_log(
                "STEP 3: Loading Detection Model",
                logger_callback
            )

            live_log(
                "Initializing anomaly detection model...",
                logger_callback
            )

            live_log(
                "Loading pretrained ML model...",
                logger_callback
            )

            detector.load_model()

            live_log(
                "Pretrained ML model loaded successfully",
                logger_callback
            )

            # ---------------------------------------------
            # Skip evaluation when pretrained model exists
            # ---------------------------------------------
            ml_metrics = {
                "accuracy": "Pretrained",
                "precision": "Pretrained",
                "recall": "Pretrained",
                "f1_score": "Pretrained"
            }

        # ---------------------------------------------------
        # TRAIN NEW MODEL
        # ---------------------------------------------------
        else:

            live_log(
                "STEP 3: Training Detection Model",
                logger_callback
            )

            live_log(
                "Initializing anomaly detection model...",
                logger_callback
            )

            live_log(
                "Training ML model on generated windows...",
                logger_callback
            )

            X_test, y_test = detector.train(
                training_texts,
                window_labels
            )

            live_log(
                "Model training completed successfully",
                logger_callback
            )

            # ---------------------------------------------------
            # MODEL EVALUATION
            # ---------------------------------------------------
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

            # ---------------------------------------------------
            # ML MODEL METRICS
            # ---------------------------------------------------
            predictions_eval = detector.predict(X_test)

            accuracy = accuracy_score(
                y_test,
                predictions_eval
            )

            precision = precision_score(
                y_test,
                predictions_eval,
                zero_division=0
            )

            recall = recall_score(
                y_test,
                predictions_eval,
                zero_division=0
            )

            f1 = f1_score(
                y_test,
                predictions_eval,
                zero_division=0
            )

            ml_metrics = {
                "accuracy":
                    round(float(accuracy), 2),

                "precision":
                    round(float(precision), 2),

                "recall":
                    round(float(recall), 2),

                "f1_score":
                    round(float(f1), 2)
            }

            logger.info(
                "ML model evaluation completed",
                extra={
                    "custom_dimensions": ml_metrics
                }
            )

        # -----------------------------
        live_log("STEP 4: Detecting Incidents", logger_callback)

        live_log(
            "Running anomaly prediction on all windows...",
            logger_callback
        )

        prediction_texts = [
            "\n".join([r["text"] for r in window])
            for window in window_texts
        ]

        with tracer.start_as_current_span("incident_detection"):
            predictions = detector.predict(prediction_texts)
        
        # ---------------------------------------------------
        # Calculate window statistics
        # ---------------------------------------------------
        anomalous_windows_count = int(sum(predictions))

        correct_windows_count = (
            len(predictions) - anomalous_windows_count
        )

        logger.info(
            "Window statistics calculated",
            extra={
                "custom_dimensions": {
                    "total_windows": len(predictions),
                    "correct_windows": correct_windows_count,
                    "anomalous_windows": anomalous_windows_count
                }
            }
        )

        live_log(
            f"Detected {anomalous_windows_count} anomalous windows",
            logger_callback
        )

        live_log(
            f"Detected {correct_windows_count} normal windows",
            logger_callback
        )

        # -----------------------------
        live_log("STEP 5: Initializing AI Components", logger_callback)

        live_log(
            "Initializing embedding provider...",
            logger_callback
        )

        BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        kb_path = os.path.join(BASE_DIR, "knowledge_base")

        rag = RAGEngine(kb_path)

        live_log(
            "Initializing diagnosis agent...",
            logger_callback
        )

        # diagnosis_agent = DiagnosisAgent(model="llama3")
        diagnosis_agent = DiagnosisAgent()

        # live_log(
        #     "Connecting to Ollama LLM...",
        #     logger_callback
        # )

        # # llm = Ollama(model="llama3")

        live_log(
            "Initializing LLM provider...",
            logger_callback
        )

        llm = UnifiedLLM()

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

            # ---------------------------------------------------
            # Use only anomalous records for RAG retrieval
            # ---------------------------------------------------
            filtered_lines = [
                record["text"]
                for record in text
                if record["label"] == 1
            ]

            # Fallback safety
            if not filtered_lines:
                filtered_lines = [
                    record["text"]
                    for record in text
                ]

            filtered_text = "\n".join(filtered_lines)

            # ---------------------------------------------------
            # FULL INCIDENT LOGGING
            # ---------------------------------------------------
            logger.info("🔹 Full Incident Window:")

            try:
                logger.info(
                    json.dumps(text, indent=2)
                )

            except Exception:
                logger.info(str(text))

            # ---------------------------------------------------
            # LOG FILTERED ANOMALOUS RECORDS
            # ---------------------------------------------------
            logger.info("🔹 Filtered Anomalous Records:")

            try:
                logger.info(filtered_text)

            except Exception:
                logger.info(str(filtered_text))

            with tracer.start_as_current_span("rag_retrieval"):
                rag_start = time.time()

                retrieved_docs = rag.retrieve(
                    filtered_text,
                    top_k=5
                )

                rag_time = time.time() - rag_start

                logger.info(
                    "Knowledge retrieval completed",
                    extra={
                        "custom_dimensions": {
                            "documents_found": len(retrieved_docs),
                            "retrieval_time_sec": round(rag_time, 2)
                        }
                    }
                )

            live_log(
                f"Retrieved {len(retrieved_docs)} relevant knowledge documents",
                logger_callback
            )

            # -----------------------------
            logger.info("🔹 Running Diagnosis")

            live_log(
                "Filtering relevant failure records...",
                logger_callback
            )

            live_log(
                "Running LLM diagnosis engine...",
                logger_callback
            )

            with tracer.start_as_current_span("llm_diagnosis") as span:

                diagnosis_start = time.time()

                diagnosis = diagnosis_agent.diagnose(
                    filtered_text,
                    retrieved_docs
                )

                diagnosis_time = time.time() - diagnosis_start

                span.set_attribute(
                    "incident.type",
                    diagnosis.get("incident_type", "unknown")
                )

                span.set_attribute(
                    "incident.severity",
                    diagnosis.get("severity", "unknown")
                )

                span.set_attribute(
                    "incident.confidence",
                    float(diagnosis.get("confidence", 0))
                )

                logger.info(
                    "Diagnosis completed",
                    extra={
                        "custom_dimensions": {
                            "incident_type":
                                diagnosis.get("incident_type"),

                            "severity":
                                diagnosis.get("severity"),

                            "confidence":
                                diagnosis.get("confidence"),

                            "diagnosis_time_sec":
                                round(diagnosis_time, 2)
                        }
                    }
                )

            logger.info("🧠 Diagnosis:")
            logger.info(json.dumps(diagnosis, indent=2))

            live_log(
                f"Diagnosis completed: "
                f"{diagnosis.get('incident_type', 'Unknown Incident')}",
                logger_callback
            )

            # -----------------------------
            nodes = extract_nodes(filtered_text)
            env.register_nodes(nodes)

            logger.info(f"🔍 Nodes: {nodes}")
            logger.info(
                "Nodes extracted",
                extra={
                    "custom_dimensions": {
                        "node_count": len(nodes),
                        "nodes": ",".join(nodes[:20])
                    }
                }
            )

            live_log(
                f"Detected {len(nodes)} impacted nodes",
                logger_callback
            )

            # ---------------------------------------------------
            # Extract only anomalous log lines for service analysis
            # ---------------------------------------------------
            service_logs = [
                record["text"]
                for record in text
                if record["label"] == 1
            ]

            # Fallback safety
            if not service_logs:
                service_logs = [
                    record["text"]
                    for record in text
                ]

            affected_components = extract_affected_components(
                filtered_text
            )

            env.register_services(
                affected_components
            )

            env.register_services(affected_components)

            logger.info(f"🔍 Services: {affected_components}")

            live_log(
                f"Detected impacted services: {affected_components}",
                logger_callback
            )

            # -----------------------------
            logger.info("⚙️ Running Remediation")

            live_log(
                "Executing remediation engine...",
                logger_callback
            )

            with tracer.start_as_current_span("remediation_engine"):
                remediation_start = time.time()

                remediation_result = remediation_engine.run(
                    diagnosis,
                    env,
                    nodes
                )

                remediation_time = (
                    time.time() - remediation_start
                )

                logger.info(
                    "Remediation completed",
                    extra={
                        "custom_dimensions": {
                            "action":
                                remediation_result.get("action"),

                            "result":
                                remediation_result.get("result"),

                            "remediation_time_sec":
                                round(remediation_time, 2)
                        }
                    }
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
                "log": filtered_text,
                "diagnosis": diagnosis,
                "nodes": nodes,
                "affected_components": affected_components,
                "action": remediation_result.get("action"),
                "result": remediation_result.get("result"),
                "metrics": metrics
            })

            incident_visualization = {
                "incident_id": incident_count,

                # -------------------------------------
                # Operational telemetry
                # -------------------------------------
                "diagnosis_time_sec":
                    round(diagnosis_time, 2),

                "remediation_time_sec":
                    round(remediation_time, 2),

                "confidence":
                    round(
                        float(
                            diagnosis.get("confidence", 0)
                        ),
                        2
                    ),

                "node_count":
                    len(nodes),

                "anomalous_windows":
                    anomalous_windows_count,

                # -------------------------------------
                # Evaluation metrics
                # -------------------------------------
                "action_correctness":
                    metrics.get(
                        "action_correctness",
                        0
                    ),

                "resolution_success":
                    metrics.get(
                        "resolution_success",
                        0
                    ),

                "reasoning_quality":
                    metrics.get(
                        "reasoning_quality",
                        0
                    )
            }

            all_metrics.append(
                incident_visualization
            )

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

        total_pipeline_time = (
            time.time() - pipeline_start_time
        )

        logger.info(
            "Pipeline execution completed",
            extra={
                "custom_dimensions": {
                    "processed_incidents":
                        incident_count,

                    "total_anomalies":
                        int(sum(predictions)),

                    "pipeline_time_sec":
                        round(total_pipeline_time, 2),

                    "avg_action_accuracy":
                        round(avg_action, 2),

                    "avg_resolution_success":
                        round(avg_success, 2)
                }
            }
        )

        return {
            "total_windows": len(window_texts),
            "correct_windows": correct_windows_count,
            "anomalous_windows": anomalous_windows_count,
            "total_anomalies": anomalous_windows_count,
            "processed_incidents": incident_count,
            "avg_action_accuracy": avg_action,
            "avg_resolution_success": avg_success,
            "incidents": incidents_output,
            "performance_metrics": all_metrics,
            "ml_metrics": ml_metrics
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