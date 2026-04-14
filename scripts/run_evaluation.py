"""
Script Evaluasi Terpadu: Pipeline A, Baseline, Proposed, dan Pipeline B (CQR Multi-Turn).
Menghitung HR@K, MRR@K, Recall@K, dan NDCG@K.

Cara pakai:
  python scripts/run_evaluation.py                    # Evaluasi semua (single-turn + multi-turn)
  python scripts/run_evaluation.py --single-turn      # Hanya single-turn (A, Baseline, Proposed)
  python scripts/run_evaluation.py --multi-turn       # Hanya multi-turn (Pipeline B CQR)
"""

import json
import requests
import math
import time
import argparse
import os
import sys

# ============================================================
# KONFIGURASI
# ============================================================
API_URL = "http://localhost:8001/api/chat"
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE_DIR, "data")

SINGLE_TURN_GT_PATH = os.path.join(DATA_DIR, "eval_ground_truths.json")
MULTI_TURN_GT_PATH = os.path.join(DATA_DIR, "eval_pipeline_b.json")
RESULTS_OUTPUT_PATH = os.path.join(DATA_DIR, "eval_results.json")

# Mode ablasi yang diperiksa untuk single-turn
SINGLE_TURN_MODES = ["baseline", "pipeline_a_only", "proposed"]

# Mode ablasi yang diperiksa untuk multi-turn (Pipeline B)
# - baseline: CQR OFF + Baseline Retrieval (kontrol negatif)
# - pipeline_b_only: CQR ON + Baseline Retrieval (isolasi kontribusi CQR)
# - proposed: CQR ON + Pipeline A Retrieval (sistem penuh)
MULTI_TURN_MODES = ["baseline", "pipeline_b_only", "proposed"]

REQUEST_TIMEOUT = 180  # detik


# ============================================================
# FUNGSI METRIK (dipakai oleh kedua jenis evaluasi)
# ============================================================

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
    hits = set(retrieved_items).intersection(set(ground_truths))
    return len(hits) / len(set(ground_truths))

def calculate_ndcg_at_k(retrieved_items, ground_truths):
    """NDCG: DCG / Ideal DCG."""
    if not ground_truths:
        return 0.0
    
    dcg = 0.0
    for i, item in enumerate(retrieved_items):
        if item in ground_truths:
            dcg += 1.0 / math.log2(i + 2)
            
    idcg = 0.0
    ideal_hits = min(len(ground_truths), len(retrieved_items))
    for i in range(ideal_hits):
        idcg += 1.0 / math.log2(i + 2)
        
    return dcg / idcg if idcg > 0 else 0.0


# ============================================================
# FUNGSI UTILITAS
# ============================================================

def extract_place_name_from_source(doc_string):
    """Mengekstrak nama tempat dari string source_document API response."""
    # Format Baseline: "Source 1: Nama Tempat: Bukit Holbung Samosir\nKategori: Wisata..."
    lines = doc_string.split('\n')
    for line in lines:
        if "Nama Tempat:" in line:
            nama = line.split("Nama Tempat:")[1].strip()
            if ". Kategori" in nama:
                nama = nama.split(". Kategori")[0].strip()
            return nama
    # Format Proposed/Pipeline A: "🎯 PlaceName (Category) [Base Skor: ...]"
    if "🎯" in doc_string:
        try:
            after_emoji = doc_string.split("🎯")[1].strip()
            place_name = after_emoji.split("(")[0].strip()
            return place_name
        except:
            pass
    return "Tempat Tidak Diketahui"


def send_chat_request(session_id, message, ablation_mode):
    """Mengirim satu permintaan chat ke API dan mengembalikan response dict atau None."""
    payload = {
        "session_id": session_id,
        "message": message,
        "ablation_mode": ablation_mode
    }
    try:
        res = requests.post(API_URL, json=payload, timeout=REQUEST_TIMEOUT)
        if res.status_code == 200:
            return res.json()
        else:
            print(f"    ⚠ HTTP {res.status_code}: {res.text[:100]}")
            return None
    except Exception as e:
        print(f"    ❌ Request error: {e}")
        return None


