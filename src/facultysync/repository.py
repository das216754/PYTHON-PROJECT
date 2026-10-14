import json
from pathlib import Path

from .models import TimeInterval


# Project root is the folder containing src/
PROJECT_ROOT = Path(__file__).resolve().parents[1]

DATA_FILE = PROJECT_ROOT / "data" / "schedule.json"


def load_schedule():
    """Load faculty availability and existing appointments."""

    if not DATA_FILE.exists():
        raise FileNotFoundError(
            f"Schedule file not found: {DATA_FILE}"
        )

    with DATA_FILE.open("r", encoding="utf-8") as file:
        data = json.load(file)

    availability = [
        TimeInterval(**item)
        for item in data.get("availability", [])
    ]

    appointments = [
        TimeInterval(**item)
        for item in data.get("appointments", [])
    ]

    return availability, appointments