import pandas as pd
import os
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_chroma import Chroma
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_core.documents import Document

# ==========================================
# KONFIGURASI
# ==========================================
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CSV_FILE_PATH = os.path.join(BASE_DIR, "data", "wisata-toba-unified-final.csv")
CHROMA_PATH = os.path.join(BASE_DIR, "data", "chroma_db_baseline")
MODEL_NAME = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"

def load_and_process_data(file_path):
    """
    Membaca CSV dan mengubahnya menjadi format Document LangChain.
    Kita menggabungkan kolom penting ke 'page_content' agar terbaca oleh vektor.
    """
    print(f"🔄 Membaca data dari {file_path}...")
    
    # Baca CSV w/ pandas
    df = pd.read_csv(file_path)
    
    # Pastikan data string tidak kosong (handling missing values)
    df.fillna("", inplace=True)
    
    documents = []
    
    for idx, row in df.iterrows():
        # ---------------------------------------------------------
        # TEKNIK BASELINE: CONTEXTUAL FLATTENING
        # Menggabungkan metadata penting ke dalam teks utama.
        # Format: "Nama: [X]. Kategori: [Y]. Deskripsi: [Z]"
        # ---------------------------------------------------------
        content_text = (
            f"Nama Tempat: {row['place_name']}. "
            f"Kategori: {row['category']}. "
            f"Deskripsi dan Ulasan: {row['description']}"
        )
        
        metadata = {
            "place_name": row['place_name'],
            "category": row['category'],
        }
        
        doc = Document(page_content=content_text, metadata=metadata)
        documents.append(doc)
        
    print(f"✅ Berhasil memuat {len(documents)} dokumen mentah.")
    return documents

def split_text(documents):
    """
    Memecah dokumen panjang menjadi potongan-potongan kecil (chunks).
    """
    print("✂️ Memulai proses text splitting (chunking)...")
    
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=1000,       # Ukuran karakter per chunk
        chunk_overlap=200,     # Overlap agar konteks kalimat tidak terputus
        separators=["\n\n", "\n", ". ", " ", ""] # Prioritas pemisah
    )
    
    chunks = text_splitter.split_documents(documents)
    print(f"✅ Data dipecah menjadi {len(chunks)} chunks.")
    return chunks

def save_to_chroma(chunks):
    """
    Melakukan embedding dan menyimpan ke ChromaDB.
    """
    # Hapus database lama jika ada (untuk memastikan data bersih saat rerun)
    if os.path.exists(CHROMA_PATH):
        print("⚠️ Menemukan database lama, menghapus dan membuat baru...")
        import shutil
        shutil.rmtree(CHROMA_PATH)

    print(f"Menginisialisasi model embedding ({MODEL_NAME})...")
    # Gunakan device='cpu' jika tidak punya GPU NVIDIA
    embedding_model = HuggingFaceEmbeddings(
        model_name=MODEL_NAME,
        model_kwargs={'device': 'cpu', 'local_files_only': False},
        encode_kwargs={'normalize_embeddings': True}
    )

    print("Menyimpan vektor ke ChromaDB...")
    
    # Proses Batch Ingestion
    # ChromaDB otomatis menghitung vektor untuk setiap chunk teks
    db = Chroma.from_documents(
        documents=chunks, 
        embedding=embedding_model, 
        persist_directory=CHROMA_PATH
    )
    
    print(f"SUCCESS! Database tersimpan di folder: {CHROMA_PATH}")
    print("Sekarang Anda bisa menjalankan script retrieval/chatbot.")

if __name__ == "__main__":
    # Load Data
    raw_docs = load_and_process_data(CSV_FILE_PATH)
    
    # Split Data
    chunked_docs = split_text(raw_docs)
    
    # Embed & Save
    save_to_chroma(chunked_docs)