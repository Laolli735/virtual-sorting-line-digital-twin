import importlib.util
from pathlib import Path
from unittest.mock import AsyncMock, patch

from fastapi.testclient import TestClient

spec = importlib.util.spec_from_file_location(
    "scada_app", Path(__file__).resolve().parents[1] / "web-scada" / "app.py"
)
scada_app = importlib.util.module_from_spec(spec)
spec.loader.exec_module(scada_app)

client = TestClient(scada_app.app)


def test_serve_hmi_html():
    res = client.get("/")
    assert res.status_code == 200
    assert "OPERATOR SCADA / HMI" in res.text


def test_reject_invalid_command():
    res = client.post("/api/command", json={"command": "INVALID_CMD"})
    assert res.status_code == 400


def test_send_valid_start_command():
    with patch.object(scada_app, "write_plc_command", new_callable=AsyncMock) as mock_write:
        res = client.post("/api/command", json={"command": "START"})
        assert res.status_code == 200
        assert res.json()["tag"] == "bCmdStart"
        mock_write.assert_awaited_once_with("bCmdStart", True)