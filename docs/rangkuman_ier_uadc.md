# Laporan Implementasi Intent-Enhanced Retriever (IER) & UGC-based Attraction Database Construction (UADC)

Dokumen ini merangkum secara detail perubahan arsitektur sistem Tourism Recommender (RAG) Danau Toba yang telah diselaraskan dengan spesifikasi akademik dari paper **UGuideRAG**. Implementasi berfokus pada dua tahapan logis: Dekomposisi Niat Pengguna (IER) dan Konstruksi Database Vektor Berdimensi berdasarkan Ulasan Pengunjung (UADC).

---

## 1. Intent-Enhanced Retriever (IER) - Fase Dekomposisi Kueri

Tahap IER bertanggung jawab untuk membedah kueri alami (natural language) dari pengguna menjadi komponen niat yang terstruktur sebelum dilakukan pencarian ke *Vector Database*.

### A. Penyesuaian Dimensi (Landscape & Content)
Pada implementasi awal, dimensi fisik hanya dinamakan `expected_landscape`. Hal ini berisiko membuat Large Language Model (LLM) hanya berfokus pada bentang alam (gunung, danau) dan mengabaikan arsitektur, peninggalan sejarah, atau fasilitas buatan manusia. 
- **Refactoring:** Dimensi tersebut diubah menjadi `expected_landscape_content` sesuai nomenklatur UGuideRAG yang menggabungkan elemen alam dan buatan/konten sejarah.

### B. Restrukturisasi Skema Output (List ke Single Tuple)
- **Sebelumnya:** Output parser Pydantic menghasilkan struktur *List* (`requirements: List[IntentDimensions]`), yang menyebabkan 1 kueri dipecah menjadi *array of dimensions*. Hal ini membuat persamaan matematika pencarian Cosine Similarity menjadi rumit karena harus melakukan agregasi.
- **Setelah Perbaikan:** Struktur output diubah menjadi entitas *single tuple* (`dimensions: IntentDimensions`). Kini 1 kueri pengguna secara deterministik akan menghasilkan tepat 1 pasang representasi (Landscape & Content, Activities, Atmosphere).

### C. Pembaruan Prompt Engineering
Instruksi sistem asisten (`SYSTEM_PROMPT_IER` di `core/prompts.py`) diperbarui secara spesifik untuk memandu model **Qwen3 (4b)**. Prompt kini melatih Qwen3 untuk memahami batasan 3 dimensi secara eksak:
1. **Landscape and Content**: Bentang alam, arsitektur, lanskap fisik, peninggalan sejarah, fasilitas.
2. **Activities**: Tindakan rekreasi spesifik.
3. **Atmosphere**: Nuansa, tingkat keramaian, dan mood.

### D. Persiapan Fungsi Pencarian Berbobot
Tanda tangan (signature) fungsi `dimension_aware_search` di kerangka aplikasi utama (`modules/retriever.py`) telah dimodifikasi untuk menerima bobot kepentingan per dimensi ($w_{lan}, w_{act}, w_{atm}$). Ini akan digunakan pada tahapan agregasi skor pencarian selanjutnya.

---

## 2. UGC-based Attraction Database Construction (UADC) - Fase Ingesti Data

Tahap ini memproses ulasan mentah pengunjung (User-Generated Content) menjadi representasi multidimensi yang dapat dipetakan secara matematis di *Vector Space*.

### A. Migrasi dari Baseline Contextual Flattening ke Multidimensi
- **Problem Baseline:** Skrip `ingest-data.py` lama memotong teks CSV asimetris secara membabi buta (*chunking*) ke ukuran 1000 huruf dan melabelinya sebagai 1 berkas. Teknik ini menghilangkan konteks dan tidak bisa disejajarkan dengan kueri 3 dimensi IER.
- **Solusi UADC:** Dibuat *pipeline* baru bernama `ingest_uadc.py`. Semua gabungan ulasan dari satu tempat wisata dipasok ke LLM Qwen3 untuk di-*parsing* dan disarikan menjadi 4 atribut Pydantic: `landscape_content_features`, `activity_features`, `atmosphere_features`, dan `summary` (deskripsi umum).

### B. Mekanisme Keamanan Eksekusi (JSON Checkpointing)
Karena LLM lokal memakan waktu komputasi (GPU/CPU) yang berbanding lurus dengan jumlah tempat wisata, proses ini rentan kehilangan *progress* apabila dibatalkan secara tak sengaja.
- **Implementasi:** Skrip membaca dan menyimpan kemajuan ekstraksi AI secara berkala (genap per-2 data) ke file `uadc_checkpoint.json`. Bila program dihentikan, pengguna cukup menjalankan skrip lagi, dan data yang sudah ada di checkpoint akan otomatis dilompati (*skipped*).

### C. Pembuatan ChromaDB Terstruktur Berdasarkan Dimensi
Setelah LLM Qwen3 selesai memilah ulasan per objek wisata, data tersebut disimpan menggunakan model embedding `paraphrase-multilingual-MiniLM-L12-v2` ke pangkalan data relasional terpisah di lokal (`chroma_db_uadc`).
- **Skema Vektor:** 1 baris objek wisata di CSV kini direpresentasikan oleh **4 entri/dokumen** terpisah di dalam ChromaDB.
- **Metadata Tagging:** Tiap dokumen memiliki stiker identitas spesifik pada metadatanya (contoh: `metadata={"dimension": "landscape_content"}`). Teknik ini mendukung pengambilan pencarian berorientasi bobot dimensi di masa depan.

---

## Kesimpulan Status
1. **Model Inferensi IER:** Telah siap sedia dan terintegrasi di `app.py`. Kueri turis valid diekstrak secara *real-time* menjadi profil 3 dimensi.
2. **Ingesti UADC:** Logika *parsing* dan *checkpointing* selesai dibuat di `ingest_uadc.py`. Proses ekstraksi data skala penuh dapat dieksekusi oleh komputer Anda kapan saja.
3. **Next Step:** Ketika Database Chroma UADC sudah terisi penuh dengan fitur multidimensi, tahapan berikutnya adalah membangun algoritma pemeringkatan akhir dan kalkulasi jarak vektor di modul *Retrieval*.
