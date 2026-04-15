# Panduan Menjalankan Evaluasi RAG

Karena evaluasi ini mengirim simulasi request ke server, Anda membutuhkan **3 terminal terpisah** yang dibiarkan menyala secara bersamaan. Ikuti urutan di bawah ini:

---

## 💻 Terminal 1: Menghidupkan Ollama (LLM)
Terminal ini akan menjadi server yang mendedikasikan komputer Anda untuk menjalankan model bahasa AI lokal (Qwen3).

1. Buka terminal baru (Linux/Jupyter terminal).
2. Ketik perintah:
   ```bash
   ollama serve
   ```
*(Biarkan terminal ini terbuka. Jangan ditutup.)*

---

## 💻 Terminal 2: Menghidupkan API Server (Backend RAG)
Terminal ini menjalankan file Python yang bertanggung jawab menangani skema RAG, membaca ChromaDB, dan mengatur prompt LLM.

1. Buka terminal baru.
2. Masuk ke folder kerja dan aktifkan Python Environtment Anda:
   ```bash
   cd /home/jovyan/work/DB
   source .venv/bin/activate
   ```
3. Jalankan file API:
   ```bash
   python src/api.py
   ```
4. **Tunggu** sampai baris terakhir memunculkan log `API Ready.`.
*(Biarkan terminal ini terbuka. Nantinya Anda akan bisa melihat proses AI berpikir untuk setiap kandidat tempat wisata di sini kueri sedang dievaluasi).*

---

## 💻 Terminal 3: Menjalankan Skrip Evaluasi (Kalkulator Metrik)
Terminal inilah yang terakhir. Tugas skrip ini hanya menembakkan "fake user message" berulang kali ke Terminal 2 dan mengurus perhitungan nilai/skor matematis dari responsnya.

1. Buka terminal baru.
2. Masuk ke folder kerja dan aktifkan Python Environtment lagi:
   ```bash
   cd /home/jovyan/work/DB
   source .venv/bin/activate
   ```
3. Pilih salah satu perintah evaluasi di bawah ini untuk dijalankan secara spesifik:

   **A. Test Singkat untuk Cek Error (Selalu Lakukan Ini Dulu)**
   Mengeksekusi hanya 1 kueri pertama untuk memverifikasi apakah server mati di tengah jalan atau tidak.
   ```bash
   python scripts/run_evaluation.py --single-turn --limit 1
   ```

   **B. Eksekusi Single-Turn (100 Kueri / Baseline vs Pipeline A)**
   Menguji performa RAG biasa. *Perhatian: Karena LLM harus mereview kandidat berulang-ulang, ini membutuhkan waktu sekitar 4-6 Jam di komputer biasa.*
   ```bash
   python scripts/run_evaluation.py --single-turn
   ```

   **C. Eksekusi Multi-Turn (28 Kueri Bertahap / Pipeline B - CQR)**
   Menguji tingkat akurasi memori dan Conversation Query Rewriting LLM dari sistem Anda. *Membutuhkan waktu kurang lebih 30-45 menit.*
   ```bash
   python scripts/run_evaluation.py --multi-turn
   ```

---

### Tempat Pengecekan Hasil Akhir
Mengingat evaluasi B (4-6 jam) sangat lama, Anda tidak perlu mengamati Terminal 3 terus-menerus. Silakan ditinggal tidur. Log akan otomatis tersimpan langsung ke dalam 2 file ini meskipun layar tertutup:
* 📄 `data/eval_report.txt` (Tabel visual akhir untuk presentasi)
* ⚙️ `data/eval_results.json` (Raw JSON skor algoritma HR, MRR, NDCG untuk skrip komputasi)
