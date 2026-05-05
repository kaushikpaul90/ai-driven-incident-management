import os
import logging

from cluster_engine import ClusterEngine

# -------------------------------
# 🔥 HARD SUPPRESSION (CRITICAL)
# -------------------------------
os.environ["TRANSFORMERS_VERBOSITY"] = "error"
os.environ["HF_HUB_DISABLE_TELEMETRY"] = "1"
os.environ["TOKENIZERS_PARALLELISM"] = "false"

# -------------------------------
# 🔥 LOGGER SUPPRESSION
# -------------------------------
logging.getLogger("transformers").setLevel(logging.ERROR)
logging.getLogger("sentence_transformers").setLevel(logging.ERROR)
logging.getLogger("huggingface_hub").setLevel(logging.ERROR)
logging.getLogger("urllib3").setLevel(logging.ERROR)
logging.getLogger("httpx").setLevel(logging.ERROR)
logging.getLogger("requests").setLevel(logging.ERROR)

import re
import sys
import json
import warnings

from rag import RAGEngine
from detection import IncidentDetector
from environment import SystemEnvironment
from diagnosis_agent import DiagnosisAgent
from evaluation import evaluate_remediation
from langchain_community.llms import Ollama
from remediation_engine import RemediationEngine
from preprocessing import load_bgl, create_windows
from entity_extractor import EntityExtractor
from collections import defaultdict
from event_classifier import EventClassifier

logging.getLogger("transformers").setLevel(logging.ERROR)
logging.getLogger("sentence_transformers").setLevel(logging.ERROR)
logging.getLogger("urllib3").setLevel(logging.ERROR)
warnings.filterwarnings("ignore", category=RuntimeWarning)
os.environ["TRANSFORMERS_VERBOSITY"] = "error"

# -----------------------------
# LOGGING SETUP
# -----------------------------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger()

# -----------------------------
# CLEAN LOGGER REDIRECTION
# -----------------------------
class StreamToLogger:
    def __init__(self, logger):
        self.logger = logger

    def write(self, buf):
        for line in buf.splitlines():
            clean = line.strip()

            if not clean:
                continue

            # ❌ Remove tqdm noise
            if "it/s" in clean or re.search(r"\d+it\s*\[", clean):
                continue

            # ❌ Remove HF logs
            if "HTTP Request" in clean:
                continue

            # ❌ Remove model loading spam
            if "Loading weights" in clean:
                continue

            # ⚠️ downgrade warnings
            if "warning" in clean.lower():
                self.logger.warning(clean)
                continue

            if "Loading weights" in clean:
                return
            
            if "HTTP Request" in clean:
                return

            if "huggingface.co" in clean:
                return

            self.logger.info(clean)

    def flush(self):
        pass

    def isatty(self):
        return False

sys.stdout = StreamToLogger(logger)
os.environ["DISABLE_TQDM"] = "1"
sys.stderr = StreamToLogger(logger)

# -----------------------------
# HELPERS
# -----------------------------
def extract_services(text):
    keywords = ["cache", "memory", "disk", "network", "io", "cpu"]
    return list({k for k in keywords if k in text.lower()})

# -----------------------------
# PIPELINE START
# -----------------------------
logger.info("STEP 1: Loading Logs")

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
log_path = os.path.join(BASE_DIR, "data", "BGL.log")

contents, labels = load_bgl(log_path)

logger.info("STEP 2: Creating Windows")

window_texts, window_labels = create_windows(
    contents, labels, window_size=100, stride=50
)

logger.info(f"Total Windows: {len(window_texts)}")

# logger.info("STEP 3: Training Detection Model")

# detector = IncidentDetector()
# X_test, y_test = detector.train(window_texts, window_labels)

logger.info("STEP 3: Training Detection Model")

# 🔹 Explain what’s about to happen
logger.info("→ Preparing features using TF-IDF vectorization")
logger.info("→ Splitting data into train/test sets")
logger.info("→ Training Logistic Regression classifier")

detector = IncidentDetector()

# (Optional but powerful for demo)
logger.info(f"→ Total samples: {len(window_texts)}")
logger.info(f"→ Positive labels (anomalies): {sum(window_labels)}")
logger.info(f"→ Negative labels (normal): {len(window_labels) - sum(window_labels)}")

X_test, y_test = detector.train(window_texts, window_labels)

logger.info("STEP 3 Completed: Model trained successfully")

logger.info("STEP 3.1: Evaluating Model")
detector.evaluate(X_test, y_test)

# logger.info("STEP 4: Detecting Incidents")

# predictions = detector.predict(window_texts)
# logger.info(f"Total Anomalies: {sum(predictions)}")

logger.info("STEP 4: Detecting Incidents")

logger.info("→ Transforming input logs using trained TF-IDF vectorizer")
logger.info("→ Applying Logistic Regression model for prediction")

predictions = detector.predict(window_texts)

total = len(predictions)
anomalies = sum(predictions)
normal = total - anomalies

