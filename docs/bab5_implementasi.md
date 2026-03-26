# BAB 5
# IMPLEMENTASI

Bab ini menguraikan proses implementasi logis dari sistem rekomendasi pariwisata Danau Toba berbasis arsitektur *Retrieval-Augmented Generation* (RAG) yang telah dioptimalkan (UGuideRAG). Sesuai dengan rancangan pada bab sebelumnya, implementasi dipecah menjadi beberapa fase fungsional utama yang dibangun secara modular, mulai dari tahap pembangunan basis pengetahuan (*knowledge base*) hingga perakitan antarmuka pengguna, tanpa menampilkan detail kode sintaksis mentah, melainkan berfokus pada logika operasional sistem.

## 5.1 Lingkungan Implementasi
Implementasi sistem dilakukan pada lingkungan lokal dan terisolasi dengan spesifikasi komputasi tingkat tinggi untuk mengeksekusi *Large Language Model* (LLM) secara efisien.
- **Perangkat Keras**: Pemrosesan utama (inferensi LLM dan pencarian vektor) dijalankan menggunakan akselerator kartu grafis standar dari arsitektur lokal yang kompatibel dengan akselerasi paralel, merujuk pada batasan mesin *server*.
- **Perangkat Lunak Utama**:
  - *Engine* Bahasa: Keluarga **Qwen 3** (*Multilingual LLM*) via *platform* inferensi *Ollama* lokal.
  - *Vector Database*: **ChromaDB** yang bersifat persisten, digunakan untuk penyimpanan multidimensi.
  - Model *Embeddings*: **HuggingFace** (`LazarusNLP/all-indo-e5-small-v4`) yang dioptimalkan khusus untuk pemrosesan semantik bahasa Indonesia, digunakan untuk mengubah teks ke ruang vektor padat (*dense vector*).
  - *Orkestrator RAG*: *Framework* fleksibel berbasis **LangChain** (Python).
  - Integrasi Layanan: Backend dibangun dengan **FastAPI**, menjembatani komunikasi data menuju antarmuka grafis Web yang dirakit menggunakan **Vite** dan **ReactJS**.

## 5.2 Realisasi Solusi terhadap Rumusan Masalah
Sebelum merinci setiap modul teknis, arsitektur sistem ini didesain secara spesifik untuk menjawab dua rumusan masalah utama penelitian:

1. **Penyelesaian Masalah 1 (Pemrosesan Multi-Intent Query)**: Kelemahan RAG standar dalam mengatasi kueri turis yang memuat banyak niat sekaligus (pemandangan, aktivitas, dan suasana) yang kerap memicu fenomena *flattening* diselesaikan melalui implementasi terintegrasi dari modul **UADC** (*User-Aware Data Construction*), **IER** (*Intent-Enhanced Retriever*), dan **LRR** (*LLM Re-Ranking*). Sistem tidak lagi mencari satu parameter secara kompresi tunggal, melainkan membedah niat pengguna menjadi 3 dimensi terpisah, mencari informasi relevannya secara berbobot, dan memeringkat ulang hasilnya layaknya kurasi kepakaran tur manusia. Hal ini secara proporsional menjawab kelemahan sistem konvensional.
2. **Penyelesaian Masalah 2 (Pemeliharaan Konteks Multi-Turn)**: Masalah degradasi memori sistem ("amnesia konteks") saat menghadapi rujukan kata ganti (contoh: "di sana") dalam percakapan yang panjang diselesaikan sepenuhnya melalui modul **CQR** (*Conversational Query Rewriting*). Solusi ini dioperasikan menggunakan pola *First-plus-Last Sliding Window* yang menghemat beban komputasi *prompt*, serta dipadukan dengan paradigma *Rewrite-Retrieve-Read* yang merumuskan ulang pertanyaan bias menjadi *standalone query* (*self-contained*) yang utuh sebelum dilakukan pencarian informasi baru.

Keberhasilan realisasi logis dari kedua solusi di atas secara kohesif dijabarkan melalui arsitektur penyusunan modul teknis pada sub-bab 5.3 hingga 5.6 berikut ini.

## 5.3 Implementasi Pembuatan Basis Pengetahuan (UADC)
Tahap pertama adalah membangun otak memori statis dari sistem. Proses modifikasi data pariwisata yang mentah (*dataset* CSV) menjadi format yang bisa dicerna *Vector Database* dikerjakan menggunakan logika *User-Aware Data Construction* (UADC).

1. **Ekstraksi Berbasis LLM**: Sistem diinstruksikan untuk membaca setiap baris destinasi wisata dan merangkum deskripsinya ke dalam tiga dimensi pengalaman turis, yaitu Pemandangan (*Landscape & Content*), Aktivitas (*Activities*), dan Suasana (*Atmosphere*).
2. **Pecahan Dokumen Terisolasi**: Hasil rangkuman dari LLM dipotong (*chunking*) dan dipetakan secara eksklusif berdasar tiga dimensi di atas beserta satu rangkuman utuh. Masing-masing dokumen tersebut diinjeksi dengan *metadata* spesifik.
3. **Penyimpanan Matriks**: Proses konversi kalimat menjadi deretan angka matematis (vektor) dilakukan agar ChromaDB dapat dengan instan melakukan kalkulasi jarak antar informasi di memori penyimpanannya.

## 5.4 Implementasi Pencarian Multi-Intent (IER)
Sistem menolak kueri pengguna yang digabungkan menjadi satu kesatuan (*flattening*). Implementasi pencarian dimodifikasi menggunakan logika *Intent-Enhanced Retriever* (IER) agar dapat melayani preferensi turis yang variatif.

