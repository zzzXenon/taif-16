"""
Synthetic Ground Truth Generator for UADC Tourism Data.
Generates eval ground truths using LLM reverse-engineering.
"""

import json
from pathlib import Path

from langchain.output_parsers import JsonOutputParser
from langchain.prompts import ChatPromptTemplate
from langchain_ollama import ChatOllama

# Paths
BASE_DIR = Path(__file__).resolve().parent.parent
UADC_PATH = BASE_DIR / "data" / "uadc_checkpoint.json"
OUTPUT_PATH = BASE_DIR / "data" / "eval_ground_truths_auto.json"

NUM_PLACES = 50

LLM = ChatOllama(
    model="qwen3:8b",
    temperature=0.6,
    format="json",
)

PROMPT = ChatPromptTemplate.from_messages([
    (
        "system",
        "You are a tourism data evaluator. Based on a given tourist place's features, "
        "you create specific questions that can uniquely identify that place as the answer.",
    ),
    (
        "human",
        """Baca fitur tempat wisata berikut:

Nama: {place_name}
Kategori: {category}
Rating: {rating}
Landscape/Content: {landscape_content_features}
Activities: {activity_features}
Atmosphere: {atmosphere_features}
Ringkasan: {summary}

Tugas: Buat 2 pertanyaan spesifik dalam bahasa Indonesia.

1. Pertanyaan PERTAMA (Level 1-2 | EKSPLISIT):
   - Pertanyaan faktual yang jawabannya tersurat secara eksplisit di deskripsi.
   - Contoh: 'Apa nama pantai dengan pasir putih bersih yang cocok untuk snorkeling?'
   - Fokus pada fasilitas, aktivitas, atau ciri fisik yang unik.

2. Pertanyaan KEDUA (Level 3-4 | IMPLISIT/SUASANA):
   - Pertanyaan yang memerlukan inferensi suasana, mood, atau pengalaman emosional.
   - Contoh: 'Tempat wisata apa yang cocok untuk meditasi di puncak dengan pemandangan memukau?'
   - Fokus pada atmosphere, suasana hati, nuansa unik.

KRITERI WAJIB:
- Jawaban KEDUA pertanyaan HARUS sama: NAMA TEMPAT INI ({place_name}).
- Pertanyaan harus cukup spesifik sehingga TIDAK ambigu ke tempat lain.
- Gunakan gaya bahasa natural seperti pertanyaan wisatawan sungguhan.

Kembalikan dalam format JSON berikut (hanya JSON, tanpa markdown atau teks tambahan):
{{
  "level_1_2": {{
    "query": "pertanyaan eksplisit level 1-2",
    "level": 2
  }},
  "level_3_4": {{
    "query": "pertanyaan implisit suasana level 3-4",
    "level": 4
  }},
  "ground_truths": ["{place_name}"]
}}""",
    ),
])


def build_chain():
    parser = JsonOutputParser()
    return PROMPT | LLM | parser


def load_uadc_data():
    with open(UADC_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)
    return data


def extract_features(place_entry):
    """Extract feature fields from a UADC place entry."""
    features = place_entry.get("features", {})
    return {
        "place_name": place_entry.get("place_name", "Unknown"),
        "category": place_entry.get("category", "Unknown"),
        "rating": place_entry.get("rating", 0),
        "landscape_content_features": features.get("landscape_content_features", ""),
        "activity_features": features.get("activity_features", ""),
        "atmosphere_features": features.get("atmosphere_features", ""),
        "summary": features.get("summary", ""),
    }


def generate_ground_truths(chain, place_entry):
    """Generate ground truth queries for a single place entry."""
    features = extract_features(place_entry)
    place_name = features["place_name"]

    try:
        result = chain.invoke(features)
        return {
            "place_name": place_name,
            "category": features["category"],
            "level_1_query": {
                "query": result["level_1_2"]["query"],
                "level": result["level_1_2"]["level"],
            },
            "level_3_query": {
                "query": result["level_3_4"]["query"],
                "level": result["level_3_4"]["level"],
            },
            "ground_truths": result["ground_truths"],
        }
    except Exception as e:
        print(f"  ⚠ Error for {place_name}: {e}")
        return None


def main():
    print("Loading UADC data...")
    data = load_uadc_data()

    # Sort by item_id and take first NUM_PLACES
    sorted_places = sorted(data.values(), key=lambda x: x.get("item_id", ""))
    places_to_process = sorted_places[:NUM_PLACES]

    print(f"Processing {len(places_to_process)} places (out of {len(data)} total)...")

    chain = build_chain()
    results = []

    for i, place in enumerate(places_to_process, 1):
        name = place.get("place_name", "Unknown")
        print(f"  [{i}/{len(places_to_process)}] {name}...", end=" ", flush=True)

        result = generate_ground_truths(chain, place)
        if result:
            results.append(result)
            print("✓ Done")
        else:
            print("✗ Failed")

    # Save results
    with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)

    print(f"\n{'='*60}")
    print(f"Success: {len(results)}/{NUM_PLACES} places processed")
    print(f"Output saved to: {OUTPUT_PATH}")
    print(f"{'='*60}")


if __name__ == "__main__":
    main()