logger.info(f"→ Total windows evaluated: {total}")
logger.info(f"→ Predicted anomalies: {anomalies}")
logger.info(f"→ Predicted normal: {normal}")

logger.info("STEP 4 Completed: Incident detection finished")

logger.info("STEP 5: Initializing AI Components" \
"")

logger.info("→ Loading Knowledge Base & Embeddings (RAG)")
rag = RAGEngine(os.path.join(BASE_DIR, "data"))

logger.info("→ Initializing Diagnosis Agent (LLM-based)")
diagnosis_agent = DiagnosisAgent()

event_classifier = EventClassifier()

logger.info("→ Loading Local LLM (LLaMA3 via Ollama)")
llm = Ollama(model="llama3")

logger.info("→ Initializing Remediation Engine")
remediation_engine = RemediationEngine(llm)

incident_count = 0

entity_extractor = EntityExtractor()
cluster_engine = ClusterEngine(rag.kb)

# -----------------------------
# INCIDENT LOOP
# -----------------------------
for text, pred in zip(window_texts, predictions):

    if pred != 1:
        continue

    logger.info("\n===================================")
    logger.info(f"INCIDENT #{incident_count+1}")
    logger.info("===================================")

    logger.info("🔹 Incident Sample:")
    logger.info(text[:250] + "...")

    text_lower = text.lower()

    # ----------------------------------
    # 🚨 HARD FILTER: SKIP SELF-HEALED LOGS
    # ----------------------------------
    if "corrected" in text_lower and "error" in text_lower:
        logger.warning("⚠️ Skipping: Corrected error detected (healthy state)")
        continue

    # -----------------------------
    # 🧠 EVENT CLASSIFICATION
    # -----------------------------
    logger.info("🧠 Classifying Event State")
    event_state = event_classifier.classify(text)

    logger.info(f"🧠 Event State: {event_state}")

    # ----------------------------------
    # ⚠️ LOW CONFIDENCE GUARD
    # ----------------------------------
    if event_state.get("confidence", 0) < 0.6:
        logger.warning("⚠️ Low confidence in event classification — skipping")
        continue

    # ----------------------------------
    # ❌ SKIP NON-FAILURE EVENTS
    # ----------------------------------
    if event_state.get("state") != "failure":
        logger.info("✅ Skipping non-failure event")
        continue

    # ----------------------------------
    # ⚠️ DETECTION vs CLASSIFICATION MISMATCH
    # ----------------------------------
    if pred == 1 and event_state["state"] != "failure":
        logger.warning("⚠️ Model detected anomaly but classified as non-failure")
        continue

    # -----------------------------
    # CLUSTERING
    # -----------------------------
    clusters = cluster_engine.cluster_window(text, rag.kb)
    logger.info(f"DEBUG: Cluster Keys → {list(clusters.keys())}")
    
    cluster_id = 1

    for cluster_type, cluster_words in clusters.items():

        if cluster_type == "unknown":
            logger.warning("⚠️ Unknown cluster detected - skipped")
            continue

        logger.info("\n-----------------------------------")
        logger.info(f"SUB-INCIDENT {incident_count+1}.{cluster_id}")
        logger.info("-----------------------------------")

        cluster_text = " ".join(cluster_words)

        logger.info(f"🔹 Cluster Type: {cluster_type}")
        logger.info(f"🔹 Sample: {cluster_text[:200]}...")

        env = SystemEnvironment()

        # -----------------------------
        # KB MATCH
        # -----------------------------
        kb_entry = next(
            (e for e in rag.kb if e["error_type"] == cluster_type),
            None
        )

        if not kb_entry:
            continue

        # -----------------------------
        # DIAGNOSIS
        # -----------------------------
        logger.info("🔹 Running Diagnosis")

        diagnosis = diagnosis_agent.diagnose(cluster_text, [kb_entry])

        logger.info("🧠 Diagnosis:")
        logger.info(json.dumps(diagnosis, indent=2))

        # -----------------------------
        # ENTITY EXTRACTION
        # -----------------------------
        nodes = entity_extractor.extract_nodes(text)
        services = entity_extractor.extract_services(cluster_text, kb_entry)

        logger.info(f"🔍 Nodes: {nodes}")
        logger.info(f"🔍 Services: {services}")

        env.register_nodes(nodes)
        env.register_services(services)

        # -----------------------------
        # REMEDIATION
        # -----------------------------
        logger.info("⚙️ Running Remediation")

        result = remediation_engine.run(
            diagnosis,
            env,
            nodes
        )

        logger.info("⚙️ Action Taken:")
        logger.info(result["action"])

        logger.info("⚙️ Result:")
        logger.info(result["result"])

        # -----------------------------
        # EVALUATION
        # -----------------------------
        metrics = evaluate_remediation(diagnosis, result)

        logger.info("📊 Metrics:")
        logger.info(metrics)

        cluster_id += 1

    incident_count += 1

    if incident_count == 3:
        break

logger.info("\n===================================")
logger.info("DEMO COMPLETE")
logger.info("===================================")