# Agentic Incident Detection & Auto-Remediation System

## Overview

This project is an AI-powered autonomous incident detection and remediation platform designed for large-scale distributed systems log analysis.

The system combines:

* Machine Learning-based anomaly detection
* Retrieval-Augmented Generation (RAG)
* Large Language Models (LLMs)
* Autonomous remediation simulation
* Azure cloud observability
* Real-time telemetry monitoring

The application processes large-scale production logs (Blue Gene/L dataset), identifies anomalies, performs AI-driven diagnosis, retrieves relevant operational knowledge, and executes simulated remediation actions.

---

# Key Features

* ML-based anomaly detection using TF-IDF + Logistic Regression
* Dynamic log parsing and anomaly classification
* RAG-powered operational context retrieval using FAISS
* LLM-based incident diagnosis using Ollama
* Autonomous remediation engine
* Real-time Streamlit dashboard
* Azure Blob Storage integration
* Azure Application Insights telemetry
* OpenTelemetry distributed tracing
* Incident visualization and downloadable results
* Local and Azure deployment support

---

# Technology Stack

| Category      | Technology                 |
| ------------- | -------------------------- |
| Frontend      | Streamlit                  |
| ML            | Scikit-learn               |
| Vector DB     | FAISS                      |
| Embeddings    | Sentence Transformers      |
| LLM Runtime   | Ollama                     |
| RAG Framework | LangChain                  |
| Observability | Azure Application Insights |
| Telemetry     | OpenTelemetry              |
| Cloud Storage | Azure Blob Storage         |
| Language      | Python                     |

---

# Project Structure

```text
ai-driven-incident-management/
│
├── .github/
│   └── workflows/
│       └── master_agentic-incident-ai.yml
│
├── .streamlit/
│   └── config.toml
│
├── .vscode/
│
├── knowledge_base/
│   ├── external_docs/
│   └── runbooks/
│
├── models/
│   └── incident_detector.pkl
│
├── sample_logs/
├── sample_prompts/
│
├── src/
│   ├── ui_app.py
│   ├── app.py
│   ├── detection.py
│   ├── diagnosis.py
│   ├── remediation_engine.py
│   ├── retrieval.py
│   ├── telemetry.py
│   ├── environment.py
│   ├── evaluation.py
│   └── ...
│
├── README.md
├── requirements.txt
├── analyze_bgl_errors.py
└── discover_error_types.py
```

---

# Prerequisites

Install the following:

* Python 3.11+
* Git
* Ollama

---

# Install Ollama

Download:

