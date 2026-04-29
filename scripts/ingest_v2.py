"""
ingest_v2.py
------------
Ingests data/entities_final.csv (produced by preprocess_entities.py)
into ChromaDB (chroma_db_baseline).

Speed optimizations vs original ingest-data.py:
  - Auto-detects GPU (CUDA) and uses it if available
  - Larger encode_batch_size on GPU (512 vs 32 on CPU)
  - Fast pandas vectorized Document construction (no iterrows)
  - Parallel text splitting via multiprocessing
  - Configurable CHROMA_BATCH_SIZE to avoid OOM on large datasets

Run locally (CPU):
  python scripts/ingest_v2.py

Run on GPU server:
  python scripts/ingest_v2.py
  (GPU is auto-detected; set FORCE_CPU=1 to override)
"""

import os
import shutil
import time
import multiprocessing
import pandas as pd
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_chroma import Chroma
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_core.documents import Document

# ─────────────────────────────────────────────────
# CONFIG
# ─────────────────────────────────────────────────
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE_DIR, "data")

CSV_FILE_PATH   = os.path.join(DATA_DIR, "entities_final.csv")
CHROMA_PATH     = os.path.join(DATA_DIR, "chroma_db_baseline")
EMBEDDING_MODEL = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"

CHUNK_SIZE    = 1000
CHUNK_OVERLAP = 200

# Tune these for your machine
FORCE_CPU         = os.environ.get("FORCE_CPU", "0") == "1"
CHROMA_BATCH_SIZE = int(os.environ.get("CHROMA_BATCH_SIZE", "1000"))  # raise on GPU server


# ─────────────────────────────────────────────────
# DEVICE DETECTION
# ─────────────────────────────────────────────────
def detect_device() -> tuple[str, int]:
    """Returns (device_str, encode_batch_size)."""
    if FORCE_CPU:
        print("   [Device] FORCE_CPU=1 → menggunakan CPU")
        return "cpu", 64

    try:
        import torch
        if torch.cuda.is_available():
            name = torch.cuda.get_device_name(0)
            vram = torch.cuda.get_device_properties(0).total_memory // (1024**2)
            print(f"   [Device] GPU terdeteksi: {name} ({vram} MB VRAM) → menggunakan CUDA")
            # Large encode batch: embedding model is small (~120 MB), VRAM headroom is generous
            batch = 512 if vram >= 6000 else 256
            return "cuda", batch
        else:
            print("   [Device] CUDA tidak tersedia → menggunakan CPU")
    except ImportError:
        print("   [Device] PyTorch tidak terinstall → menggunakan CPU")

    return "cpu", 64


# ─────────────────────────────────────────────────
# STEP 1: Load CSV → LangChain Documents (vectorized)
# ─────────────────────────────────────────────────
def load_documents(file_path: str) -> list[Document]:
    print(f"\n[1/4] Membaca data dari {file_path}...")
    t0 = time.time()

    df = pd.read_csv(file_path).fillna("")

    # Build page_content: prefer prebuilt description, fallback to minimal string
    has_desc = df["description"].str.strip().astype(bool)
    fallback  = (
        "Nama: " + df["place_name"] + ". " +
        "Kategori: " + df["category"] + ". " +
        "Alamat: " + df["address"] + "."
    )
    content = df["description"].where(has_desc, fallback)

    documents = [
        Document(
            page_content=c,
            metadata={
                "place_name":   pn,
                "category":     cat,
                "address":      addr,
                "city_regency": cr,
            },
        )
        for c, pn, cat, addr, cr in zip(
            content,
            df["place_name"],
            df["category"],
            df["address"],
            df["city_regency"],
        )
    ]

    print(f"   → {len(documents)} dokumen dimuat dalam {time.time()-t0:.1f}s")
    return documents


# ─────────────────────────────────────────────────
# STEP 2: Parallel chunking
# ─────────────────────────────────────────────────
def _split_batch(docs: list[Document]) -> list[Document]:
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=CHUNK_SIZE,
        chunk_overlap=CHUNK_OVERLAP,
        separators=["\n\n", "\n", ". ", " ", ""],
    )
    return splitter.split_documents(docs)


