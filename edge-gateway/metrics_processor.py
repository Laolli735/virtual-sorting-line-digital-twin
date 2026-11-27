from dataclasses import dataclass
from typing import Any

STATE_MAP = {
    0: "IDLE",
    10: "RUN",
    20: "WARNING",
    99: "FAULT",
}

@dataclass
class ProductionTelemetry:
    system_state: int
    total_count: int
    sorted_a: int
    sorted_b: int
    oee_availability: float

    @property
    def state_label(self) -> str:
        return STATE_MAP.get(self.system_state, "UNKNOWN")

def validate_and_normalize(raw: dict[str, Any]) -> ProductionTelemetry:
    """Validates raw PLC OPC UA tag values and normalizes them for DB insertion."""
    state = int(raw.get("system_state", 0))
    total = max(0, int(raw.get("total_count", 0)))
    a = max(0, int(raw.get("sorted_a", 0)))
    b = max(0, int(raw.get("sorted_b", 0)))

    # Ensure total_count is never less than the sum of sorted branches
    total = max(total, a + b)

    oee = float(raw.get("oee_availability", 0.0))
    oee = round(min(100.0, max(0.0, oee)), 2)

    return ProductionTelemetry(
        system_state=state,
        total_count=total,
        sorted_a=a,
        sorted_b=b,
        oee_availability=oee,
    )
