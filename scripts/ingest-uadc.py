"""
ingest-uadc.py  (v2)
---------------------
Reads entities_final.csv, calls Ollama LLM to extract 4 feature dimensions
per entity, saves results to uadc_checkpoint.json, then builds chroma_db_uadc.

Changes from original:
  - Source CSV: entities_final.csv (instead of wisata-toba-unified-final.csv)
  - Embedding device: auto-detect GPU
  - LLM model: configurable via env var UADC_LLM (default: qwen3:14b)
  - Paths overridable via env vars
  - Parallel-friendly: resumes from checkpoint, skips already-processed entities

Run:
  python scripts/ingest-uadc.py

Override model:
  UADC_LLM=qwen3:8b python scripts/ingest-uadc.py
"""

import os
import json
import time
import sys

import pandas as pd
from langchain_ollama import ChatOllama
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import PydanticOutputParser, StrOutputParser
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_chroma import Chroma
from langchain_core.documents import Document

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(BASE_DIR, "src"))
from schemas import AttractionFeatures

# ─────────────────────────────────────────────────
# CONFIG  (all overridable via env vars)
# ─────────────────────────────────────────────────
CSV_FILE_PATH   = os.environ.get("ENTITIES_CSV",  os.path.join(BASE_DIR, "data", "entities_final.csv"))
CHECKPOINT_FILE = os.environ.get("UADC_CHECKPOINT", os.path.join(BASE_DIR, "data", "uadc_checkpoint.json"))
CHROMA_PATH     = os.environ.get("CHROMA_UADC",   os.path.join(BASE_DIR, "data", "chroma_db_uadc"))
EMBEDDING_MODEL = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
LLM_MODEL       = os.environ.get("UADC_LLM", "qwen3:14b")

REVIEW_CHAR_LIMIT = 4000   # ~1300 tokens; keeps prompts manageable

# ─────────────────────────────────────────────────
# DEVICE DETECTION
# ─────────────────────────────────────────────────
def detect_device() -> tuple[str, int]:
    try:
        import torch
        if torch.cuda.is_available():
            name = torch.cuda.get_device_name(0)
            vram = torch.cuda.get_device_properties(0).total_memory // (1024**2)
            print(f"   [Device] GPU: {name} ({vram} MB) → CUDA")
            return "cuda", 512 if vram >= 6000 else 256
    except ImportError:
        pass
    print("   [Device] → CPU")
    return "cpu", 64


# ─────────────────────────────────────────────────
# LLM FEATURE EXTRACTION
# ─────────────────────────────────────────────────
SYSTEM_PROMPT_UADC = """
Anda adalah pakar pariwisata yang bertugas menganalisis tempat wisata di Danau Toba.
Berdasarkan informasi dan ulasan pengunjung berikut, ekstrak fitur-fitur tempat tersebut menjadi 4 bagian:
1. Landscape & Content (Fitur alam, peninggalan sejarah, bangunan, kualitas fisik, arsitektur, fasilitas)
2. Activities (Aktivitas yang bisa dilakukan oleh pengunjung)
3. Atmosphere (Nuansa emosional, tingkat keramaian, mood, dan suasana hati)
4. Summary (Deskripsi singkat umum 1-2 kalimat)

Gunakan bahasa Indonesia. Jika tidak ada informasi eksplisit untuk suatu dimensi,
berikan estimasi masuk akal berdasarkan nama/kategori tempat. JANGAN KOSONG.
"""


def extract_features_with_llm(place_name: str, category: str, description: str) -> dict:
    """Extract 4 feature dimensions from entity description using LLM."""
    llm    = ChatOllama(model=LLM_MODEL, temperature=0.1, format="json")
    parser = PydanticOutputParser(pydantic_object=AttractionFeatures)

    prompt = ChatPromptTemplate.from_messages([
        ("system", SYSTEM_PROMPT_UADC + "\n\nFormat keluaran JSON:\n{format_instructions}"),
        ("human",  "Nama: {place_name}\nKategori: {category}\nInformasi & Ulasan:\n{description}")
    ])

    chain = prompt | llm | StrOutputParser()

    try:
        raw = chain.invoke({
            "place_name":          place_name,
            "category":            category,
            "description":         description[:REVIEW_CHAR_LIMIT],
            "format_instructions": parser.get_format_instructions(),
        })
        result = parser.parse(raw)
        return result.dict()
    except Exception as e:
        print(f"   [WARN] LLM extraction failed for '{place_name}': {e}")
        return {
            "landscape_content_features": f"Pemandangan alam dan fasilitas di {place_name}.",
            "activity_features":          f"Berbagai aktivitas rekreasi di {place_name}.",
            "atmosphere_features":        f"Suasana wisata yang khas di {place_name}.",
            "summary":                    f"{place_name} — tempat {category} di kawasan Danau Toba.",
        }