def split_documents(documents: list[Document]) -> list[Document]:
    print(f"\n[2/4] Memecah {len(documents)} dokumen menjadi chunks...")
    t0 = time.time()

    n_workers = max(1, min(multiprocessing.cpu_count() - 1, 8))
    chunk_size_per_worker = max(1, len(documents) // n_workers)

    # Split docs into sub-lists for each worker
    sub_lists = [
        documents[i : i + chunk_size_per_worker]
        for i in range(0, len(documents), chunk_size_per_worker)
    ]

    if n_workers > 1:
        print(f"   Menggunakan {n_workers} worker proses...")
        with multiprocessing.Pool(n_workers) as pool:
            results = pool.map(_split_batch, sub_lists)
        chunks = [c for batch in results for c in batch]
    else:
        chunks = _split_batch(documents)

    print(f"   → {len(chunks)} chunks dalam {time.time()-t0:.1f}s")
    return chunks


# ─────────────────────────────────────────────────
# STEP 3: Embed & store to ChromaDB
# ─────────────────────────────────────────────────
def save_to_chroma(chunks: list[Document], device: str, encode_batch_size: int):
    if os.path.exists(CHROMA_PATH):
        print(f"\n[3/4] Menghapus database lama di {CHROMA_PATH}...")
        shutil.rmtree(CHROMA_PATH)

    print(f"\n[3/4] Menginisialisasi model embedding ({EMBEDDING_MODEL}) pada {device.upper()}...")
    t0 = time.time()

    embedding_model = HuggingFaceEmbeddings(
        model_name=EMBEDDING_MODEL,
        model_kwargs={"device": device, "local_files_only": False},
        encode_kwargs={
            "normalize_embeddings": True,
            "batch_size": encode_batch_size,   # throughput tuneable
        },
    )
    print(f"   Model siap dalam {time.time()-t0:.1f}s")

    total = len(chunks)
    print(f"   Menyimpan {total} chunks ke ChromaDB (batch={CHROMA_BATCH_SIZE})...")
    t0 = time.time()

    db = None
    n_batches = (total + CHROMA_BATCH_SIZE - 1) // CHROMA_BATCH_SIZE
    for i in range(0, total, CHROMA_BATCH_SIZE):
        batch  = chunks[i : i + CHROMA_BATCH_SIZE]
        end    = min(i + CHROMA_BATCH_SIZE, total)
        b_num  = i // CHROMA_BATCH_SIZE + 1
        elapsed = time.time() - t0
        eta    = (elapsed / b_num) * (n_batches - b_num) if b_num > 1 else 0
        print(f"   Batch {b_num}/{n_batches}: chunks {i+1}–{end}  "
              f"[elapsed {elapsed:.0f}s | ETA {eta:.0f}s]")

        if db is None:
            db = Chroma.from_documents(
                documents=batch,
                embedding=embedding_model,
                persist_directory=CHROMA_PATH,
            )
        else:
            db.add_documents(batch)

    total_time = time.time() - t0
    print(f"   → ChromaDB tersimpan di: {CHROMA_PATH}  ({total_time:.1f}s total)")


# ─────────────────────────────────────────────────
# STEP 4: Sanity check
# ─────────────────────────────────────────────────
def sanity_check(device: str):
    print("\n[4/4] Sanity check – menjalankan sample query...")
    embedding_model = HuggingFaceEmbeddings(
        model_name=EMBEDDING_MODEL,
        model_kwargs={"device": device, "local_files_only": True},
        encode_kwargs={"normalize_embeddings": True},
    )
    db = Chroma(persist_directory=CHROMA_PATH, embedding_function=embedding_model)

    total = db._collection.count()
    print(f"   Total vectors dalam DB: {total}")

    test_query = "pantai di danau toba"
    results = db.similarity_search(test_query, k=3, filter={"city_regency": "Samosir"})
    print(f"\n   Query: '{test_query}' filter city_regency='Samosir'")
    if results:
        for r in results:
            print(f"   • {r.metadata.get('place_name')} [{r.metadata.get('city_regency')}]")
    else:
        print("   Tidak ada hasil. Coba tanpa filter:")
        for r in db.similarity_search(test_query, k=3):
            print(f"   • {r.metadata.get('place_name')} [{r.metadata.get('city_regency')}]")

    print("\n[DONE] Ingestion selesai.")


# ─────────────────────────────────────────────────
# MAIN
# ─────────────────────────────────────────────────
if __name__ == "__main__":
    # Required for Windows multiprocessing
    multiprocessing.freeze_support()

    print("=" * 60)
    print("  Ingest v2 — entities_final.csv → chroma_db_baseline")
    print("=" * 60)

    t_start = time.time()

    device, encode_batch_size = detect_device()
    raw_docs = load_documents(CSV_FILE_PATH)
    chunks   = split_documents(raw_docs)
    save_to_chroma(chunks, device, encode_batch_size)
    sanity_check(device)

    print(f"\n{'='*60}")
    print(f"  TOTAL WAKTU: {time.time() - t_start:.1f} detik")
    print(f"{'='*60}")
