"""
patch_checkpoint_city.py
------------------------
Patches uadc_checkpoint.json to add missing 'city_regency' field
to each entity, read from entities_final.csv.

No LLM calls needed. Safe to run on existing checkpoint.

Run:
  python scripts/patch_checkpoint_city.py
"""
import os
import json
import pandas as pd

BASE_DIR       = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CHECKPOINT_FILE = os.path.join(BASE_DIR, "data", "uadc_checkpoint.json")
CSV_FILE        = os.path.join(BASE_DIR, "data", "entities_final.csv")

def main():
    if not os.path.exists(CHECKPOINT_FILE):
        print(f"Checkpoint not found: {CHECKPOINT_FILE}")
        return
    if not os.path.exists(CSV_FILE):
        print(f"CSV not found: {CSV_FILE}")
        return

    print(f"Loading checkpoint ({CHECKPOINT_FILE})...")
    with open(CHECKPOINT_FILE, "r", encoding="utf-8") as f:
        checkpoint = json.load(f)
    print(f"  {len(checkpoint)} entities in checkpoint.")

    print(f"Loading CSV ({CSV_FILE})...")
    df = pd.read_csv(CSV_FILE).fillna("")
    if "item_id" not in df.columns:
        df["item_id"] = range(1, len(df) + 1)

    # Build lookup: item_id → city_regency
    city_lookup = {
        str(row["item_id"]): str(row.get("city_regency", "")).strip()
        for _, row in df.iterrows()
    }
    print(f"  {len(city_lookup)} entries in CSV lookup.")

    # Patch checkpoint
    patched = 0
    already_had = 0
    for item_id, data in checkpoint.items():
        if data.get("city_regency", "") != "":
            already_had += 1
            continue
        city = city_lookup.get(item_id, "")
        data["city_regency"] = city
        patched += 1

    print(f"\nPatching complete:")
    print(f"  Already had city_regency : {already_had}")
    print(f"  Patched                  : {patched}")

    print(f"\nSaving patched checkpoint...")
    with open(CHECKPOINT_FILE, "w", encoding="utf-8") as f:
        json.dump(checkpoint, f, indent=2, ensure_ascii=False)
    print("Done.")

if __name__ == "__main__":
    main()
