# logika utama Intent Decomposition & pencarian ChromaDB

from langchain_ollama import ChatOllama
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import PydanticOutputParser, StrOutputParser
from schemas import CAIEROutput
from core.prompts import SYSTEM_PROMPT_CA_IER, SYSTEM_PROMPT_NLG
from sentence_transformers import CrossEncoder
import os

os.makedirs("logs", exist_ok=True)

def log_llm_response(module_name, raw_text):
    """Fungsi pembantu untuk mencatat raw output LLM ke file log."""
    with open("logs/json_parsing.log", "a", encoding="utf-8") as f:
        f.write(f"\n[{module_name}] RAW OUTPUT:\n")
        f.write(raw_text)
        f.write("\n" + "-"*40 + "\n")

def get_ca_ier(current_query: str, chat_history: list) -> CAIEROutput:
    """Modul CA-IER: Menganalisis riwayat obrolan dan mengekstrak dimensi pencarian sekaligus."""
    llm = ChatOllama(model="qwen3:8b", temperature=0.0, format="json")
    parser = PydanticOutputParser(pydantic_object=CAIEROutput)
    
    # Format riwayat chat menjadi string
    history_str = "Tidak ada riwayat. Ini adalah pesan pertama."
    if chat_history:
        history_lines = []
        for role, content in chat_history:
            prefix = "User: " if role == "user" else "AI: "
            history_lines.append(f"{prefix}{content}")
        history_str = "\n".join(history_lines)
        
    prompt = ChatPromptTemplate.from_messages([
        ("system", SYSTEM_PROMPT_CA_IER + "\n\nBuatlah dalam format JSON yang valid sesuai instruksi:\n{format_instructions}"),
    ])
    
    chain = prompt | llm | StrOutputParser()
    
    try:
        raw_result = chain.invoke({
            "chat_history": history_str,
            "current_query": current_query,
            "format_instructions": parser.get_format_instructions()
        })
        log_llm_response("CA-IER", raw_result)
        result = parser.parse(raw_result)
        return result
    except Exception as e:
        print(f"CA-IER Parse Error: {e}")
        return CAIEROutput(
            standalone_query=current_query, 
            is_search_required=True,
            expected_landscape_content="",
            expected_activities="",
            expected_atmosphere=""
        )

def dimension_aware_search(vector_db, intent_dimensions, w_lan=1.0, w_act=1.0, w_atm=1.0, top_k=5):
    """
    Mencari di ChromaDB per dimensi dengan bobot:
    Score_i = w_lan * sim(query_lan, item_lan) + w_act * sim(query_act, item_act) + w_atm * sim(query_atm, item_atm)
    """
    # 1. Kueri terpisah untuk setiap dimensi
    res_lan = vector_db.similarity_search_with_relevance_scores(
        intent_dimensions.expected_landscape_content, 
        k=15, 
        filter={"dimension": "landscape_content"}
    )
    
    res_act = vector_db.similarity_search_with_relevance_scores(
        intent_dimensions.expected_activities, 
        k=15, 
        filter={"dimension": "activity"}
    )
    
    res_atm = vector_db.similarity_search_with_relevance_scores(
        intent_dimensions.expected_atmosphere, 
        k=15, 
        filter={"dimension": "atmosphere"}
    )

    # Dictionary untuk menyimpan agregasi skor per item_id
    item_scores = {}
    
    # Fungsi pembantu untuk memproses hasil kueri
    def process_results(results, weight):
        for doc, score in results:
            item_id = doc.metadata.get("item_id")
            if not item_id: continue
            
            if item_id not in item_scores:
                item_scores[item_id] = {
                    "item_id": item_id,
                    "place_name": doc.metadata.get("place_name"),
                    "category": doc.metadata.get("category"),
                    "rating": doc.metadata.get("rating"),
                    "total_score": 0.0,
                    "dimensions_found": 0
                }
            
            # Tambahkan bagian bobot
            item_scores[item_id]["total_score"] += weight * score
            item_scores[item_id]["dimensions_found"] += 1
            
    # Memproses ketiga hasil kueri
    process_results(res_lan, w_lan)
    process_results(res_act, w_act)
    process_results(res_atm, w_atm)
    
    # Konversi dictionary ke list dan urutkan berdasarkan skor total secara descending
    final_results = list(item_scores.values())
    final_results.sort(key=lambda x: x["total_score"], reverse=True)
    
    # Kembalikan hanya Top-K
    return final_results[:top_k]

