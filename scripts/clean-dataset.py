import pandas as pd
import re
import csv

def clean_review_final(text):
    if pd.isna(text) or text == "":
        return ""
    
    # 1. Hilangkan karakter baris baru (\n atau \r) agar teks menyatu
    text = str(text).replace('\n', ' ').replace('\r', ' ')
    
    text = text.lower()

    # 2. Menangani translasi Google
    if "diterjemahkan oleh google" in text:
        parts = text.split("diterjemahkan oleh google")
        text = parts[-1].strip()
        if "asli" in text:
            text = text.split("asli")[0].strip()

    # 3. Normalisasi Slang & Kata Tidak Baku
    slang_map = {
        r'\bngopi\b': 'minum kopi',
        r'\byg\b': 'yang',
        r'\btp\b': 'tapi',
        r'\bgak\b': 'tidak',
        r'\bgk\b': 'tidak',
        r'\bga\b': 'tidak',
        r'\budah\b': 'sudah',
        r'\bdah\b': 'sudah',
        r'\bbgt\b': 'sangat',
        r'\bbanget\b': 'sangat',
        r'\bmantap\b': 'bagus',
        r'\brecomended\b': 'direkomendasikan',
        r'\brekomended\b': 'direkomendasikan',
        r'\bkrn\b': 'karena',
        r'\bdgn\b': 'dengan',
        r'\butk\b': 'untuk',
        r'\btpt\b': 'tempat',
        r'\baja\b': 'saja',
        r'\bpake\b': 'pakai',
        r'\brame\b': 'ramai',
        r'\bsy\b': 'saya',
        r'\bblm\b': 'belum',
        r'\bhtm\b': 'harga tiket masuk',
        r'\blks\b': 'lokasi',
        r'\bjln\b': 'jalan',
        r'\bviewnya\b': 'pemandangannya',
        r'\boke\b': 'bagus',
        r'\bok\b': 'bagus'
    }

    for pattern, replacement in slang_map.items():
        text = re.sub(pattern, replacement, text)

    # 4. Hapus karakter non-alfabet (kecuali spasi, titik, koma)
    text = re.sub(r'[^a-zA-Z0-9\s\.,]', ' ', text)

    # 5. Hapus spasi ganda
    text = re.sub(r'\s+', ' ', text).strip()
    
    return text

def main():
    input_file = 'wisata-toba-cleaned.csv'
    output_file = 'wisata-toba-final-v2.csv'
    
    print(f"Memproses file...")
    try:
        # Load data
        df = pd.read_csv(input_file)
        
        if 'reviews' in df.columns:
            # GANTI isi kolom reviews yang lama dengan hasil cleaning
            df['reviews'] = df['reviews'].apply(clean_review_final)
            
            # Simpan dengan format CSV yang aman (quoting semua string jika perlu)
            # Ini memastikan kolom tidak berantakan jika ada tanda koma di dalam teks
            df.to_csv(output_file, index=False, quoting=csv.QUOTE_NONNUMERIC)
            
            print(f"Sukses! Jumlah kolom tetap: {len(df.columns)}")
            print(f"File disimpan sebagai: {output_file}")
        else:
            print("Kolom 'reviews' tidak ditemukan.")
            
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    main()