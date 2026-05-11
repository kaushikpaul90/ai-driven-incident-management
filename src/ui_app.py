import streamlit as st
import pandas as pd
import time
from datetime import datetime

from src.test_diagnosis_pipeline import run_pipeline

# ---------------------------------------------------
# PAGE CONFIG
# ---------------------------------------------------
st.set_page_config(
    page_title="Agentic Incident AI",
    layout="wide"
)

# ---------------------------------------------------
# HEADER
# ---------------------------------------------------
st.title("🚨 Agentic Incident Detection & Auto-Remediation System")
st.markdown("Live AI-powered log analysis using ML + LLM + RAG")

# ---------------------------------------------------
# SIDEBAR
# ---------------------------------------------------
st.sidebar.header("⚙️ Controls")

max_incidents = st.sidebar.slider(
    "Max Incidents to Process",
    min_value=1,
    max_value=20,
    value=5
)

uploaded_file = st.sidebar.file_uploader(
    "📂 Upload Log File (BGL.log)",
    type=["log", "txt"]
)

run_button = st.sidebar.button("▶️ Run Pipeline")

# ---------------------------------------------------
# PARSE BGL FILE
# ---------------------------------------------------
def parse_bgl(uploaded_file):

    logs = []
    labels = []

    lines = uploaded_file.getvalue().decode(
        "utf-8",
        errors="ignore"
    ).splitlines()

    for line in lines:

        parts = line.split()

        if len(parts) < 2:
            continue

        label_token = parts[0]

        if label_token == "-":
            labels.append(0)
        else:
            labels.append(1)

        logs.append(" ".join(parts[1:]))

    return logs, labels

# ---------------------------------------------------
# LIVE LOGGING HELPERS
# ---------------------------------------------------
execution_logs = []

def add_log(message):

    timestamp = datetime.now().strftime("%H:%M:%S")

    execution_logs.append(
        f"[{timestamp}] {message}"
    )

    log_placeholder.code(
        "\n".join(execution_logs),
        language="text"
    )

# ---------------------------------------------------
# PROGRESS
# ---------------------------------------------------
progress_bar = st.progress(0)

# ---------------------------------------------------
# PIPELINE STATUS
# ---------------------------------------------------
st.subheader("⚙️ Pipeline Execution Status")

step1_box = st.empty()
step2_box = st.empty()
step3_box = st.empty()
step4_box = st.empty()

# ---------------------------------------------------
# LIVE EXECUTION LOGS
# ---------------------------------------------------
st.subheader("🖥️ Live Backend Execution Logs")

log_placeholder = st.empty()

