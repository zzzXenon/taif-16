from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import sys
import os
import json
import time

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from modules.retriever import get_ca_ier, dimension_aware_search, cross_encoder_rerank, generate_final_response
from schemas import CAIEROutput
from database import init_db, create_session, save_message, get_chat_history, get_first_query

from langchain_chroma import Chroma
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_ollama import ChatOllama
from langchain_classic.chains import RetrievalQA

app = FastAPI(title="UGuideRAG API Backend", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE_DIR, "data")

CHROMA_PATH = os.path.join(DATA_DIR, "chroma_db_uadc")
EMBEDDING_MODEL = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"

vector_db = None
baseline_db = None
baseline_qa = None

@app.on_event("startup")
def startup_event():
    global vector_db, baseline_db, baseline_qa
    print("Mempersiapkan database rekam jejak (SQLite)...")
    init_db()
    
    print("Mempersiapkan database wisata dimensi (ChromaDB UADC)...")
    embedding_model = HuggingFaceEmbeddings(
        model_name=EMBEDDING_MODEL,
        model_kwargs={'device': 'cpu', 'local_files_only': False},
        encode_kwargs={'normalize_embeddings': True}
    )
    vector_db = Chroma(persist_directory=CHROMA_PATH, embedding_function=embedding_model)
    
    print("Mempersiapkan database wisata KLASIK (Baseline)...")
    baseline_db = Chroma(persist_directory=os.path.join(DATA_DIR, "chroma_db_baseline"), embedding_function=embedding_model)
    
    llm = ChatOllama(model="qwen3:8b", temperature=0.7)
    retriever = baseline_db.as_retriever(search_kwargs={"k": 5})
    baseline_qa = RetrievalQA.from_chain_type(
        llm=llm,
        chain_type="stuff",
        retriever=retriever,
        return_source_documents=True
    )
    print("API Ready.")

class ChatRequest(BaseModel):
    session_id: str
    message: str
    ablation_mode: str = "proposed" # 'proposed', 'pipeline_a_only', 'pipeline_b_only', 'baseline'

class ChatResponse(BaseModel):
    reply: str
    standalone_query: str
    source_documents: list[str] = []
    json_parse_fails: int = 0
    latency_seconds: float = 0.0

