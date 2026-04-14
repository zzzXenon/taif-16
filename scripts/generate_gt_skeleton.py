import json
import pandas as pd
import re
import os

def parse_markdown_queries(filepath):
    queries = []
    current_level = 0
    with open(filepath, 'r', encoding='utf-8') as f:
        lines = f.readlines()
        for line in lines:
            line = line.strip()
            if line.startswith("## Level"):
                # Extract level number
                match = re.search(r"Level (\d+)", line)
                if match:
                    current_level = int(match.group(1))
            elif re.match(r"^\d+\.\s", line):
                # Ensure it's inside Level 1-5
                if 1 <= current_level <= 5:
                    query_text = re.sub(r"^\d+\.\s", "", line).strip()
                    queries.append({
                        "level": current_level,
                        "query": query_text,
                        "ground_truths": [] # TBD by user
                    })
    return queries

def main():
    md_path = 'docs/eval_dataset_queries.md'
    csv_path = 'data/wisata-toba-unified-final.csv'
    
    # 1. Parse Markdown to JSON Skeleton
    print("Mengekstrak kueri dari Markdown...")
    skeleton = parse_markdown_queries(md_path)
    
    out_json = 'data/eval_ground_truths.json'
    if not os.path.exists(out_json):
        with open(out_json, 'w', encoding='utf-8') as f:
            json.dump(skeleton, f, indent=2, ensure_ascii=False)
        print(f"Buku kerja Ground Truth berhasil dibuat -> {out_json}")
    else:
        print(f"File {out_json} sudah ada, melewati pembuatan ulang (jangan sampai anotasi tertimpa).")
        
    # 2. Extract Valid Database Names
    print("Mengekstrak kumpulan nama tempat asli untuk contekan Anotator...")
    try:
        df = pd.read_csv(csv_path)
        places = sorted(df['place_name'].astype(str).unique().tolist())
        
        with open('data/referensi_tempat_wisata.json', 'w', encoding='utf-8') as f:
            json.dump(places, f, indent=2, ensure_ascii=False)
        print(f"Daftar nama pariwisata persis CSV berhasil diekspor -> data/referensi_tempat_wisata.json")
    except Exception as e:
        print("Gagal membaca CSV database:", e)
        
    print("\nSilakan lengkapi array 'ground_truths' di dalam 'data/eval_ground_truths.json' menggunakan nama-nama persis yang ada di 'referensi_tempat_wisata.json' sebelum menjalankan run_evaluation.py.")

if __name__ == "__main__":
    main()