# ─────────────────────────────────────────────────
# STEP 1: LLM Extraction with checkpoint
# ─────────────────────────────────────────────────
def process_and_checkpoint(limit=None) -> dict:
    print(f"\n[1/2] Membaca {CSV_FILE_PATH}...")
    if not os.path.exists(CSV_FILE_PATH):
        raise FileNotFoundError(
            f"File tidak ditemukan: {CSV_FILE_PATH}\n"
            f"Set env var: ENTITIES_CSV=/path/to/entities_final.csv"
        )

    df = pd.read_csv(CSV_FILE_PATH).fillna("")
    if "item_id" not in df.columns:
        df["item_id"] = range(1, len(df) + 1)

    if limit:
        df = df.head(limit)
        print(f"   [DRY RUN] Hanya memproses {limit} entitas pertama.")

    total = len(df)
    print(f"   Total entitas: {total}")
    print(f"   LLM model    : {LLM_MODEL}")

    # Resume from checkpoint
    extracted: dict = {}
    if os.path.exists(CHECKPOINT_FILE):
        with open(CHECKPOINT_FILE, "r", encoding="utf-8") as f:
            try:
                extracted = json.load(f)
                print(f"   Melanjutkan dari checkpoint: {len(extracted)} sudah diproses.")
            except json.JSONDecodeError:
                print("   [WARN] Checkpoint rusak, mulai dari awal.")

    new_count = 0
    t0 = time.time()

    for idx, row in df.iterrows():
        item_id = str(row["item_id"])
        if item_id in extracted:
            continue

        place_name = str(row.get("place_name", "")).strip()
        category   = str(row.get("category",   "")).strip()
        description = str(row.get("description", "")).strip()

        done_so_far = len(extracted)
        eta_s = ""
        if new_count > 0:
            elapsed = time.time() - t0
            rate    = elapsed / new_count
            remaining = total - done_so_far - 1
            eta_s = f" | ETA ~{remaining * rate / 60:.0f} mnt"

        print(f"   [{done_so_far+1}/{total}] {place_name}{eta_s}")

        features = extract_features_with_llm(place_name, category, description)

        extracted[item_id] = {
            "item_id":    item_id,
            "place_name": place_name,
            "category":   category,
            "rating":     float(row.get("rating", 0.0)) if str(row.get("rating", "")).replace(".", "").isdigit() else 0.0,
            "features":   features,
        }
        new_count += 1

        # Save checkpoint every 5 new entries
        if new_count % 5 == 0:
            _save_checkpoint(extracted)

    _save_checkpoint(extracted)
    print(f"\n   Ekstraksi selesai. Total di checkpoint: {len(extracted)} entitas.")
    return extracted


def _save_checkpoint(data: dict):
    with open(CHECKPOINT_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


# ─────────────────────────────────────────────────
# STEP 2: Build chroma_db_uadc
# ─────────────────────────────────────────────────
def build_chroma_uadc(extracted: dict, device: str, encode_batch_size: int):
    import shutil
    print(f"\n[2/2] Membangun chroma_db_uadc ({len(extracted)} entitas × 4 dimensi)...")

    if os.path.exists(CHROMA_PATH):
        print(f"   Menghapus DB lama...")
        shutil.rmtree(CHROMA_PATH)

    print(f"   Menginisialisasi embedding model pada {device.upper()}...")
    embedding_model = HuggingFaceEmbeddings(
        model_name=EMBEDDING_MODEL,
        model_kwargs={"device": device, "local_files_only": False},
        encode_kwargs={"normalize_embeddings": True, "batch_size": encode_batch_size},
    )

    documents = []
    for item_id, data in extracted.items():
        base_meta = {
            "item_id":    data["item_id"],
            "place_name": data["place_name"],
            "category":   data["category"],
            "rating":     data["rating"],
        }
        feats = data["features"]

        dims = [
            ("landscape_content", feats["landscape_content_features"]),
            ("activity",          feats["activity_features"]),
            ("atmosphere",        feats["atmosphere_features"]),
            ("summary",           feats["summary"]),
        ]
        for dim_name, dim_text in dims:
            meta = base_meta.copy()
            meta["dimension"] = dim_name
            documents.append(Document(page_content=dim_text, metadata=meta))

    print(f"   Menyimpan {len(documents)} vektor ke ChromaDB...")
    t0 = time.time()
    db = Chroma.from_documents(
        documents=documents,
        embedding=embedding_model,
        persist_directory=CHROMA_PATH,
    )
    print(f"   → Selesai dalam {time.time()-t0:.1f}s. DB: {CHROMA_PATH}")
    print(f"   Total vectors: {db._collection.count()}")


# ─────────────────────────────────────────────────
# MAIN
# ─────────────────────────────────────────────────
if __name__ == "__main__":
    print("=" * 60)
    print("  UADC Ingest v2 — entities_final.csv → chroma_db_uadc")
    print("=" * 60)

    device, encode_batch = detect_device()

    # Step 1: LLM extraction (resumes from checkpoint automatically)
    extracted = process_and_checkpoint()

    # Step 2: Build vector DB
    build_chroma_uadc(extracted, device, encode_batch)

    print("\n[DONE] UADC ingestion selesai.")