def extract_retrieved_places(response_data):
    """Mengekstrak daftar nama tempat dari response API."""
    source_docs = response_data.get("source_documents", [])
    return [extract_place_name_from_source(doc) for doc in source_docs]


def compute_all_metrics(retrieved_places, ground_truths):
    """Menghitung semua 4 metrik sekaligus dan mengembalikan dict."""
    return {
        "hr": calculate_hr_at_k(retrieved_places, ground_truths),
        "mrr": calculate_mrr_at_k(retrieved_places, ground_truths),
        "recall": calculate_recall_at_k(retrieved_places, ground_truths),
        "ndcg": calculate_ndcg_at_k(retrieved_places, ground_truths),
    }


# ============================================================
# BAGIAN 1: EVALUASI SINGLE-TURN (Pipeline A, Baseline, Proposed)
# ============================================================

def run_single_turn_evaluation():
    """Menjalankan evaluasi single-turn dari eval_ground_truths.json."""
    print("\n" + "=" * 60)
    print("BAGIAN 1: EVALUASI SINGLE-TURN (Baseline / Pipeline A / Proposed)")
    print("=" * 60)
    
    try:
        with open(SINGLE_TURN_GT_PATH, 'r', encoding='utf-8') as f:
            data = json.load(f)
    except FileNotFoundError:
        print(f"❌ File tidak ditemukan: {SINGLE_TURN_GT_PATH}")
        return None
    
    eval_data = [d for d in data if isinstance(d.get("ground_truths"), list) and len(d["ground_truths"]) > 0]
    
    if not eval_data:
        print("❌ Tidak ada data evaluasi yang valid!")
        return None
    
    print(f"📊 Ditemukan {len(eval_data)} kueri siap evaluasi.\n")
    
    # Struktur: { mode: { level: { "hr": [], "mrr": [], "recall": [], "ndcg": [] } } }
    results_db = {
        m: {L: {"hr": [], "mrr": [], "recall": [], "ndcg": []} for L in range(1, 6)} 
        for m in SINGLE_TURN_MODES
    }

    for idx, item in enumerate(eval_data):
        level = item["level"]
        query = item["query"]
        ground_truths = item["ground_truths"]
        
        print(f"  [{idx+1}/{len(eval_data)}] L{level}: {query[:50]}...")
        
        for mode in SINGLE_TURN_MODES:
            session_id = f"eval_st_{mode}_{idx}_{int(time.time())}"
            resp = send_chat_request(session_id, query, mode)
            
            if resp:
                retrieved = extract_retrieved_places(resp)
                metrics = compute_all_metrics(retrieved, ground_truths)
                
                for metric_name, val in metrics.items():
                    results_db[mode][level][metric_name].append(val)
                    
                print(f"    {mode:18s} → HR={metrics['hr']:.1f} MRR={metrics['mrr']:.3f} RCL={metrics['recall']:.3f} NDCG={metrics['ndcg']:.3f}  |  Retrieved: {retrieved[:3]}")
            else:
                print(f"    {mode:18s} → GAGAL")
    
    return results_db


# ============================================================
# BAGIAN 2: EVALUASI MULTI-TURN (Pipeline B — CQR)
# ============================================================

