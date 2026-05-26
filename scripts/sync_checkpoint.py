import json
import pandas as pd
import os
import re

def clean_name(name):
    # Remove Batak script suffix (separated by '|') and non-alphanumeric characters for comparison
    name = name.split("|")[0]
    name = re.sub(r'[^a-zA-Z0-9]', '', name).lower().strip()
    return name

def sync_checkpoint():
    csv_path = "data/entities_final.csv"
    checkpoint_path = "data/uadc_checkpoint.json"
    
    if not os.path.exists(checkpoint_path):
        print(f"File {checkpoint_path} tidak ditemukan. Ingest-uadc akan berjalan dari awal.")
        return

    print("Membaca entities_final.csv...")
    df = pd.read_csv(csv_path)
    
    # Petakan nama tempat yang dinormalisasi ke data baris CSV baru (berisi item_id baru)
    csv_dict = {}
    for idx, row in df.iterrows():
        # item_id harus sinkron dengan logika penomoran di ingest-uadc.py
        item_id = str(row.get("item_id", idx + 1))
        place_name = str(row.get("place_name", "")).strip()
        
        csv_dict[clean_name(place_name)] = {
            "item_id": item_id,
            "place_name": place_name,
            "category": str(row.get("category", "")).strip(),
            "city_regency": str(row.get("city_regency", "")).strip(),
            "rating": float(row.get("rating", 0.0)) if str(row.get("rating", "")).replace(".", "").isdigit() else 0.0,
        }

    print("Membaca uadc_checkpoint.json...")
    with open(checkpoint_path, "r", encoding="utf-8") as f:
        checkpoint_data = json.load(f)

    new_checkpoint_data = {}
    keys_deleted_count = 0
    updated_metadata_count = 0
    preserved_count = 0

    # Lakukan pencocokan berdasarkan NAMA tempat (place_name), bukan indeks angka (item_id)
    # Ini mencegah rusaknya seluruh cache akibat pergeseran indeks setelah baris dihapus/deduplikasi.
    for old_key, data in list(checkpoint_data.items()):
        old_pn = str(data.get("place_name", "")).strip()
        cleaned_old_name = clean_name(old_pn)
        
        if cleaned_old_name in csv_dict:
            new_data = csv_dict[cleaned_old_name]
            new_item_id = new_data["item_id"]
            
            old_desc = json.dumps(data.get("features", {}))
            
            # Deteksi teks kotor (Google review)
            has_corrupt_text = (
                "google.com" in old_pn.lower() or 
                "google.com" in old_desc.lower() or 
                "(sc:" in old_pn.lower() or 
                "(sc:" in old_desc.lower()
            )
            
            if has_corrupt_text:
                keys_deleted_count += 1
            else:
                # Perbarui metadata agar sesuai persis dengan CSV baru
                data["item_id"] = new_item_id
                
                # Cek jika ada metadata ringan yang berubah
                metadata_updated = (
                    data.get("category") != new_data["category"] or 
                    data.get("city_regency") != new_data["city_regency"] or 
                    data.get("rating") != new_data["rating"] or
                    data.get("place_name") != new_data["place_name"]
                )
                
                data["place_name"] = new_data["place_name"]
                data["category"] = new_data["category"]
                data["city_regency"] = new_data["city_regency"]
                data["rating"] = new_data["rating"]
                
                if metadata_updated:
                    updated_metadata_count += 1
                
                # Simpan ulang dengan kunci item_id yang baru agar sinkron dengan indeks CSV
                new_checkpoint_data[new_item_id] = data
                preserved_count += 1
        else:
            keys_deleted_count += 1

    # Tulis kembali ke checkpoint file
    with open(checkpoint_path, "w", encoding="utf-8") as f:
        json.dump(new_checkpoint_data, f, indent=2, ensure_ascii=False)

    print("\n" + "="*50)
    print("SINKRONISASI CHECKPOINT SELESAI")
    print("="*50)
    print(f"Total cache dibersihkan (akan di-extract ulang) : {keys_deleted_count}")
    print(f"Total metadata diperbarui                        : {updated_metadata_count}")
    print(f"Sisa cache bersih di checkpoint                  : {preserved_count}")
    print("="*50)
    print("Silakan commit script ini ke Git, jalankan di server, baru kemudian jalankan 'python scripts/ingest-uadc.py'.")

if __name__ == "__main__":
    sync_checkpoint()
