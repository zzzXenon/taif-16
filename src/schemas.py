from pydantic import BaseModel, Field
from typing import List

# 1. SKEMA UNTUK IER (INFERENCE / QUERY)
class IntentDimensions(BaseModel):
    """Skema untuk dekomposisi niat pengguna (IER) berdasarkan paper UGuideRAG."""
    expected_landscape_content: str = Field(description="Elemen visual, fisik, alam, peninggalan sejarah, fasilitas, dan arsitektur yang diharapkan.")
    expected_activities: str = Field(description="Tindakan atau kegiatan spesifik yang ingin dilakukan.")
    expected_atmosphere: str = Field(description="Nuansa, mood, atau kualitas emosional yang dicari.")

class IEROutput(BaseModel):
    """Output dari modul Intent-Enhanced Retriever."""
    dimensions: IntentDimensions

# 2. SKEMA UNTUK UADC (INGESTION / DATABASE)
class AttractionFeatures(BaseModel):
    """Skema untuk mengekstrak fitur dari ulasan (UADC)."""
    landscape_content_features: str = Field(description="Rangkuman fitur visual/fisik, pemandangan, alam, sejarah, dan bangunan dari ulasan.")
    activity_features: str = Field(description="Rangkuman aktivitas yang sering disebut pengunjung.")
    atmosphere_features: str = Field(description="Rangkuman suasana/mood berdasarkan emosi pengunjung.")
    summary: str = Field(description="Deskripsi umum/karakteristik tempat wisata.")

# 3. SKEMA UNTUK LRR (RE-RANKING)
class LRRScoring(BaseModel):
    """Skema output untuk LLM Re-Ranking."""
    reasoning: str = Field(description="Alasan logis mengapa tempat wisata ini cocok atau tidak cocok dengan kueri pengguna.")
    score: float = Field(description="Skor relasional dari 0.0 hingga 10.0.")

# 4. SKEMA UNTUK CQR (PIPELINE B - REWRITING)
class CQRResult(BaseModel):
    """Skema output dari Conversational Query Rewriting (CQR)."""
    standalone_query: str = Field(description="Kueri yang telah dibersihkan dari referensi ambigu (anaphora) dan dapat berdiri sendiri. Tetap dalam bahasa Indonesia asli.")
    is_search_required: bool = Field(description="True jika pengguna mencari rekomendasi/informasi wisata yang perlu ditarik dari database ChromaDB, False jika hanya sapaan casual/chit-chat.")