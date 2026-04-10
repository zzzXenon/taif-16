import pandas as pd
import re
import csv
import os

def clean_review_final(text):
    if pd.isna(text) or text == "" or not isinstance(text, str):
        return ""
    
    text = str(text).replace('\n', ' ').replace('\r', ' ')
    text = text.lower()

    if "diterjemahkan oleh google" in text:
        parts = text.split("diterjemahkan oleh google")
        text = parts[-1].strip()
        if "asli" in text:
            text = text.split("asli")[0].strip()

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

    text = re.sub(r'[^a-zA-Z0-9\s\.,]', ' ', text)
    text = re.sub(r'\s+', ' ', text).strip()
    return text

def main():
    print("Membaca data asal...")
    df_w = pd.read_csv('data-pdf-new/data - wisata-v2.csv')
    df_r = pd.read_csv('data-pdf-new/data - resto-hotel-v2.csv')
    df_meta = pd.read_csv('data-pdf-new/data - wisata-metadata.csv')

    # Gabung UGC
    df_ugc = pd.concat([df_w, df_r]).dropna(subset=['review-text'])
    df_ugc['text_len'] = df_ugc['review-text'].astype(str).apply(len)
    
    # Sorting by place and length (longest first)
    df_ugc = df_ugc.sort_values(by=['place-name', 'text_len'], ascending=[True, False])
    
    print("Mengagregasi max 50 review terpanjang per tempat...")
    grouped = []
    
    for place, group in df_ugc.groupby('place-name'):
        top_50 = group.head(50)
        
        # Bersihkan & rangkai 50 review
        cleaned_reviews = [clean_review_final(r) for r in top_50['review-text']]
        cleaned_reviews = [r for r in cleaned_reviews if len(r.split()) > 3] # buang yang isinya cuma 2-3 kata walau aneh
        
        combined_text = ""
        for i, review in enumerate(cleaned_reviews):
            combined_text += f"[Ulasan {i+1}]: {review} "
            
        grouped.append({'place_name': str(place).strip(), 'aggregated_reviews': combined_text.strip()})
        
    df_agg = pd.DataFrame(grouped)
    
    # Persiapkan Metadata
    df_meta['place_name'] = df_meta['place-name'].astype(str).str.strip()
    df_meta['category'] = df_meta['place-type'].fillna('Umum')
    df_meta['official_desc'] = df_meta['description'].fillna('')
    meta_subset = df_meta[['place_name', 'category', 'official_desc']].drop_duplicates(subset=['place_name'])
    
    # Merge Metadata & UGC (Full Outer Join)
    print("Menggabungkan deskripsi metadata dengan agregasi ulasan...")
    df_final = pd.merge(meta_subset, df_agg, on='place_name', how='outer')
    
    # Jika kategori NaN karena tidak ada di metadata, diisi 'Pariwisata / Lainnya'
    df_final['category'] = df_final['category'].fillna('Pariwisata / UMKM')
    
    # Buat kolom description final:
    def combine_info(row):
        desc = ""
        if pd.notna(row['official_desc']) and row['official_desc'] != "":
            desc += f"[Deskripsi Resmi]: {row['official_desc']} "
        if pd.notna(row['aggregated_reviews']) and row['aggregated_reviews'] != "":
            desc += f"[Kumpulan Ulasan dari Pengunjung]: {row['aggregated_reviews']}"
        return desc.strip()
        
    df_final['description'] = df_final.apply(combine_info, axis=1)
    
    # Buang tempat yang deskripsinya kosong sama sekali
    df_final = df_final[df_final['description'] != ""]
    
    out_df = df_final[['place_name', 'category', 'description']]
    
    os.makedirs('data', exist_ok=True)
    out_path = 'data/wisata-toba-unified-final.csv'
    out_df.to_csv(out_path, index=False, quoting=csv.QUOTE_NONNUMERIC)
    print(f"SELESAI! Kolom akhir: {list(out_df.columns)}")
    print(f"Total Tempat Tersimpan: {len(out_df)}")
    print(f"Disimpan di: {out_path}")

if __name__ == '__main__':
    main()