1. **Dekomposisi Niat Terstruktur**: Setiap permintaan masuk dari wisatawan ditangkap oleh LLM. LLM memecah syarat dari pengguna menjadi objek JSON tiga bagian yang identik dengan arsitektur UADC (dimensi *Landscape*, *Activity*, *Atmosphere*).
2. **Dimension-Aware Search**: Mesin pencari (ChromaDB) diinstruksikan secara *paralel* untuk mencari kandidat wisata yang paling mirip secara matematis terhadap masing-masing dimensi hasil pecahan tadi.
3. **Penyatuan dan Kalkulasi Skor**: Sistem mengalkulasi *Cosine Similarity* berbobot agregatif untuk memunculkan daftar Top-K (*Top candidates*) rekomendasi wisata yang menyeimbangkan semua keinginan dimensi si turis secara proporsional.

## 5.5 Implementasi LLM Re-Ranking dan Sintesis Jawaban (NLG)
Implementasi perhitungan jarak matematis di atas masih rentan terhadap kebutaan semantik (*semantic mismatch*). Oleh karenanya, sistem dilengkapi tahap evaluasi kualitatif dan generasi jawaban natural.

1. **Evaluasi Re-Ranker (LRR)**: Daftar rekomendasi teratas yang ditangkap secara kasar oleh mesin pencari akan diserahkan ulang kepada LLM (Qwen3). LLM bertindak layaknya juri manusia yang membaca kesesuaian profil tempat wisata terhadap niat asli pengguna, kemudian memberikan skor logika (1-10) beserta alasannya. Rekomendasi diurutkan ulang berdasarkan total skor gabungan LRR tersebut.
2. **Generasi Respons (NLG)**: Kandidat yang menempati peringkat tertinggi dari proses fusi LRR diumpankan sebagai bahan rujukan utama (konteks) bagi fungsi *Natural Language Generation*. Di fase ini, sistem merakit balasan menggunakan gaya bahasa pemandu wisata yang ramah, informatif, dan tidak berhalusinasi.

## 5.6 Implementasi Pemeliharaan Konteks Percakapan (CQR)
Guna melayani komunikasi multi-putaran layaknya manusia, sistem diimplementasikan dengan komponen retensi ingatan proaktif agar sistem "tidak amnesia" di kala turis membalas dengan kalimat bergantung-konteks seperti *"Bagaimana dengan cuaca di sana?"*.

1. **Manajemen Memori Transaksional**: Sistem menggunakan pangkalan data relasional ringan (SQLite) terenkapsulasi *Session ID* spesifik. Setiap obrolan manusia dan *bot* direkam berurutan.
2. **Jendela Percakapan Berpola (First-plus-Last Sliding Window)**: Guna menghemat konsumsi token LLM asisten, hanya riwayat pertanyaan absolut paling pertama dan empat riwayat obrolan terbaru dikumpulkan sebagai acuan sejarah (*history log*).
3. **Strategi Rewrite-Retrieve-Read**: Sebelum masuk ke ranah pembedahan IER, kueri yang samar akan ditulis ulang dengan rujukan utuh oleh LLM berdasarkan *history log* (misal: "di sana" diubah secara internal menjadi "di Desa Adat Batak"). Proses pencarian selanjutnya (*Retrieve*) dan peringkasan jawaban akhir (*Read*) terjamin akurasi targetnya.

## 5.7 Integrasi Orkestrasi dan Arsitektur Multi-Pipeline
Agar seluruh komponen riset ini dapat diuji secara ilmiah berdasarkan metode *Ablation Study*, sistem diimplementasikan dalam arsitektur gerbang terpadu, baik *backend* maupun *frontend*.

1. **Logika Kontrol Ablasi Tingkat Lanjut**: Mesin aplikasi dikonfigurasi menggunakan struktur kontrol kondisional penyekat, di mana alur dapat dialihkan secara dinamis. Parameter kendali yang dibangun meliputi:
   - **Mode Penuh (A+B)**: Mengaktifkan CQR untuk ingatan dan IER untuk pembedahan matematis dimensi rekomendasi wisata.
   - **Mode Pipeline A**: Menonaktifkan modul memori *Rewrite*, mencerminkan sistem RAG tangguh tapi dengan limitasi amnesia dialog multi-tur.
   - **Mode Pipeline B**: Mematikan kecanggihan dimensi IER; kembali ke pencarian *Dense Retrieval* usang dengan memori CQR tetap menyala.
   - **Mode Baseline RAG**: Menonaktifkan seluruh komponen modifikasi pakar (tanpa IER dan tanpa CQR), merepresentasikan arsitektur RAG konvensional murni sebagai garis dasar (*baseline*) perbandingan riset.
2. **Implementasi Komunikasi End-to-End**: Logika *Ablation* dibungkus ke dalam kerangka *Backend* FastAPI berbasis REST yang menjamin rute HTTP asinkron berkecepatan tinggi, dan difasilitasi oleh Antarmuka Web Premium interaktif di pihak pengguna berbasis React, di mana sakelar mode eksperimen dapat diubah-suai saat itu juga.

## 5.8 Skenario Pengujian Operasional
Pasca integrasi alur kerja RAG tingkat lanjut di atas, skenario pembuktian disiapkan secara sistematis. Sistem akan diuji berdasarkan koleksi kuesioner kompleks yang merangkumi fenomena penjejalan instruksi hingga level "5-Intent", serta skenario serbuan dialog beruntun untuk menilai keandalan ingatan sistem versus parameter uji batas wajar standar RAG murni. Evaluasi empiris dan pengangkatan nilai kualitatif skenario pengujian akan dijabarkan lebih lanjut pada ruang lingkup analitika di Bab 6.
