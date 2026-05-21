"""
debug_ier_pipeline_a.py

Menguji IER (Intent & Entity Recognition via CA-IER) untuk Pipeline A:
- Single-turn queries TANPA chat history (ablation_mode = 'pipeline_a_only')
- Memvalidasi: standalone_query, is_search_required, location, 3 dimensi IER
- Menampilkan hasil dimension_aware_search dari ChromaDB (top-5 kandidat)
  sehingga kita bisa melihat apakah IER menghasilkan query retrieval yang relevan.

Jalankan dari root direktori proyek:
    python scripts/debug_ier_pipeline_a.py
"""
import sys
import os
import json

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, BASE_DIR)
sys.path.insert(0, os.path.join(BASE_DIR, "src"))

from modules.retriever import get_ca_ier, dimension_aware_search
from modules.llm_loader import load_model

# ─────────────────────────────────────────────────
# Test cases Pipeline A: murni single-turn, tanpa riwayat
# Setiap entri: (label, query, notes)
# ─────────────────────────────────────────────────
TEST_CASES = [
    (
        "A-1: Rekomendasi Wisata Alam",
        "Rekomendasikan tempat wisata alam yang sejuk di sekitar Danau Toba",
        "Semua 3 dimensi seharusnya terisi"
    ),
    (
        "A-2: Kuliner Spesifik Lokasi",
        "Carikan restoran seafood yang enak di Parapat",
        "location='Parapat', landscape dan activities terisi, atmosphere='Enak'"
    ),
    (
        "A-3: Pertanyaan Tanpa Lokasi",
        "Tempat kemping paling bagus di Sumatera Utara buat keluarga",
        "location kosong, activities='Kemping', atmosphere='Keluarga'"
    ),
    (
        "A-4: Hanya Chit-Chat (is_search_required=False)",
        "Hai, siapa kamu?",
        "is_search_required=False, semua dimensi kosong"
    ),
    (
        "A-5: Pertanyaan Spesifik Fasilitas",
        "Hotel bintang 3 yang ada kolam renangnya di Samosir",
        "location='Samosir', landscape='Hotel, kolam renang'"
    ),
    (
        "A-6: Wisata Budaya dan Sejarah",
        "Ada museum atau situs budaya Batak yang bisa dikunjungi?",
        "landscape='Museum, situs budaya Batak', activities='Wisata budaya'"
    ),
    (
        "A-7: Query Ambigu (tanpa kata kunci jelas)",
        "Mau liburan santai minggu depan",
        "is_search_required=True, dimensi minimal—model harus inferensi atmosphere='Santai'"
    ),
]

CHROMA_PATH = os.path.join(BASE_DIR, "data", "chroma_db_uadc")
EMBEDDING_MODEL = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"

def load_vector_db():
    try:
        from langchain_chroma import Chroma
        from langchain_huggingface import HuggingFaceEmbeddings
        embedding_model = HuggingFaceEmbeddings(
            model_name=EMBEDDING_MODEL,
            model_kwargs={'device': 'cpu', 'local_files_only': False},
            encode_kwargs={'normalize_embeddings': True}
        )
        db = Chroma(persist_directory=CHROMA_PATH, embedding_function=embedding_model)
        print(f"  ✅ ChromaDB dimuat dari: {CHROMA_PATH}")
        return db
    except Exception as e:
        print(f"  ⚠️  ChromaDB tidak tersedia: {e}")
        print("  → Retrieval test akan dilewati, hanya IER yang diuji.")
        return None

def print_separator(char="─", width=60):
    print(char * width)

def run_ier_tests(vector_db):
    passed = 0
    failed = 0
    results_summary = []

    for idx, (label, query, expectation) in enumerate(TEST_CASES, 1):
        print_separator()
        print(f"\n[Test {idx}] {label}")
        print(f"  Query       : {query}")
        print(f"  Ekspektasi  : {expectation}")

        # Pipeline A: kirim history kosong (tidak ada riwayat)
        ca_ier = get_ca_ier(query, chat_history=[])

        print(f"\n  📤 Hasil IER:")
        print(f"     standalone_query    : {ca_ier.standalone_query}")
        print(f"     is_search_required  : {ca_ier.is_search_required}")
        print(f"     location            : '{ca_ier.location}'")
        print(f"     expected_landscape  : '{ca_ier.expected_landscape_content}'")
        print(f"     expected_activities : '{ca_ier.expected_activities}'")
        print(f"     expected_atmosphere : '{ca_ier.expected_atmosphere}'")

        # Quick sanity check
        issues = []
        if not ca_ier.standalone_query.strip():
            issues.append("standalone_query kosong!")
        if ca_ier.is_search_required and not any([
            ca_ier.expected_landscape_content,
            ca_ier.expected_activities,
            ca_ier.expected_atmosphere,
        ]):
            issues.append("is_search_required=True tapi SEMUA dimensi kosong!")

        # Retrieval test (hanya jika search diperlukan dan DB tersedia)
        if ca_ier.is_search_required and vector_db is not None:
            print(f"\n  🔍 Menjalankan dimension_aware_search...")
            try:
                top_results = dimension_aware_search(
                    vector_db=vector_db,
                    intent_dimensions=ca_ier,
                    w_lan=1.0, w_act=1.0, w_atm=1.0,
                    top_k=5
                )
                if top_results:
                    print(f"  Top {len(top_results)} kandidat dari ChromaDB:")
                    for i, r in enumerate(top_results, 1):
                        print(f"     {i}. {r['place_name']} ({r['category']}) "
                              f"[skor={r['total_score']:.4f}]")
                else:
                    issues.append("Retrieval mengembalikan 0 hasil!")
                    print("  ⚠️  Tidak ada hasil dari ChromaDB!")
            except Exception as e:
                issues.append(f"Retrieval error: {e}")
                print(f"  ❌ Retrieval gagal: {e}")
        elif not ca_ier.is_search_required:
            print("  ℹ️  is_search_required=False → retrieval dilewati (benar untuk chit-chat)")

        # Status
        if issues:
            status = "❌ FAIL"
            failed += 1
            print(f"\n  ⚠️  Masalah ditemukan:")
            for issue in issues:
                print(f"     - {issue}")
        else:
            status = "✅ PASS"
            passed += 1

        print(f"\n  Status: {status}")
        results_summary.append({
            "label": label,
            "query": query,
            "standalone_query": ca_ier.standalone_query,
            "is_search_required": ca_ier.is_search_required,
            "location": ca_ier.location,
            "landscape": ca_ier.expected_landscape_content,
            "activities": ca_ier.expected_activities,
            "atmosphere": ca_ier.expected_atmosphere,
            "issues": issues,
            "status": status,
        })

    print_separator("═")
    print(f"\n  RINGKASAN: {passed} PASSED, {failed} FAILED dari {len(TEST_CASES)} test cases")

    # Save detailed results
    out_path = os.path.join(BASE_DIR, "data", "debug_ier_pipeline_a_results.json")
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(results_summary, f, indent=2, ensure_ascii=False)
    print(f"  Detail hasil disimpan ke: {out_path}")
    print_separator("═")


if __name__ == "__main__":
    print("=" * 60)
    print("  Debug IER — Pipeline A (Single-Turn, No History)")
    print("=" * 60)

    print("\n[1/2] Memuat model LLM Qwen3...")
    load_model()
    print("  ✅ Model siap.\n")

    print("[2/2] Memuat ChromaDB untuk retrieval test...")
    vector_db = load_vector_db()

    print("\n" + "=" * 60)
    print("  Memulai Test Cases...")
    print("=" * 60)

    run_ier_tests(vector_db)