# ---------------------------------------------------
# RUN PIPELINE
# ---------------------------------------------------
if run_button:

    if uploaded_file is None:
        st.error("❌ Please upload a BGL.log file")
        st.stop()

    start_time = time.time()

    # =================================================
    # STEP 1
    # =================================================
    step1_box.info(
        "🔄 Step 1: Parsing Uploaded Log File..."
    )

    logs, labels = parse_bgl(uploaded_file)

    progress_bar.progress(15)

    step1_box.success(
        f"✅ Step 1 Completed | "
        f"Parsed {len(logs)} log lines"
    )

    # ---------------------------------------------------
    # VALIDATION
    # ---------------------------------------------------
    if len(set(labels)) < 2:

        st.error(
            "❌ Uploaded file must contain both "
            "normal and anomaly logs."
        )

        st.stop()

    # =================================================
    # STEP 2
    # =================================================
    step2_box.info(
        "🔄 Step 2: Preparing Data Windows..."
    )

    progress_bar.progress(35)

    step2_box.success(
        "✅ Step 2 Completed | "
        "Log windows prepared successfully"
    )

    # =================================================
    # STEP 3
    # =================================================
    step3_box.info(
        "🔄 Step 3: Running Detection + "
        "Diagnosis + Remediation..."
    )

    progress_bar.progress(50)

    # ---------------------------------------------------
    # LONG RUNNING TASK MESSAGE
    # ---------------------------------------------------
    long_task_box = st.empty()

    long_task_box.warning(
        "⏳ AI pipeline execution in progress.\n\n"
        "The backend is currently:\n"
        "- Training ML models\n"
        "- Running anomaly detection\n"
        "- Initializing embeddings\n"
        "- Loading RAG pipeline\n"
        "- Running LLM diagnosis\n"
        "- Executing remediation engine\n\n"
        "Please monitor the live backend logs below."
    )

    progress_bar.progress(60)

    # ---------------------------------------------------
    # EXECUTE PIPELINE
    # ---------------------------------------------------
    data = run_pipeline(
        logs=logs,
        labels=labels,
        max_incidents=max_incidents,
        logger_callback=add_log
    )

    progress_bar.progress(85)

    long_task_box.success(
        "✅ AI processing completed successfully"
    )

    step3_box.success(
        "✅ Step 3 Completed | "
        "Detection + Diagnosis + Remediation finished"
    )

    # =================================================
    # STEP 4
    # =================================================
    step4_box.info(
        "🔄 Step 4: Finalizing Results..."
    )

    progress_bar.progress(100)

    end_time = time.time()

    execution_time = round(
        end_time - start_time,
        2
    )

    step4_box.success(
        f"✅ Step 4 Completed | "
        f"Execution finished in "
        f"{execution_time} sec"
    )

    # ---------------------------------------------------
    # SUCCESS MESSAGE
    # ---------------------------------------------------
    st.success(
        "🎉 Pipeline execution completed successfully!"
    )

    # ---------------------------------------------------
    # INCIDENT EXTRACTION
    # ---------------------------------------------------
    incidents = []

    if isinstance(data, dict):
        incidents = data.get("incidents", [])

    elif isinstance(data, list):
        incidents = data

    processed_count = len(incidents)

    if isinstance(data, dict):

        total_detected = data.get(
            "total_anomalies",
            processed_count
        )

    else:
        total_detected = processed_count

    # ---------------------------------------------------
    # SYSTEM METRICS
    # ---------------------------------------------------
    st.subheader("📊 System Metrics")

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric(
            "Total Log Lines",
            len(logs)
        )

    with col2:
        st.metric(
            "Detected Incidents",
            total_detected
        )

    with col3:
        st.metric(
            "Processed Incidents",
            processed_count
        )

    with col4:
        st.metric(
            "Execution Time",
            f"{execution_time} sec"
        )

    # ---------------------------------------------------
    # PERFORMANCE CHART
    # ---------------------------------------------------
    chart_data = []

    for idx, incident in enumerate(incidents):

        if isinstance(incident, dict):

            metrics = incident.get(
                "metrics",
                {}
            )

            chart_data.append({
                "incident_id": idx + 1,
                "action_correctness": metrics.get(
                    "action_correctness", 0
                ),
                "resolution_success": metrics.get(
                    "resolution_success", 0
                ),
                "reasoning_quality": metrics.get(
                    "reasoning_quality", 0
                )
            })

    if len(chart_data) > 0:

        st.subheader(
            "📈 Performance Visualization"
        )

        df = pd.DataFrame(chart_data)

        st.line_chart(
            df.set_index("incident_id")
        )

    # ---------------------------------------------------
    # INCIDENT DETAILS
    # ---------------------------------------------------
    st.subheader("🚨 Incident Analysis")

    for i, incident in enumerate(incidents):

        with st.expander(f"Incident {i+1}"):

            if isinstance(incident, dict):

                st.markdown("### 📄 Log Sample")

                log_text = (
                    incident.get("log")
                    or incident.get("pattern")
                    or "N/A"
                )

                st.code(log_text)

                col1, col2 = st.columns(2)

                with col1:

                    st.markdown("### 🧠 Diagnosis")

                    st.write(
                        incident.get(
                            "diagnosis",
                            "N/A"
                        )
                    )

                    if "nodes" in incident:

                        st.markdown("### 🔍 Nodes")

                        st.write(
                            incident.get("nodes")
                        )

                    if "services" in incident:

                        st.markdown("### 🔍 Services")

                        st.write(
                            incident.get("services")
                        )

                with col2:

                    st.markdown(
                        "### ⚙️ Action Taken"
                    )

                    st.success(
                        str(
                            incident.get(
                                "action",
                                "N/A"
                            )
                        )
                    )

                    if "result" in incident:

                        st.markdown(
                            "### ⚙️ Result"
                        )

                        st.json(
                            incident.get("result")
                        )

                    if "metrics" in incident:

                        st.markdown(
                            "### 📊 Metrics"
                        )

                        st.json(
                            incident.get("metrics")
                        )

            else:

                st.markdown(
                    "### 📄 Raw Incident Output"
                )

                st.code(
                    str(incident),
                    language="text"
                )

    # ---------------------------------------------------
    # RAW LOGS PREVIEW
    # ---------------------------------------------------
    with st.expander(
        "📜 View Raw Logs (First 200 Lines)"
    ):

        preview_logs = logs[:200]

        st.code(
            "\n".join(preview_logs),
            language="text"
        )

        st.info(
            f"Showing 200 out of "
            f"{len(logs)} total log lines"
        )

    # ---------------------------------------------------
    # DOWNLOADS
    # ---------------------------------------------------
    st.subheader("⬇️ Download Results")

    st.download_button(
        label="Download Full Uploaded Logs",
        data="\n".join(logs),
        file_name="uploaded_logs.txt",
        mime="text/plain"
    )

    st.download_button(
        label="Download Incident Results",
        data=str(data),
        file_name="incident_results.json",
        mime="application/json"
    )