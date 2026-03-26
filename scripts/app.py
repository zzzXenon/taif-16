import sys
import os
import argparse

# Configure stdout to handle emojis in Windows Console
sys.stdout.reconfigure(encoding='utf-8')

# Ensure is in path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from modules.retriever import get_ier_decomposition, dimension_aware_search, llm_reranker, generate_final_response, rewrite_query
from schemas import CQRResult
import json
import uuid
from database import init_db, create_session, save_message, get_chat_history, get_first_query
from langchain_chroma import Chroma
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_ollama import ChatOllama
from langchain_classic.chains import RetrievalQA

CHROMA_PATH = "./chroma_db_uadc"
EMBEDDING_MODEL = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"

def get_vector_db():
    embedding_model = HuggingFaceEmbeddings(
        model_name=EMBEDDING_MODEL,
        model_kwargs={'device': 'cpu', 'local_files_only': True},
        encode_kwargs={'normalize_embeddings': True}
    )
    return Chroma(persist_directory=CHROMA_PATH, embedding_function=embedding_model)

def get_baseline_vector_db():
    embedding_model = HuggingFaceEmbeddings(
        model_name=EMBEDDING_MODEL,
        model_kwargs={'device': 'cpu', 'local_files_only': True},
        encode_kwargs={'normalize_embeddings': True}
    )
    return Chroma(persist_directory="./chroma_db_baseline", embedding_function=embedding_model)

def get_baseline_qa_chain(baseline_db):
    llm = ChatOllama(model="qwen3:1.7b", temperature=0.7)
    retriever = baseline_db.as_retriever(search_kwargs={"k": 4})
    qa_chain = RetrievalQA.from_chain_type(
        llm=llm,
        chain_type="stuff",
        retriever=retriever,
        return_source_documents=True
    )
    return qa_chain

def get_baseline_vector_db():
    embedding_model = HuggingFaceEmbeddings(
        model_name=EMBEDDING_MODEL,
        model_kwargs={'device': 'cpu', 'local_files_only': True},
        encode_kwargs={'normalize_embeddings': True}
    )
    return Chroma(persist_directory="./chroma_db_baseline", embedding_function=embedding_model)

def get_baseline_qa_chain(baseline_db):
    llm = ChatOllama(model="qwen3:1.7b", temperature=0.7)
    retriever = baseline_db.as_retriever(search_kwargs={"k": 4})
    qa_chain = RetrievalQA.from_chain_type(
        llm=llm,
        chain_type="stuff",
        retriever=retriever,
        return_source_documents=True
    )
    return qa_chain

