# Virtual Sorting Line — Industrial Digital Twin (IIoT Pipeline)

> 🇫🇮 **Suomenkielinen kuvaus ja käyttöohjeet löytyvät alempaa [tästä linkistä](#suomeksi).**

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

* **PLC Control Logic (\CODESYS V3.5.21.60\)**: Simulates an automated sorting line with a state machine (\system_state\), part counters (\	otal_count\, \sorted_a\, \sorted_b\), and OEE availability calculation (\oee_availability\).
* **Secure OPC UA Communication**: Uses X.509 client/server certificate authentication with \Basic256Sha256\ (\SignAndEncrypt\) security policy.
* **Edge Gateway (\edge-gateway/opcua_to_db.py\)**: Asynchronous Python service reading PLC symbol nodes and persisting metrics into PostgreSQL using environment variables (\.env\).
* **Containerized Data & Visualization Stack**: Docker Compose setup running PostgreSQL 15 and Grafana with live production charts, OEE gauge, and machine state indicators.

## Quick Start (English)

### 1. Configure Environment Variables
Copy \.env.example\ to \.env\ and set your local credentials:
\\\powershell
Copy-Item .env.example .env
\\\

### 2. Start Database & Grafana Containers
\\\powershell
docker compose up -d
\\\

### 3. Configure Python Environment & Certificates
\\\powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
pip install asyncua psycopg2-binary cryptography python-dotenv
\\\
Generate X.509 client certificates (\client_cert.der\, \client_key.pem\) in \edge-gateway/\, run the gateway once, and move the client certificate from **Quarantined Certificates** to **Trusted Certificates** in the CODESYS Security Screen.

### 4. Run the Edge Gateway & Simulation
\\\powershell
cd edge-gateway
python .\opcua_to_db.py
\\\
* Open Grafana at \http://localhost:3000\ and connect PostgreSQL (\Host: factory_postgres:5432\, \Database: factory_data\).
* Start the PLC simulation in CODESYS (\Online -> Login\, \Debug -> Start\).

---

<a name="suomeksi"></a>
# Virtuaalinen lajittelulinja — Teollinen digitaalinen kaksonen (IIoT)

Kokonaisvaltainen teollisen internetin (IIoT) ja digitaalisen kaksosen toteutus, joka yhdistää **CODESYS V3.5** -logiikan (PLC), **PostgreSQL**-tietokannan ja **Grafana**-analytiikkanäkymän salatun **OPC UA** -yhteyden ja Python-pohjaisen Edge Gatewayn avulla.

## Keskeiset ominaisuudet

* **PLC-ohjauslogiikka (\CODESYS V3.5.21.60\)**: Simuloi automaattista lajittelulinjaa tilakoneen (\system_state\), kappalelaskureiden (\	otal_count\, \sorted_a\, \sorted_b\) ja OEE-käytettävyyslaskennan (\oee_availability\) avulla.
* **Suojattu OPC UA -tietoliikenne**: Hyödyntää X.509-sertifikaatteja sekä \Basic256Sha256\ (\SignAndEncrypt\) -salausta asiakkaan ja palvelimen välillä.
* **Python Edge Gateway (\edge-gateway/opcua_to_db.py\)**: Asynkroninen Python-palvelu, joka lukee logiikan symbolimuuttujat kahden sekunnin välein ja tallentaa mittausdatan tietokantaan.
* **Kontitettu tietokanta ja visualisointi**: Docker Compose -ympäristö, jossa pyörivät PostgreSQL 15 ja Grafana reaaliaikaisilla tuotantokäyrillä, OEE-mittarilla sekä linjan tilakoodinäytöllä.

## Esivaatimukset

* Windows 10/11 ja **CODESYS Development System V3.5** (\CODESYS Control Win V3 x64\)
* **Docker Desktop**
* **Python 3.10+**

## Käyttöönotto (Suomeksi)

### 1. Määritä ympäristömuuttujat
Kopioi mallitiedosto \.env.example\ nimelle \.env\ ja aseta omat paikalliset salasanasi:
\\\powershell
Copy-Item .env.example .env
\\\

### 2. Käynnistä tietokanta- ja Grafana-kontit
\\\powershell
docker compose up -d
\\\

### 3. Asenna Python-riippuvuudet ja hyväksy sertifikaatti
\\\powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
pip install asyncua psycopg2-binary cryptography python-dotenv
\\\
Luo asiakassertifikaatit (\client_cert.der\, \client_key.pem\) \edge-gateway/\-kansioon, käynnistä skripti kerran ja siirrä sertifikaatti CODESYSin **Security Screen** -näkymässä kansiosta *Quarantined Certificates* kansioon *Trusted Certificates*.

### 4. Käynnistä tiedonkeruu ja simulaatio
\\\powershell
cd edge-gateway
python .\opcua_to_db.py
\\\
* Avaa Grafana selaimessa osoitteessa \http://localhost:3000\ ja lisää PostgreSQL-tietolähde (\Host: factory_postgres:5432\, \Database: factory_data\).
* Kirjaudu logiikalle CODESYSissa (\Online -> Login\) ja käynnistä ajo (\Debug -> Start\).
