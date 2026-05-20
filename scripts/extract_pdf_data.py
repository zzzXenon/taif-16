import os
import re
import pandas as pd
import pdfplumber

def extract_text_from_pdf(pdf_path):
    text = ""
    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            text += page.extract_text() + "\n"
    return text

def parse_structure_a(text, default_category, status_tag=None):
    """Parses Review-based PDFs (Kafe, Resto, Oleh-oleh)"""
    results = []
    
    # Split blocks by double newlines or similar heuristics
    # The place name is usually followed by "Alamat :"
    blocks = re.split(r'\n(?=[^\n]+(?:\n\s*)?Alamat\s*:)', text)
    
    for i, block in enumerate(blocks):
        if 'Alamat' not in block:
            # Could be the very first block containing header info, or place name of the first item
            continue
            
        # In a split like this, the previous block contains the place name at the end
        if i == 0:
            lines = [l.strip() for l in block.split('\n') if l.strip()]
            place_name = lines[-1] if lines else ""
        else:
            # The place name is at the end of the previous block
            prev_lines = [l.strip() for l in blocks[i-1].split('\n') if l.strip()]
            place_name = prev_lines[-1] if prev_lines else ""
            
            # Since the current block has Alamat, we extract it
            alamat_match = re.search(r'Alamat\s*:\s*(.*?)(?=\nHarga|\nUlasan|$)', block, re.IGNORECASE | re.DOTALL)
            harga_match = re.search(r'Harga\s*:\s*(.*?)(?=\nUlasan|$)', block, re.IGNORECASE | re.DOTALL)
            ulasan_match = re.search(r'Ulasan\s*:\s*(.*)', block, re.IGNORECASE | re.DOTALL)
            
            if not place_name or not alamat_match:
                # Sometimes the place name is the first line of the current block if split failed
                lines = [l.strip() for l in block.split('\n') if l.strip()]
                if 'Alamat' in lines[0]:
                    pass # Place name is definitely in previous block
                else:
                    place_name = lines[0]
            
            # Clean place name
            place_name = re.sub(r'\(Halal\)', '', place_name, flags=re.IGNORECASE).strip()
            place_name = re.sub(r'\(Non\s*-\s*Halal\)', '', place_name, flags=re.IGNORECASE).strip()
            
            alamat = alamat_match.group(1).replace('\n', ' ').strip() if alamat_match else ""
            harga = harga_match.group(1).replace('\n', ' ').strip() if harga_match else "-"
            ulasan = ulasan_match.group(1).replace('\n', ' ').strip() if ulasan_match else "-"
            
            if ulasan == '-' or not ulasan:
                ulasan_text = ""
            else:
                ulasan_text = f"[Kumpulan Ulasan dari Pengunjung]: [Ulasan 1]: {ulasan}"
            
            desc_lines = [
                f"Nama: {place_name}",
                f"Kategori: {default_category}",
                f"Alamat: {alamat}",
                f"Harga: {harga}"
            ]
            
            if status_tag:
                desc_lines.insert(3, f"[Status]: {status_tag}")
                
            if ulasan_text:
                desc_lines.append(ulasan_text)
                
            description = "\n".join(desc_lines)
            
            city_regency = ""
            if "Toba" in alamat or "Balige" in alamat or "Porsea" in alamat:
                city_regency = "Toba"
            elif "Simalungun" in alamat or "Parapat" in alamat:
                city_regency = "Simalungun"
            elif "Dairi" in alamat or "Sidikalang" in alamat:
                city_regency = "Dairi"
            elif "Karo" in alamat or "Berastagi" in alamat:
                city_regency = "Karo"
            elif "Tapanuli Utara" in alamat or "Tarutung" in alamat or "Muara" in alamat:
                city_regency = "Tapanuli Utara"
            elif "Samosir" in alamat:
                city_regency = "Samosir"
            elif "Humbang Hasundutan" in alamat or "Dolok Sanggul" in alamat:
                city_regency = "Humbang Hasundutan"
            
            results.append({
                "place_name": place_name,
                "category": default_category,
                "address": alamat,
                "city_regency": city_regency,
                "description": description
            })
            
    return results

