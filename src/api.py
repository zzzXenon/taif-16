from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import sys
import os
import json

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from modules.retriever import get_ier_decomposition, dimension_aware_search, llm_reranker, generate_final_response, rewrite_query
from schemas import CQRResult
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
    retriever = baseline_db.as_retriever(search_kwargs={"k": 4})
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

@app.post("/api/chat", response_model=ChatResponse)
async def chat_endpoint(request: ChatRequest):
    query = request.message
    session_id = request.session_id
    ablation_mode = request.ablation_mode
    
    if not query.strip():
        raise HTTPException(status_code=400, detail="Pesan kosong")
        
    create_session(session_id)
    
    cqr = None
    if ablation_mode in ["pipeline_a_only", "baseline"]:
        print(f"\n[Ablation Study] Pipeline B (CQR) dinonaktifkan untuk mode '{ablation_mode}'.")
        cqr = CQRResult(standalone_query=query, is_search_required=True)
    else:
        print(f"\n[🔄 Modul CQR] Sedang membersihkan konteks...")
        q1 = get_first_query(session_id)
        recent_history = get_chat_history(session_id, limit=4)
        
        prompt_history = []
        if q1 and (not recent_history or recent_history[0][1] != q1):
            prompt_history.append(("user", f"[PESAN PERTAMA]: {q1}"))
            
        prompt_history.extend(recent_history)
        
        cqr = rewrite_query(query, prompt_history)
        
        if not cqr.is_search_required:
            print("\nAiYukToba (Chit-Chat):")
            llm = ChatOllama(model="qwen3:8b", temperature=0.5)
            casual_response = llm.invoke(f"Berdasarkan percakapan ini, jawab sapaan pengguna dengan ramah: '{query}'")
            reply = casual_response.content
            
            save_message(session_id, "user", query, cqr.standalone_query)
            save_message(session_id, "ai", reply)
            
            return ChatResponse(
                reply=reply,
                standalone_query=cqr.standalone_query,
                source_documents=[]
            )

    source_docs = []
    
    if ablation_mode in ["pipeline_b_only", "baseline"]:
        mode_nm = "Pipeline B" if ablation_mode == "pipeline_b_only" else "Baseline RAG"
        print(f"\n[Ablation Study] Menjalankan {mode_nm} dengan Pencarian Standar...")
        result = baseline_qa.invoke({"query": cqr.standalone_query})
        final_output = result["result"]
        for i, doc in enumerate(result["source_documents"]):
            place_name = doc.metadata.get("place_name", "Tidak Diketahui")
            source_docs.append(f"Source {i+1}: Nama Tempat: {place_name}. Kategori: {doc.metadata.get('category', '')}\nIsi: {doc.page_content[:200]}...")
            
        save_message(session_id, "user", query, cqr.standalone_query)
        save_message(session_id, "ai", final_output)
        
        return ChatResponse(
            reply=final_output,
            standalone_query=cqr.standalone_query,
            source_documents=source_docs
        )
        
    # Proposed (A+B) or pipeline_a_only
    print("\nSedang memproses intent dengan IER...")
    try:
        intent = get_ier_decomposition(cqr.standalone_query)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Gagal mendekomposisi niat: {e}")
        
    print("\nSedang mencari kecocokan matematis di database dimensi...")
    top_results = dimension_aware_search(
        vector_db=vector_db, 
        intent_dimensions=intent,
        w_lan=1.0, w_act=1.0, w_atm=1.0,
        top_k=4
    )
    
    print("\nSedang mengevaluasi ulang dengan LLM Re-Ranker...")
    try:
        uadc_data_path = os.path.join(DATA_DIR, "uadc_checkpoint.json")
        with open(uadc_data_path, "r", encoding="utf-8") as f:
            uadc_data_dict = json.load(f)
    except Exception:
        uadc_data_dict = {}

    reranked_results = llm_reranker(cqr.standalone_query, top_results, uadc_data_dict)
    
    format_fails = 0
    for res in reranked_results:
        if res.get("format_failed", False):
            format_fails += 1
            
        source_docs.append(
            f"🎯 {res['place_name']} ({res['category']}) "
            f"[Base Skor: {res['total_score']:.4f} -> LRR Skor: {res.get('lrr_score', 'N/A')}/10.0] "
            f"\n💡 Info: {res.get('lrr_reasoning', 'N/A')}"
        )
        
    print("\nMenyusun respons akhir (NLG)...")
    final_output = generate_final_response(cqr.standalone_query, reranked_results)
    
    save_message(session_id, "user", query, cqr.standalone_query)
    save_message(session_id, "ai", final_output)
    
    return ChatResponse(
        reply=final_output,
        standalone_query=cqr.standalone_query,
        source_documents=source_docs,
        json_parse_fails=format_fails
    )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8001)
