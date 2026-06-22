# logika utama Intent Decomposition & pencarian ChromaDB
import os
import re
import json
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from schemas import CAIEROutput
from core.prompts import SYSTEM_PROMPT_CA_IER, SYSTEM_PROMPT_NLG, SYSTEM_PROMPT_INFORMATIONAL
from sentence_transformers import CrossEncoder
from modules.llm_loader import get_chat_llm, get_chat_llm_no_think, strip_thinking

os.makedirs("logs", exist_ok=True)


def log_llm_response(module_name, raw_text):
    with open("logs/json_parsing.log", "a", encoding="utf-8") as f:
        f.write(f"\n[{module_name}] RAW OUTPUT:\n")
        f.write(raw_text)
        f.write("\n" + "-"*40 + "\n")


def _parse_ca_ier_json(raw: str, fallback_query: str) -> CAIEROutput:
    """Extract and parse JSON from LLM output, return fallback on failure."""
    # First: strip any Qwen3 <think>...</think> reasoning blocks that slipped through
    raw = strip_thinking(raw)
    # Strip markdown code fences
    raw = re.sub(r"```(?:json)?", "", raw).strip().rstrip("```").strip()
    # Find first { ... } block
    start = raw.find("{")
    if start != -1:
        depth = 0
        for i, c in enumerate(raw[start:], start=start):
            if c == "{": depth += 1
            elif c == "}":
                depth -= 1
                if depth == 0:
                    try:
                        data = json.loads(raw[start:i+1])
                        return CAIEROutput(
                            standalone_query=data.get("standalone_query", fallback_query),
                            is_search_required=bool(data.get("is_search_required", True)),
                            location=data.get("location", ""),
                            expected_landscape_content=data.get("expected_landscape_content", ""),
                            expected_activities=data.get("expected_activities", ""),
                            expected_atmosphere=data.get("expected_atmosphere", ""),
                            query_type=data.get("query_type", "recommendation"),
                            is_ambiguous=bool(data.get("is_ambiguous", False)),
                            target_category=data.get("target_category", "Semua"),
                        )
                    except Exception:
                        break
    raise ValueError(f"No valid JSON found in: {raw[:200]}")


def get_ca_ier(current_query: str, chat_history: list) -> CAIEROutput:
    llm = get_chat_llm_no_think(temperature=0.0, max_new_tokens=1024)

    history_str = "Tidak ada riwayat. Ini adalah pesan pertama."
    if chat_history:
        history_lines = []
        for role, content in chat_history:
            prefix = "User: " if role == "user" else "AI: "
            history_lines.append(f"{prefix}{content}")
        history_str = "\n".join(history_lines)

    prompt = ChatPromptTemplate.from_messages([
        ("human", SYSTEM_PROMPT_CA_IER),
    ])

    chain = prompt | llm | StrOutputParser()

    try:
        raw_result = chain.invoke({
            "chat_history": history_str,
            "current_query": current_query,
        })
        raw_result = strip_thinking(raw_result)
        log_llm_response("CA-IER", raw_result)
        return _parse_ca_ier_json(raw_result, current_query)
    except Exception as e:
        print(f"CA-IER Parse Error: {e}")
        log_llm_response("CA-IER FALLBACK", f"Exception: {e}")
        return CAIEROutput(
            standalone_query=current_query,
            is_search_required=True,
            expected_landscape_content=current_query,
            expected_activities=current_query,
            expected_atmosphere=current_query
        )

_location_cache = None

