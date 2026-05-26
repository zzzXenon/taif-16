import pandas as pd
import re
import os

def clean_name(name):
    # Remove Batak script suffix (separated by '|') and non-alphanumeric characters for comparison
    name = name.split("|")[0]
    name = re.sub(r'[^a-zA-Z0-9]', '', name).lower().strip()
    return name

def deduplicate():
    csv_path = "data/entities_final.csv"
    if not os.path.exists(csv_path):
        print(f"File {csv_path} tidak ditemukan.")
        return

    df = pd.read_csv(csv_path)
    print(f"Jumlah entitas awal: {len(df)}")

    # 1. Bersihkan nama untuk perbandingan (abaikan casing, spasi, tanda baca, dan aksara Batak)
    df['temp_clean_name'] = df['place_name'].astype(str).apply(clean_name)
    
    # 2. Urutkan berdasarkan kemiripan nama, panjang nama tempat (agar menyimpan yang ada aksara Batak),
    #    dan panjang deskripsi (agar menyimpan informasi terlengkap)
    df['name_len'] = df['place_name'].astype(str).str.len()
    df['desc_len'] = df['description'].astype(str).str.len()
    
    # Urutkan desc_len secara descending agar yang paling lengkap keterangannya diutamakan
    df = df.sort_values(by=['temp_clean_name', 'name_len', 'desc_len'], ascending=[True, False, False])
    
    # Cetak duplikat yang terdeteksi sebelum dihapus
    duplicates = df[df.duplicated(subset=['temp_clean_name'], keep=False)]
    if not duplicates.empty:
        print("\nMenghapus duplikat berikut (hanya akan menyimpan entri dengan nama paling lengkap & deskripsi terpanjang):")
        grouped = duplicates.groupby('temp_clean_name')
        for name, group in grouped:
            print(f"- Group '{name}': {group['place_name'].tolist()}")

    # 3. Hapus duplikat
    df_cleaned = df.drop_duplicates(subset=['temp_clean_name'], keep='first')
    
    # Buang kolom bantuan
    df_cleaned = df_cleaned.drop(columns=['temp_clean_name', 'name_len', 'desc_len'])
    
    # 4. Simpan kembali ke file
    df_cleaned.to_csv(csv_path, index=False)
    print(f"\nJumlah entitas setelah pembersihan: {len(df_cleaned)}")
    print("Deduplikasi selesai dan disimpan ke data/entities_final.csv.")

if __name__ == "__main__":
    deduplicate()
