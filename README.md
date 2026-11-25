# Virtual Sorting Line — Industrial Digital Twin (IIoT Pipeline)

End-to-end Industrial IoT (IIoT) and Digital Twin proof-of-concept connecting a **CODESYS V3.5** virtual PLC to a **PostgreSQL** time-series database and **Grafana** real-time analytics dashboard via an encrypted **OPC UA** Python Edge Gateway.

## Architecture

\\\
[CODESYS Control Win V3 x64]
        │  OPC UA (Basic256Sha256 / SignAndEncrypt)
        ▼
[Python Edge Gateway (asyncua + psycopg2)]
        │  SQL Inserts (2s polling interval)
        ▼
[PostgreSQL 15 (Docker: factory_postgres)]
        │  SQL Queries
        ▼
[Grafana Dashboard (Docker: factory_grafana)]
\\\

## Key Features

* **PLC Control Logic (CODESYS V3.5.21.60)**: Simulates an automated sorting line with state machine (system_state), part counters (	otal_count, sorted_a, sorted_b), and OEE availability calculation (oee_availability).
* **Secure OPC UA Communication**: Uses X.509 client/server certificate authentication with Basic256Sha256 (SignAndEncrypt) security policy.
* **Edge Gateway (edge-gateway/opcua_to_db.py)**: Asynchronous Python service reading PLC symbol nodes and persisting metrics into PostgreSQL.
* **Containerized Data & Visualization Stack**: Docker Compose setup running PostgreSQL 15 and Grafana with live production charts, OEE gauge, and machine state indicators.

## Prerequisites

* Windows 10/11 with **CODESYS Development System V3.5** (CODESYS Control Win V3 x64)
* **Docker Desktop**
* **Python 3.10+**

## Quick Start

### 1. Start Database & Grafana Containers
\\\powershell
docker compose up -d
\\\

### 2. Configure Python Environment & Certificates
\\\powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
pip install asyncua psycopg2-binary cryptography
\\\
Generate client certificates (client_cert.der, client_key.pem) in edge-gateway/, run the gateway once, and move the client certificate from **Quarantined Certificates** to **Trusted Certificates** in the CODESYS Security Screen.

### 3. Run the Edge Gateway
\\\powershell
cd edge-gateway
python .\opcua_to_db.py
\\\

### 4. View Live Dashboard
* Open Grafana at \http://localhost:3000\
* Configure PostgreSQL data source (\Host: factory_postgres:5432\, \Database: factory_data\, \User: admin\)
* Start the PLC simulation in CODESYS (\Online -> Login\, \Debug -> Start\)
