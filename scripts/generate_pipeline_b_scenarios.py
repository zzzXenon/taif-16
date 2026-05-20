#!/usr/bin/env python3
"""
Script to generate Pipeline B multi-turn evaluation data.
This script constructs eval_pipeline_b.json using actual place data from uadc_checkpoint.json.
"""

import json
import os

def load_checkpoint_data():
    """Load the checkpoint data from uadc_checkpoint.json"""
    data_path = os.path.join(os.path.dirname(__file__), "..", "data", "uadc_checkpoint.json")
    with open(data_path, "r", encoding="utf-8") as f:
        return json.load(f)

def get_place_by_name(checkpoint_data, place_name):
    """Find a place by exact name"""
    for key, value in checkpoint_data.items():
        if value.get("place_name") == place_name:
            return value
    return None

def generate_scenario_1_chitchat_survivor():
    """
    SCENARIO 1: The Chit-Chat Survivor (8 Turns)
    Goal: Test if the system retains context through pure chit-chat.
    Setup: Pick Tao Silalahi Hotel as the final target.
    """
    scenario = {
        "id": "scenario_b_001",
        "name": "The Chit-Chat Survivor",
        "description": "Tests if the system retains context through pure chit-chat conversations without explicit place filters",
        "eval_turn": [1, 2, 5, 8],
        "turns": [
            {
                "turn": 1,
                "message": "Saya ingin mencari penginapan di sekitar Toba. Ada rekomendasi hotel atau penginapan yang bagus?",
                "expected_standalone": "cari hotel penginapan di Toba",
                "ground_truths": [
                    "Tao Silalahi Hotel",
                    "Hotel Nabasa",
                    "Hotel Sere Nauli",
                    "Mutiara Balige Hotel"
                ]
            },
            {
                "turn": 2,
                "message": "Yang punya view pemandangan danau Toba yang indah, punya kolam renang juga boleh.",
                "expected_standalone": "cari hotel dengan view danau Toba dan kolam renang",
                "ground_truths": [
                    "Tao Silalahi Hotel",
                    "Mutiara Balige Hotel"
                ]
            },
            {
                "turn": 3,
                "message": "Wah mantap! Suasananya kayak gimana ya?",
                "expected_standalone": "chit-chat tentang suasana",
                "ground_truths": []
            },
            {
                "turn": 4,
                "message": "Suhunya dingin ga disana?",
                "expected_standalone": "chit-chat tentang cuaca suhu",
                "ground_truths": []
            },
            {
                "turn": 5,
                "message": "Ada yang lebih tenang ga ya? Saya suka suasana yang sepi nih.",
                "expected_standalone": "cari hotel dengan suasana tenang sepi",
                "ground_truths": [
                    "Tao Silalahi Hotel"
                ]
            },
            {
                "turn": 6,
                "message": "Okeoke, kalau masalah harga gimana?",
                "expected_standalone": "chit-chat tentang harga",
                "ground_truths": []
            },
            {
                "turn": 7,
                "message": "Jadi kalau mau booking hari ini bisa langsung datang ga ya?",
                "expected_standalone": "chit-chat tentang booking",
                "ground_truths": []
            },
            {
                "turn": 8,
                "message": "Nah, kalau Tau Silalahi Hotel itu termasuk hotel baru atau lama ya?",
                "expected_standalone": "informasi tentang Tao Silalahi Hotel",
                "ground_truths": [
                    "Tao Silalahi Hotel"
                ]
            }
        ]
    }
    return scenario

