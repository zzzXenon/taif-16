import sqlite3
import os
import sys
import argparse

# Find the database path
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_PATH = os.path.join(BASE_DIR, "data", "chat_history.db")

def list_sessions():
    if not os.path.exists(DB_PATH):
        print(f"Database tidak ditemukan di path: {DB_PATH}")
        return
        
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    try:
        # Dapatkan semua sesi beserta jumlah pesan di dalamnya
        cursor.execute('''
            SELECT s.session_id, s.created_at, COUNT(m.id) as msg_count
            FROM sessions s
            LEFT JOIN messages m ON s.session_id = m.session_id
            GROUP BY s.session_id
            ORDER BY s.created_at DESC
        ''')
        sessions = cursor.fetchall()
        
        if not sessions:
            print("Tidak ada sesi chat yang terdaftar di database.")
            return
            
        print("\n=== DAFTAR SESI CHAT DI DATABASE ===")
        print(f"{'No':<3} | {'Session ID':<35} | {'Dibuat Pada':<19} | {'Jml Pesan':<9}")
        print("-" * 75)
        for idx, (sess_id, created, count) in enumerate(sessions):
            print(f"{idx+1:<3} | {sess_id:<35} | {created:<19} | {count:<9}")
        print("-" * 75)
        
    except sqlite3.OperationalError as e:
        print(f"Error mengakses database: {e}")
        print("Pastikan skema database sudah diinisialisasi dengan menjalankan API backend atau skrip debug terlebih dahulu.")
    finally:
        conn.close()

def show_session_detail(session_id):
    if not os.path.exists(DB_PATH):
        print(f"Database tidak ditemukan di path: {DB_PATH}")
        return
        
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    try:
        cursor.execute('''
            SELECT id, role, content, standalone_content, created_at
            FROM messages
            WHERE session_id = ?
            ORDER BY id ASC
        ''', (session_id,))
        messages = cursor.fetchall()
        
        if not messages:
            print(f"\nTidak ditemukan pesan untuk Session ID: '{session_id}'")
            return
            
        print(f"\n=====================================================================")
        print(f" DETAIL HISTORI UNTUK SESI: {session_id}")
        print(f"=====================================================================")
        
        for msg_id, role, content, standalone, created in messages:
            print(f"\n[{created}] #{msg_id} - {role.upper()}:")
            print(f"  Raw Content: {content.strip()}")
            if role == "user":
                print(f"  CQR Standalone Query: {standalone if standalone else 'NULL / Sama dengan Raw'}")
            print("-" * 69)
            
    except sqlite3.OperationalError as e:
        print(f"Error membaca pesan: {e}")
    finally:
        conn.close()

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Melihat history percakapan RAG di SQLite")
    parser.add_argument("--session", type=str, help="Session ID yang ingin dilihat detailnya")
    args = parser.parse_args()
    
    if args.session:
        show_session_detail(args.session)
    else:
        list_sessions()
        print("\nPetunjuk:")
        print("1. Untuk melihat detail histori sesi, jalankan:")
        print("   python scripts/view_chat_history.py --session <SESSION_ID>")
