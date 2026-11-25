import asyncio
import os
from dotenv import load_dotenv
load_dotenv()
import time

import psycopg2
from asyncua import Client

OPCUA_URL = "opc.tcp://127.0.0.1:4840"
DEVICE_NAME = "CODESYS Control Win V3 x64"
PREFIX = f"ns=4;s=|var|{DEVICE_NAME}.Application.PLC_PRG"

DB_CONFIG = {
    "host": "localhost",
    "port": 5432,
    "dbname": os.getenv("DB_NAME", "factory data"),
    "user": os.getenv("DB_USER", "admin"),
    "password": os.getenv("DB_PASSWORD", ""),
}

def init_db():
    conn = psycopg2.connect(**DB_CONFIG)
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS production_metrics (
            id SERIAL PRIMARY KEY,
            timestamp TIMESTAMPTZ DEFAULT NOW(),
            system_state INTEGER,
            total_count INTEGER,
            sorted_a INTEGER,
            sorted_b INTEGER,
            oee_availability REAL
        );
    """)
    conn.commit()
    return conn, cur

async def main():
    conn, cur = init_db()
    start_time = time.time()
    running_time = 0.0
    last_check = start_time

    print(f"Yhdistetään OPC UA -palvelimeen: {OPCUA_URL} ({DEVICE_NAME})...")
    client = Client(url=OPCUA_URL)
    client.set_user(os.getenv("DB_USER", "admin"))
    client.set_password(os.getenv("DB_PASSWORD", ""))
    client = Client(url=OPCUA_URL)
    client.application_uri = "urn:python:edgegateway"
    await client.set_security_string("Basic256Sha256,SignAndEncrypt,client_cert.der,client_key.pem")
    async with client:

        node_state = client.get_node(f"{PREFIX}.nSystemState")
        node_total = client.get_node(f"{PREFIX}.nTotalCount")
        node_a = client.get_node(f"{PREFIX}.nSortedACount")
        node_b = client.get_node(f"{PREFIX}.nSortedBCount")

        print("Yhteys muodostettu! KerÃ¤tÃ¤Ã¤n dataa tietokantaan...")
        while True:
            now = time.time()
            dt = now - last_check
            last_check = now

            state = await node_state.read_value()
            total = await node_total.read_value()
            count_a = await node_a.read_value()
            count_b = await node_b.read_value()

            if state == 10:  # 10 = Running
                running_time += dt

            total_elapsed = max(now - start_time, 0.001)
            availability = round((running_time / total_elapsed) * 100.0, 1)

            cur.execute(
                """
                INSERT INTO production_metrics
                (system_state, total_count, sorted_a, sorted_b, oee_availability)
                VALUES (%s, %s, %s, %s, %s)
                """,
                (state, total, count_a, count_b, availability),
            )
            conn.commit()

            print(f"[Tila: {state}] YhteensÃ¤: {total} (A: {count_a}, B: {count_b}) | KÃ¤ytettÃ¤vyys: {availability}%")
            await asyncio.sleep(2)

if __name__ == "__main__":
    asyncio.run(main())

