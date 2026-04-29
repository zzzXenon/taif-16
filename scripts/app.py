"""
CLI Chatbot Manual.
Gunakan ini untuk interaksi langsung di terminal.

Cara pakai:
  python scripts/app.py                             # Proposed (Pipeline A+B)
  python scripts/app.py --ablation baseline         # Baseline RAG only
  python scripts/app.py --ablation pipeline_a_only  # Pipeline A only (no CQR)
  python scripts/app.py --ablation pipeline_b_only  # Pipeline B only (CQR + baseline检索)
"""

import sys
import os
import argparse

# Add project root to path so 'core' module can be found
PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(PROJECT_ROOT, ".."))
sys.path.insert(0, os.path.join(PROJECT_ROOT, "..", "src"))

from modules.retriever import get_ca_ier, dimension_aware_search, cross_encoder_rerank, generate_final_response
from schemas import CAIEROutput
import json
import uuid

sys.stdout.reconfigure(encoding='utf-8')

from database import init_db, create_session, save_message, get_chat_history, get_first_query
from langchain_chroma import Chroma
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_ollama import ChatOllama
from langchain_classic.chains import RetrievalQA

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE_DIR, "data")

CHROMA_PATH = os.path.join(DATA_DIR, "chroma_db_uadc")
BASELINE_CHROMA_PATH = os.path.join(DATA_DIR, "chroma_db_baseline")
EMBEDDING_MODEL = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"


def get_vector_db():
    embedding_model = HuggingFaceEmbeddings(
        model_name=EMBEDDING_MODEL,
        model_kwargs={'device': 'cpu', 'local_files_only': False},
        encode_kwargs={'normalize_embeddings': True}
    )
    return Chroma(persist_directory=CHROMA_PATH, embedding_function=embedding_model)


def get_baseline_vector_db():
    embedding_model = HuggingFaceEmbeddings(
        model_name=EMBEDDING_MODEL,
        model_kwargs={'device': 'cpu', 'local_files_only': False},
        encode_kwargs={'normalize_embeddings': True}
    )
    return Chroma(persist_directory=BASELINE_CHROMA_PATH, embedding_function=embedding_model)


def get_baseline_qa_chain(baseline_db):
    llm = ChatOllama(model="qwen3:8b", temperature=0.7)
    retriever = baseline_db.as_retriever(search_kwargs={"k": 5})
    qa_chain = RetrievalQA.from_chain_type(
        llm=llm,
        chain_type="stuff",
        retriever=retriever,
        return_source_documents=True
    )
    return qa_chain


