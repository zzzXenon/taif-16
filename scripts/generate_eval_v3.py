"""
generate_eval_v3.py
--------------------
Generates evaluation ground truth files from scratch based on actual entities
in entities_final.csv and uadc_checkpoint.json.

Key principle: Ground truths are valid BY CONSTRUCTION because queries are
generated FROM the entity features already indexed in the vector DB.

Outputs:
  data/eval_ground_truths_v3.json   (Pipeline A: 50 single-turn queries)
  data/eval_pipeline_b_v2.json      (Pipeline B: 4 multi-turn scenarios)

Run:
  python scripts/generate_eval_v3.py

Override LLM model:
  EVAL_LLM=qwen3:8b python scripts/generate_eval_v3.py
"""

import os
import sys
import json
import random
import time

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(BASE_DIR, "src"))

from langchain_ollama import ChatOllama
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser

# ─────────────────────────────────────────────────
# CONFIG
# ─────────────────────────────────────────────────
CHECKPOINT_FILE    = os.environ.get("UADC_CHECKPOINT", os.path.join(BASE_DIR, "data", "uadc_checkpoint.json"))
OUT_PIPELINE_A     = os.path.join(BASE_DIR, "data", "eval_ground_truths_v3.json")
OUT_PIPELINE_B     = os.path.join(BASE_DIR, "data", "eval_pipeline_b_v2.json")
EVAL_A_CHECKPOINT  = os.path.join(BASE_DIR, "data", "eval_a_progress.json")  # resume support
LLM_MODEL          = os.environ.get("EVAL_LLM", "qwen3:14b")
OLLAMA_TIMEOUT     = int(os.environ.get("OLLAMA_TIMEOUT", "300"))  # seconds

SEED = 42
random.seed(SEED)


# ─────────────────────────────────────────────────
# LEVEL DEFINITIONS
# ─────────────────────────────────────────────────
LEVEL_SPECS = {
    1: {
        "name": "Simple",
        "n_seeds": 3,
        "description": "Query sederhana, satu dimensi/kata kunci utama, bahasa sehari-hari.",
        "example": "Carikan air terjun di kawasan Danau Toba.",
    },
    2: {
        "name": "Moderate",
        "n_seeds": 3,
        "description": "Query dengan dua kriteria: kategori tempat + satu fitur utama.",
        "example": "Hotel yang punya fasilitas kolam renang di Toba.",
    },
    3: {
        "name": "Complex",
        "n_seeds": 2,
        "description": "Query tiga dimensi: lanskap/fasilitas + aktivitas + suasana.",
        "example": "Kafe pinggir danau buat nongkrong romantis dengan live music.",
    },
    4: {
        "name": "Very Complex",
        "n_seeds": 2,
        "description": "Query empat+ constraint sangat spesifik, mencakup lokasi/kategori/aktivitas/suasana.",
        "example": "Penginapan mewah di Samosir dengan kolam renang dan view danau, suasana sepi.",
    },
    5: {
        "name": "Expert",
        "n_seeds": 1,
        "description": "Query naratif panjang, deskriptif, multi-constraint ekstrem, seperti tulisan orang yang sangat tahu apa yang dia mau.",
        "example": "Saya ingin tempat nongkrong dengan arsitektur kayu tradisional Batak yang menjorok ke tepi danau, hawanya sunyi cocok untuk bekerja, ada menu kopi khas Lintong, dan pemandangannya langsung ke Pulau Samosir.",
    },
}


# ─────────────────────────────────────────────────
# LLM HELPERS
# ─────────────────────────────────────────────────
def get_llm():
    return ChatOllama(
        model=LLM_MODEL,
        temperature=0.7,
        timeout=OLLAMA_TIMEOUT,
        keep_alive="10m",  # keep model loaded between calls
    )


def ping_ollama():
    """Send a trivial request to keep Ollama warm before a batch."""
    try:
        llm = ChatOllama(model=LLM_MODEL, temperature=0.0, keep_alive="10m")
        llm.invoke("ping")
    except Exception:
        pass


