"""
Dummy apartment seeder for Jakarta Rental Dashboard. Author: Avatar Putra Sigit.

Generates 100 realistic apartment listings and:
  1. writes them to ``data/apartments.csv`` (the spec schema), and
  2. seeds them into the SQLite ``dummy_data`` table via
     ``core.database.seed_dummy_data`` for the shared-architecture history/cache.

Columns: id, area, price, bedrooms, bathrooms, furnished, sqm,
building_age, contact_name, contact_phone.

Price logic: Jakarta Selatan & Pusat are pricier (8-15 jt); Utara/Timur/Barat
are cheaper (3-10 jt). Reproducible via random seed=42.
"""
from __future__ import annotations

import csv
import os
import random
import sys
from typing import Dict, List

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.database import init_db, seed_dummy_data, get_dummy_data  # noqa: E402

BASE_DIR: str = os.path.dirname(os.path.abspath(__file__))
CSV_PATH: str = os.path.join(BASE_DIR, "apartments.csv")
CATEGORY: str = "apartments"
SEP: str = "|||"

AREAS: List[str] = [
    "Jakarta Selatan", "Jakarta Pusat", "Jakarta Utara",
    "Jakarta Timur", "Jakarta Barat",
]
PREMIUM_AREAS: set = {"Jakarta Selatan", "Jakarta Pusat"}
FIRST_NAMES: List[str] = [
    "Budi", "Sari", "Andi", "Dewi", "Rizki", "Putri", "Agus", "Maya",
    "Hadi", "Indah", "Fajar", "Nina", "Eko", "Lia", "Yusuf", "Rina",
]
LAST_NAMES: List[str] = [
    "Santoso", "Wijaya", "Pratama", "Lestari", "Nugroho", "Halim",
    "Saputra", "Anggraini", "Kurniawan", "Permata",
]


def _build_rows(n: int = 100, seed: int = 42) -> List[Dict[str, object]]:
    """Build ``n`` synthetic apartment rows.

    Args:
        n: Number of listings.
        seed: RNG seed for reproducibility.

    Returns:
        List of listing dicts with the full spec schema.
    """
    try:
        rng = random.Random(seed)
        rows: List[Dict[str, object]] = []
        for i in range(1, n + 1):
            area = rng.choice(AREAS)
            if area in PREMIUM_AREAS:
                price = rng.randint(8, 15) * 1_000_000
            else:
                price = rng.randint(3, 10) * 1_000_000
            bedrooms = rng.randint(1, 3)
            bathrooms = rng.randint(1, 2)
            furnished = rng.choice(["yes", "no"])
            sqm = rng.randint(25, 80)
            building_age = rng.randint(0, 20)
            name = f"{rng.choice(FIRST_NAMES)} {rng.choice(LAST_NAMES)}"
            phone = f"08{rng.randint(11, 99)}{rng.randint(1000000, 9999999)}"
            rows.append(
                {
                    "id": i,
                    "area": area,
                    "price": price,
                    "bedrooms": bedrooms,
                    "bathrooms": bathrooms,
                    "furnished": furnished,
                    "sqm": sqm,
                    "building_age": building_age,
                    "contact_name": name,
                    "contact_phone": phone,
                }
            )
        return rows
    except Exception as exc:  # pragma: no cover - defensive
        print(f"[ERROR] Apartment row generation failed: {exc}")
        return []


def _write_csv(rows: List[Dict[str, object]]) -> None:
    """Write listings to apartments.csv."""
    try:
        if not rows:
            return
        with open(CSV_PATH, "w", newline="", encoding="utf-8") as fh:
            writer = csv.DictWriter(fh, fieldnames=list(rows[0].keys()))
            writer.writeheader()
            writer.writerows(rows)
    except OSError as exc:
        print(f"[ERROR] Could not write {CSV_PATH}: {exc}")


def seed_apartments(force: bool = False) -> int:
    """Generate apartments.csv and seed the SQLite dummy_data table.

    Args:
        force: When True, regenerate even if data already exists.

    Returns:
        Number of listings generated (0 if skipped or on failure).
    """
    try:
        init_db()
        csv_exists = os.path.exists(CSV_PATH)
        db_seeded = bool(get_dummy_data(CATEGORY, limit=1))
        if not force and csv_exists and db_seeded:
            return 0

        rows = _build_rows()
        if not rows:
            return 0

        if force or not csv_exists:
            _write_csv(rows)

        if force or not db_seeded:
            # Encode each listing for the generic (value, label) dummy_data schema.
            encoded = [
                {
                    "value": float(r["price"]),
                    "label": f"{r['area']}{SEP}{r['bedrooms']}BR{SEP}{r['furnished']}{SEP}{r['sqm']}m2",
                }
                for r in rows
            ]
            seed_dummy_data(CATEGORY, encoded)
        return len(rows)
    except Exception as exc:  # pragma: no cover - defensive
        print(f"[ERROR] seed_apartments failed: {exc}")
        return 0


if __name__ == "__main__":
    inserted = seed_apartments(force="--force" in sys.argv)
    print(f"[OK] Seeded {inserted} apartment listings (csv + dummy_data '{CATEGORY}').")