def run_multi_turn_evaluation():
    """Menjalankan evaluasi multi-turn dari eval_pipeline_b.json."""
    print("\n" + "=" * 60)
    print("BAGIAN 2: EVALUASI MULTI-TURN / PIPELINE B (CQR)")
    print("=" * 60)
    
    try:
        with open(MULTI_TURN_GT_PATH, 'r', encoding='utf-8') as f:
            data = json.load(f)
    except FileNotFoundError:
        print(f"❌ File tidak ditemukan: {MULTI_TURN_GT_PATH}")
        return None
    
    scenarios = data.get("scenarios", [])
    if not scenarios:
        print("❌ Tidak ada skenario yang ditemukan!")
        return None
    
    print(f"📊 Ditemukan {len(scenarios)} skenario multi-turn.\n")
    
    # Struktur: { mode: { scenario_id: { metrics + details } } }
    results_db = {m: {} for m in MULTI_TURN_MODES}
    
    for sc_idx, scenario in enumerate(scenarios):
        sc_id = scenario["id"]
        sc_name = scenario["name"]
        turns = scenario["turns"]
        eval_turn = scenario["eval_turn"]
        ground_truths = scenario["ground_truths"]
        expected_intents = scenario.get("expected_standalone_intents", "")
        
        print(f"\n{'─' * 50}")
        print(f"📋 Skenario {sc_idx+1}: {sc_name}")
        print(f"   Jumlah Turn: {len(turns)} | Evaluasi pada Turn: {eval_turn}")
        print(f"   Ground Truths: {ground_truths}")
        print(f"   Expected Intents: {expected_intents[:80]}...")
        print(f"{'─' * 50}")
        
        for mode in MULTI_TURN_MODES:
            # Setiap mode mendapat session_id unik agar histori tidak tercampur
            session_id = f"eval_mt_{sc_id}_{mode}_{int(time.time())}"
            
            print(f"\n  🔧 Mode: {mode}")
            
            final_response = None
            standalone_query_returned = ""
            
            for turn in turns:
                turn_num = turn["turn"]
                message = turn["message"]
                is_eval_turn = (turn_num == eval_turn)
                
                marker = "⭐ EVAL" if is_eval_turn else f"  T{turn_num}"
                print(f"    {marker}: {message[:60]}...")
                
                resp = send_chat_request(session_id, message, mode)
                
                if resp is None:
                    print(f"        ❌ Gagal mendapatkan respons!")
                    if is_eval_turn:
                        break
                    continue
                
                # Tampilkan standalone_query yang dikembalikan CQR
                sq = resp.get("standalone_query", "")
                if sq:
                    print(f"        CQR → \"{sq[:80]}...\"")
                
                if is_eval_turn:
                    final_response = resp
                    standalone_query_returned = sq
                    
                # Jeda kecil antar turn agar tidak membanjiri server
                time.sleep(0.5)
            
            # Hitung metrik dari Turn Terakhir
            if final_response:
                retrieved = extract_retrieved_places(final_response)
                metrics = compute_all_metrics(retrieved, ground_truths)
                
                results_db[mode][sc_id] = {
                    "scenario_name": sc_name,
                    "standalone_query": standalone_query_returned,
                    "retrieved_places": retrieved,
                    "ground_truths": ground_truths,
                    **metrics
                }
                
                print(f"\n    📊 Hasil {mode}:")
                print(f"       HR={metrics['hr']:.1f}  MRR={metrics['mrr']:.3f}  Recall={metrics['recall']:.3f}  NDCG={metrics['ndcg']:.3f}")
                print(f"       Retrieved: {retrieved[:4]}")
                print(f"       CQR Output: \"{standalone_query_returned[:100]}\"")
            else:
                results_db[mode][sc_id] = {
                    "scenario_name": sc_name,
                    "error": "Tidak mendapat respons pada turn evaluasi"
                }
                print(f"\n    ❌ {mode}: Tidak ada respons untuk dievaluasi.")
    
    return results_db


# ============================================================
# DISPLAY & SAVE
# ============================================================

def print_single_turn_report(results_db):
    """Mencetak tabel laporan evaluasi single-turn."""
    if not results_db:
        return
    
    print("\n\n" + "=" * 60)
    print("LAPORAN EVALUASI SINGLE-TURN (RATA-RATA PER LEVEL)")
    print("=" * 60)
    
    for level in range(1, 6):
        print(f"\n--- INTENT LEVEL {level} ---")
        print(f"{'Mode':<18} | {'HR@4':<6} | {'MRR@4':<6} | {'RCL@4':<6} | {'NDCG@4':<6}")
        print("-" * 55)
        for mode in SINGLE_TURN_MODES:
            m = results_db[mode][level]
            if len(m["hr"]) == 0:
                continue
            avg_hr = sum(m["hr"]) / len(m["hr"])
            avg_mrr = sum(m["mrr"]) / len(m["mrr"])
            avg_rec = sum(m["recall"]) / len(m["recall"])
            avg_ndcg = sum(m["ndcg"]) / len(m["ndcg"])
            print(f"{mode:<18} | {avg_hr:.4f} | {avg_mrr:.4f} | {avg_rec:.4f} | {avg_ndcg:.4f}")