def main():
    parser = argparse.ArgumentParser(description="UGuideRAG Interactive Chatbot")
    parser.add_argument("--disable-cqr", action="store_true", help="Nonaktifkan Pipeline B (CQR) untuk ablation study (hanya Pipeline A)")
    args = parser.parse_args()

    print("--- AiYukToba Assistant Active ---")
    
    print("Mempersiapkan database rekam jejak (SQLite)...")
    init_db()
    
    # Buat sesi unik untuk setiap run script
    current_session = str(uuid.uuid4())
    create_session(current_session)
    
    print("Mempersiapkan database wisata (ChromaDB)...")
    vector_db = get_vector_db()
    
    print("Ready! Ketik 'exit' atau 'keluar' untuk mengakhiri.\n")

    while True:
        query = input("😎 Anda: ")
        
        if query.strip().lower() in ['exit', 'keluar', 'quit']:
            print("Sampai jumpa lagi! 👋")
            break
            
        if not query.strip():
            continue
            
        if args.pipeline_a_only:
            print(f"\n[⚠️ Ablation Study] Pipeline B (CQR) dinonaktifkan. Mengembalikan raw query (Pipeline A Saja)...")
            cqr = CQRResult(standalone_query=query, is_search_required=True)
        else:
            # Pipeline B: Tarik History
            # Menggunakan "First-plus-last sliding window"
            # Ambil Q1 sebagai anchor, dan 3 pesan terakhir
            q1 = get_first_query(current_session)
            recent_history = get_chat_history(current_session, limit=4) # 2 pasang terakhir
            
            # Susun history yang disalurkan ke LLM CQR
            prompt_history = []
            if q1 and (not recent_history or recent_history[0][1] != q1):
                prompt_history.append(("user", f"[PESAN PERTAMA]: {q1}"))
                
            prompt_history.extend(recent_history)
            
            print(f"\n[🔄 Modul CQR] Sedang membersihkan konteks... (History {len(prompt_history)} nodes)")
            cqr = rewrite_query(query, prompt_history)
            
            print(f"[🔍 Standalone Query]: {cqr.standalone_query}")
            print(f"[⚙️ Is Search Required?]: {cqr.is_search_required}")
            
            if not cqr.is_search_required:
                # Chit-chat Mode
                print("\n🤖 AiYukToba:")
                llm = ChatOllama(model="qwen3:1.7b", temperature=0.5)
                casual_response = llm.invoke(f"Berdasarkan percakapan ini, jawab sapaan pengguna dengan ramah: '{query}'")
                print(casual_response.content)
                print("=" * 60)
                
                # Simpan chat non-search ke DB
                save_message(current_session, "user", query, cqr.standalone_query)
                save_message(current_session, "ai", casual_response.content)
                continue
            
        # PIPELINE A / BASELINE EXECUTION
        if args.pipeline_b_only:
            print("\n[⚠️ Ablation Study] Menjalankan Pipeline B + Pencarian Standar...")
            result = baseline_qa.invoke({"query": cqr.standalone_query})
            
            print("\n=== DOKUMEN REFERENSI (BASELINE RAG) ===")
            for i, doc in enumerate(result["source_documents"]):
                print(f"{i+1}. [Source snippet]: {doc.page_content[:100]}...")
            
            final_output = result["result"]
            print("\nMenyusun respons akhir...\n")
            print("=" * 60)
            print("🤖 AiYukToba (Baseline QA):")
            print(final_output)
            print("=" * 60)
            
            save_message(current_session, "user", query, cqr.standalone_query)
            save_message(current_session, "ai", final_output)
            continue

        # PIPELINE A: Jika perlu dicarikan tempat wisata
        print("\nSedang memproses intent anda...")
        try:
            intent = get_ier_decomposition(cqr.standalone_query)
            print("\n=== HASIL DEKOMPOSISI (IER) ===")
            print(f"Landscape & Content : {intent.expected_landscape_content}")
            print(f"Activities          : {intent.expected_activities}")
            print(f"Atmosphere          : {intent.expected_atmosphere}")
        except Exception as e:
            print(f"\nGagal mendekomposisi niat: {e}")
            continue

        # Vector Search
        print("\nSedang mencari kecocokan matematis di database...")
        top_results = dimension_aware_search(
            vector_db=vector_db, 
            intent_dimensions=intent,
            w_lan=1.0, w_act=1.0, w_atm=1.0,
            top_k=4
        )
        
        print("\n=== TOP 4 REKOMENDASI (MATEMATIS) ===")
        for i, res in enumerate(top_results):
            print(f"{i+1}. {res['place_name']} (Kategori: {res['category']}, Base Skor: {res['total_score']:.4f})")
        
        # LLM Re-Ranking
        print("\nSedang mengevaluasi ulang dengan LLM Re-Ranker (Qwen3)...")
        try:
            with open("uadc_checkpoint.json", "r", encoding="utf-8") as f:
                uadc_data_dict = json.load(f)
        except Exception as e:
            print(f"Gagal memuat checkpoint UADC: {e}")
            uadc_data_dict = {}

        reranked_results = llm_reranker(cqr.standalone_query, top_results, uadc_data_dict)
        
        print("\n=== TOP 4 REKOMENDASI (HASIL RE-RANKING LLM) ===")
        for i, res in enumerate(reranked_results):
            print(f"\n{i+1}. {res['place_name']}")
            print(f"   Kategori   : {res['category']}")
            print(f"   Base Skor  : {res['total_score']:.4f} -> LRR Skor: {res.get('lrr_score', 'N/A')}/10.0")
            print(f"   Reasoning  : {res.get('lrr_reasoning', 'N/A')}")
            
        with open("lrr_debug.json", "w", encoding="utf-8") as f:
            json.dump(reranked_results, f, indent=4, ensure_ascii=False)
        
        # Generate Response
        print("\nMenyusun respons akhir...\n")
        print("=" * 60)
        print("🤖 AiYukToba:")
        final_output = generate_final_response(cqr.standalone_query, reranked_results)
        print(final_output)
        print("=" * 60)
        
        # PIPELINE B: Simpan state memori ke DB (User dan AI)
        save_message(current_session, "user", query, cqr.standalone_query)
        save_message(current_session, "ai", final_output)

if __name__ == "__main__":
    main()