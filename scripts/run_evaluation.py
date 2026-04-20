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
# Output paths will be generated dynamically in main()

# Mode ablasi yang diperiksa untuk single-turn
SINGLE_TURN_MODES = ["baseline", "pipeline_a_only", "proposed"]

# Mode ablasi yang diperiksa untuk multi-turn (Pipeline B)
# - baseline: CQR OFF + Baseline Retrieval (kontrol negatif)
# - pipeline_b_only: CQR ON + Baseline Retrieval (isolasi kontribusi CQR)
# - proposed: CQR ON + Pipeline A Retrieval (sistem penuh)
MULTI_TURN_MODES = ["baseline", "pipeline_b_only", "proposed"]

REQUEST_TIMEOUT = 1000  # detik (Pipeline A/Proposed bisa lambat karena multi-LLM call)


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
    # Format Baseline: "Source 1: Nama Tempat: Bukit Holbung Samosir. Kategori: Wisata..."
    if "Nama Tempat:" in doc_string:
        try:
            nama = doc_string.split("Nama Tempat:")[1].strip()
            # Potong di separator berikutnya
            for sep in [". Kategori", ".\n", "\n"]:
                if sep in nama:
                    nama = nama.split(sep)[0].strip()
                    break
            # Bersihkan titik di akhir
            return nama.rstrip('.')
        except:
            pass
    # Format Proposed/Pipeline A: "🎯 PlaceName (Category) [Base Skor: ...]"
    if "🎯" in doc_string:
        try:
            after_emoji = doc_string.split("🎯")[1].strip()
            place_name = after_emoji.split("(")[0].strip()
            return place_name
        except:
            pass
    # Format place_name di metadata
    if "place_name" in doc_string:
        try:
            nama = doc_string.split("place_name")[1]
            nama = nama.split(":")[1].strip().strip('"').strip("'")
            for sep in [",", "\n", "}"]:
                if sep in nama:
                    nama = nama.split(sep)[0].strip().strip('"')
                    break
            return nama
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
    except requests.exceptions.ReadTimeout:
        print(f"    ⏱ Timeout ({REQUEST_TIMEOUT}s) untuk mode '{ablation_mode}'")
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

DEBUG_RAW_DOCS = False  # Matikan untuk eksekusi real


# ============================================================
# BAGIAN 1: EVALUASI SINGLE-TURN (Pipeline A, Baseline, Proposed)
# ============================================================

def run_single_turn_evaluation(limit=0):
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
        
    if limit > 0:
        eval_data = eval_data[:limit]
        print(f"📊 Ditemukan {len(data)} kueri, DIBATASI HANYA {limit} kueri untuk tes.\n")
    else:
        print(f"📊 Ditemukan {len(eval_data)} kueri siap evaluasi.\n")
    
    # Struktur: { mode: { level: { "hr": [], "mrr": [], "recall": [], "ndcg": [] } } }
    results_db = {
        m: {L: {"hr": [], "mrr": [], "recall": [], "ndcg": []} for L in range(1, 6)} 
        for m in SINGLE_TURN_MODES
    }
    results_db["meta"] = {m: {"json_fails": 0, "total_lrr_calls": 0} for m in SINGLE_TURN_MODES}

    for idx, item in enumerate(eval_data):
        level = item["level"]
        query = item["query"]
        ground_truths = item["ground_truths"]
        
        print(f"  [{idx+1}/{len(eval_data)}] L{level}: {query[:50]}...")
        
        for mode in SINGLE_TURN_MODES:
            session_id = f"eval_st_{mode}_{idx}_{int(time.time())}"
            resp = send_chat_request(session_id, query, mode)
            
            if resp:
                # Debug: cetak raw source_documents sekali saja untuk lihat formatnya
                if DEBUG_RAW_DOCS and idx == 0:
                    raw_docs = resp.get("source_documents", [])
                    print(f"\n    [DEBUG] Raw source_documents for mode '{mode}':")
                    for di, rd in enumerate(raw_docs[:2]):
                        print(f"      Doc {di}: {rd[:150]}...")
                    print()
                
                retrieved = extract_retrieved_places(resp)
                metrics = compute_all_metrics(retrieved, ground_truths)
                
                # Track Format Compliance errors
                fails = resp.get("json_parse_fails", 0)
                results_db["meta"][mode]["json_fails"] += fails
                if mode != "baseline":
                    results_db["meta"][mode]["total_lrr_calls"] += 5 # top_k=5 in API
                
                for metric_name, val in metrics.items():
                    results_db[mode][level][metric_name].append(val)
                    
                print(f"    {mode:18s} → HR={metrics['hr']:.1f} MRR={metrics['mrr']:.3f} RCL={metrics['recall']:.3f} NDCG={metrics['ndcg']:.3f} | Fails={fails}  |  Retrieved: {retrieved[:5]}")
            else:
                print(f"    {mode:18s} → GAGAL")
    
    return results_db


