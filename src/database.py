import sqlite3
import os

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_PATH = os.path.join(BASE_DIR, "data", "chat_history.db")

def init_db():
    """Inisialisasi tabel untuk sesi dan histori chat."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Tabel Sessions
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS sessions (
            session_id TEXT PRIMARY KEY,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Tabel Messages (menyimpan raw dialog & hasil standalone query)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id TEXT,
            role TEXT,
            content TEXT,
            standalone_content TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(session_id) REFERENCES sessions(session_id)
        )
    ''')
    
    conn.commit()
    conn.close()

def create_session(session_id: str):
    """Membuat sesi baru jika belum ada."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('INSERT OR IGNORE INTO sessions (session_id) VALUES (?)', (session_id,))
    conn.commit()
    conn.close()

def save_message(session_id: str, role: str, content: str, standalone_content: str = None):
    """Menyimpan isi pesan AI atau User ke database."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO messages (session_id, role, content, standalone_content)
        VALUES (?, ?, ?, ?)
    ''', (session_id, role, content, standalone_content))
    conn.commit()
    conn.close()

def get_chat_history(session_id: str, limit: int = 6):
    """
    Menarik $N$ pesan terakhir (ideal = 6 atau 3 pasang).
    Dikembalikan dalam urutan kronologis yang benar.
    """
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT role, content 
        FROM messages 
        WHERE session_id = ? 
        ORDER BY id DESC 
        LIMIT ?
    ''', (session_id, limit))
    
    rows = cursor.fetchall()
    conn.close()
    
    # Karena kita ORDER BY DESC (agar dapat N teratas), hasilnya terbalik (baru -> lama)
    # Kita harus mereverse list-nya menjadi urutan baca (lama -> baru)
    return rows[::-1]

def get_first_query(session_id: str):
    """
    Mendapatkan pesan PERTAMA (Q1) sebagai anchor topik.
    """
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT content 
        FROM messages 
        WHERE session_id = ? AND role = 'user'
        ORDER BY id ASC 
        LIMIT 1
    ''', (session_id,))
    
    row = cursor.fetchone()
    conn.close()
    
    return row[0] if row else None
