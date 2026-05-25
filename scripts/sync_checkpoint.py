import json
import pandas as pd
import os

def sync_checkpoint():
    csv_path = "data/entities_final.csv"
    checkpoint_path = "data/uadc_checkpoint.json"
    
    if not os.path.exists(checkpoint_path):
        print(f"File {checkpoint_path} tidak ditemukan di server. Ingest-uadc akan berjalan dari awal.")
        return

    print("Membaca entities_final.csv...")
    df = pd.read_csv(csv_path)
    
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

    keys_to_delete = []
    updated_metadata_count = 0

    for item_id, data in list(checkpoint_data.items()):
        if item_id in csv_dict:
            new_data = csv_dict[item_id]
            
            # Cek apakah ada perubahan nama tempat (berarti baris ini telah kita bersihkan/perbaiki)
            # Atau apakah di dalam data checkpoint yang lama masih mengandung teks kotor
            old_pn = data.get("place_name", "")
            old_desc = json.dumps(data.get("features", {}))
            
            has_corrupt_text = (
                "google.com" in old_pn.lower() or 
                "google.com" in old_desc.lower() or 
                "(sc:" in old_pn.lower() or 
                "(sc:" in old_desc.lower()
            )
            
            name_changed = old_pn.strip().lower() != new_data["place_name"].strip().lower()
            category_changed = data.get("category", "").strip().lower() != new_data["category"].strip().lower()

            if name_changed or has_corrupt_text or category_changed:
                # Hapus dari cache agar LLM melakukan ekstraksi ulang untuk baris yang bersih ini
                keys_to_delete.append(item_id)
            else:
                # Hanya sinkronkan metadata ringan jika tidak ada perubahan signifikan
                if (data.get("category") != new_data["category"] or 
                    data.get("city_regency") != new_data["city_regency"] or 
                    data.get("rating") != new_data["rating"]):
                    data["category"] = new_data["category"]
                    data["city_regency"] = new_data["city_regency"]
                    data["rating"] = new_data["rating"]
                    updated_metadata_count += 1
        else:
            # Jika item_id tidak ada di CSV baru, hapus dari cache
            keys_to_delete.append(item_id)

    # Lakukan penghapusan cache kotor
    for k in keys_to_delete:
        del checkpoint_data[k]

    # Simpan kembali checkpoint yang sudah disinkronkan dan dibersihkan
    with open(checkpoint_path, "w", encoding="utf-8") as f:
        json.dump(checkpoint_data, f, indent=2, ensure_ascii=False)

    print("\n" + "="*50)
    print("SINKRONISASI CHECKPOINT SELESAI")
    print("="*50)
    print(f"Total cache dibersihkan (akan di-extract ulang) : {len(keys_to_delete)}")
    print(f"Total metadata diperbarui                        : {updated_metadata_count}")
    print(f"Sisa cache bersih di checkpoint                  : {len(checkpoint_data)}")
    print("="*50)
    print("Silakan commit script ini ke Git, jalankan di server, baru kemudian jalankan 'python scripts/ingest-uadc.py'.")

if __name__ == "__main__":
    sync_checkpoint()
