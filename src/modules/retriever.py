# logika utama Intent Decomposition & pencarian ChromaDB

from langchain_ollama import ChatOllama
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import PydanticOutputParser, StrOutputParser
from schemas import IEROutput, LRRScoring, CQRResult
from core.prompts import SYSTEM_PROMPT_IER, SYSTEM_PROMPT_LRR, SYSTEM_PROMPT_NLG, SYSTEM_PROMPT_CQR

def get_ier_decomposition(user_input):
    """Membedah niat menggunakan LLM dan mengembalikan objek IntentDimensions"""
    llm = ChatOllama(model="qwen3:8b", temperature=0.1)
    parser = PydanticOutputParser(pydantic_object=IEROutput)
    
    prompt = ChatPromptTemplate.from_messages([
        ("system", SYSTEM_PROMPT_IER + "\n\nBuatlah dalam format JSON yang valid:\n{format_instructions}"),
        ("human", "{query}")
    ])
    
    try:
        response = chain.invoke({
            "query": user_input,
            "format_instructions": parser.get_format_instructions()
        })
        return response.dimensions
    except Exception as e:
        # Fallback empty dimensions if JSON fails
        from schemas import IntentDimensions
        print(f"IER JSON Parse Error: {e}")
        return IntentDimensions(expected_landscape_content="", expected_activities="", expected_atmosphere="")

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

def llm_reranker(user_query, top_results, uadc_data_dict):
    """
    Modul LLM-based Reranker (LRR) untuk menilai ulang (re-rank) kandidat hasil pencarian matematis
    menggunakan model Qwen3 untuk mendapatkan penalaran logis dan skor 0-10.
    """
    llm = ChatOllama(model="qwen3:8b", temperature=0.0)
    parser = PydanticOutputParser(pydantic_object=LRRScoring)
    
    prompt = ChatPromptTemplate.from_messages([
        ("system", SYSTEM_PROMPT_LRR + "\n\nFormat jawaban:\n{format_instructions}"),
    ])
    chain = prompt | llm | parser

    reranked_results = []
    
    for res in top_results:
        item_id = str(res["item_id"])
        # Ambil full context fitur dari UADC JSON checkpoint
        candidate_info = uadc_data_dict.get(item_id, {})
        features = candidate_info.get("features", {})
        
        try:
            llm_eval = chain.invoke({
                "query": user_query,
                "place_name": res["place_name"],
                "landscape": features.get("landscape_content_features", ""),
                "activities": features.get("activity_features", ""),
                "atmosphere": features.get("atmosphere_features", ""),
                "summary": features.get("summary", ""),
                "format_instructions": parser.get_format_instructions()
            })
            
            res["lrr_score"] = llm_eval.score
            res["lrr_reasoning"] = llm_eval.reasoning
            res["format_failed"] = False
        except Exception as e:
            # Fallback jika LLM gagal mengurai JSON
            res["lrr_score"] = res["total_score"] # gunakan base score sebagai fallback
            res["lrr_reasoning"] = f"Gagal mengevaluasi reasoning: {e}"
            res["format_failed"] = True
        
        reranked_results.append(res)
    
    # Urutkan ulang (sort) berdasarkan lrr_score
    reranked_results.sort(key=lambda x: x["lrr_score"], reverse=True)
    
    # Ambil 3 rekomendasi LRR tertinggi agar hasil akhir lebih terfokus jika awalnya ada lebih dari 3
    final_lrr_candidates = reranked_results[:3]
    return final_lrr_candidates


def generate_final_response(user_query, reranked_results):
    """
    Modul Natural Language Generation (NLG).
    Mengubah hasil re-ranking kaku menjadi respons teks layaknya pemandu wisata.
    """
    llm = ChatOllama(model="qwen3:8b", temperature=0.3)
    
    # Bangun teks konteks (Knowledge) dari hasil LRR
    context_text = ""
    for i, res in enumerate(reranked_results):
        context_text += f"{i+1}. Nama Tempat: {res['place_name']}\n"
        context_text += f"   Kategori: {res['category']}\n"
        context_text += f"   Keunggulan Relavan: {res.get('lrr_reasoning', 'Sangat direkomendasikan.')}\n\n"
        
    prompt = ChatPromptTemplate.from_messages([
        ("system", SYSTEM_PROMPT_NLG),
        ("human", "Kueri Pengguna: {query}\n\nRekomendasi Tempat:\n{context}")
    ])
    
    chain = prompt | llm | StrOutputParser()
    
    response = chain.invoke({
        "query": user_query,
        "context": context_text
    })
    
    return response

def rewrite_query(current_query: str, chat_history: list) -> CQRResult:
    """
    Modul CQR: Menulis ulang kueri berdasarkan riwayat obrolan (First-plus-Last Sliding Window)
    """
    llm = ChatOllama(model="qwen3:8b", temperature=0.0)
    parser = PydanticOutputParser(pydantic_object=CQRResult)
    
    # Format riwayat chat menjadi string
    history_str = "Tidak ada riwayat. Ini adalah pesan pertama."
    if chat_history:
        history_lines = []
        for role, content in chat_history:
            prefix = "User: " if role == "user" else "AI: "
            history_lines.append(f"{prefix}{content}")
        history_str = "\n".join(history_lines)
        
    prompt = ChatPromptTemplate.from_messages([
        ("system", SYSTEM_PROMPT_CQR + "\n\nFormat output harus JSON sesuai skema berikut:\n{format_instructions}"),
    ])
    
    chain = prompt | llm | parser
    
    result = chain.invoke({
        "chat_history": history_str,
        "current_query": current_query,
        "format_instructions": parser.get_format_instructions()
    })
    
    return result