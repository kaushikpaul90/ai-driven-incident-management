````md
# Agentic Incident Detection & Auto-Remediation System

## Overview

This project is an AI-powered autonomous incident detection and remediation platform designed for large-scale distributed systems log analysis.

The system combines:

- Machine Learning-based anomaly detection
- Retrieval-Augmented Generation (RAG)
- Large Language Models (LLMs)
- Autonomous remediation simulation
- Azure cloud observability
- Real-time telemetry monitoring

The application processes large-scale production logs (Blue Gene/L dataset), identifies anomalies, performs AI-driven diagnosis, retrieves relevant operational knowledge, and executes simulated remediation actions.

---

# Key Features

- ML-based anomaly detection using TF-IDF + Logistic Regression
- Dynamic log parsing and anomaly classification
- RAG-powered operational context retrieval using FAISS
- LLM-based incident diagnosis using Ollama
- Autonomous remediation engine
- Real-time Streamlit dashboard
- Azure Blob Storage integration
- Azure Application Insights telemetry
- OpenTelemetry distributed tracing
- Incident visualization and downloadable results
- Local and Azure deployment support

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
├── run_app.sh
├── .env.example
├── .gitignore
├── README.md
├── requirements.txt
├── analyze_bgl_errors.py
└── discover_error_types.py
````

---

# Prerequisites

Install the following:

* Python 3.11+
* Git
* Ollama

---

# Install Ollama

Download:

[https://ollama.com](https://ollama.com)

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

# Create Environment File

Copy:

```bash
cp .env.example .env
```

Update `.env` with your configuration values.

---

# Example `.env`

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

## 1. Start Ollama

Before launching the application, ensure Ollama is running:

```bash
ollama serve
```

---

## 2. Grant Execute Permission

Run once:

```bash
chmod +x run_app.sh
```

---

## 3. Execute the Script

```bash
./run_app.sh
```

---

# run_app.sh Content

```bash
#!/bin/bash

echo "========================================="
echo "Clearing Streamlit cache..."
echo "========================================="

streamlit cache clear

echo ""
echo "========================================="
echo "Removing Streamlit session state..."
echo "========================================="

rm -rf ~/.streamlit

echo ""
echo "========================================="
echo "Starting Streamlit application..."
echo "========================================="

python -m streamlit run src/ui_app.py --server.maxUploadSize 1024
```

---

# Manual Alternative (Optional)

If preferred, the application can also be started manually:

## Clear Streamlit Cache

```bash
streamlit cache clear
```

---

## Remove Existing Streamlit Session State

### Mac/Linux

```bash
rm -rf ~/.streamlit
```

### Windows (PowerShell)

```powershell
Remove-Item -Recurse -Force $HOME\.streamlit
```

---

## Run Streamlit Application

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

# Additional Azure Configuration

## Azure AI Foundry Setup

This project supports Azure-hosted LLMs and embeddings through Azure AI Foundry / Azure OpenAI.

If using Azure instead of Ollama:

Update `.env`:

```env
LLM_PROVIDER=azure
EMBEDDING_PROVIDER=azure
```

---

## 1. Create Azure AI Foundry Resource

Azure Portal:

```text
Azure AI Foundry → Create
```

OR

```text
Azure OpenAI → Create
```

---

## 2. Deploy Models

Inside Azure AI Foundry:

Deploy:

* Chat model
* Embedding model

Recommended:

| Purpose         | Model                  |
| --------------- | ---------------------- |
| Chat Completion | GPT-4o-mini            |
| Embeddings      | text-embedding-3-small |

---

## 3. Collect Required Values

From Azure AI Foundry:

| Setting              | Example                             |
| -------------------- | ----------------------------------- |
| Endpoint             | https://<resource>.openai.azure.com |
| API Version          | 2025-01-01-preview                  |
| Deployment Name      | gpt-4o-mini                         |
| Embedding Deployment | text-embedding-3-small              |

---

# Azure Key Vault Setup

The application stores sensitive secrets inside Azure Key Vault.

---

## 1. Create Key Vault

Azure Portal:

```text
Key Vaults → Create
```

Example:

```text
kv-agentic-incident-ai
```

---

## 2. Add Secrets

Inside Key Vault:

```text
Secrets → Generate/Import
```

Add the following secrets:

| Secret Name                           | Description                    |
| ------------------------------------- | ------------------------------ |
| AZURE-OPENAI-ENDPOINT                 | Azure OpenAI endpoint          |
| AZURE-OPENAI-API-KEY                  | Azure OpenAI API key           |
| AZURE-OPENAI-DEPLOYMENT               | Chat model deployment          |
| AZURE-EMBEDDING-DEPLOYMENT            | Embedding deployment           |
| APPLICATIONINSIGHTS-CONNECTION-STRING | App Insights connection string |
| AZURE-STORAGE-CONNECTION-STRING       | Blob storage connection string |

---

# Managed Identity Configuration

The App Service uses Managed Identity to securely access Azure Key Vault without hardcoding credentials.

---

## 1. Enable Managed Identity

Azure Portal:

```text
App Service
→ Identity
→ System assigned
→ Status = On
→ Save
```

This creates a Managed Identity for the App Service.

---

# Grant Key Vault Access

The Managed Identity must be granted permission to read Key Vault secrets.

---

## OPTION 1 — Recommended (RBAC)

### 1. Open Key Vault

```text
Key Vault
→ Access control (IAM)
→ Add role assignment
```

---

### 2. Assign Role

Assign:

```text
Key Vault Secrets User
```

to:

```text
<your-app-service-name>
```

---

## OPTION 2 — Access Policies (Older Method)

### 1. Open Key Vault

```text
Key Vault
→ Access Policies
→ Create
```

---

### 2. Secret Permissions

Enable:

```text
Get
List
```

---

### 3. Select Principal

Choose:

```text
<your-app-service-managed-identity>
```

Save changes.

---

# Configure Azure Environment Variables

Azure Portal:

```text
App Service
→ Environment Variables
```

Add:

```text
LLM_PROVIDER=azure
EMBEDDING_PROVIDER=azure
AZURE_OPENAI_API_VERSION=2025-01-01-preview
AZURE_KEYVAULT_URL=https://kv-agentic-incident-ai.vault.azure.net/
```

---

# How Authentication Works

```text
App Service Managed Identity
        ↓
Azure Key Vault
        ↓
Secrets Retrieved Securely
        ↓
Azure OpenAI + Storage + App Insights
```

No credentials are hardcoded inside source code.

---

# Local Development with Azure Services

Install Azure CLI:

[https://learn.microsoft.com/en-us/cli/azure/install-azure-cli](https://learn.microsoft.com/en-us/cli/azure/install-azure-cli)

Login:

```bash
az login
```

The application will automatically use your Azure developer identity to access Key Vault.

---

# Recommended Production Architecture

```text
Streamlit App Service
        ↓
Managed Identity
        ↓
Azure Key Vault
        ↓
Azure OpenAI
Azure Blob Storage
Application Insights
```

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

[https://zenodo.org/records/8196385/files/BGL.zip?download=1](https://zenodo.org/records/8196385/files/BGL.zip?download=1)

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

# Recommended .gitignore Entries

```gitignore
.env
.venv/
__pycache__/
*.pyc
.streamlit/
models/*.pkl
```

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

```
```