def generate_pipeline_a_query(level: int, seeds: list[dict]) -> str:
    """Generate a single-turn query from seed entity features."""
    spec = LEVEL_SPECS[level]

    seed_context = ""
    for s in seeds:
        f = s["features"]
        seed_context += (
            f"Nama: {s['place_name']} | Kategori: {s['category']}\n"
            f"  Lanskap/Fasilitas: {f['landscape_content_features']}\n"
            f"  Aktivitas: {f['activity_features']}\n"
            f"  Suasana: {f['atmosphere_features']}\n"
            f"  Ringkasan: {f['summary']}\n\n"
        )

    prompt = ChatPromptTemplate.from_messages([
        ("system", """Anda adalah penguji sistem rekomendasi wisata Danau Toba.
Tugas Anda: buat SATU query pencarian yang NATURAL seperti ditulis oleh wisatawan Indonesia sungguhan,
yang jawabannya adalah tempat-tempat berikut ini.

Aturan wajib:
- Query HARUS dalam Bahasa Indonesia yang alami dan percakapan
- Level {level} ({level_name}): {description}
- Contoh gaya query level ini: "{example}"
- Query HARUS bisa dijawab oleh SEMUA tempat yang diberikan (bukan hanya satu)
- JANGAN sebutkan nama tempat secara eksplisit dalam query
- JANGAN tambahkan penjelasan, langsung tulis querynya saja
- Panjang query: Level 1-2 = 1 kalimat; Level 3-4 = 1-2 kalimat; Level 5 = 2-4 kalimat
"""),
        ("human", "Tempat-tempat target:\n{seed_context}\n\nTulis query Level {level}:")
    ])

    chain = prompt | get_llm() | StrOutputParser()
    result = chain.invoke({
        "level": level,
        "level_name": spec["name"],
        "description": spec["description"],
        "example": spec["example"],
        "seed_context": seed_context,
    })
    return result.strip().strip('"').strip("'").strip()


def generate_pipeline_b_scenario(
    scenario_id: str,
    scenario_name: str,
    scenario_desc: str,
    anchor_entities: list[dict],
    n_turns: int,
    pivot_entities: list[dict] = None,
) -> dict:
    """Generate a full multi-turn Pipeline B scenario."""

    anchor_ctx = _format_entity_context(anchor_entities)
    pivot_ctx = _format_entity_context(pivot_entities) if pivot_entities else "Tidak ada pivot."

    prompt = ChatPromptTemplate.from_messages([
        ("system", """Anda adalah perancang skenario evaluasi sistem RAG wisata Danau Toba.
Buat skenario percakapan multi-turn antara USER dan sistem AI wisata.

ATURAN WAJIB:
1. Total turns persis = {n_turns}
2. Turns retrieval (butuh cari DB wisata): user bertanya soal tempat/hotel/resto/wisata
3. Turns chit-chat (tidak perlu DB): user komentar, ucapan terima kasih, tanya harga umum, tanya cuaca, dsb
4. Distribusi: sekitar 50-60% retrieval, 40-50% chit-chat
5. Setiap turn ada: "turn" (nomor), "message" (pesan user), "expected_standalone" (intent), "is_retrieval" (true/false), "ground_truths" (list nama entitas, kosong jika chit-chat)
6. Skenario harus NATURAL dan mengalir seperti percakapan nyata
7. Bahasa Indonesia percakapan
8. Ground truth HANYA dari nama entitas yang diberikan — JANGAN karang nama tempat lain
9. Output: JSON array dari turns saja, tanpa penjelasan

Entitas anchor (topic utama):
{anchor_ctx}

Entitas pivot (topik yang muncul di bagian akhir, opsional):
{pivot_ctx}

Deskripsi skenario: {scenario_desc}
"""),
        ("human", "Buat {n_turns} turns untuk skenario '{scenario_name}'. Output hanya JSON array:")
    ])

    chain = prompt | get_llm() | StrOutputParser()
    raw = chain.invoke({
        "n_turns": n_turns,
        "scenario_name": scenario_name,
        "scenario_desc": scenario_desc,
        "anchor_ctx": anchor_ctx,
        "pivot_ctx": pivot_ctx,
    })

    # Parse the JSON from LLM output
    turns = _parse_json_from_llm(raw, fallback=[])

    # Determine eval_turn (retrieval turns) and clean up ground_truths
    eval_turns = []
    cleaned_turns = []
    valid_names = {e["place_name"].lower() for e in (anchor_entities + (pivot_entities or []))}

    for t in turns:
        turn_num = t.get("turn", len(cleaned_turns) + 1)
        is_retrieval = t.get("is_retrieval", len(t.get("ground_truths", [])) > 0)

        # Clean ground truths — keep only valid entity names
        raw_gts = t.get("ground_truths", [])
        clean_gts = [
            g for g in raw_gts
            if any(v in g.lower() or g.lower() in v for v in valid_names)
        ]

        if is_retrieval:
            eval_turns.append(turn_num)

        cleaned_turns.append({
            "turn": turn_num,
            "message": t.get("message", ""),
            "expected_standalone": t.get("expected_standalone", ""),
            "ground_truths": clean_gts,
        })

    return {
        "id": scenario_id,
        "name": scenario_name,
        "description": scenario_desc,
        "eval_turn": eval_turns,
        "turns": cleaned_turns,
    }