[Ollama Official Website](https://ollama.com?utm_source=chatgpt.com)

Install required model:

```bash
ollama pull llama3
```

Verify installation:

```bash
ollama list
```

---

# Clone Repository

```bash
git clone https://github.com/kaushikpaul90/ai-driven-incident-management.git
cd ai-driven-incident-management
```

---

# Create Virtual Environment

## Windows

```bash
python -m venv .venv
.venv\Scripts\activate
```

## Mac/Linux

```bash
python3 -m venv .venv
source .venv/bin/activate
```

---

# Install Dependencies

```bash
pip install -r requirements.txt
```

---

# Requirements.txt

```txt
pandas
numpy
scikit-learn
tqdm
sentence-transformers
faiss-cpu
ollama
langchain
langchain-community
langchain_core
langchain-openai
streamlit
torch
torchvision
watchdog
azure-identity
azure-keyvault-secrets
azure-storage-blob
python-dotenv
openai
joblib
azure-monitor-opentelemetry==1.6.4
opentelemetry-api==1.30.0
opentelemetry-sdk==1.30.0
opentelemetry-semantic-conventions==0.51b0
plotly
```

---

# Environment Variables

Create a `.env` file in the project root.

## Example `.env`

```env
LLM_PROVIDER=ollama
# LLM_PROVIDER=azure

OLLAMA_MODEL=llama3

EMBEDDING_PROVIDER=local
# EMBEDDING_PROVIDER=azure

AZURE_OPENAI_API_VERSION=2025-01-01-preview

AZURE_KEYVAULT_URL=https://kv-agentic-incident-ai.vault.azure.net/

APPLICATIONINSIGHTS_CONNECTION_STRING=<your-application-insights-connection-string>

AZURE_STORAGE_CONNECTION_STRING=<your-storage-connection-string>
```

---

# Running the Application Locally

## 1. Clear Streamlit Cache

```bash
streamlit cache clear
```

---

## 2. Remove Existing Streamlit Session State

### Mac/Linux

```bash
rm -rf ~/.streamlit
```

### Windows (PowerShell)

```powershell
Remove-Item -Recurse -Force $HOME\.streamlit
```

---

## 3. Start Ollama

```bash
ollama serve
```

---

## 4. Run Streamlit Application

```bash
python -m streamlit run src/ui_app.py --server.maxUploadSize 1024
```

---

# Application Features

The UI supports two log sources:

| Source             | Description                           |
| ------------------ | ------------------------------------- |
| Local Upload       | Upload log file from local machine    |
| Azure Blob Storage | Read logs directly from Azure Storage |

---

# Azure Blob Storage Setup

## 1. Create Storage Account

Azure Portal:

```text
Storage Accounts → Create
```

Recommended:

* Standard
* Locally Redundant Storage (LRS)

---

## 2. Create Blob Container

Container name:

```text
incidentlogs
```

---

## 3. Upload Dataset

Upload:

```text
BGL.log
```

---

# Azure Application Insights Setup

## 1. Create Application Insights Resource

Azure Portal:

```text
Application Insights → Create
```

---

## 2. Copy Connection String

```text
Overview → Connection String
```

Add it inside `.env`.

---

# Azure App Service Deployment

## 1. Create Azure App Service

Recommended configuration:

| Setting      | Value             |
| ------------ | ----------------- |
| OS           | Linux             |
| Runtime      | Python 3.11       |
| Pricing Tier | Basic B1 or above |

---

## 2. Configure Environment Variables

Azure Portal:

```text
App Service
→ Environment Variables
```

Add:

```text
APPLICATIONINSIGHTS_CONNECTION_STRING
AZURE_STORAGE_CONNECTION_STRING
OLLAMA_MODEL
LLM_PROVIDER
EMBEDDING_PROVIDER
AZURE_KEYVAULT_URL
```

---

## 3. Configure Startup Command

Azure Portal:

```text
App Service
→ Configuration
→ General Settings
→ Startup Command
```

Use:

```bash
python -m streamlit run src/ui_app.py --server.port 8000 --server.address 0.0.0.0
```

---

## 4. Deploy Code

Deployment options:

* GitHub Actions
* VS Code Azure Extension
* Zip Deployment

---

# Azure Telemetry & Observability

The project uses:

* OpenTelemetry
* Azure Monitor
* Application Insights

Telemetry includes:

* Blob storage tracing
* RAG retrieval operations
* LLM diagnosis tracing
* Remediation execution tracing
* End-to-end pipeline monitoring

---

# Viewing Application Insights Logs

Azure Portal:

```text
Application Insights → Logs
```

Query:

```kusto
traces
| order by timestamp desc
```

---

# Viewing Azure Blob Telemetry

```kusto
dependencies
| where name contains "azure_blob_download"
| order by timestamp desc
```

---

# ML Model Persistence

The anomaly detection model is trained once and stored using `joblib`.

Saved model:

```text
models/incident_detector.pkl
```

Subsequent runs load the persisted model automatically.

---

# Supported Remediation Actions

* restart_service
* restart_node
* isolate_node

---

# Dataset

This project uses the:

## Blue Gene/L (BGL) Supercomputer Log Dataset

Contains:

* ~4.7 million log entries
* real-world HPC failure logs
* anomaly labels

---

# Dataset Download

The Blue Gene/L dataset can be downloaded from:

[BGL Dataset (Zenodo)](https://zenodo.org/records/8196385/files/BGL.zip?download=1&utm_source=chatgpt.com)

After downloading:

1. Extract the ZIP file
2. Locate:

```text
BGL.log
```

3. Upload the file:

   * through the Streamlit UI
   * OR to Azure Blob Storage container:

```text
incidentlogs
```

> Note:
> The BGL.log dataset is approximately 700MB in size.
> For cloud deployments, Azure Blob Storage is strongly recommended instead of browser upload.

---

# Troubleshooting

## Ollama Connection Error

Ensure:

```bash
ollama serve
```

is running before launching the application.

---

## Azure Blob Download Failure

Verify:

* Storage connection string
* Blob container name
* Blob file name
* App Service environment variables

---

## Application Insights Logs Not Visible

Verify:

* Application Insights connection string
* OpenTelemetry configuration
* App Service restart after deployment

---

# Future Enhancements

* Real infrastructure remediation
* Kubernetes integration
* Multi-agent orchestration
* Real-time streaming ingestion
* Automated rollback strategies
* Root cause correlation engine

---

# Author

Kaushik Paul

M.Tech (Cloud Computing)
BITS Pilani Work Integrated Learning Programme

---

# License

This project is intended for academic and research purposes only.
