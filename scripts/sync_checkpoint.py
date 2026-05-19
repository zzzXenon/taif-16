import json
import pandas as pd
import os

def sync_checkpoint():
    csv_path = "data/entities_final.csv"
    checkpoint_path = "data/uadc_checkpoint.json"
    
    if not os.path.exists(checkpoint_path):
        print(f"File {checkpoint_path} tidak ditemukan. Tidak ada yang perlu disinkronkan.")
        return

    print("Membaca entities_final.csv...")
    df = pd.read_csv(csv_path)
    
    # Buat dictionary pemetaan dari item_id (index/baris) ke data terbaru di CSV
    # Asumsi: item_id di-generate berurutan dari 1 saat pertama kali di-ingest
    csv_dict = {}
    for idx, row in df.iterrows():
        item_id = str(row.get("item_id", idx + 1))
        csv_dict[item_id] = {
            "place_name": str(row.get("place_name", "")).strip(),
            "category": str(row.get("category", "")).strip(),
            "city_regency": str(row.get("city_regency", "")).strip(),
            "rating": float(row.get("rating", 0.0)) if str(row.get("rating", "")).replace(".", "").isdigit() else 0.0,
        }

    print("Membaca uadc_checkpoint.json...")
    with open(checkpoint_path, "r", encoding="utf-8") as f:
        checkpoint_data = json.load(f)

    updates = 0
    for item_id, data in checkpoint_data.items():
        if item_id in csv_dict:
            new_data = csv_dict[item_id]
            # Cek apakah ada perubahan
            if (data["place_name"] != new_data["place_name"] or 
                data["category"] != new_data["category"] or
                data.get("city_regency", "") != new_data["city_regency"]):
                
                # Update data di checkpoint dengan data baru dari CSV
                data["place_name"] = new_data["place_name"]
                data["category"] = new_data["category"]
                data["city_regency"] = new_data["city_regency"]
                data["rating"] = new_data["rating"]
                updates += 1

    if updates > 0:
        with open(checkpoint_path, "w", encoding="utf-8") as f:
            json.dump(checkpoint_data, f, indent=2, ensure_ascii=False)
        print(f"Berhasil mensinkronkan {updates} entitas yang diubah dari CSV ke Checkpoint!")
    else:
        print("Semua data sudah sinkron, tidak ada perubahan metadata yang ditemukan.")

if __name__ == "__main__":
    sync_checkpoint()