@app.post("/api/chat", response_model=ChatResponse)
async def chat_endpoint(request: ChatRequest):
    start_time_total = time.time()
    
    query = request.message
    session_id = request.session_id
    ablation_mode = request.ablation_mode
    
    if not query.strip():
        raise HTTPException(status_code=400, detail="Pesan kosong")
        
    create_session(session_id)
    
    ca_ier = None
    if ablation_mode == "baseline":
        print("\n[Ablation Study] Menjalankan Baseline RAG murni.")
        ca_ier = CAIEROutput(
            standalone_query=query, 
            is_search_required=True,
            expected_landscape_content="",
            expected_activities="",
            expected_atmosphere=""
        )
    else:
        print(f"\n[🔄 Modul CA-IER] Memproses Kueri...")
        prompt_history = []
        
        # Pipeline A Only ignores chat history to test isolated retrieval
        if ablation_mode in ["proposed", "pipeline_b_only"]:
            q1 = get_first_query(session_id)
            recent_history = get_chat_history(session_id, limit=4)
            if q1 and (not recent_history or recent_history[0][1] != q1):
                prompt_history.append(("user", f"[PESAN PERTAMA]: {q1}"))
            prompt_history.extend(recent_history)
        
        start_ca_ier = time.time()
        ca_ier = get_ca_ier(query, prompt_history)
        time_ca_ier = time.time() - start_ca_ier
        print(f"  [Timer] CA-IER Selesai dalam {time_ca_ier:.2f} detik")
        
        if not ca_ier.is_search_required:
            print("\nAiYukToba (Chit-Chat):")
            start_nlg = time.time()
            llm = ChatOllama(model="qwen3:8b", temperature=0.5)
            casual_response = llm.invoke(f"Berdasarkan percakapan ini, jawab sapaan pengguna dengan ramah: '{query}'")
            reply = casual_response.content
            time_nlg = time.time() - start_nlg
            print(f"  [Timer] Casual Chat Selesai dalam {time_nlg:.2f} detik")
            
            save_message(session_id, "user", query, ca_ier.standalone_query)
            save_message(session_id, "ai", reply)
            
            total_time = time.time() - start_time_total
            print(f"== [Timer] TOTAL KESELURUHAN: {total_time:.2f} detik ==\n")
            return ChatResponse(
                reply=reply,
                standalone_query=ca_ier.standalone_query,
                source_documents=[],
                latency_seconds=total_time
            )

    source_docs = []
    
    if ablation_mode in ["pipeline_b_only", "baseline"]:
        mode_nm = "Pipeline B" if ablation_mode == "pipeline_b_only" else "Baseline RAG"
        print(f"\n[Ablation Study] Menjalankan {mode_nm} dengan Pencarian Standar...")
        start_base = time.time()
        result = baseline_qa.invoke({"query": ca_ier.standalone_query})
        time_base = time.time() - start_base
        print(f"  [Timer] {mode_nm} QA Selesai dalam {time_base:.2f} detik")
        
        final_output = result["result"]
        for i, doc in enumerate(result["source_documents"]):
            place_name = doc.metadata.get("place_name", "Tidak Diketahui")
            source_docs.append(f"Source {i+1}: Nama Tempat: {place_name}. Kategori: {doc.metadata.get('category', '')}\nIsi: {doc.page_content[:200]}...")
            
        save_message(session_id, "user", query, ca_ier.standalone_query)
        save_message(session_id, "ai", final_output)
        
        total_time = time.time() - start_time_total
        print(f"== [Timer] TOTAL KESELURUHAN: {total_time:.2f} detik ==\n")
        return ChatResponse(
            reply=final_output,
            standalone_query=ca_ier.standalone_query,
            source_documents=source_docs,
            latency_seconds=total_time
        )
        
    # Proposed (A+B) or pipeline_a_only
    print("\nSedang mencari kecocokan matematis di database dimensi...")
    start_db = time.time()
    top_results = dimension_aware_search(
        vector_db=vector_db, 
        intent_dimensions=ca_ier,
        w_lan=1.0, w_act=1.0, w_atm=1.0,
        top_k=15 # Lebarkan corong untuk cross-encoder
    )
    time_db = time.time() - start_db
    print(f"  [Timer] Pencarian Database Selesai dalam {time_db:.2f} detik")
    
    print("\nSedang mengevaluasi ulang dengan Cross-Encoder Reranker...")
    try:
        uadc_data_path = os.path.join(DATA_DIR, "uadc_checkpoint.json")
        with open(uadc_data_path, "r", encoding="utf-8") as f:
            uadc_data_dict = json.load(f)
    except Exception:
        uadc_data_dict = {}

    start_lrr = time.time()
    reranked_results = cross_encoder_rerank(ca_ier.standalone_query, top_results, uadc_data_dict)
    time_lrr = time.time() - start_lrr
    print(f"  [Timer] Cross-Encoder Reranker Selesai dalam {time_lrr:.2f} detik")
    
    format_fails = 0
    for res in reranked_results:
        if res.get("format_failed", False):
            format_fails += 1
            
        source_docs.append(
            f"🎯 {res['place_name']} ({res['category']}) "
            f"[Base Skor: {res['total_score']:.4f} -> Cross-Encoder Skor: {res.get('lrr_score', 0):.4f}]"
        )
        
    print("\nMenyusun respons akhir (NLG)...")
    start_nlg = time.time()
    final_output = generate_final_response(ca_ier.standalone_query, reranked_results, uadc_data_dict)
    time_nlg = time.time() - start_nlg
    print(f"  [Timer] NLG Selesai dalam {time_nlg:.2f} detik")
    
    save_message(session_id, "user", query, ca_ier.standalone_query)
    save_message(session_id, "ai", final_output)
    
    total_time = time.time() - start_time_total
    print(f"== [Timer] TOTAL KESELURUHAN: {total_time:.2f} detik ==\n")
    
    return ChatResponse(
        reply=final_output,
        standalone_query=ca_ier.standalone_query,
        source_documents=source_docs,
        json_parse_fails=format_fails,
        latency_seconds=total_time
    )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8001)
