from pydantic import BaseModel, Field
from typing import List

class CAIEROutput(BaseModel):
    """Skema untuk Context-Aware Intent Extraction (CA-IER)."""
    standalone_query: str = Field(description="Kueri yang dibersihkan dari anaphora berdasarkan riwayat chat.")
    is_search_required: bool = Field(description="True jika butuh database wisata, False jika chit-chat biasa.")
    location: str = Field(default="", description="Nama kabupaten/kota yang disebutkan pengguna (tanpa prefix Kota/Kabupaten). Contoh: 'Samosir', 'Toba', 'Humbang Hasundutan'. Kosongkan jika tidak ada lokasi spesifik.")
    expected_landscape_content: str = Field(description="Kata kunci untuk lanskap/visual/fasilitas. Kosongkan jika tidak relevan.")
    expected_activities: str = Field(description="Kata kunci untuk aktivitas. Kosongkan jika tidak relevan.")
    expected_atmosphere: str = Field(description="Kata kunci untuk suasana/mood. Kosongkan jika tidak relevan.")

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
