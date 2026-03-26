import os
import json
import pandas as pd
from langchain_community.chat_models import ChatOllama
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import PydanticOutputParser
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_chroma import Chroma
from langchain_core.documents import Document

import sys
# Make sure we can import from the current project directory
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from schemas import AttractionFeatures

# ==========================================
# KONFIGURASI
# ==========================================
CSV_FILE_PATH = "./wisata-toba-final-v2.csv"
CHECKPOINT_FILE = "./uadc_checkpoint.json"
CHROMA_PATH = "./chroma_db_uadc"
EMBEDDING_MODEL = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"

# Prompt Ekstraksi LLM
SYSTEM_PROMPT_UADC = """
Anda adalah pakar pariwisata yang bertugas menganalisis tempat wisata di Danau Toba.
Berdasarkan ulasan pengunjung berikut, ekstrak fitur-fitur tempat wisata tersebut menjadi 4 bagian:
1. Landscape & Content (Fitur alam, peninggalan sejarah, bangunan, kualitas fisik, dan arsitektur)
2. Activities (Aktivitas yang bisa dilakukan oleh pengunjung)
3. Atmosphere (Nuansa emosional, tingkat keramaian, mood, dan suasana hati)
4. Summary (Deskripsi singkat umum)

Gunakan bahasa Indonesia. Jika tidak ada informasi eksplisit untuk suatu dimensi, berikan estimasi yang masuk akal berdasarkan konteks tempat tersebut, JANGAN KOSONG.
"""

def extract_features_with_llm(place_name, category, reviews):
    """Mengekstrak 4 dimensi fitur dari ulasan menggunakan LLM"""
    llm = ChatOllama(model="qwen3:1.7b", temperature=0.1)
    parser = PydanticOutputParser(pydantic_object=AttractionFeatures)
    
    prompt = ChatPromptTemplate.from_messages([
        ("system", SYSTEM_PROMPT_UADC + "\n\nFormat keluaran harus persis seperti JSON berikut:\n{format_instructions}"),
        ("human", "Nama Tempat: {place_name}\nKategori: {category}\nUlasan Pengunjung:\n{reviews}")
    ])
    
    chain = prompt | llm | parser
    
    try:
        response = chain.invoke({
            "place_name": place_name,
            "category": category,
            "reviews": reviews,
            "format_instructions": parser.get_format_instructions()
        })
        return response.dict()
    except Exception as e:
        print(f"Error LLM extraction for '{place_name}': {e}")
        # Default fallback if LLM fails
        return {
            "landscape_content_features": f"Pemandangan alam dan bangunan di {place_name}.",
            "activity_features": f"Berbagai aktivitas rekreasi di {place_name}.",
            "atmosphere_features": f"Suasana wisata yang khas di {place_name}.",
            "summary": f"Tempat wisata {place_name} dengan kategori {category}."
        }

def process_and_checkpoint_data(limit=None):
    """Mengekstrak fitur dan menyimpannya ke JSON checkpoint sementara"""
    df = pd.read_csv(CSV_FILE_PATH).fillna("")
    
    print(f"Total baris raw: {len(df)}")
    
    # KUNCI UTAMA: Gabungkan (Group) ribuan ulasan menjadi 1 baris per tempat wisata
    df = df.groupby(['item_id', 'place_name', 'category']).agg({
        'reviews': lambda x: ' | '.join(x.astype(str)),
        'rating': 'mean'
    }).reset_index()
    
    print(f"Setelah di-group berdasarkan tempat wisata: {len(df)} tempat unik.")
    
    if limit:
        df = df.head(limit)
        print(f"⚠️ Menjalankan mode DRY RUN untuk {limit} tempat pertama...")
    
    # Load existing checkpoint if any
    extracted_data = {}
    if os.path.exists(CHECKPOINT_FILE):
        with open(CHECKPOINT_FILE, "r", encoding="utf-8") as f:
            try:
                extracted_data = json.load(f)
                print(f"✅ Memuat {len(extracted_data)} data dari checkpoint yang sudah ada.")
            except:
                pass
            
    # Process rows
    new_extractions = 0
    for idx, row in df.iterrows():
        item_id = str(row['item_id'])
        
        # Skip if already processed
        if item_id in extracted_data:
            continue
            
        print(f"🔄 Mengekstrak dimensi untuk: {row['place_name']} ({idx+1}/{len(df)})")
        
        # Limit review text length to avoid token limit errors
        reviews_text = str(row['reviews'])[:3000] # roughly 1000 tokens
        
        features = extract_features_with_llm(
            place_name=row['place_name'],
            category=row['category'],
            reviews=reviews_text
        )
        
        # Add metadata
        extracted_data[item_id] = {
            "item_id": item_id,
            "place_name": row['place_name'],
            "category": row['category'],
            "rating": float(row['rating']) if row['rating'] else 0.0,
            "features": features
        }
        new_extractions += 1
        
        # Save checkpoint periodically
        if new_extractions % 2 == 0:
            with open(CHECKPOINT_FILE, "w", encoding="utf-8") as f:
                json.dump(extracted_data, f, indent=4, ensure_ascii=False)
                
    # Final save
    with open(CHECKPOINT_FILE, "w", encoding="utf-8") as f:
        json.dump(extracted_data, f, indent=4, ensure_ascii=False)
        
    print(f"✅ Ekstraksi LLM selesai. Total data di checkpoint: {len(extracted_data)}")
    return extracted_data

def build_chroma_database(extracted_data):
    """Membangun dimensi vektor 4 arah dari data yang sudah diekstrak"""
    print(f"Menyiapkan model embedding {EMBEDDING_MODEL}...")
    embedding_model = HuggingFaceEmbeddings(
        model_name=EMBEDDING_MODEL,
        model_kwargs={'device': 'cpu', 'local_files_only': True},
        encode_kwargs={'normalize_embeddings': True}
    )
    
    documents = []
    print("Mempersiapkan dokumen berdimensi...")
    
    for item_id, data in extracted_data.items():
        base_meta = {
            "item_id": data["item_id"],
            "place_name": data["place_name"],
            "category": data["category"],
            "rating": data["rating"],
        }
        
        feats = data["features"]
        
        # 1. LANDSCAPE & CONTENT
        meta_lan = base_meta.copy()
        meta_lan["dimension"] = "landscape_content"
        documents.append(Document(page_content=feats["landscape_content_features"], metadata=meta_lan))
        
        # 2. ACTIVITIES
        meta_act = base_meta.copy()
        meta_act["dimension"] = "activity"
        documents.append(Document(page_content=feats["activity_features"], metadata=meta_act))
        
        # 3. ATMOSPHERE
        meta_atm = base_meta.copy()
        meta_atm["dimension"] = "atmosphere"
        documents.append(Document(page_content=feats["atmosphere_features"], metadata=meta_atm))
        
        # 4. SUMMARY (digunakan untuk fallback atau deskripsi umum)
        meta_sum = base_meta.copy()
        meta_sum["dimension"] = "summary"
        documents.append(Document(page_content=feats["summary"], metadata=meta_sum))

    print(f"Menyimpan {len(documents)} vektor (dari {len(extracted_data)} tempat * 4 dimensi) ke ChromaDB...")
    
    # Hapus DB lama secara manual jika diperlukan, tapi kita gunakan folder terpisah: chroma_db_uadc
    db = Chroma.from_documents(
        documents=documents,
        embedding=embedding_model,
        persist_directory=CHROMA_PATH
    )
    print(f"SUCCESS! Database UADC tersimpan di: {CHROMA_PATH}")

if __name__ == "__main__":
    data = process_and_checkpoint_data()
    
    build_chroma_database(data)