def main():
    parser = argparse.ArgumentParser(description="CLI Chatbot")
    parser.add_argument(
        "--ablation",
        type=str,
        default="proposed",
        choices=["proposed", "pipeline_a_only", "pipeline_b_only", "baseline"],
        help="Mode ablasi: proposed (A+B), pipeline_a_only (A без CQR), pipeline_b_only (B+baseline检索), baseline (tanpa CQR & tanpa dimensi)"
    )
    parser.add_argument("--top-k", type=int, default=5, help="Jumlah hasil pencarian untuk ditampilkan")
    args = parser.parse_args()

    ablation_mode = args.ablation

    print("=" * 60)
    print("🤖 AiYukToba CLI - Mode:", ablation_mode)
    print("=" * 60)
    
    print("\n📂 Memuat database...")
    init_db()
    vector_db = get_vector_db()
    baseline_db = get_baseline_vector_db()
    baseline_qa = get_baseline_qa_chain(baseline_db)
    print("✅ Database siap.\n")

    session_id = str(uuid.uuid4())
    create_session(session_id)
    
    print("💬 Ketik pesan anda (atau 'exit'/'keluar' untuk mengakhiri)\n")

    while True:
        query = input("😎 Anda: ").strip()
        
        if query.lower() in ['exit', 'keluar', 'quit', 'keluar']:
            print("\n👋 Sampai jumpa!")
            break
            
        if not query:
            continue
        
        print(f"\n[📝 Query]: {query}")
        
        if ablation_mode == "baseline":
            print("\n[Baseline] Langsung searchtanpa CQR atau dimensi...")
            result = baseline_qa.invoke({"query": query})
            
            print("\n=== DOKUMEN REFERENSI (BASELINE) ===")
            source_docs = []
            for i, doc in enumerate(result["source_documents"]):
                place_name = doc.metadata.get("place_name", "Tidak Diketahui")
                print(f"  {i+1}. {place_name} [{doc.metadata.get('category', '')}]")
                source_docs.append(f"Source {i+1}: Nama Tempat: {place_name}. Kategori: {doc.metadata.get('category', '')}")
            
            print("\n" + "=" * 60)
            print("🤖 AiYukToba (Baseline):")
            print(result["result"])
            print("=" * 60)
            
            save_message(session_id, "user", query, query)
            save_message(session_id, "ai", result["result"])
            continue
        
        # Pipeline A, Pipeline B, atau Proposed: Jalankan CA-IER (Context-Aware Intent Entity Recognition)
        print(f"\n[🔄 Modul CA-IER] Memproses konteks ({ablation_mode})...")
        prompt_history = []
        
        if ablation_mode in ["proposed", "pipeline_b_only"]:
            q1 = get_first_query(session_id)
            recent_history = get_chat_history(session_id, limit=4)
            if q1 and (not recent_history or recent_history[0][1] != q1):
                prompt_history.append(("user", f"[PESAN PERTAMA]: {q1}"))
            prompt_history.extend(recent_history)
            print(f"  [History] {len(prompt_history)} percakapan terakhir")
        
        ca_ier = get_ca_ier(query, prompt_history)
        
        print(f"\n[📤 Standalone Query]: {ca_ier.standalone_query}")
        print(f"  ├─ is_search_required: {ca_ier.is_search_required}")
        print(f"  ├─ Landscape/Content: {ca_ier.expected_landscape_content or '(none)'}")
        print(f"  ├─ Activities: {ca_ier.expected_activities or '(none)'}")
        print(f"  └─ Atmosphere: {ca_ier.expected_atmosphere or '(none)'}")
        
        if not ca_ier.is_search_required:
            print("\n[💬 Chit-Chat Mode]")
            llm = ChatOllama(model="qwen3:8b", temperature=0.5)
            casual_response = llm.invoke(f"Jawab dengan ramah: '{query}'")
            print("\n" + "=" * 60)
            print("🤖 AiYukToba:")
            print(casual_response.content)
            print("=" * 60)
            save_message(session_id, "user", query, ca_ier.standalone_query)
            save_message(session_id, "ai", casual_response.content)
            continue
        
        if ablation_mode == "pipeline_b_only":
            print("\n[Pipeline B Only] Baseline Retrieval...")
            result = baseline_qa.invoke({"query": ca_ier.standalone_query})
            
            print("\n=== DOKUMEN REFERENSI (Pipeline B) ===")
            source_docs = []
            for i, doc in enumerate(result["source_documents"][:args.top_k]):
                place_name = doc.metadata.get("place_name", "Tidak Diketahui")
                print(f"  {i+1}. {place_name} [{doc.metadata.get('category', '')}]")
                source_docs.append(f"Source {i+1}: Nama Tempat: {place_name}. Kategori: {doc.metadata.get('category', '')}")
            
            print("\n" + "=" * 60)
            print("🤖 AiYukToba (Pipeline B):")
            print(result["result"])
            print("=" * 60)
            
            save_message(session_id, "user", query, ca_ier.standalone_query)
            save_message(session_id, "ai", result["result"])
            continue
        
        if ablation_mode == "pipeline_a_only":
            print("\n[Pipeline A Only] tanpa CQR (history diabaikan)...")
        
        # Proposed / Pipeline A: Dimension-Aware Search
        print("\n[🔍 Dimension-Aware Search] Mencari di database...")
        top_results = dimension_aware_search(
            vector_db=vector_db,
            intent_dimensions=ca_ier,
            w_lan=1.0, w_act=1.0, w_atm=1.0,
            top_k=15
        )
        
        print(f"\n=== TOP {min(10, len(top_results))} HASIL PENCARIAN ===")
        for i, res in enumerate(top_results[:args.top_k]):
            print(f"  {i+1}. {res['place_name']} [{res['category']}] (score: {res['total_score']:.4f})")
        
        # Cross-Encoder Reranking
        print("\n[🎯 Cross-Encoder Reranker] Meranking ulang...")
        try:
            uadc_data_path = os.path.join(DATA_DIR, "uadc_checkpoint.json")
            with open(uadc_data_path, "r", encoding="utf-8") as f:
                uadc_data_dict = json.load(f)
        except Exception as e:
            print(f"  ⚠ Gagal load checkpoint: {e}")
            uadc_data_dict = {}
        
        reranked_results = cross_encoder_rerank(ca_ier.standalone_query, top_results, uadc_data_dict)
        
        print(f"\n=== TOP {min(5, len(reranked_results))} REKOMENDASI ===")
        for i, res in enumerate(reranked_results[:args.top_k]):
            ce_score = res.get('lrr_score', 0)
            print(f"  {i+1}. {res['place_name']} [{res['category']}]")
            print(f"      Base: {res['total_score']:.4f} → CE: {ce_score:.4f}")
            if res.get('lrr_reasoning'):
                print(f"      Reasoning: {res['lrr_reasoning'][:80]}...")
        
        # Generate Final Response
        print("\n[📝 Generating Response]...")
        final_output = generate_final_response(ca_ier.standalone_query, reranked_results, uadc_data_dict)
        
        print("\n" + "=" * 60)
        print("🤖 AiYukToba:")
        print(final_output)
        print("=" * 60)
        
        save_message(session_id, "user", query, ca_ier.standalone_query)
        save_message(session_id, "ai", final_output)


if __name__ == "__main__":
    main()