def parse_structure_b(text, default_category):
    """Parses Description-based PDFs (Fasilitas Umum)"""
    results = []
    
    blocks = re.split(r'\n(?=[^\n]+(?:\n\s*)?Deskripsi\s*:)', text)
    
    for i, block in enumerate(blocks):
        if 'Deskripsi' not in block:
            continue
            
        if i == 0:
            lines = [l.strip() for l in block.split('\n') if l.strip()]
            place_name = lines[-1] if lines else ""
        else:
            prev_lines = [l.strip() for l in blocks[i-1].split('\n') if l.strip()]
            place_name = prev_lines[-1] if prev_lines else ""
            
        deskripsi_match = re.search(r'Deskripsi\s*:\s*(.*?)(?=\nLong & Lat|\nLokasi|$)', block, re.IGNORECASE | re.DOTALL)
        lokasi_match = re.search(r'Lokasi\s*:\s*(.*?)(?=\nKategori|$)', block, re.IGNORECASE | re.DOTALL)
        kategori_match = re.search(r'Kategori\s*:\s*(.*)', block, re.IGNORECASE | re.DOTALL)
        
        deskripsi = deskripsi_match.group(1).replace('\n', ' ').strip() if deskripsi_match else ""
        lokasi = lokasi_match.group(1).replace('\n', ' ').strip() if lokasi_match else ""
        sub_kategori = kategori_match.group(1).replace('\n', ' ').strip() if kategori_match else default_category
        
        desc_lines = [
            f"Nama: {place_name}",
            f"Kategori: {sub_kategori}",
            f"Alamat: {lokasi}",
            f"Deskripsi Umum: {deskripsi}"
        ]
        
        description = "\n".join(desc_lines)
        
        city_regency = ""
        if "Toba" in lokasi or "Balige" in lokasi or "Porsea" in lokasi:
            city_regency = "Toba"
        elif "Simalungun" in lokasi or "Parapat" in lokasi:
            city_regency = "Simalungun"
        elif "Dairi" in lokasi or "Sidikalang" in lokasi:
            city_regency = "Dairi"
        elif "Karo" in lokasi or "Berastagi" in lokasi:
            city_regency = "Karo"
        elif "Tapanuli Utara" in lokasi or "Tarutung" in lokasi or "Muara" in lokasi:
            city_regency = "Tapanuli Utara"
        elif "Samosir" in lokasi:
            city_regency = "Samosir"
        elif "Humbang Hasundutan" in lokasi or "Dolok Sanggul" in lokasi:
            city_regency = "Humbang Hasundutan"
            
        results.append({
            "place_name": place_name,
            "category": default_category, # Use top-level category for schema
            "address": lokasi,
            "city_regency": city_regency,
            "description": description
        })
        
    return results

def main():
    os.makedirs("data", exist_ok=True)
    
    # 1. Pusat Oleh-Oleh
    print("Processing Pusat Oleh-Oleh...")
    text_oleh = extract_text_from_pdf("data-pdf-new/data pusat oleh oleh.pdf")
    data_oleh = parse_structure_a(text_oleh, "Pusat Oleh-Oleh")
    pd.DataFrame(data_oleh).to_csv("data/pdf-pusat-oleh-oleh.csv", index=False)
    
    # 2. Kuliner
    print("Processing Kuliner...")
    text_cafe = extract_text_from_pdf("data-pdf-new/data cafe.pdf")
    data_cafe = parse_structure_a(text_cafe, "Kafe")
    
    text_halal = extract_text_from_pdf("data-pdf-new/data rumah makan.pdf")
    data_halal = parse_structure_a(text_halal, "Restoran (Halal)", status_tag="Halal")
    
    text_nonhalal = extract_text_from_pdf("data-pdf-new/data rumah makan non halal.pdf")
    data_nonhalal = parse_structure_a(text_nonhalal, "Restoran (Non-Halal)", status_tag="Non-Halal")
    
    data_kuliner = data_cafe + data_halal + data_nonhalal
    pd.DataFrame(data_kuliner).to_csv("data/pdf-kuliner.csv", index=False)
    
    # 3. Fasilitas Umum
    print("Processing Fasilitas Umum...")
    text_fasum = extract_text_from_pdf("data-pdf-new/data fasilitas umum.pdf")
    data_fasum = parse_structure_b(text_fasum, "Fasilitas Umum")
    pd.DataFrame(data_fasum).to_csv("data/pdf-fasilitas-umum.csv", index=False)
    
    print("Extraction complete! Check the data/ folder for 3 new CSV files.")

if __name__ == "__main__":
    main()
