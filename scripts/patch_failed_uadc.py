import json
import os

def patch_checkpoint():
    checkpoint_path = "data/uadc_checkpoint.json"
    
    if not os.path.exists(checkpoint_path):
        print(f"Checkpoint file {checkpoint_path} tidak ditemukan.")
        return
        
    print(f"Membaca {checkpoint_path}...")
    with open(checkpoint_path, "r", encoding="utf-8") as f:
        checkpoint_data = json.load(f)
        
    failed_keys = []
    for key, data in checkpoint_data.items():
        place_name = data.get("place_name", "").strip()
        features = data.get("features", {})
        landscape = features.get("landscape_content_features", "").strip()
        
        # Deteksi fallback string yang diset oleh ingest-uadc.py jika LLM gagal
        fallback_str = f"Pemandangan alam dan fasilitas di {place_name}."
        if landscape == fallback_str or landscape.startswith("Pemandangan alam dan fasilitas di"):
            failed_keys.append(key)
            
    print(f"Ditemukan {len(failed_keys)} entri yang gagal diekstrak (menggunakan fallback).")
    
    if failed_keys:
        for k in failed_keys:
            print(f"  - Menghapus dari cache: {checkpoint_data[k]['place_name']} (ID: {k})")
            del checkpoint_data[k]
            
        with open(checkpoint_path, "w", encoding="utf-8") as f:
            json.dump(checkpoint_data, f, indent=2, ensure_ascii=False)
            
        print("\nPenghapusan selesai! Silakan jalankan kembali 'python scripts/ingest-uadc.py'.")
        print("Skrip ingest akan mendeteksi entri-entri ini sebagai belum diproses dan mencoba mengekstraknya kembali.")
    else:
        print("\nTidak ada entri gagal/fallback yang ditemukan. Semua data di checkpoint bersih!")

if __name__ == "__main__":
    patch_checkpoint()
