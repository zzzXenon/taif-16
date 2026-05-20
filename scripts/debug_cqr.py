import sys
import os
import time

# Ensure v2 root is in python path
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, BASE_DIR)
sys.path.insert(0, os.path.join(BASE_DIR, "src"))

from database import init_db, create_session, save_message, get_chat_history, get_first_query
from modules.retriever import get_ca_ier
from modules.llm_loader import load_model

def run_cqr_debug():
    print("=== INISIALISASI DATABASE & MODEL ===")
    init_db()
    
    # Load model if needed (handles singleton loading)
    print("Memuat model LLM Qwen3...")
    load_model()
    
    # Setup test session
    session_id = f"debug_cqr_session_{int(time.time())}"
    create_session(session_id)
    
    # 1. Turn 1
    q1 = "Rekomendasikan hotel murah di Balige."
    a1 = "Tentu! Ada Hotel Niagara (Rp 200rb/malam) dan Hotel Mulia (Rp 250rb/malam) yang cukup terjangkau."
    standalone_q1 = q1
    print(f"\n[Turn 1] User: {q1}")
    print(f"[Turn 1] AI: {a1}")
    save_message(session_id, "user", q1, standalone_q1)
    save_message(session_id, "ai", a1)
    
    # 2. Turn 2
    q2 = "Apakah ada fasilitas kolam renang di sana?"
    a2 = "Hotel Niagara memiliki kolam renang umum, sedangkan Hotel Mulia tidak menyediakannya."
    # Let's run CA-IER for Turn 2
    history_2 = []
    q1_db = get_first_query(session_id)
    recent_history_2 = get_chat_history(session_id, limit=4)
    if q1_db:
        history_2.append(("user", f"[PESAN PERTAMA]: {q1_db}"))
    history_2.extend(recent_history_2)
    
    print("\n--- Memproses Turn 2 melalui CA-IER ---")
    ca_ier_2 = get_ca_ier(q2, history_2)
    print(f"  [CQR Rewrite]: {ca_ier_2.standalone_query}")
    print(f"  [IER Dimensi]: Lan='{ca_ier_2.expected_landscape_content}', Act='{ca_ier_2.expected_activities}', Atm='{ca_ier_2.expected_atmosphere}'")
    
    save_message(session_id, "user", q2, ca_ier_2.standalone_query)
    save_message(session_id, "ai", a2)
    
    # 3. Turn 3 (The Third Query)
    q3 = "Kalau yang kedua harganya berapa?"
    print(f"\n[Turn 3] User: {q3}")
    
    # Read history for Turn 3
    history_3 = []
    q1_db = get_first_query(session_id)
    recent_history_3 = get_chat_history(session_id, limit=4)
    if q1_db and (not recent_history_3 or recent_history_3[0][1] != q1_db):
        history_3.append(("user", f"[PESAN PERTAMA]: {q1_db}"))
    history_3.extend(recent_history_3)
    
    print("\n--- Memproses Turn 3 (Kueri Ketiga) melalui CA-IER ---")
    print("Formatted History being sent to LLM:")
    for role, content in history_3:
        prefix = "User: " if role == "user" else "AI: "
        print(f"  {prefix}{content}")
    print(f"Current Query: {q3}")
    
    ca_ier_3 = get_ca_ier(q3, history_3)
    
    print("\n=== HASIL REWRITE KETIGA (CQR Output) ===")
    print(f"Standalone Query  : {ca_ier_3.standalone_query}")
    print(f"Is Search Required: {ca_ier_3.is_search_required}")
    print(f"Location Filter   : {ca_ier_3.location}")
    print(f"Landscape Content : {ca_ier_3.expected_landscape_content}")
    print(f"Activities        : {ca_ier_3.expected_activities}")
    print(f"Atmosphere        : {ca_ier_3.expected_atmosphere}")

if __name__ == "__main__":
    run_cqr_debug()