# ============================================================
# BAGIAN 2: EVALUASI MULTI-TURN (Pipeline B — CQR)
# ============================================================

def run_multi_turn_evaluation(limit=0):
    """Menjalankan evaluasi multi-turn dari eval_pipeline_b.json.

    New Checkpoint Evaluation Schema:
      - eval_turn: array of integers (mis. [1, 2, 3])
      - ground_truths: per-turn (di dalam setiap turn dict)
      - expected_standalone: per-turn

    Aturan:
      1. Hanya evaluasi turn yang ada di eval_turn array
      2. Chit-chat (is_search_required=False ATAU source_documents kosong) → skip metrik
      3. Agregasi hanya dari turn yang benar-benar dihitung
    """
    print("\n" + "=" * 60)
    print("BAGIAN 2: EVALUASI MULTI-TURN / PIPELINE B (CQR)")
    print("=" * 60)

    try:
        with open(MULTI_TURN_GT_PATH, 'r', encoding='utf-8') as f:
            data = json.load(f)
    except FileNotFoundError:
        print(f"❌ File tidak ditemukan: {MULTI_TURN_GT_PATH}")
        return None

    scenarios = data if isinstance(data, list) else data.get("scenarios", [])
    if not scenarios:
        print("❌ Tidak ada skenario yang ditemukan!")
        return None

    if limit > 0:
        scenarios = scenarios[:limit]
        print(f"📊 DIBATASI HANYA {limit} skenario multi-turn untuk tes.\n")
    else:
        print(f"📊 Ditemukan {len(scenarios)} skenario multi-turn.\n")

    results_db = {m: {} for m in MULTI_TURN_MODES}

    for sc_idx, scenario in enumerate(scenarios):
        sc_id = scenario["id"]
        sc_name = scenario.get("name", "Unnamed")
        turns = scenario["turns"]
        raw_eval_turn = scenario.get("eval_turn", [])

        if isinstance(raw_eval_turn, int):
            eval_turns = [raw_eval_turn]
        elif isinstance(raw_eval_turn, list):
            eval_turns = [int(t) for t in raw_eval_turn]
        else:
            print(f"  ⚠ eval_turn tidak valid: {raw_eval_turn},lewatkan skenario ini.")
            continue

        turn_map = {t["turn"]: t for t in turns}

        print(f"\n{'─' * 50}")
        print(f"📋 Skenario {sc_idx+1}: {sc_name}")
        print(f"   Jumlah Turn: {len(turns)} | Eval Turn: {eval_turns}")
        print(f"{'─' * 50}")

        for mode in MULTI_TURN_MODES:
            session_id = f"eval_mt_{sc_id}_{mode}_{int(time.time())}"

            print(f"\n  🔧 Mode: {mode}")

            eval_results = []
            standalone_queries = []

            for turn in turns:
                turn_num = turn["turn"]
                message = turn["message"]
                is_eval_turn = (turn_num in eval_turns)
                expected_standalone = turn.get("expected_standalone", "")
                turn_ground_truths = turn.get("ground_truths", [])

                marker = "⭐ EVAL" if is_eval_turn else f"  T{turn_num}"
                print(f"    {marker}: {message[:60]}...")

                resp = send_chat_request(session_id, message, mode)

                if resp is None:
                    print(f"        ❌ Gagal mendapat respons!")
                    if is_eval_turn:
                        eval_results.append({
                            "turn": turn_num,
                            "error": "Tidak respons"
                        })
                    continue

                sq = resp.get("standalone_query", "")
                source_docs = resp.get("source_documents", [])
                is_chitchat = False

                if is_eval_turn:
                    if sq and source_docs:
                        is_search_required = True
                    elif not source_docs:
                        is_search_required = False
                    else:
                        is_search_required = True

                    if not is_search_required or not source_docs:
                        is_chitchat = True
                        print(f"        [INFO] Turn {turn_num} dilewati: Chit-chat terdeteksi (is_search_required=False)")
                        eval_results.append({
                            "turn": turn_num,
                            "chitchat": True,
                            "standalone_query": sq,
                            "expected_standalone": expected_standalone,
                        })
                    else:
                        if sq:
                            standalone_queries.append({"turn": turn_num, "query": sq})

                        retrieved = extract_retrieved_places(resp)
                        metrics = compute_all_metrics(retrieved, turn_ground_truths)

                        eval_results.append({
                            "turn": turn_num,
                            "chitchat": False,
                            "standalone_query": sq,
                            "expected_standalone": expected_standalone,
                            "retrieved_places": retrieved,
                            "ground_truths": turn_ground_truths,
                            **metrics,
                        })

                        hr = metrics["hr"]
                        mrr = metrics["mrr"]
                        recall = metrics["recall"]
                        ndcg_val = metrics["ndcg"]
                        print(f"        📊 Turn {turn_num}: HR={hr:.1f} MRR={mrr:.3f} RCL={recall:.3f} NDCG={ndcg_val:.3f}")
                        print(f"           Retrieved: {retrieved[:4]}")

                time.sleep(0.3)

            # Filter chit-chat & abaikan turn yang mengalami error (tidak memiliki metrik HR)
            valid_results = [r for r in eval_results if not r.get("chitchat", False) and "hr" in r]

            if valid_results:
                count = len(valid_results)
                avg_hr = sum(r["hr"] for r in valid_results) / count
                avg_mrr = sum(r["mrr"] for r in valid_results) / count
                avg_recall = sum(r["recall"] for r in valid_results) / count
                avg_ndcg = sum(r["ndcg"] for r in valid_results) / count

                chitchat_skips = sum(1 for r in eval_results if r.get("chitchat"))

                results_db[mode][sc_id] = {
                    "scenario_name": sc_name,
                    "eval_turns": eval_turns,
                    "valid_turns_count": count,
                    "avg_hr": avg_hr,
                    "avg_mrr": avg_mrr,
                    "avg_recall": avg_recall,
                    "avg_ndcg": avg_ndcg,
                    "turn_details": eval_results,
                    "chitchat_skips": chitchat_skips,
                }

                note = f" | {chitchat_skips} chitchat skipped" if chitchat_skips > 0 else ""
                print(f"\n    📊 Agregasi {mode}{note}:"
                      f"  HR={avg_hr:.4f}  MRR={avg_mrr:.4f}  Recall={avg_recall:.4f}  NDCG={avg_ndcg:.4f}")

            elif eval_results and all(r.get("chitchat") for r in eval_results):
                results_db[mode][sc_id] = {
                    "scenario_name": sc_name,
                    "eval_turns": eval_turns,
                    "status": "all_chitchat",
                    "turn_details": eval_results,
                    "chitchat_skips": len(eval_results),
                }
                print(f"\n    💬 {mode}: Semua eval turns = chit-chat.")
            else:
                results_db[mode][sc_id] = {
                    "scenario_name": sc_name,
                    "eval_turns": eval_turns,
                    "error": "Tidak ada respons valid",
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
        print(f"{'Mode':<18} | {'HR@5':<6} | {'MRR@5':<6} | {'RCL@5':<6} | {'NDCG@5':<6}")
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

    print(f"\n--- FORMAT COMPLIANCE RATE (JSON PARSING) ---")
    for mode in SINGLE_TURN_MODES:
        if mode == "baseline": continue
        fails = results_db.get("meta", {}).get(mode, {}).get("json_fails", 0)
        total = results_db.get("meta", {}).get(mode, {}).get("total_lrr_calls", 0)
        if total == 0: 
            print(f"{mode:<18} | N/A")
            continue
        rate = ((total - fails) / total) * 100
        print(f"{mode:<18} | JSON Fails: {fails} / {total} candidate ops | Compliance Rate: {rate:.1f}%")


def print_multi_turn_report(results_db):
    """Mencetak tabel laporan evaluasi multi-turn Pipeline B."""
    if not results_db:
        return
    
    print("\n\n" + "=" * 60)
    print("LAPORAN EVALUASI MULTI-TURN / PIPELINE B (CQR)")
    print("=" * 60)
    
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
        print(f"{'Mode':<18} | {'HR@5':<6} | {'MRR@5':<6} | {'RCL@5':<6} | {'NDCG@5':<6} | Valid Turns")
        print("-" * 90)
        
        for mode in MULTI_TURN_MODES:
            entry = results_db[mode].get(sc_id, {})
            if "error" in entry:
                print(f"{mode:<18} | {'ERR':<6} | {'ERR':<6} | {'ERR':<6} | {'ERR':<6} | {entry['error']}")
            elif "avg_hr" in entry:
                valid = entry.get("valid_turns_count", 0)
                skips = entry.get("chitchat_skips", 0)
                note = f"{valid} valid, {skips} skip"
                print(f"{mode:<18} | {entry['avg_hr']:.4f} | {entry['avg_mrr']:.4f} | {entry['avg_recall']:.4f} | {entry['avg_ndcg']:.4f} | {note}")
            elif entry.get("status") == "all_chitchat":
                skips = entry.get("chitchat_skips", 0)
                print(f"{mode:<18} | {'----':<6} | {'----':<6} | {'----':<6} | {'----':<6} | All chitchat ({skips})")
    
    print(f"\n--- RATA-RATA KESELURUHAN ---")
    print(f"{'Mode':<18} | {'HR@5':<6} | {'MRR@5':<6} | {'RCL@5':<6} | {'NDCG@5':<6}")
    print("-" * 55)
    for mode in MULTI_TURN_MODES:
        hrs, mrrs, recs, ndcgs = [], [], [], []
        for sc_id, entry in results_db[mode].items():
            if "avg_hr" in entry:
                hrs.append(entry["avg_hr"])
                mrrs.append(entry["avg_mrr"])
                recs.append(entry["avg_recall"])
                ndcgs.append(entry["avg_ndcg"])
        if hrs:
            print(f"{mode:<18} | {sum(hrs)/len(hrs):.4f} | {sum(mrrs)/len(mrrs):.4f} | {sum(recs)/len(recs):.4f} | {sum(ndcgs)/len(ndcgs):.4f}")


def save_results(single_turn_results, multi_turn_results, output_path):
    """Menyimpan semua hasil ke file JSON."""
    output = {}
    if single_turn_results:
        output["single_turn"] = single_turn_results
    if multi_turn_results:
        output["multi_turn"] = multi_turn_results
    
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(output, f, indent=2, ensure_ascii=False)


# ============================================================
# ENTRY POINT
# ============================================================

class Tee:
    """Menulis output ke console DAN file secara bersamaan."""
    def __init__(self, filepath, mode='w'):
        self.file = open(filepath, mode, encoding='utf-8')
        self.stdout = sys.stdout
    
    def write(self, data):
        self.stdout.write(data)
        self.file.write(data)
    
    def flush(self):
        self.stdout.flush()
        self.file.flush()
    
    def close(self):
        self.file.close()
        sys.stdout = self.stdout


def main():
    global SINGLE_TURN_MODES, MULTI_TURN_MODES
    parser = argparse.ArgumentParser(description="Evaluasi RAG Pipeline Terpadu")
    parser.add_argument("--single-turn", action="store_true", help="Hanya evaluasi single-turn (A, Baseline, Proposed)")
    parser.add_argument("--multi-turn", action="store_true", help="Hanya evaluasi multi-turn (Pipeline B CQR)")
    parser.add_argument("--limit", type=int, default=0, help="Batasi jumlah kueri (0 = semua). Gunakan --limit 5 untuk tes cepat.")
    parser.add_argument("--mode", type=str, help="Hanya evaluasi mode spesifik (misal: 'baseline', 'pipeline_a_only', 'proposed')")
    args = parser.parse_args()
    
    file_suffix = ""
    # Filter mode berdasarkan argumen
    if args.mode:
        if args.mode in SINGLE_TURN_MODES:
            SINGLE_TURN_MODES = [args.mode]
        if args.mode in MULTI_TURN_MODES:
            MULTI_TURN_MODES = [args.mode]
        file_suffix += f"_{args.mode}"
    else:
        file_suffix += "_all"
        
    if args.single_turn:
        file_suffix += "_ST"
    if args.multi_turn:
        file_suffix += "_MT"
        
    results_path = os.path.join(DATA_DIR, f"eval_results{file_suffix}.json")
    report_path = os.path.join(DATA_DIR, f"eval_report{file_suffix}.txt")
    
    # Redirect semua output ke console + file
    from datetime import datetime
    tee = Tee(report_path, mode='w')
    sys.stdout = tee
    
    print(f"Evaluasi dimulai: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Laporan teks disimpan ke: {report_path}")
    print(f"Data JSON di: {results_path}")
    
    # Default: jalankan keduanya jika tidak ada flag
    run_st = True
    run_mt = True
    if args.single_turn or args.multi_turn:
        run_st = args.single_turn
        run_mt = args.multi_turn
    
    st_results = None
    mt_results = None
    
    if run_st:
        st_results = run_single_turn_evaluation(limit=args.limit)
        print_single_turn_report(st_results)
    
    if run_mt:
        mt_results = run_multi_turn_evaluation(limit=args.limit)
        print_multi_turn_report(mt_results)
    
    save_results(st_results, mt_results, results_path)
    
    print(f"\nEvaluasi selesai: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Laporan teks: {report_path}")
    print(f"Data JSON: {results_path}")
    
    tee.close()


if __name__ == "__main__":
    main()
