# Panduan Setup

## 🛠️ Persyaratan Sistem (Prerequisites)
Pastikan sistem operasi Anda (Windows/Linux/Mac) sudah terinstal:
1. **Python 3.10+** (Untuk *Backend* FastAPI & LangChain AI)
2. **Node.js v18+** (Untuk *Frontend* React)
3. **Git** (Opsional, untuk *cloning*)
4. **Ollama** (Wajib terinstal dan dijalankan di local background dengan model `qwen3:1b` ter-*pull*. Command: `ollama run qwen3:1b`)

## Langkah 1: Persiapan Repositori & Backend
Buka terminal/CMD Anda dan ikuti instruksi berikut:

**1. Clone Repositori**
```bash
git clone https://github.com/zzzXenon/taif-16.git
cd taif-16
```

**2. Buat dan Aktifkan Virtual Environment (Sangat Disarankan)**
```bash
# Windows
python -m venv .venv
.venv\Scripts\activate

# Mac/Linux
python3 -m venv .venv
source .venv/bin/activate
```

**3. Instal Dependensi Python**
Anda wajib menginstal pustaka modul inti yang mengoperasikan sistem AI dan aplikasi *web*:
```bash
# Instal seluruh paket melalui file requirements
pip install -r requirements.txt

# Atau, Anda juga dapat menginstalnya secara manual:
pip install langchain langchain-community langchain-chroma chromadb sentence-transformers ollama fastapi uvicorn pydantic pandas
```

## Langkah 2: Pemrosesan Data & *Vector Database* (ChromaDB)
Repositori GitHub **tidak** menyimpan *database* vektor (*ChromaDB*) karena terlalu berat dan diblokir melalui `.gitignore`. Anda harus "menanam" vektornya sendiri pada komputer pertama kali:

**1. Ekstraksi Data Mentah Menjadi Golden Dataset (Opsional)**
*Jika file `data/wisata-toba-unified-final.csv` sudah ada di folder hasil download, lewati langkah ini.*
```bash
python scripts/process-new-data.py
```

**2. Membangun Vektor UGuideRAG (Proposed Mode)**
Menjalankan *Semantic Chunking* berbasis 3 Dimensi (*Landscape, Activities, Atmosphere*) menggunakan model *embedding* `LazarusNLP`. Membutuhkan waktu beberapa menit.
```bash
python scripts/ingest-uadc.py
```

**3. Membangun Vektor Baseline RAG (Pembanding)**
Untuk kebutuhan Ablation Study (Chapter 6), bangun juga *database* pembanding menggunakan pemotongan karakter biasa:
```bash
python scripts/ingest-data.py
```

Setelah berhasil, Anda akan melihat folder `data/chroma_db_uadc/` dan `data/chroma_db_baseline/` secara lokal.

## Langkah 3: Setup Frontend (Antarmuka React)
Buka tab terminal **baru** (biarkan tab *backend* terbuka atau tutup sementaranya tidak apa-apa):
```bash
cd frontend
npm install
```

## Langkah 4: Cara Menjalankan Keseluruhan Sistem 

Untuk menggunakan web aplikasi interaktif, Anda membutuhkan 2 terminal yang berjalan secara paralel:

### Terminal 1 (Menjalankan API Backend)
Pastikan Anda berada di *root folder* (folder `taif-16/` atau tempat Anda melakukan kloning) dan *virtual environment* Python Anda sedang aktif:
```bash
python -m uvicorn src.api:app --reload --port 8000
```
> Server FastAPI akan berjalan di `http://localhost:8000`

### Terminal 2 (Menjalankan UI Frontend)
Berpindahlah ke dalam folder `frontend/` lalu jalankan server React:
```bash
cd frontend
npm run dev
```
> Buka tautan lokal yang muncul (misalnya `http://localhost:5173`) di *browser*, dan Sistem Chat RAG Toba Anda siap digunakan!

---

## 🔍 Cara Pengujian Evaluasi (*Ablation Study*)
Aplikasi web ini memiliki modul uji (Ablation Mode) di layar UI. Anda dapat dengan dinamis mengganti *pipeline* pemrosesan:
1. **Proposed UGuideRAG**: Pipeline Lengkap (IER UADC + CQR LRR)
2. **Ablation A (Retrieval Only)**: Hanya IER UADC (Tanpa penyimpanan Konteks CQR)
3. **Ablation B (Conversation Only)**: Hanya CQR LRR (Tanpa UADC, menggunakan Baseline Chunking)
4. **Standard RAG Baseline**: Tanpa sistem cerdas modifikasi sama sekali.

Gunakan skenario 100 *query* yang ada di `docs/eval_dataset_queries.md` untuk mengukur HR, MRR, NDCG, dan Recall. 