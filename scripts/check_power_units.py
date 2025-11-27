"""Temporary helper to inspect stored vehicle power values."""

from __future__ import annotations

import sqlite3
from pathlib import Path
from statistics import mean
from typing import List, Tuple

BASE_DIR = Path(__file__).resolve().parents[1]
DB_PATH = BASE_DIR / "data" / "truck_bot.db"


def fetch_power_samples(limit: int = 20) -> List[Tuple[int, str, str, int]]:
    """Return sample vehicles with non-null power values."""
    with sqlite3.connect(DB_PATH) as conn:
        conn.row_factory = sqlite3.Row
        cursor = conn.execute(
            """
            SELECT id, brand, model, power_hp
            FROM vehicles
            WHERE power_hp IS NOT NULL
            ORDER BY power_hp DESC
            LIMIT ?
            """,
            (limit,),
        )
        return [(row["id"], row["brand"], row["model"], row["power_hp"]) for row in cursor]


def fetch_power_stats() -> Tuple[int, int, int]:
    """Return count, min, max for power values."""
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.execute(
            """
            SELECT COUNT(power_hp), MIN(power_hp), MAX(power_hp)
            FROM vehicles
            WHERE power_hp IS NOT NULL
            """
        )
        count, min_power, max_power = cursor.fetchone()
        return count or 0, min_power or 0, max_power or 0


def fetch_power_mean() -> float:
    """Return mean of power values (naive, for quick inspection)."""
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.execute(
            "SELECT power_hp FROM vehicles WHERE power_hp IS NOT NULL"
        )
        values = [row[0] for row in cursor]
        return mean(values) if values else 0.0


def main() -> None:
    if not DB_PATH.exists():
        raise SystemExit(f"Database not found at {DB_PATH}")

    total, min_power, max_power = fetch_power_stats()
    avg_power = fetch_power_mean()

    print(f"DB path: {DB_PATH}")
    print(f"Vehicles with power: {total}")
    if total:
        print(f"Min: {min_power} | Max: {max_power} | Avg: {avg_power:.1f}")

        print("\nSample vehicles (top by power):")
        for vehicle_id, brand, model, power in fetch_power_samples():
            title = " ".join(filter(None, [brand, model])).strip() or "Unnamed"
            print(f"- ID {vehicle_id}: {title} -> {power} кВт")
    else:
        print("No vehicles with stored power values.")


if __name__ == "__main__":
    main()


