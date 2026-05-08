import os
import logging

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
from clustering import IncidentClusterer
from environment import SystemEnvironment
from diagnosis_agent import DiagnosisAgent
from evaluation import evaluate_remediation
from langchain_community.llms import Ollama
from remediation_engine import RemediationEngine
from preprocessing import load_bgl, create_windows

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
def extract_nodes(log_text):
    patterns = [
        r'R\d+-M\d+-L\d+-U\d+-C',
        r'R\d+-M\d+-N\d+',
        r'\bR\d{1,2}-[A-Z0-9][\w-]+\b',
        r'\d+\.\d+\.\d+\.\d+'   # IP addresses
    ]

    nodes = set()
    for p in patterns:
        nodes.update(re.findall(p, log_text, re.IGNORECASE))

    return [n.lower() for n in nodes]

def extract_services(text):
    keywords = ["cache", "memory", "disk", "network", "io", "cpu"]
    return list({k for k in keywords if k in text.lower()})

def split_into_incidents(window_text):

    lines = window_text.split("\n")

    incidents = []
    current = []

    for line in lines:
        line = line.strip()
        if not line:
            continue

        if (
            "ciod:" in line.lower()
            or "error" in line.lower()
            or "failed" in line.lower()
        ):
            if current:
                incidents.append(" ".join(current))
                current = []

        current.append(line)

    if current:
        incidents.append(" ".join(current))

    return [i for i in incidents if len(i) > 50]

def is_corrected_log(text):
    text_lower = text.lower()

    # Strong signals → always safe to skip
    strong_patterns = [
        "detected and corrected",
        "ce sym",
        "bit sparing",
        "scrubbed"
    ]

    if any(p in text_lower for p in strong_patterns):
        return True

    # Weak signal → needs context
    if "corrected" in text_lower:
        escalation_keywords = [
            "failure",
            "fatal",
            "unrecoverable",
            "panic",
            "crash",
            "degraded",
            "multiple"
        ]

        if not any(e in text_lower for e in escalation_keywords):
            return True

    return False

def normalize_log(text):
    """
    Normalize logs to remove variable parts (IP, ports, numbers)
    """
    text = text.lower()

    text = re.sub(r'\d+\.\d+\.\d+\.\d+', 'IP', text)  # IPs
    text = re.sub(r':\d+', ':PORT', text)             # ports
    text = re.sub(r'0x[0-9a-f]+', 'HEX', text)        # hex
    text = re.sub(r'\b\d{2,}\b', 'NUM', text)         # numbers

    return text

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
rag = RAGEngine(os.path.join(BASE_DIR, "knowledge_base"))

logger.info("→ Initializing Diagnosis Agent (LLM-based)")
diagnosis_agent = DiagnosisAgent()

logger.info("→ Loading Local LLM (LLaMA3 via Ollama)")
llm = Ollama(model="llama3")

logger.info("→ Initializing Remediation Engine")
remediation_engine = RemediationEngine(llm)

incident_count = 0
seen_incidents = set()
seen_normalized_logs = set()
clusterer = IncidentClusterer(threshold=0.85)

# -----------------------------
# INCIDENT LOOP
# -----------------------------
for text, pred in zip(window_texts, predictions):

    if pred != 1:
        continue

    # Split window into multiple incidents
    incident_chunks = split_into_incidents(text)

    for chunk in incident_chunks:

        # Skip corrected logs
        if is_corrected_log(chunk):
            logger.info("⚠️ Skipping corrected log (auto-resolved)")
            continue

        # Lightweight pre-filter (before LLM)
        normalized = normalize_log(chunk)

        if normalized in seen_normalized_logs:
            logger.info("⚠️ Skipping duplicate incident (fast pre-filter)")
            continue

        # Cluster-Level filter (semantic duplicate BEFORE LLM)
        if clusterer.is_duplicate(normalized):
            logger.info("⚠️ Skipping duplicate incident (clustered)")
            continue

        seen_normalized_logs.add(normalized)

        logger.info("\n===================================")

        logger.info("🔹 Incident Sample:")
        logger.info(chunk[:250] + "...")

        env = SystemEnvironment()

        # RAG
        logger.info("🔹 Retrieving Knowledge")
        docs = rag.retrieve(chunk, top_k=5)

        # Diagnosis
        logger.info("🔹 Running Diagnosis")
        diagnosis = diagnosis_agent.diagnose(chunk, docs)

        logger.info("🧠 Diagnosis:")
        logger.info(json.dumps(diagnosis, indent=2))

        # Nodes + Services
        nodes = extract_nodes(chunk)
        services = extract_services(chunk)

        logger.info(f"🔍 Nodes: {nodes}")
        logger.info(f"🔍 Services: {services}")

        # Deduplication
        signature = diagnosis.get("incident_type", "") + "_" + "_".join(sorted(nodes))

        if signature in seen_incidents:
            logger.info("⚠️ Skipping duplicate incident (semantic)")
            continue

        seen_incidents.add(signature)

        incident_count += 1

        logger.info(f"INCIDENT #{incident_count}")
        logger.info("===================================")

        env.register_nodes(nodes)
        env.register_services(services)

        # Remediation
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

        # Evaluation
        metrics = evaluate_remediation(diagnosis, result)

        logger.info("📊 Metrics:")
        logger.info(metrics)

        # Add to cluster AFTER successful processing
        clusterer.add_incident(normalized)

        if incident_count == 3:
            break

    if incident_count == 3:
        break

logger.info("\n===================================")
logger.info("DEMO COMPLETE")
logger.info("===================================")