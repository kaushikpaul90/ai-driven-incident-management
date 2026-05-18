"""Streamlit application for incident detection, diagnosis, and remediation."""

import json
import logging
import os
import re
import time

import pandas as pd
import streamlit as st
from azure.storage.blob import BlobServiceClient
from dotenv import load_dotenv
from opentelemetry import trace

from app import run_pipeline
from telemetry import setup_telemetry

load_dotenv()
setup_telemetry()
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

AZURE_STORAGE_CONNECTION_STRING = os.getenv("AZURE_STORAGE_CONNECTION_STRING")
BLOB_CONTAINER_NAME = "incidentlogs"
BLOB_FILE_NAME = "BGL.log"


def initialize_session_state():
    """Initialize UI session state values used across the app."""

    defaults = {
        "pipeline_results": None,
        "pipeline_completed": False,
        "logs": [],
        "execution_time": 0,
        "execution_logs": [],
        "active_step": "",
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value


def parse_bgl_lines(lines):
    """Parse lines from a BGL file into logs and labels."""

    logs = []
    labels = []
    for line in lines:
        parts = line.split()
        if len(parts) < 2:
            continue
        labels.append(0 if parts[0] == "-" else 1)
        logs.append(line.strip())
    return logs, labels


def parse_uploaded_file(uploaded_file):
    """Decode an uploaded file and parse its BGL lines."""

    raw = uploaded_file.getvalue().decode("utf-8", errors="ignore")
    return parse_bgl_lines(raw.splitlines())


def download_blob_logs(connection_string, container_name, blob_name):
    """Download a log blob from Azure and parse it into logs and labels."""

    tracer = trace.get_tracer(__name__)
    with tracer.start_as_current_span("azure_blob_download") as span:
        span.set_attribute("blob.container", container_name)
        span.set_attribute("blob.name", blob_name)

        blob_service_client = BlobServiceClient.from_connection_string(connection_string)
        blob_client = blob_service_client.get_blob_client(container=container_name, blob=blob_name)
        blob_data = blob_client.download_blob().readall()

        span.set_attribute("blob.size_bytes", len(blob_data))
        raw_text = blob_data.decode("utf-8", errors="ignore")
        logs, labels = parse_bgl_lines(raw_text.splitlines())
        span.set_attribute("parsed.total_logs", len(logs))
        return logs, labels


def get_active_step(message):
    """Return a UI-friendly active step label based on a log message."""

    mapping = {
        "Training ML model": "🤖 Training ML Model",
        "Running anomaly prediction": "🚨 Running Anomaly Detection",
        "Generating embeddings": "🧠 Generating Embeddings",
        "Running diagnosis": "🔍 Running LLM Diagnosis",
        "Executing remediation": "⚙️ Executing Remediation",
        "processing completed": "✅ Incident Processing Completed",
    }
    for key, label in mapping.items():
        if key in message:
            return label
    return st.session_state.active_step


def append_log(message, placeholder):
    """Append a log message to the session and render it in the UI."""

    if not message or message.strip() == "":
        return

    if re.fullmatch(r"=+", message.strip()):
        return

    st.session_state.active_step = get_active_step(message)
    st.session_state.execution_logs.append(message.strip())
    placeholder.text("\n".join(st.session_state.execution_logs))


def format_duration(seconds):
    """Format elapsed seconds into a human-readable duration string."""

    if seconds < 60:
        return f"{round(seconds, 2)} sec"
    if seconds < 3600:
        return f"{round(seconds / 60, 2)} min"
    return f"{round(seconds / 3600, 2)} hr"


initialize_session_state()

st.set_page_config(page_title="Agentic Incident AI", layout="wide")

st.title("🚨 Agentic Incident Detection & Auto-Remediation System")
st.markdown("Live AI-powered log analysis using ML + LLM + RAG")

max_incidents = st.sidebar.number_input("Max Incidents to Process", min_value=1, max_value=4747963, value=5, step=1)
log_source = st.sidebar.radio("Select Log Source", ["Azure Blob Storage", "Local Upload"])
uploaded_file = None

if log_source == "Local Upload":
    uploaded_file = st.sidebar.file_uploader("Upload Log File", type=["log", "txt"])

run_button = st.sidebar.button("▶️ Run Pipeline")
log_placeholder = st.empty()
progress_bar = st.progress(0)

st.subheader("⚙️ Pipeline Execution Status")
if st.session_state.pipeline_completed:
    st.success("✅ Pipeline execution completed successfully!")

step1_box = st.empty()
step2_box = st.empty()
step3_box = st.empty()
step4_box = st.empty()
long_task_box = st.empty()

if st.session_state.pipeline_completed:
    with st.expander("📜 View Backend Execution Logs", expanded=False):
        st.text("\n".join(st.session_state.execution_logs))
else:
    log_placeholder = st.empty()

if run_button:
    if log_source == "Local Upload" and uploaded_file is None:
        st.error("❌ Please upload a BGL.log file")
        st.stop()

    start_time = time.time()
    st.session_state.execution_logs = []

    step1_box.info("🔄 Step 1: Parsing Uploaded Log File...")
    try:
        if log_source == "Azure Blob Storage":
            logs, labels = download_blob_logs(AZURE_STORAGE_CONNECTION_STRING, BLOB_CONTAINER_NAME, BLOB_FILE_NAME)
        else:
            logs, labels = parse_uploaded_file(uploaded_file)
    except Exception as ex:
        logger.exception("Blob download failed: %s", ex)
        st.error("❌ Failed to load log file")
        st.stop()

    progress_bar.progress(15)
    step1_box.success(f"✅ Step 1 Completed | Parsed {len(logs)} log lines")

    if len(set(labels)) < 2:
        st.error("❌ Uploaded file must contain both normal and anomaly logs.")
        st.stop()

    step2_box.info("🔄 Step 2: Preparing Data Windows...")
    progress_bar.progress(35)
    step2_box.success("✅ Step 2 Completed | Log windows prepared successfully")

    step3_box.info("🔄 Step 3: Running Detection + Diagnosis + Remediation...")
    progress_bar.progress(50)

    with long_task_box.container():
        st.info("⏳ AI pipeline execution in progress...")
        with st.expander("⚙️ View Active Backend Tasks", expanded=False):
            st.markdown("""
                - Training ML models
                - Running anomaly detection
                - Initializing embeddings
                - Loading RAG pipeline
                - Running LLM diagnosis
                - Executing remediation engine
            """)

    progress_bar.progress(60)
    data = run_pipeline(logs=logs, labels=labels, max_incidents=max_incidents, logger_callback=lambda message: append_log(message, log_placeholder))
    execution_time = format_duration(time.time() - start_time)

    st.session_state.execution_time = execution_time
    st.session_state.pipeline_results = data
    st.session_state.pipeline_completed = True
    st.session_state.logs = logs

    progress_bar.progress(100)
    st.rerun()

if st.session_state.pipeline_completed:
    data = st.session_state.pipeline_results
    logs = st.session_state.logs
    long_task_box.empty()
    step1_box.empty()
    step2_box.empty()
    step3_box.empty()
    step4_box.empty()

    step4_box.info("🔄 Step 4: Finalizing Results...")
    progress_bar.progress(100)

    total_windows = data.get("total_windows", 0)
    correct_windows = data.get("correct_windows", 0)
    anomalous_windows = data.get("anomalous_windows", 0)
    incidents = data.get("incidents", []) if isinstance(data, dict) else data
    processed_count = len(incidents)
    total_detected = data.get("total_anomalies", processed_count) if isinstance(data, dict) else processed_count

    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Total Log Lines", len(logs))
        st.metric("Total Windows", total_windows)
    with col2:
        st.metric("Correct Windows", correct_windows)
        st.metric("Anomalous Windows", anomalous_windows)
    with col3:
        st.metric("Processed Incidents", processed_count)
        st.metric("Execution Time", st.session_state.execution_time)

    st.subheader("📈 AI Performance Visualization")
    performance_metrics = data.get("performance_metrics", [])
    if performance_metrics:
        perf_df = pd.DataFrame(performance_metrics)
        perf_df["incident_id"] = perf_df["incident_id"] + 1
        st.markdown("### ⚙️ AI Operational Telemetry")
        telemetry_metrics = ["diagnosis_time_sec", "remediation_time_sec", "confidence", "node_count"]
        for metric in telemetry_metrics:
            st.markdown(f"#### {metric}")
            chart_df = perf_df[["incident_id", metric]].copy().round(2).set_index("incident_id")
            max_value = chart_df[metric].max()
            if max_value > 100:
                chart_df[metric] = (chart_df[metric] / max_value) * 100
            st.bar_chart(chart_df)
    else:
        st.warning("No performance metrics available for visualization.")

    st.subheader("🚨 Incident Analysis")
    if incidents:
        with st.expander(f"View Detailed Incident Analysis ({len(incidents)} Incidents)", expanded=False):
            selected_incident_index = st.selectbox(
                "Select Incident",
                options=list(range(len(incidents))),
                format_func=lambda x: f"Incident {x+1}",
            )
            incident = incidents[selected_incident_index]
            if isinstance(incident, dict):
                st.markdown("### 📄 Log Sample")
                log_text = incident.get("log") or incident.get("pattern") or "N/A"
                st.code(log_text)
                col1, col2 = st.columns(2)
                with col1:
                    st.markdown("### 🧠 Diagnosis")
                    st.write(incident.get("diagnosis", "N/A"))
                    if "nodes" in incident:
                        st.markdown("### 🔍 Nodes")
                        st.write(incident.get("nodes"))
                    if "affected_components" in incident:
                        st.markdown("### 🔍 Affected Components")
                        st.write(incident.get("affected_components"))
                with col2:
                    st.markdown("### ⚙️ Action Taken")
                    st.success(str(incident.get("action", "N/A")))
                    if "result" in incident:
                        st.markdown("### ⚙️ Result")
                        st.json(incident.get("result"))
                    if "metrics" in incident:
                        st.markdown("### 📊 Metrics")
                        st.json(incident.get("metrics"))
            else:
                st.markdown("### 📄 Raw Incident Output")
                st.code(str(incident), language="text")
    else:
        st.warning("No incidents available.")

    st.subheader("⬇️ Download Results")
    st.download_button(label="Download Full Uploaded Logs", data="\n".join(logs), file_name="uploaded_logs.txt", mime="text/plain")
    st.download_button(label="Download Incident Results", data=json.dumps(data, indent=2), file_name="incident_results.json", mime="application/json")