_cross_encoder_model = None

def get_cross_encoder():
    global _cross_encoder_model
    if _cross_encoder_model is None:
        print("\nMemuat model Qwen3-Reranker-0.6B ke memori (Hanya satu kali)...")
        _cross_encoder_model = CrossEncoder('Qwen/Qwen3-Reranker-0.6B', trust_remote_code=True)
    return _cross_encoder_model

def cross_encoder_rerank(standalone_query, top_results, uadc_data_dict):
    """
    Menilai ulang kandidat menggunakan Cross-Encoder (Qwen3-Reranker-0.6B).
    """
    try:
        model = get_cross_encoder()
    except Exception as e:
        print(f"CrossEncoder failed to load: {e}")
        # Return fallback if model fails
        return top_results[:3]
        
    pairs = []
    for res in top_results:
        item_id = str(res["item_id"])
        candidate_info = uadc_data_dict.get(item_id, {})
        features = candidate_info.get("features", {})
        
        # Gabungkan semua fitur menjadi satu teks konteks yang kaya
        landscape = features.get("landscape_content_features", "")
        activities = features.get("activity_features", "")
        atmosphere = features.get("atmosphere_features", "")
        summary = features.get("summary", "")
        
        context_text = f"{summary} {landscape} {activities} {atmosphere}"
        pairs.append([standalone_query, context_text])
        
    # Prediksi skor menggunakan Cross-Encoder
    if pairs:
        scores = model.predict(pairs)
        for idx, res in enumerate(top_results):
            # Normalize or just attach raw score. BGE outputs logit scores.
            res["lrr_score"] = float(scores[idx])
            # Remove reasoning since CrossEncoder doesn't output text
            res["lrr_reasoning"] = "Dinilai menggunakan Cross-Encoder."
            res["format_failed"] = False
            
    # Sort descending based on Cross-Encoder score
    top_results.sort(key=lambda x: x.get("lrr_score", 0), reverse=True)
    
    return top_results[:3]


def generate_final_response(user_query, reranked_results, uadc_data_dict=None):
    """
    Modul Natural Language Generation (NLG).
    Mengubah hasil re-ranking menjadi respons teks dengan penalaran logis.
    """
    llm = ChatOllama(model="qwen3:8b", temperature=0.3)
    
    # Bangun teks konteks (Knowledge) dari hasil Reranking + Fitur UADC
    context_text = ""
    for i, res in enumerate(reranked_results):
        item_id = str(res.get("item_id", ""))
        features = {}
        if uadc_data_dict and item_id in uadc_data_dict:
            features = uadc_data_dict[item_id].get("features", {})
            
        landscape = features.get("landscape_content_features", "Pemandangan alam")
        activities = features.get("activity_features", "Aktivitas wisata umum")
        atmosphere = features.get("atmosphere_features", "Suasana nyaman")
            
        context_text += f"{i+1}. Nama Tempat: {res['place_name']}\n"
        context_text += f"   Kategori: {res['category']}\n"
        context_text += f"   Fitur Lanskap/Fasilitas: {landscape}\n"
        context_text += f"   Aktivitas: {activities}\n"
        context_text += f"   Suasana: {atmosphere}\n\n"
        
    prompt = ChatPromptTemplate.from_messages([
        ("system", SYSTEM_PROMPT_NLG),
        ("human", "Kueri Pengguna: {query}\n\nRekomendasi Tempat dan Fiturnya:\n{context}")
    ])
    
    chain = prompt | llm | StrOutputParser()
    
    response = chain.invoke({
        "query": user_query,
        "context": context_text
    })
    
    return response