def generate_scenario_2_constraint_pivot():
    """
    SCENARIO 2: The Constraint Pivot (9 Turns)
    Goal: Test if the system can overwrite old constraints (e.g., replacing 'murah' with 'mewah').
    Setup: Pick Tao Silalahi Hotel as target - it's expensive/luxury.
    """
    scenario = {
        "id": "scenario_b_002",
        "name": "The Constraint Pivot",
        "description": "Tests if the system can pivot from one constraint (cheap) to another (luxury) while maintaining context",
        "eval_turn": [1, 2, 3, 4, 9],
        "turns": [
            {
                "turn": 1,
                "message": "Lagi cari hotel di Toba yang murah meriah aja, buat numpang tidur sementara.",
                "expected_standalone": "cari hotel murah di Toba",
                "ground_truths": [
                    "Hotel Adela",
                    "RAP Hotel Balige",
                    "Hotel Santo Djaya"
                ]
            },
            {
                "turn": 2,
                "message": "Yang penting ada AC dan kamar mandi bersih, harga di bawah 300rb.",
                "expected_standalone": "cari hotel murah dengan AC di bawah 300rb",
                "ground_truths": [
                    "Hotel Adela",
                    "RAP Hotel Balige"
                ]
            },
            {
                "turn": 3,
                "message": "Deket pusat kota Balige ga? Supaya mudah cari makanan.",
                "expected_standalone": "cari hotel murah dekat pusat kota",
                "ground_truths": [
                    "Hotel Adela",
                    "RAP Hotel Balige",
                    "Mutiara Balige Hotel"
                ]
            },
            {
                "turn": 4,
                "message": "Eh gajadi cari yang murah, saya mau cari yang paling mewah dan fasilitas lengkap saja.",
                "expected_standalone": "cari hotel mewah dan fasilitas lengkap di Toba",
                "ground_truths": [
                    "Tao Silalahi Hotel",
                    "Thyesza Hotel Resort",
                    "Labersa Hotel and Convention Center Toba, Balige"
                ]
            },
            {
                "turn": 5,
                "message": "Wah kalau yang mewah itu bedanya dimana ya?",
                "expected_standalone": "chit-chat tentang hotel mewah",
                "ground_truths": []
            },
            {
                "turn": 6,
                "message": "Fasilitas kolam renangnya ada yang 24 jam ga?",
                "expected_standalone": "chit-chat tentang kolam renang hotel",
                "ground_truths": []
            },
            {
                "turn": 7,
                "message": "Breakfast nya juga included kan?",
                "expected_standalone": "chit-chat tentang sarapan hotel",
                "ground_truths": []
            },
            {
                "turn": 8,
                "message": " Kalau buat staycation family weekend gitu cocok ga ya?",
                "expected_standalone": "chit-chat tentang staycation keluarga",
                "ground_truths": []
            },
            {
                "turn": 9,
                "message": "Saya denger Tau Silalahi Hotel itu view-nya langsung menghadap danau ya?",
                "expected_standalone": "informasi tentang Tao Silalahi Hotel",
                "ground_truths": [
                    "Tao Silalahi Hotel"
                ]
            }
        ]
    }
    return scenario