def get_dynamic_city_regency_mapping(location_query: str) -> list:
    """
    Dynamically maps a location query (which could be a village, subdistrict, or landmark)
    to its corresponding city_regency from entities_final.csv.
    """
    global _location_cache
    
    loc_clean = location_query.lower().strip()
    if not loc_clean:
        return []

    # 1. Base list of known regencies/cities in our dataset
    known_regencies = {
        "samosir": "Samosir",
        "toba": "Toba",
        "humbang hasundutan": "Humbang Hasundutan",
        "dairi": "Dairi",
        "karo": "Karo",
        "simalungun": "Simalungun",
        "tapanuli utara": "Tapanuli Utara",
        "pakpak bharat": "Pakpak Bharat",
        "pematang siantar": "Pematang Siantar",
        "balige": "Toba",
    }
    
    # If it directly matches a known regency, return it
    if loc_clean in known_regencies:
        if loc_clean == "toba" or loc_clean == "balige":
            return ["Toba", "Balige"]
        if loc_clean == "samosir":
            return ["Samosir", "Pangururan"]
        return [known_regencies[loc_clean]]

    # 2. Hardcoded mapping for common towns / subdistricts
    location_mapping = {
        "pangururan": ["Samosir", "Pangururan"],
        "parapat": ["Simalungun", "Parapat"],
        "sidikalang": ["Dairi", "Sidikalang"],
        "tarutung": ["Tapanuli Utara", "Tarutung"],
        "dolok sanggul": ["Humbang Hasundutan", "Dolok Sanggul", "Doloksanggul"],
        "doloksanggul": ["Humbang Hasundutan", "Dolok Sanggul", "Doloksanggul"],
        "kabanjahe": ["Karo", "Kabanjahe"],
        "berastagi": ["Karo", "Berastagi"],
        "salak": ["Pakpak Bharat", "Salak"],
    }
    if loc_clean in location_mapping:
        return location_mapping[loc_clean]

    # 3. Dynamic lookup from entities_final.csv
    try:
        import pandas as pd
        if _location_cache is None:
            # Resolve CSV path
            module_dir = os.path.dirname(os.path.abspath(__file__))
            project_root = os.path.dirname(os.path.dirname(module_dir))
            csv_path = os.path.join(project_root, "data", "entities_final.csv")
            if os.path.exists(csv_path):
                df = pd.read_csv(csv_path).fillna("")
                # Cache only necessary columns to save memory
                _location_cache = df[["place_name", "address", "city_regency"]].to_dict(orient="records")
            else:
                _location_cache = []
        
        # Search the cache for matches
        matches = []
        for row in _location_cache:
            place_name = str(row["place_name"]).lower()
            address = str(row["address"]).lower()
            if loc_clean in place_name or loc_clean in address:
                regency = str(row["city_regency"]).strip()
                if regency:
                    matches.append(regency)
                    
        if matches:
            # Find the most common regency
            from collections import Counter
            most_common = Counter(matches).most_common(1)[0][0]
            print(f"  [Location Match] Dynamic map '{location_query}' -> '{most_common}' based on address lookup.")
            return [most_common, location_query, location_query.title()]
    except Exception as e:
        print(f"  [WARN] Dynamic location lookup failed: {e}")

    # Fallback to the original title cased location query if all else fails
    return [location_query, loc_clean.title()]

def dimension_aware_search(vector_db, intent_dimensions, w_lan=1.0, w_act=1.0, w_atm=1.0, top_k=5):
    res_lan, res_act, res_atm = [], [], []

    lan_q = intent_dimensions.expected_landscape_content.strip()
    act_q = intent_dimensions.expected_activities.strip()
    atm_q = intent_dimensions.expected_atmosphere.strip()

    # Fallback: if all dimensions empty, use standalone_query for all
    if not lan_q and not act_q and not atm_q:
        fallback_q = intent_dimensions.standalone_query.strip()
        print(f"  [WARN] All dimensions empty — falling back to standalone query: '{fallback_q[:60]}'")
        lan_q = act_q = atm_q = fallback_q

    target_cat = getattr(intent_dimensions, "target_category", "Semua")
    location = getattr(intent_dimensions, "location", "").strip()

    # category mapping
    category_mapping = {
        "Akomodasi": ["Akomodasi"],
        "Kuliner": ["Restoran", "Kafe"],
        "Wisata": ["Wisata Alam", "Wisata Budaya & Sejarah", "Wisata Buatan", "Tempat Ibadah"],
        "Umum": ["Fasilitas Umum", "Pusat Oleh-Oleh"],
        "Semua": ["Akomodasi", "Restoran", "Kafe", "Wisata Alam", "Wisata Budaya & Sejarah", "Wisata Buatan", "Tempat Ibadah", "Fasilitas Umum", "Pusat Oleh-Oleh"]
    }
    allowed_categories = category_mapping.get(target_cat, category_mapping["Semua"])

    # Construct metadata filter
    def get_filter(dimension_name):
        and_clauses = [
            {"dimension": dimension_name},
            {"category": {"$in": allowed_categories}}
        ]
        if location:
            allowed_locations = get_dynamic_city_regency_mapping(location)
            and_clauses.append({"city_regency": {"$in": allowed_locations}})
        return {"$and": and_clauses}

    if lan_q:
        res_lan = vector_db.similarity_search_with_relevance_scores(
            lan_q, k=15, filter=get_filter("landscape_content")
        )

    if act_q:
        res_act = vector_db.similarity_search_with_relevance_scores(
            act_q, k=15, filter=get_filter("activity")
        )

    if atm_q:
        res_atm = vector_db.similarity_search_with_relevance_scores(
            atm_q, k=15, filter=get_filter("atmosphere")
        )

    item_scores = {}

    def process_results(results, weight):
        for doc, score in results:
            item_id = doc.metadata.get("item_id")
            if not item_id:
                continue

            if item_id not in item_scores:
                item_scores[item_id] = {
                    "item_id": item_id,
                    "place_name": doc.metadata.get("place_name"),
                    "category": doc.metadata.get("category"),
                    "rating": doc.metadata.get("rating"),
                    "total_score": 0.0,
                    "dimensions_found": 0
                }

            positive_score = score + 1.0
            item_scores[item_id]["total_score"] += weight * positive_score
            item_scores[item_id]["dimensions_found"] += 1

    process_results(res_lan, w_lan)
    process_results(res_act, w_act)
    process_results(res_atm, w_atm)

    final_results = list(item_scores.values())
    final_results.sort(key=lambda x: x["total_score"], reverse=True)

    return final_results[:top_k]