def _format_entity_context(entities: list[dict]) -> str:
    if not entities:
        return "Tidak ada."
    ctx = ""
    for e in entities:
        f = e["features"]
        ctx += (
            f"- {e['place_name']} ({e['category']})\n"
            f"  Fitur: {f['summary']}\n"
            f"  Aktivitas: {f['activity_features']}\n"
        )
    return ctx


def _parse_json_from_llm(raw: str, fallback):
    """Extract JSON from LLM output, handling markdown code blocks."""
    import re
    # Strip markdown code fences
    raw = re.sub(r"```(?:json)?", "", raw).strip().rstrip("```").strip()
    # Find first [ or {
    for start_char, end_char in [("[", "]"), ("{", "}")]:
        idx = raw.find(start_char)
        if idx != -1:
            # Find matching end
            depth = 0
            for i, c in enumerate(raw[idx:], start=idx):
                if c == start_char:
                    depth += 1
                elif c == end_char:
                    depth -= 1
                    if depth == 0:
                        try:
                            return json.loads(raw[idx : i + 1])
                        except json.JSONDecodeError:
                            break
    try:
        return json.loads(raw)
    except Exception:
        return fallback


# ─────────────────────────────────────────────────
# PIPELINE A GENERATION
# ─────────────────────────────────────────────────
def build_pipeline_a(checkpoint: dict) -> list:
    entities = list(checkpoint.values())
    print(f"\n[Pipeline A] {len(entities)} entitas tersedia.")
    print(f"   Target: 10 queries × 5 levels = 50 total")

    # ── Resume from checkpoint ───────────────────
    progress: dict = {}  # {level_str: [queries]}
    if os.path.exists(EVAL_A_CHECKPOINT):
        with open(EVAL_A_CHECKPOINT, "r", encoding="utf-8") as f:
            progress = json.load(f)
        done_levels = [int(k) for k in progress]
        print(f"   Melanjutkan dari checkpoint: Level {done_levels} sudah selesai.")
    print()

    # Group by category for diverse sampling
    by_category: dict[str, list] = {}
    for e in entities:
        cat = e.get("category", "Lainnya")
        by_category.setdefault(cat, []).append(e)

    results = []

    for level in range(1, 6):
        level_key = str(level)

        # Skip if already done
        if level_key in progress:
            print(f"   Level {level} — sudah ada di checkpoint, skip.")
            results.extend(progress[level_key])
            continue

        spec = LEVEL_SPECS[level]
        n_seeds = spec["n_seeds"]
        print(f"   Level {level} ({spec['name']}) — generating 10 queries...")

        # Warm up Ollama before each level
        ping_ollama()

        queries_this_level = []
        attempts = 0
        max_attempts = 25
        cat_list = list(by_category.keys())

        while len(queries_this_level) < 10 and attempts < max_attempts:
            attempts += 1

            random.shuffle(cat_list)
            seeds = []
            for cat in cat_list:
                if len(seeds) >= n_seeds:
                    break
                pool = by_category[cat]
                if pool:
                    seeds.append(random.choice(pool))

            if len(seeds) < 1:
                continue

            try:
                query = generate_pipeline_a_query(level, seeds)
                if len(query) < 10:
                    continue

                ground_truths = [s["place_name"] for s in seeds]
                queries_this_level.append({
                    "level": level,
                    "query": query,
                    "ground_truths": ground_truths,
                })
                print(f"      [{len(queries_this_level)}/10] ✓ {query[:70]}...")

            except Exception as e:
                print(f"      [WARN] Query generation failed: {e}")
                time.sleep(2)

        # Save checkpoint after each level
        progress[level_key] = queries_this_level
        with open(EVAL_A_CHECKPOINT, "w", encoding="utf-8") as f:
            json.dump(progress, f, indent=2, ensure_ascii=False)

        results.extend(queries_this_level)
        print(f"   Level {level} done: {len(queries_this_level)} queries — checkpoint saved.\n")

    return results