def generate_scenario_3_cross_domain():
    """
    SCENARIO 3: The Cross-Domain Jump (11 Turns)
    Goal: Pivot from searching one category to another while keeping location context.
    Setup: Pick Sigurgur Beach & Restaurant (Nature) and a Restaurant in the same area.
    - Turn 1-4: Find the Nature place
    - Turn 5-6: Chit-chat
    - Turn 7: Pivot to Restaurant
    - Turn 8-10: Narrow down restaurant
    - Turn 11: Final filter
    """
    scenario = {
        "id": "scenario_b_003",
        "name": "The Cross-Domain Jump",
        "description": "Tests if the system can pivot from one category (Wisata Alam) to another (Restaurant/Kuliner) while maintaining location context",
        "eval_turn": [1, 2, 3, 4, 7, 8, 9, 10, 11],
        "turns": [
            {
                "turn": 1,
                "message": "Lagi cari tempat wisatam alam di Toba yang punya pantai buat berenang.",
                "expected_standalone": "cari tempat wisata alam pantai di Toba",
                "ground_truths": [
                    "Sigurgur Beach & Restaurant",
                    "Pantai Pulo Tao",
                    "Pantai Pasir Putih Parparean",
                    "Pantai Lumban Bul-bul Balige"
                ]
            },
            {
                "turn": 2,
                "message": "Yang pantainya masih bersih dan ga terlalu rame ya, punya spotlight",
                "expected_standalone": "cari pantai alami bersih dan sepi",
                "ground_truths": [
                    "Sigurgur Beach & Restaurant",
                    "Pantai Pulo Tao"
                ]
            },
            {
                "turn": 3,
                "message": "Ada yang bisa main banana boat juga ga?",
                "expected_standalone": "cari pantai dengan fasilitas banana boat",
                "ground_truths": [
                    "Sigurgur Beach & Restaurant",
                    "Pantai Lumban Bul-bul Balige",
                    "Long Beach"
                ]
            },
            {
                "turn": 4,
                "message": "Nah yang di area Silalahi itu ada ga ya?",
                "expected_standalone": "cari pantai di area Silalahi",
                "ground_truths": [
                    "Sigurgur Beach & Restaurant"
                ]
            },
            {
                "turn": 5,
                "message": "Wah beach-nya bersih banget ya, jarang2 nih nemu pantai sepi beginsi.",
                "expected_standalone": "chit-chat tentang pantai",
                "ground_truths": []
            },
            {
                "turn": 6,
                "message": "Pemandangannya langsung menghadap Toba juga kan?",
                "expected_standalone": "chit-chat tentang pemandangan",
                "ground_truths": []
            },
            {
                "turn": 7,
                "message": "Ehbtw, kalau di dekat wisata alam tadi ada restoran yang enak ga?",
                "expected_standalone": "cari restoran dekat Sigurgur Beach",
                "ground_truths": [
                    "3J Lamongan Cafe N Resto",
                    "WF Coffee&Resto",
                    "Sigurgur Beach & Restaurant",
                    "Betesda Cafe Balige"
                ]
            },
            {
                "turn": 8,
                "message": "Yang menyediakan makanan khas Batak tapi ga terlalu pedas, anak2 juga bisa makan.",
                "expected_standalone": "cari restoran makanan Batak tidak pedas",
                "ground_truths": [
                    "3J Lamongan Cafe N Resto",
                    "Sigurgur Beach & Restaurant",
                    "Restaurant Dugul"
                ]
            },
            {
                "turn": 9,
                "message": "Yang punya view danau juga bagus gitu, jadi bisa makan sambil lihat pemandangan.",
                "expected_standalone": "cari restoran dengan view danau Toba",
                "ground_truths": [
                    "WF Coffee&Resto",
                    "3J Lamongan Cafe N Resto",
                    "Betesda Cafe Balige"
                ]
            },
            {
                "turn": 10,
                "message": "Yang harga makanannya still affordable gitu ada ga ya?",
                "expected_standalone": "cari restoran harga terjangkau",
                "ground_truths": [
                    "3J Lamongan Cafe N Resto",
                    "Sigurgur Beach & Restaurant",
                    "Betesda Cafe Balige"
                ]
            },
            {
                "turn": 11,
                "message": "Kalau Sigurgur Beach & Restaurant itu makanannya biasa ga?",
                "expected_standalone": "informasi tentang Sigurgur Beach & Restaurant",
                "ground_truths": [
                    "Sigurgur Beach & Restaurant"
                ]
            }
        ]
    }
    return scenario

def main():
    print("Loading checkpoint data...")
    checkpoint_data = load_checkpoint_data()
    
    print(f"Loaded {len(checkpoint_data)} places from database")
    
    print("\n=== Generating Pipeline B Scenarios ===\n")
    
    scenarios = []
    
    print("Generating Scenario 1: The Chit-Chat Survivor...")
    s1 = generate_scenario_1_chitchat_survivor()
    scenarios.append(s1)
    print(f"  - ID: {s1['id']}")
    print(f"  - Name: {s1['name']}")
    print(f"  - Turns: {len(s1['turns'])}")
    print(f"  - Eval turns: {s1['eval_turn']}")
    
    print("\nGenerating Scenario 2: The Constraint Pivot...")
    s2 = generate_scenario_2_constraint_pivot()
    scenarios.append(s2)
    print(f"  - ID: {s2['id']}")
    print(f"  - Name: {s2['name']}")
    print(f"  - Turns: {len(s2['turns'])}")
    print(f"  - Eval turns: {s2['eval_turn']}")
    
    print("\nGenerating Scenario 3: The Cross-Domain Jump...")
    s3 = generate_scenario_3_cross_domain()
    scenarios.append(s3)
    print(f"  - ID: {s3['id']}")
    print(f"  - Name: {s3['name']}")
    print(f"  - Turns: {len(s3['turns'])}")
    print(f"  - Eval turns: {s3['eval_turn']}")
    
    output_path = os.path.join(os.path.dirname(__file__), "..", "data", "eval_pipeline_b.json")
    
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(scenarios, f, ensure_ascii=False, indent=2)
    
    print(f"\n=== Output saved to {output_path} ===\n")
    print(f"Total scenarios: {len(scenarios)}")
    
    for s in scenarios:
        turn_stats = {
            "total_turns": len(s["turns"]),
            "eval_turns": len(s["eval_turn"]),
            "chitchat_turns": sum(1 for t in s["turns"] if t["ground_truths"] == []),
            "search_turns": sum(1 for t in s["turns"] if t["ground_truths"] != [])
        }
        print(f"  {s['id']}: {turn_stats}")

if __name__ == "__main__":
    main()