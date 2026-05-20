import pandas as pd
import re
import os

def remove_emojis(text):
    if not isinstance(text, str):
        return text
    # Remove emojis and other non-standard symbols using regex
    # Matches typical emoji unicode ranges
    emoji_pattern = re.compile(
        r'[\U00010000-\U0010ffff]'
        r'|[\u2700-\u27BF]'
        r'|[\uE000-\uF8FF]'
        r'|[\u2011-\u26FF]'
    )
    return emoji_pattern.sub(r'', text)

def clean_slang(text):
    if not isinstance(text, str):
        return text
        
    slang_dict = {
        r'\bgak\b': 'tidak',
        r'\bnggak\b': 'tidak',
        r'\bngga\b': 'tidak',
        r'\bsdh\b': 'sudah',
        r'\bdgn\b': 'dengan',
        r'\byg\b': 'yang',
        r'\btpt\b': 'tempat',
        r'\baja\b': 'saja',
        r'\bbrp\b': 'berapa',
        r'\bbgt\b': 'banget',
        r'\bapa2\b': 'apa-apa',
        r'\butk\b': 'untuk',
        r'\bkrn\b': 'karena',
        r'\bbgs\b': 'bagus',
        r'\btrs\b': 'terus',
        r'\btp\b': 'tapi'
    }
    
    for slang, formal in slang_dict.items():
        # Use regex substitution with ignorecase
        text = re.sub(slang, formal, text, flags=re.IGNORECASE)
        
    return text

def remove_redundant_kategori(text):
    if not isinstance(text, str):
        return text
    # Remove lines that start with "Kategori:" in the description
    return re.sub(r'^Kategori:\s*.*?\n', '', text, flags=re.MULTILINE)

def consolidate_category(cat):
    if not isinstance(cat, str):
        return cat
        
    cat = cat.strip()
    
    if cat in ['Hotel', 'Hotel bintang 2', 'Hotel bintang 3', 'Guest house', 'Rumah wisata', 'Pondok', 'Vila', 'Hotel Resor', 'Motel']:
        return 'Akomodasi'
    elif cat in ['Wisata Budaya / Sejarah', 'Museum']:
        return 'Wisata Budaya & Sejarah'
    elif cat in ['Wisata Buatan', 'Wisata Bisnis']:
        return 'Wisata Buatan'
    elif cat == 'Balai Masyarakat':
        return 'Fasilitas Umum'
    elif cat in ['Restoran', 'China']:
        return 'Restoran'
    elif cat == 'Wisata Rohani':
        return 'Tempat Ibadah'
    else:
        # Wisata Alam, Pariwisata / UMKM, etc will remain as is
        return cat

def main():
    input_file = "data/entities_final.csv"
    output_file = "data/entities_final_cleaned.csv"
    
    if not os.path.exists(input_file):
        print(f"File {input_file} not found.")
        return
        
    print(f"Loading {input_file}...")
    df = pd.read_csv(input_file)
    
    print("Cleaning descriptions (removing emojis, slang, and redundant 'Kategori: ' line)...")
    df['description'] = df['description'].apply(remove_emojis)
    df['description'] = df['description'].apply(clean_slang)
    df['description'] = df['description'].apply(remove_redundant_kategori)
    
    print("Consolidating categories...")
    df['category'] = df['category'].apply(consolidate_category)
    
    print(f"Saving cleaned data to {output_file}...")
    df.to_csv(output_file, index=False)
    
    print("Clean up complete! Here is the new category distribution:")
    print(df['category'].value_counts())

if __name__ == "__main__":
    main()
