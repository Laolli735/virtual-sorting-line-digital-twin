# Virtual Sorting Line — Industrial IIoT & Digital Twin Pipeline

An end-to-end Industrial Internet of Things (IIoT) and Digital Twin portfolio project demonstrating secure PLC-to-Cloud telemetry, real-time OEE calculation, and bidirectional Web-SCADA operator control.

## System Architecture

```text
+-----------------------+       OPC UA (Basic256Sha256)       +------------------------+
|  CODESYS Control Win  | <=================================> |   Python Edge Gateway  |
|  (IEC 61131-3 ST PLC) |      SignAndEncrypt + X.509v3       |   (opcua_to_db.py)     |
+-----------------------+                                     +------------------------+
            ^                                                              |
            | OPC UA Write                                                 | SQL Insert
            | (Start/Stop/Reset/Fault)                                     v
+-----------------------+       REST API / Alarm Ack          +------------------------+
|   Web-SCADA / HMI     | <---------------------------------> |  PostgreSQL Database   |
| (FastAPI + HTML5/JS)  |                                     | (Metrics & Alarms DB)  |
+-----------------------+                                     +------------------------+
                                                                           |
                                                                           v
                                                              +------------------------+
                                                              |   Grafana Dashboard    |
                                                              | (Real-time OEE & KPIs) |
                                                              +------------------------+
Key Features & Engineering Highlights
IEC 61131-3 PLC Control Logic (plc-logic/): Structured Text (ST) state machine (IDLE, RUN, FAULT) for an automated optical sorting conveyor with emergency stop interlocks, height-based pneumatic pusher timing, and branch counters.

Zero-Trust OPC UA Security: Encrypted and signed communication (Basic256Sha256 / SignAndEncrypt) between CODESYS Control Win V3 and Python clients using custom X.509v3 certificates (urn:python:edgegateway) and explicit certificate trust management.

Python Edge Gateway (edge-gateway/): Asynchronous asyncua telemetry collector that samples PLC tags, computes real-time OEE Availability, reconciles production counts, and persists time-series records into PostgreSQL.

Bidirectional Web-SCADA / HMI (web-scada/): FastAPI backend and browser-based operator panel supporting live KPI monitoring, remote PLC commands (START, STOP, RESET, FAULT_TEST), and persistent alarm acknowledgement workflows.

Containerized Data & Visualization Stack: Docker Compose setup running PostgreSQL and Grafana for historical trend analysis.

Automated CI/CD Quality Gate (.github/workflows/): Every push and pull request is validated via GitHub Actions using ruff (linting/formatting) and pytest (unit and API endpoint testing).

Project Structure
Plaintext
├── .github/workflows/   # GitHub Actions CI pipeline (Ruff + Pytest)
├── edge-gateway/        # OPC UA telemetry collector, metrics processor & Docker Compose
├── plc-logic/           # CODESYS Structured Text (ST) source code
├── tests/               # Automated unit and FastAPI integration tests
├── web-scada/           # FastAPI Web-SCADA server and HTML5/JS HMI frontend
└── requirements.txt     # Python dependencies
Quick Start
1. Start Database & Grafana Containers
Bash
docker compose -f edge-gateway/docker-compose.yml up -d
2. Run PLC & Edge Gateway Collector
Open the PLC project in CODESYS Development System, log in to CODESYS Control Win V3, and set the program to RUN.

Start the telemetry bridge:

Bash
python edge-gateway/opcua_to_db.py
3. Launch Web-SCADA Operator HMI
Bash
uvicorn web-scada.app:app --reload --port 8000
Open http://localhost:8000 in your browser to control the sorting line and manage alarms.

Running Quality Checks Locally
Bash
ruff check .
pytest -v