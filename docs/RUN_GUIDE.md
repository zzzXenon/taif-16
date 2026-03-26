# Panduan Eksekusi UGuideRAG

Dokumen ini berisi panduan singkat untuk menjalankan seluruh mode sistem rekomendasi wisata Danau Toba yang telah kita bangun, baik melalui Terminal (CLI) maupun Antarmuka Web (UI/UX).

**Syarat Utama:** 
Pastikan Anda selalu berada di *root folder* proyek (`c:\Users\ASUS\labs\RAG\v2`) dan *Virtual Environment* Python telah aktif:
```powershell
.\.venv\Scripts\Activate.ps1
```

---

## 💻 1. Mode Terminal (Command Line Interface)
Aplikasi CLI sangat cocok untuk pengujian *Ablation Study* secara *backend* statis dengan visibilitas log langsung. Skrip utamanya adalah `app.py`.

### A. The Proposed Model (Pipeline A + Pipeline B)
Mode *Default*. Sistem akan menggunakan *Memori Chat (CQR)* untuk melacak kata ganti (misal: "di sekitar sana"), lalu melakukan *Dimension-aware Search* dan *LLM Re-Ranking*.
```bash
python app.py
```

### B. Ablation Tingkat 1: Pipeline A Saja (Tanpa Memori LLM)
Sistem **TIDAK** akan mengingat riwayat *chat* sebelumnya. Berguna untuk membuktikan bahwa RAG konvensional (tanpa CQR) akan gagal saat pengguna memakai kata ganti "Di sana". Pencarian tetap menggunakan metode *Dimension-Aware* yang canggih.
```bash
python app.py --pipeline-a-only
```

### C. Ablation Tingkat 2: Pipeline B Saja (Pencarian Vektor Klasik)
Sistem **AKAN** mengingat riwayat chat dengan sempurna (CQR aktif), **TETAPI** hasil pencarian hanya menggunakan metode kemiripan *Keyword* (Cosine Similarity standar) dari ChromaDB tanpa dipecah ke dimensi lanskap, aktivitas, dan tanpa di- *Re-Ranking* oleh Qwen3.
```bash
python app.py --pipeline-b-only
```

*(Ketik `exit` atau `keluar` pada terminal saat aplikasi sedang berjalan untuk menghentikannya).*

---

## 🌐 2. Mode Antarmuka Web (Premium UI)
Gunakan mode ini saat demonstrasi thesis / presentasi *live* agar terlihat seperti perangkat lunak profesional. Mode Web bekerja dengan arsitektur *Client-Server*. Sistem ini dapat dikontrol saklar ablasi-nya langsung dari tombol di layar.

Anda harus membuka **Dua Terminal Baru** dan menjalankan perintah berikut secara bersamaan.

**Terminal 1 (Menyalakan Otak AI / Backend):**
Pastikan *Virtual Environment* aktif, lalu jalankan server FastAPI:
```bash
python api.py
```
*(Tunggu hingga muncul tulisan `Uvicorn running on http://127.0.0.1:8000`)*

**Terminal 2 (Menyalakan Visualisasi Perangkat Muka / Frontend):**
Buka terminal baru, masuk ke dalam folder `frontend`, dan nyalakan server *Node/React*:
```bash
cd frontend
npm run dev
```

**Melihat Hasil Akhir:**
Buka *browser* Anda (Chrome/Edge/Safari) dan ketikkan alamat:
👉 **[http://localhost:5173](http://localhost:5173)**

*Catatan: Tombol kontrol "Ablation Study Mode" ada pada kolom sebelah kiri website. Anda bisa menggantinya secara langsung sebelum mengirim pesan chat tanpa perlu mematikan server!*
