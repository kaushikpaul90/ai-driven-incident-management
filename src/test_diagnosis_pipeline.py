import os

# -------------------------------
# 🔥 HARD SUPPRESSION (MUST BE FIRST)
# -------------------------------
os.environ["TRANSFORMERS_VERBOSITY"] = "error"
os.environ["HF_HUB_DISABLE_TELEMETRY"] = "1"
os.environ["TOKENIZERS_PARALLELISM"] = "false"
os.environ["DISABLE_TQDM"] = "0"   # allow tqdm

import re
import sys
import json
import logging
import warnings

# -------------------------------
# LOGGER SUPPRESSION
# -------------------------------
logging.getLogger("transformers").setLevel(logging.ERROR)
logging.getLogger("sentence_transformers").setLevel(logging.ERROR)
logging.getLogger("huggingface_hub").setLevel(logging.ERROR)
logging.getLogger("urllib3").setLevel(logging.ERROR)
logging.getLogger("httpx").setLevel(logging.ERROR)
logging.getLogger("requests").setLevel(logging.ERROR)

warnings.filterwarnings("ignore", category=RuntimeWarning)

# -------------------------------
# IMPORTS
# -------------------------------
from rag import RAGEngine
from detection import IncidentDetector
from environment import SystemEnvironment
from diagnosis_agent import DiagnosisAgent
from evaluation import evaluate_remediation
from langchain_community.llms import Ollama
from remediation_engine import RemediationEngine
from preprocessing import load_bgl, create_windows

# -----------------------------
# LOGGING SETUP
# -----------------------------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)]
)

logger = logging.getLogger()

# -----------------------------
# STREAM FILTER
# -----------------------------
class StreamToLogger:
    def __init__(self, logger):
        self.logger = logger

    def write(self, buf):
        for line in buf.splitlines():
            clean = line.strip()
            if not clean:
                continue

            if "HTTP Request" in clean or "huggingface.co" in clean:
                continue

            if "Loading weights" in clean:
                continue

            self.logger.info(clean)

    def flush(self):
        pass

    def isatty(self):
        return False


sys.stdout = StreamToLogger(logger)
sys.stderr = StreamToLogger(logger)

# -----------------------------
# HELPERS
# -----------------------------
def extract_nodes(log_text):
    patterns = [
        r'R\d+-M\d+-L\d+-U\d+-C',
        r'R\d+-M\d+-N\d+',
    ]
    nodes = set()
    for p in patterns:
        nodes.update(re.findall(p, log_text, re.IGNORECASE))
    return [n.lower() for n in nodes]


def extract_services(text):
    keywords = ["cache", "memory", "disk", "network", "io", "cpu"]
    return list({k for k in keywords if k in text.lower()})


# -----------------------------
# PIPELINE
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

# -----------------------------
# STEP 3: TRAINING
# -----------------------------
logger.info("STEP 3: Training Detection Model")
logger.info("→ Preparing features using TF-IDF vectorization")
logger.info("→ Splitting data into train/test sets")
logger.info("→ Training Logistic Regression classifier")

logger.info(f"→ Total samples: {len(window_texts)}")
logger.info(f"→ Positive labels (anomalies): {sum(window_labels)}")
logger.info(f"→ Negative labels (normal): {len(window_labels) - sum(window_labels)}")

detector = IncidentDetector()
X_test, y_test = detector.train(window_texts, window_labels)

logger.info("STEP 3 Completed: Model trained successfully")

# -----------------------------
# STEP 3.1: EVALUATION
# -----------------------------
logger.info("STEP 3.1: Evaluating Model")
detector.evaluate(X_test, y_test)

# -----------------------------
# STEP 4: PREDICTION
# -----------------------------
logger.info("STEP 4: Detecting Incidents")
logger.info("→ Transforming input logs using trained TF-IDF vectorizer")
logger.info("→ Applying Logistic Regression model for prediction")

predictions = detector.predict(window_texts)

total = len(predictions)
anomalies = sum(predictions)

logger.info(f"→ Total windows evaluated: {total}")
logger.info(f"→ Predicted anomalies: {anomalies}")
logger.info(f"→ Predicted normal: {total - anomalies}")

logger.info("STEP 4 Completed: Incident detection finished")

# -----------------------------
# STEP 5: AI COMPONENTS
# -----------------------------
logger.info("STEP 5: Initializing AI Components")

logger.info("→ Loading Knowledge Base & Embeddings (RAG)")
rag = RAGEngine(os.path.join(BASE_DIR, "knowledge_base"))

logger.info("→ Initializing Diagnosis Agent (LLM-based)")
diagnosis_agent = DiagnosisAgent()

logger.info("→ Loading Local LLM (LLaMA3 via Ollama)")
llm = Ollama(model="llama3")

logger.info("→ Initializing Remediation Engine")
remediation_engine = RemediationEngine(llm)

# -----------------------------
# INCIDENT LOOP
# -----------------------------
incident_count = 0

for text, pred in zip(window_texts, predictions):

    if pred != 1:
        continue

    logger.info("\n===================================")
    logger.info(f"INCIDENT #{incident_count+1}")
    logger.info("===================================")

    logger.info("🔹 Incident Sample:")
    logger.info(text[:250] + "...")

    env = SystemEnvironment()

    logger.info("🔹 Retrieving Knowledge")
    docs = rag.retrieve(text, top_k=5)

    logger.info("🔹 Running Diagnosis")
    diagnosis = diagnosis_agent.diagnose(text, docs)

    logger.info("🧠 Diagnosis:")
    logger.info(json.dumps(diagnosis, indent=2))

    nodes = extract_nodes(text)
    services = extract_services(text)

    logger.info(f"🔍 Nodes: {nodes}")
    logger.info(f"🔍 Services: {services}")

    env.register_nodes(nodes)
    env.register_services(services)

    logger.info("⚙️ Running Remediation")
    result = remediation_engine.run(diagnosis, env, nodes)

    logger.info("⚙️ Action Taken:")
    logger.info(result["action"])

    logger.info("⚙️ Result:")
    logger.info(result["result"])

    metrics = evaluate_remediation(diagnosis, result)

    logger.info("📊 Metrics:")
    logger.info(metrics)

    incident_count += 1
    if incident_count == 3:
        break

logger.info("\n===================================")
logger.info("DEMO COMPLETE")
logger.info("===================================")