_cross_encoder_model = None

def get_cross_encoder():
    global _cross_encoder_model
    if _cross_encoder_model is None:
        print("\nMemuat model BAAI/bge-reranker-v2-m3 ke memori (Hanya satu kali)...")
        _cross_encoder_model = CrossEncoder('BAAI/bge-reranker-v2-m3')
    return _cross_encoder_model

def cross_encoder_rerank(standalone_query, top_results, uadc_data_dict):
    try:
        model = get_cross_encoder()
    except Exception as e:
        print(f"CrossEncoder failed to load: {e}")
        return top_results[:5]

    pairs = []
    for res in top_results:
        item_id = str(res["item_id"])
        candidate_info = uadc_data_dict.get(item_id, {})
        features = candidate_info.get("features", {})

        landscape = features.get("landscape_content_features", "")
        activities = features.get("activity_features", "")
        atmosphere = features.get("atmosphere_features", "")
        summary = features.get("summary", "")

        context_text = f"{summary} {landscape} {activities} {atmosphere}"
        pairs.append([standalone_query, context_text])

    if pairs:
        scores = model.predict(pairs)
        for idx, res in enumerate(top_results):
            res["lrr_score"] = float(scores[idx])
            res["lrr_reasoning"] = "Dinilai menggunakan Cross-Encoder."
            res["format_failed"] = False

    top_results.sort(key=lambda x: x.get("lrr_score", 0), reverse=True)

    return top_results[:5]

def generate_final_response(user_query, reranked_results, uadc_data_dict=None):
    llm = get_chat_llm(temperature=0.6, max_new_tokens=1024)

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

    return strip_thinking(response)

def generate_informational_response(user_query, reranked_results, uadc_data_dict=None):
    llm = get_chat_llm(temperature=0.4, max_new_tokens=1024)

    context_text = ""
    if reranked_results:
        res = reranked_results[0]
        item_id = str(res.get("item_id", ""))
        features = {}
        if uadc_data_dict and item_id in uadc_data_dict:
            features = uadc_data_dict[item_id].get("features", {})

        landscape = features.get("landscape_content_features", "Detail fisik tempat")
        activities = features.get("activity_features", "Aktivitas di tempat")
        atmosphere = features.get("atmosphere_features", "Suasana tempat")
        summary = features.get("summary", "Deskripsi umum")

        context_text += f"Nama Tempat: {res['place_name']}\n"
        context_text += f"Kategori: {res['category']}\n"
        context_text += f"Deskripsi: {summary}\n"
        context_text += f"Fitur Fisik/Fasilitas: {landscape}\n"
        context_text += f"Aktivitas: {activities}\n"
        context_text += f"Suasana: {atmosphere}\n"

    prompt = ChatPromptTemplate.from_messages([
        ("system", SYSTEM_PROMPT_INFORMATIONAL),
        ("human", "Kueri Pengguna: {query}\n\nInformasi Tempat Wisata:\n{context}")
    ])

    chain = prompt | llm | StrOutputParser()

    response = chain.invoke({
        "query": user_query,
        "context": context_text
    })

    return strip_thinking(response)