# ─────────────────────────────────────────────────
# PIPELINE B GENERATION
# ─────────────────────────────────────────────────
SCENARIO_TEMPLATES = [
    {
        "id": "scenario_b_001",
        "name": "The Hotel Hunter",
        "description": "User mencari penginapan di Toba, berpindah dari budget ke mewah, diselingi chit-chat tentang fasilitas dan lokasi.",
        "n_turns": 8,
        "anchor_categories": ["Hotel", "Penginapan", "Akomodasi"],
        "pivot_categories": None,
    },
    {
        "id": "scenario_b_002",
        "name": "The Nature Explorer",
        "description": "User mencari wisata alam pantai lalu beralih ke wisata bukit/panorama, diselingi chit-chat tentang akses dan cuaca.",
        "n_turns": 9,
        "anchor_categories": ["Wisata Alam"],
        "pivot_categories": ["Wisata Alam"],
    },
    {
        "id": "scenario_b_003",
        "name": "The Food Wanderer",
        "description": "User mencari kuliner lokal halal, berpindah topik ke kafe/tempat nongkrong, diselingi chit-chat tentang harga dan menu.",
        "n_turns": 10,
        "anchor_categories": ["Restoran", "Rumah Makan", "Kuliner"],
        "pivot_categories": ["Kafe", "Cafe"],
    },
    {
        "id": "scenario_b_004",
        "name": "The Weekend Planner",
        "description": "User merencanakan liburan lengkap (wisata → makan → menginap) dalam satu sesi percakapan, dengan banyak pivot antar domain.",
        "n_turns": 11,
        "anchor_categories": ["Wisata Alam", "Wisata Budaya", "Wisata Sejarah"],
        "pivot_categories": ["Hotel", "Restoran", "Rumah Makan"],
    },
]


def _sample_entities_by_category(checkpoint: dict, categories: list[str], n: int = 3) -> list[dict]:
    """Sample n entities matching any of the given category keywords."""
    candidates = []
    for e in checkpoint.values():
        cat = e.get("category", "").lower()
        if any(kw.lower() in cat for kw in categories):
            candidates.append(e)
    if not candidates:
        # fallback: random
        candidates = list(checkpoint.values())
    return random.sample(candidates, min(n, len(candidates)))


def build_pipeline_b(checkpoint: dict) -> list:
    print(f"\n[Pipeline B] Generating 4 multi-turn scenarios...")
    results = []

    for tmpl in SCENARIO_TEMPLATES:
        print(f"\n   Scenario: {tmpl['name']} ({tmpl['n_turns']} turns)...")

        anchor = _sample_entities_by_category(
            checkpoint, tmpl["anchor_categories"], n=3
        )
        pivot = (
            _sample_entities_by_category(checkpoint, tmpl["pivot_categories"], n=2)
            if tmpl["pivot_categories"]
            else None
        )

        scenario = generate_pipeline_b_scenario(
            scenario_id=tmpl["id"],
            scenario_name=tmpl["name"],
            scenario_desc=tmpl["description"],
            anchor_entities=anchor,
            n_turns=tmpl["n_turns"],
            pivot_entities=pivot,
        )

        # Validate turn count
        actual_turns = len(scenario["turns"])
        print(f"      Turns generated: {actual_turns} (target: {tmpl['n_turns']})")
        print(f"      Eval turns: {scenario['eval_turn']}")

        results.append(scenario)

    return results


# ─────────────────────────────────────────────────
# MAIN
# ─────────────────────────────────────────────────
if __name__ == "__main__":
    print("=" * 60)
    print("  Eval Generator v3 — Building from entities_final")
    print("=" * 60)
    print(f"  LLM: {LLM_MODEL}")
    print(f"  Checkpoint: {CHECKPOINT_FILE}")

    # Load UADC checkpoint
    if not os.path.exists(CHECKPOINT_FILE):
        raise FileNotFoundError(
            f"UADC checkpoint not found: {CHECKPOINT_FILE}\n"
            "Run ingest-uadc.py first."
        )
    with open(CHECKPOINT_FILE, "r", encoding="utf-8") as f:
        checkpoint = json.load(f)
    print(f"\n  Loaded {len(checkpoint)} entities from checkpoint.")

    t_start = time.time()

    # ── Pipeline A ─────────────────────────────────
    pipeline_a = build_pipeline_a(checkpoint)
    with open(OUT_PIPELINE_A, "w", encoding="utf-8") as f:
        json.dump(pipeline_a, f, indent=2, ensure_ascii=False)
    print(f"\n✅ Pipeline A: {len(pipeline_a)} queries → {OUT_PIPELINE_A}")

    # ── Pipeline B ─────────────────────────────────
    pipeline_b = build_pipeline_b(checkpoint)
    with open(OUT_PIPELINE_B, "w", encoding="utf-8") as f:
        json.dump(pipeline_b, f, indent=2, ensure_ascii=False)
    print(f"✅ Pipeline B: {len(pipeline_b)} scenarios → {OUT_PIPELINE_B}")

    print(f"\n{'='*60}")
    print(f"  TOTAL WAKTU: {(time.time()-t_start)/60:.1f} menit")
    print(f"{'='*60}")
