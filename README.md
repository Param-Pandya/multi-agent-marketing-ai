# 📌 Marketing Multi-Agent System with Adaptive Memory (Prototype)

This repository contains the implementation of a **Multi-Agent Marketing System** designed for the AIML Assessment (October 2025). The system demonstrates how multiple intelligent agents can collaborate to automate **lead triage, customer engagement, and campaign optimization**, while leveraging an **adaptive four-layer memory model**.

---

## 🚀 Features
- **Three Specialized Agents**
  - 🧾 **Lead Triage Agent** – classifies leads into *Cold, General Inquiry, Campaign Qualified*.  
  - ✉️ **Engagement Agent** – prepares and sends personalized outreach messages.  
  - 📊 **Campaign Optimization Agent** – analyzes campaign performance and recommends best campaigns.  

- **Adaptive Memory Layers**
  - **Short-Term Memory (STM)** – recent interaction context.  
  - **Long-Term Memory (LTM)** – persistent lead history & classifications.  
  - **Episodic Memory** – chronological event logs.  
  - **Semantic Memory** – knowledge graph for personalization.  

- **MCP Server (FastAPI)**
  - REST endpoints (`/tables`, `/query`) for dataset access.  
  - WebSocket endpoint (`/ws`) for JSON-RPC inter-agent communication.  

- **End-to-End Demo**
  - Loads dataset (CSV files).  
  - Runs classification, outreach, and optimization for sample leads.  
  - Stores logs in `run_log.json`.  

---

## 📂 Repository Structure  <br />
├── agents.py <br />
├── mcp_local.py <br />
├── mcp_server.py  <br />
├── demo_runner.py <br />
├── requirements.txt <br />
├── run_log.json  <br />
├── data/  <br />
└── README.md <br />


---

## ⚙️ Installation
1. Clone this repository:
   ```bash
   git clone https://github.com/your-username/marketing-agents.git
   cd marketing-agents

2. Install dependencies:
    pip install -r requirements.txt

Usage
1. Run Local Prototype

Runs all agents in a single process with in-memory MCP.

python demo_runner.py


Logs saved in run_log.json.

2. Run MCP Server

Start the server to expose datasets and JSON-RPC relay.

# For Windows
$env:MM_DATA_DIR="./data"
python mcp_server.py

# For Linux or Mac
export MM_DATA_DIR=./data
python mcp_server.py


Access API docs at: http://127.0.0.1:8000/docs