def print_multi_turn_report(results_db):
    """Mencetak tabel laporan evaluasi multi-turn Pipeline B."""
    if not results_db:
        return
    
    print("\n\n" + "=" * 60)
    print("LAPORAN EVALUASI MULTI-TURN / PIPELINE B (CQR)")
    print("=" * 60)
    
    # Kumpulkan semua scenario_id
    all_scenario_ids = set()
    for mode in MULTI_TURN_MODES:
        all_scenario_ids.update(results_db[mode].keys())
    
    for sc_id in sorted(all_scenario_ids):
        first_entry = None
        for mode in MULTI_TURN_MODES:
            if sc_id in results_db[mode] and "scenario_name" in results_db[mode][sc_id]:
                first_entry = results_db[mode][sc_id]
                break
        
        sc_name = first_entry["scenario_name"] if first_entry else sc_id
        print(f"\n--- {sc_name} ---")
        print(f"{'Mode':<18} | {'HR@4':<6} | {'MRR@4':<6} | {'RCL@4':<6} | {'NDCG@4':<6} | CQR Standalone Query")
        print("-" * 100)
        
        for mode in MULTI_TURN_MODES:
            entry = results_db[mode].get(sc_id, {})
            if "error" in entry:
                print(f"{mode:<18} | {'ERR':<6} | {'ERR':<6} | {'ERR':<6} | {'ERR':<6} | {entry['error']}")
            elif "hr" in entry:
                sq = entry.get("standalone_query", "N/A")[:60]
                print(f"{mode:<18} | {entry['hr']:.4f} | {entry['mrr']:.4f} | {entry['recall']:.4f} | {entry['ndcg']:.4f} | \"{sq}...\"")
    
    # Cetak rata-rata keseluruhan per mode
    print(f"\n--- RATA-RATA KESELURUHAN ---")
    print(f"{'Mode':<18} | {'HR@4':<6} | {'MRR@4':<6} | {'RCL@4':<6} | {'NDCG@4':<6}")
    print("-" * 55)
    for mode in MULTI_TURN_MODES:
        hrs, mrrs, recs, ndcgs = [], [], [], []
        for sc_id, entry in results_db[mode].items():
            if "hr" in entry:
                hrs.append(entry["hr"])
                mrrs.append(entry["mrr"])
                recs.append(entry["recall"])
                ndcgs.append(entry["ndcg"])
        if hrs:
            print(f"{mode:<18} | {sum(hrs)/len(hrs):.4f} | {sum(mrrs)/len(mrrs):.4f} | {sum(recs)/len(recs):.4f} | {sum(ndcgs)/len(ndcgs):.4f}")


def save_results(single_turn_results, multi_turn_results):
    """Menyimpan semua hasil ke file JSON."""
    output = {}
    if single_turn_results:
        output["single_turn"] = single_turn_results
    if multi_turn_results:
        output["multi_turn"] = multi_turn_results
    
    with open(RESULTS_OUTPUT_PATH, 'w', encoding='utf-8') as f:
        json.dump(output, f, indent=2, ensure_ascii=False)
    print(f"\n💾 Hasil evaluasi disimpan di: {RESULTS_OUTPUT_PATH}")


# ============================================================
# ENTRY POINT
# ============================================================

def main():
    parser = argparse.ArgumentParser(description="Evaluasi RAG Pipeline Terpadu")
    parser.add_argument("--single-turn", action="store_true", help="Hanya evaluasi single-turn (A, Baseline, Proposed)")
    parser.add_argument("--multi-turn", action="store_true", help="Hanya evaluasi multi-turn (Pipeline B CQR)")
    args = parser.parse_args()
    
    # Default: jalankan keduanya jika tidak ada flag
    run_st = True
    run_mt = True
    if args.single_turn or args.multi_turn:
        run_st = args.single_turn
        run_mt = args.multi_turn
    
    st_results = None
    mt_results = None
    
    if run_st:
        st_results = run_single_turn_evaluation()
        print_single_turn_report(st_results)
    
    if run_mt:
        mt_results = run_multi_turn_evaluation()
        print_multi_turn_report(mt_results)
    
    save_results(st_results, mt_results)
    
    print("\n✅ Evaluasi selesai.")


if __name__ == "__main__":
    main()
