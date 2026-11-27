import os
from datetime import UTC, datetime
from pathlib import Path

import psycopg2
from asyncua import Client, ua
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

ROOT_DIR = Path(__file__).resolve().parents[1]
load_dotenv(ROOT_DIR / ".env", override=False)
load_dotenv(ROOT_DIR / "edge-gateway" / ".env", override=False)

app = FastAPI(title="Virtual Sorting Line Web-SCADA")
app.mount("/static", StaticFiles(directory=Path(__file__).parent / "static"), name="static")

OPCUA_URL = os.getenv("OPCUA_URL", "opc.tcp://127.0.0.1:4840")
PLC_PREFIX = os.getenv("PLC_NODE_PREFIX", "ns=4;s=|var|CODESYS Control Win V3 x64.Application.PLC_PRG")
CERT_PATH = ROOT_DIR / "client_cert.der"
KEY_PATH = ROOT_DIR / "client_key.pem"

STATE_LABELS = {0: "IDLE", 10: "RUN", 20: "WARNING", 99: "FAULT"}


def get_db_conn():
    return psycopg2.connect(
        host=os.getenv("DB_HOST", "localhost"),
        port=int(os.getenv("DB_PORT", "5432")),
        dbname=os.getenv("DB_NAME", "factory_data"),
        user=os.getenv("DB_USER", "admin"),
        password=os.getenv("DB_PASSWORD", ""),
    )


def init_alarms_table():
    with get_db_conn() as conn, conn.cursor() as cur:
        cur.execute("""
            CREATE TABLE IF NOT EXISTS scada_alarms (
                id SERIAL PRIMARY KEY,
                created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
                alarm_code VARCHAR(32) NOT NULL,
                message TEXT NOT NULL,
                active BOOLEAN NOT NULL DEFAULT TRUE,
                acknowledged_by VARCHAR(64),
                acknowledged_at TIMESTAMPTZ
            );
        """)
        conn.commit()


class CommandRequest(BaseModel):
    command: str


class AckRequest(BaseModel):
    operator: str = "Operator_1"


async def write_plc_command(tag_name: str, value: bool = True):
    client = Client(url=OPCUA_URL)
    client.application_uri = "urn:python:edgegateway"
    await client.set_security_string(f"Basic256Sha256,SignAndEncrypt,{CERT_PATH},{KEY_PATH}")
    async with client:
        node = client.get_node(f"{PLC_PREFIX}.{tag_name}")
        await node.write_value(ua.DataValue(ua.Variant(value, ua.VariantType.Boolean)))


@app.on_event("startup")
def on_startup():
    try:
        init_alarms_table()
    except psycopg2.Error as exc:
        print(f"Warning: could not initialize alarms table on startup: {exc}")


@app.get("/")
def serve_hmi():
    return FileResponse(Path(__file__).parent / "static" / "index.html")


@app.get("/api/status")
def get_status():
    with get_db_conn() as conn, conn.cursor() as cur:
        cur.execute("""
            SELECT timestamp, system_state, total_count, sorted_a, sorted_b, oee_availability
            FROM production_metrics
            ORDER BY id DESC
            LIMIT 1;
        """)
        row = cur.fetchone()

        if not row:
            return {"connected": False, "state": 0, "state_label": "NO DATA"}

        ts, state, total, a, b, oee = row

        if state == 99:
            cur.execute("SELECT id FROM scada_alarms WHERE active = TRUE LIMIT 1;")
            if not cur.fetchone():
                cur.execute(
                    "INSERT INTO scada_alarms (alarm_code, message) VALUES (%s, %s);",
                    ("ALM-99", "Conveyor jam or emergency stop active (PLC State 99)"),
                )
                conn.commit()

        cur.execute("""
            SELECT id, created_at, alarm_code, message, active, acknowledged_by, acknowledged_at
            FROM scada_alarms
            ORDER BY id DESC
            LIMIT 10;
        """)
        alarms = [
            {
                "id": r[0],
                "created_at": r[1].isoformat(),
                "alarm_code": r[2],
                "message": r[3],
                "active": r[4],
                "acknowledged_by": r[5],
                "acknowledged_at": r[6].isoformat() if r[6] else None,
            }
            for r in cur.fetchall()
        ]

    return {
        "connected": True,
        "timestamp": ts.isoformat(),
        "state": state,
        "state_label": STATE_LABELS.get(state, "UNKNOWN"),
        "total_count": total,
        "sorted_a": a,
        "sorted_b": b,
        "oee_availability": float(oee),
        "alarms": alarms,
    }


@app.post("/api/command")
async def send_command(req: CommandRequest):
    tag_map = {
        "START": "bCmdStart",
        "STOP": "bCmdStop",
        "RESET": "bCmdReset",
        "FAULT_TEST": "bSimFault",
    }
    cmd = req.command.upper()
    if cmd not in tag_map:
        raise HTTPException(status_code=400, detail=f"Unsupported command: {cmd}")

    try:
        await write_plc_command(tag_map[cmd], True)
    except psycopg2.Error as exc:
        raise HTTPException(status_code=502, detail=f"OPC UA write failed: {exc}") from exc

    return {"status": "sent", "command": cmd, "tag": tag_map[cmd]}


@app.post("/api/alarms/{alarm_id}/ack")
def acknowledge_alarm(alarm_id: int, req: AckRequest):
    with get_db_conn() as conn, conn.cursor() as cur:
        cur.execute(
            """
            UPDATE scada_alarms
            SET active = FALSE, acknowledged_by = %s, acknowledged_at = %s
            WHERE id = %s;
            """,
            (req.operator, datetime.now(UTC), alarm_id),
        )
        conn.commit()
    return {"status": "acknowledged", "alarm_id": alarm_id, "operator": req.operator}