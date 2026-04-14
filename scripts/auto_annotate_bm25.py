import json
import pandas as pd
import re

def get_keywords(text):
    text = text.lower()
    text = re.sub(r'[^a-z0-9\s]', '', text)
    stop_words = {"tolong", "carikan", "di", "sekitar", "kawasan", "saja", "yang", "dan", "untuk", "coba", "sebutkan", "adakah", "ada", "saya", "mencari", "mana", "berikan", "ingin", "banget", "buat", "mau", "cari", "tempat", "lokasi", "rekomendasi", "butuh"}
    words = text.split()
    return [w for w in words if w not in stop_words and len(w) > 2]

def rank_places(query_keywords, df):
    scores = []
    for idx, row in df.iterrows():
        score = 0
        target_text = str(row['place_name']).lower() + " " + str(row['category']).lower() + " " + str(row['description']).lower()
        for kw in query_keywords:
            if kw in target_text:
                score += 1
                # Boost if exact keyword in place_name or category
                if kw in str(row['place_name']).lower() or kw in str(row['category']).lower():
                    score += 2
        scores.append((row['place_name'], score))
    
    # Sort by score desc
    scores = sorted(scores, key=lambda x: x[1], reverse=True)
    # Take top 3 with score > 1
    return [s[0] for s in scores if s[1] > 1][:3]

def main():
    print("Membaca data...")
    try:
        with open('data/eval_ground_truths.json', 'r', encoding='utf-8') as f:
            eval_data = json.load(f)
    except FileNotFoundError:
        print("eval_ground_truths.json belum ada, jalankan generate_gt_skeleton.py dulu.")
        return
        
    df = pd.read_csv('data/wisata-toba-unified-final.csv')
    
    print("Melakukan Auto-Annotate (Keyword Matching) untuk", len(eval_data), "kueri...")
    
    filled_count = 0
    for item in eval_data:
        # Jika belum ada ground truth
        if not item.get("ground_truths"):
            kws = get_keywords(item["query"])
            top_places = rank_places(kws, df)
            if top_places:
                item["ground_truths"] = top_places
                filled_count += 1
                
    with open('data/eval_ground_truths.json', 'w', encoding='utf-8') as f:
        json.dump(eval_data, f, indent=2, ensure_ascii=False)
        
    print(f"Berhasil! {filled_count} dari {len(eval_data)} kueri tersisa telah terisi dengan prediksi Ground Truth awal.")
    print("Silakan buka data/eval_ground_truths.json untuk melihat/menghapusnya.")

if __name__ == "__main__":
    main()
