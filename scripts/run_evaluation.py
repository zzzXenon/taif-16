import json
import requests
import math
import time

def calculate_hr_at_k(retrieved_items, ground_truths):
    """Hit Rate: 1.0 jika minimal 1 benar muncul, 0.0 jika meleset semua."""
    if not ground_truths:
        return 0.0
    for item in retrieved_items:
        if item in ground_truths:
            return 1.0
    return 0.0

def calculate_mrr_at_k(retrieved_items, ground_truths):
    """MRR: 1 / rank dari dokumen benar pertama."""
    if not ground_truths:
        return 0.0
    for i, item in enumerate(retrieved_items):
        if item in ground_truths:
            return 1.0 / (i + 1)
    return 0.0

def calculate_recall_at_k(retrieved_items, ground_truths):
    """Recall: Jumlah ditebak benar dibagi Total ground truth."""
    if not ground_truths:
        return 0.0
    # Berapa banyak dokumen unik yang ditebak benar
    hits = set(retrieved_items).intersection(set(ground_truths))
    return len(hits) / len(set(ground_truths))

def calculate_ndcg_at_k(retrieved_items, ground_truths):
    """NDCG: DCG / Ideal DCG."""
    if not ground_truths:
        return 0.0
    
    dcg = 0.0
    for i, item in enumerate(retrieved_items):
        if item in ground_truths:
            # Relevance = 1 untuk hit sederhana. Logaritma basis 2
            dcg += 1.0 / math.log2(i + 2)
            
    # Hitung Ideal DCG
    idcg = 0.0
    ideal_hits = min(len(ground_truths), len(retrieved_items))
    for i in range(ideal_hits):
        idcg += 1.0 / math.log2(i + 2)
        
    return dcg / idcg if idcg > 0 else 0.0

def extract_place_nama_dari_source(doc_string):
    # Asumsi: "Source 1: Nama Tempat: Bukit Holbung Samosir\nKategori: Wisata..." -> Regex / Split
    # Paling aman tangkap bari yang mengandung "Nama Tempat: "
    lines = doc_string.split('\n')
    for line in lines:
        if "Nama Tempat:" in line:
            return line.split("Nama Tempat:")[1].strip()
    # Fallback string manipulation jika struktur berbeda
    return "Tempat Tidak Diketahui"

def main():
    try:
        with open('data/eval_ground_truths.json', 'r', encoding='utf-8') as f:
            data = json.load(f)
    except Exception as e:
        print("Gagal membaca eval_ground_truths.json. Silakan jalankan generate_gt_skeleton.py terlebih dahulu.")
        return

    API_URL = "http://localhost:8000/api/chat"
    ablation_modes = ["baseline", "pipeline_a_only", "proposed"]
    
    # Filter hanya kueri yang sudah diisi Ground Truth-nya oleh Anotator
    eval_data = [d for d in data if isinstance(d.get("ground_truths"), list) and len(d["ground_truths"]) > 0]
    
    if not eval_data:
        print("TIDAK ADA DATA! Pastikan Anda sudah memberikan nilai di array 'ground_truths' pada file JSON.")
        return

    print(f"Ditemukan {len(eval_data)} kueri yang siap dievaluasi.")
    
    # Struktur Data Metrik
    # { mode: { level: { "hr": [], "mrr": [], "recall": [], "ndcg": [] } } }
    results_db = {m: {L: {"hr": [], "mrr": [], "recall": [], "ndcg": []} for L in range(1, 6)} for m in ablation_modes}

    for idx, item in enumerate(eval_data):
        level = item["level"]
        query = item["query"]
        ground_truths = item["ground_truths"]
        
        print(f"\nMengevaluasi ([{idx+1}/{len(eval_data)}]) L{level}: {query[:40]}...")
        
        for mode in ablation_modes:
            # Mengakali memori Pipeline B, jika mode independen kita set session bebas
            session_id = f"eval_{mode}_{idx}" 
            payload = {
                "session_id": session_id,
                "message": query,
                "ablation_mode": mode
            }
            
            try:
                res = requests.post(API_URL, json=payload, timeout=60)
                if res.status_code == 200:
                    resp_data = res.json()
                    source_docs = resp_data.get("source_documents", [])
                    
                    retrieved_places = []
                    for doc in source_docs:
                        place_name = extract_place_nama_dari_source(doc)
                        retrieved_places.append(place_name)
                    
                    # Hitung skor matematika matematik
                    hr = calculate_hr_at_k(retrieved_places, ground_truths)
                    mrr = calculate_mrr_at_k(retrieved_places, ground_truths)
                    rec = calculate_recall_at_k(retrieved_places, ground_truths)
                    ndcg = calculate_ndcg_at_k(retrieved_places, ground_truths)
                    
                    results_db[mode][level]["hr"].append(hr)
                    results_db[mode][level]["mrr"].append(mrr)
                    results_db[mode][level]["recall"].append(rec)
                    results_db[mode][level]["ndcg"].append(ndcg)
                    
            except Exception as e:
                print(f"  Error pada mode '{mode}': {e}")
            
    # Mencetak Agregat Tabel
    print("\n\n" + "="*50)
    print("LAPORAN EVALUASI AKHIR (AVERAGE SCORES)")
    print("="*50)
    
    for level in range(1, 6):
        print(f"\n--- INTENT LEVEL {level} ---")
        print(f"{'Mode':<18} | {'HR@4':<6} | {'MRR@4':<6} | {'RCL@4':<6} | {'NDCG@4':<6}")
        print("-" * 50)
        for mode in ablation_modes:
            m_metrics = results_db[mode][level]
            if len(m_metrics["hr"]) == 0:
                continue
            
            avg_hr = sum(m_metrics["hr"]) / len(m_metrics["hr"])
            avg_mrr = sum(m_metrics["mrr"]) / len(m_metrics["mrr"])
            avg_rec = sum(m_metrics["recall"]) / len(m_metrics["recall"])
            avg_ndcg = sum(m_metrics["ndcg"]) / len(m_metrics["ndcg"])
            
            print(f"{mode:<18} | {avg_hr:.4f} | {avg_mrr:.4f} | {avg_rec:.4f} | {avg_ndcg:.4f}")

if __name__ == "__main__":
    main()
