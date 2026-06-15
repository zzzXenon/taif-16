import os
import pandas as pd
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_chroma import Chroma

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE_DIR, "data")
CSV_PATH = os.path.join(DATA_DIR, "entities_final.csv")
CHROMA_PATH = os.path.join(DATA_DIR, "chroma_db_baseline")
EMBEDDING_MODEL = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"

print("=" * 60)
print("  DIAGNOSTIC SCRIPT: DATABASE & CSV CHECK")
print("=" * 60)

# 1. Check CSV file
print("\n[1/4] Memeriksa file CSV di server...")
if os.path.exists(CSV_PATH):
    df = pd.read_csv(CSV_PATH)
    print(f"   CSV ditemukan. Total baris: {len(df)}")
    parbaba_csv = df[df['place_name'].str.contains('Parbaba', case=False, na=False)]
    if not parbaba_csv.empty:
        print("   Baris Parbaba di CSV:")
        for idx, row in parbaba_csv.iterrows():
            print(f"     - {row['place_name']} -> city_regency: '{row['city_regency']}'")
    else:
        print("   [WARNING] Pantai Pasir Putih Parbaba tidak ditemukan di CSV!")
else:
    print("   [ERROR] entities_final.csv tidak ditemukan di server!")

# 2. Check Database existence
print("\n[2/4] Memeriksa database Chroma di server...")
if os.path.exists(CHROMA_PATH):
    print(f"   Folder database ditemukan di: {CHROMA_PATH}")
else:
    print(f"   [ERROR] Folder database tidak ditemukan di: {CHROMA_PATH}")
    print("   Harap jalankan: python scripts/ingest_v2.py")
    exit(1)

# 3. Load embeddings & database
print("\n[3/4] Memuat database Chroma...")
try:
    embedding_model = HuggingFaceEmbeddings(
        model_name=EMBEDDING_MODEL,
        model_kwargs={"device": "cpu"},
        encode_kwargs={"normalize_embeddings": True},
    )
    db = Chroma(persist_directory=CHROMA_PATH, embedding_function=embedding_model)
    total_vectors = db._collection.count()
    print(f"   Total vektor di database baseline: {total_vectors}")
except Exception as e:
    print(f"   [ERROR] Gagal memuat database: {e}")
    exit(1)

# 4. Search for Parbaba in DB without filter
print("\n[4/4] Mencari entitas 'Parbaba' di database...")
results_no_filter = db.similarity_search("Pantai Pasir Putih Parbaba", k=5)
print("   Hasil pencarian TANPA filter:")
for i, r in enumerate(results_no_filter):
    print(f"     {i+1}. {r.metadata.get('place_name')} | city_regency: '{r.metadata.get('city_regency')}'")

# 5. Search with filter
print("\n[5/5] Mencari dengan filter city_regency='Samosir'...")
results_filter = db.similarity_search("Pantai Pasir Putih Parbaba", k=5, filter={"city_regency": "Samosir"})
print("   Hasil pencarian DENGAN filter city_regency='Samosir':")
if results_filter:
    for i, r in enumerate(results_filter):
        print(f"     {i+1}. {r.metadata.get('place_name')} | city_regency: '{r.metadata.get('city_regency')}'")
else:
    print("   [FAIL] Pencarian dengan filter Samosir mengembalikan 0 hasil!")

print("\n" + "=" * 60)
