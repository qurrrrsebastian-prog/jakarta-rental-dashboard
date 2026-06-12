"""Generate a synthetic Jakarta rental property dataset.

Produces 800 realistic rental listings across Greater Jakarta and saves
them to ``data/jakarta_rentals.csv``. Pricing follows market-like rules:
unit type determines the base range, premium locations carry a multiplier,
and proximity to MRT stations adds a premium.
"""

from __future__ import annotations

import os
import random
from typing import Dict, List, Tuple

import pandas as pd

SEED: int = 42
N_ROWS: int = 800

LOCATIONS: List[str] = [
    "Jakarta Selatan",
    "Jakarta Barat",
    "Jakarta Pusat",
    "Jakarta Timur",
    "Jakarta Utara",
    "Depok",
    "Tangerang",
    "Bekasi",
]

PREMIUM_LOCATIONS: List[str] = ["Jakarta Selatan", "Jakarta Pusat"]

# (min_price, max_price) in IDR per month, and (min_area, max_area) in m2.
TYPE_SPECS: Dict[str, Dict[str, Tuple[float, float]]] = {
    "Studio": {"price": (2_500_000, 4_500_000), "area": (18, 30)},
    "1BR": {"price": (3_500_000, 6_000_000), "area": (28, 45)},
    "2BR": {"price": (5_000_000, 9_000_000), "area": (40, 75)},
    "3BR": {"price": (7_000_000, 15_000_000), "area": (65, 130)},
}

FACILITY_POOL: List[str] = [
    "Kolam Renang",
    "Gym",
    "Keamanan 24 Jam",
    "Parkir",
    "AC",
    "Furnished",
    "Laundry",
    "Minimarket",
    "Akses Kartu",
    "Taman Bermain",
]

PROPERTY_PREFIXES: List[str] = [
    "Apartemen", "Residence", "Tower", "Suites", "Kost Eksklusif",
]

PROPERTY_NAMES: List[str] = [
    "Sudirman", "Kemang", "Senayan", "Casablanca", "Thamrin", "Kuningan",
    "Menteng", "Kelapa Gading", "Pluit", "Cervino", "Margonda", "Alam Sutera",
    "Bintaro", "Grand Galaxy", "Pondok Indah", "Tebet", "Cikini", "Permata",
    "Green Bay", "Royal Mediterania",
]


def generate_listing(listing_id: int) -> Dict[str, object]:
    """Generate a single rental listing as a dictionary.

    Args:
        listing_id: Sequential identifier for the listing.

    Returns:
        A dict with all listing columns; empty dict on failure.
    """
    try:
        lokasi = random.choice(LOCATIONS)
        tipe = random.choice(list(TYPE_SPECS.keys()))
        spec = TYPE_SPECS[tipe]

        luas_m2 = round(random.uniform(*spec["area"]), 1)
        harga = random.uniform(*spec["price"])

        # Premium locations (Jaksel, Jakpus) command a 1.2x-1.4x multiplier.
        if lokasi in PREMIUM_LOCATIONS:
            harga *= random.uniform(1.2, 1.4)

        jarak_mrt = round(random.uniform(0.1, 12.0), 2)

        # Listings within 1 km of an MRT station get a 15-25% premium.
        if jarak_mrt < 1.0:
            harga *= random.uniform(1.15, 1.25)

        fasilitas = ", ".join(
            sorted(random.sample(FACILITY_POOL, k=random.randint(3, 6)))
        )

        nama = (
            f"{random.choice(PROPERTY_PREFIXES)} "
            f"{random.choice(PROPERTY_NAMES)} {random.choice(['A', 'B', 'C', 'I', 'II'])}"
        )

        return {
            "id": listing_id,
            "nama_property": nama,
            "lokasi": lokasi,
            "tipe": tipe,
            "luas_m2": luas_m2,
            "harga_sewa_bulan": int(round(harga, -4)),
            "fasilitas": fasilitas,
            "jarak_ke_mrt_km": jarak_mrt,
            "rating_review": round(random.uniform(3.0, 5.0), 1),
        }
    except (KeyError, ValueError) as exc:
        print(f"[WARN] Failed to generate listing {listing_id}: {exc}")
        return {}


def generate_dataset(n_rows: int = N_ROWS) -> pd.DataFrame:
    """Generate the full rental dataset.

    Args:
        n_rows: Number of listings to generate.

    Returns:
        DataFrame with one row per listing.

    Raises:
        RuntimeError: If no valid rows could be generated.
    """
    try:
        random.seed(SEED)
        rows = [generate_listing(i + 1) for i in range(n_rows)]
        rows = [r for r in rows if r]
        if not rows:
            raise RuntimeError("No valid listings were generated.")
        return pd.DataFrame(rows)
    except Exception as exc:
        raise RuntimeError(f"Dataset generation failed: {exc}") from exc


def main() -> None:
    """Generate the dataset and write it next to this script."""
    try:
        out_dir = os.path.dirname(os.path.abspath(__file__))
        out_path = os.path.join(out_dir, "jakarta_rentals.csv")
        df = generate_dataset()
        df.to_csv(out_path, index=False)
        print(f"[OK] Generated {len(df)} listings -> {out_path}")
        print(df.head().to_string(index=False))
    except (OSError, RuntimeError) as exc:
        print(f"[ERROR] {exc}")
        raise SystemExit(1)


if __name__ == "__main__":
    main()
