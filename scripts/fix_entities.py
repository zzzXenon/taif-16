import pandas as pd

def fix_entities():
    file_path = 'data/entities_final.csv'
    df = pd.read_csv(file_path)
    
    mapping = {
        "Toko Khas Parapat (Jalan lintas Parapat)": "Toko Khas Parapat",
        "Toba Nauli (Jalan Haranggaol no 3)": "Toba Nauli",
        "Pago-Pago (Jalan Haranggaol no 3)": "Pago-Pago",
        "Toko Kopi Berastagi Pak RM (Jl. Veteran, Kabanjahe)": "Toko Kopi Berastagi Pak RM",
        "Zhorenta Minyak Karo (Gg. Bakti, Kabanjahe)": "Zhorenta Minyak Karo",
        "Pasar Buah Berastagi": "Pasar Buah Berastagi",
        "Marysca Souvenir (Kawasan Tuktuk Siadong, Simanindo, Kab Samosir),22395 (0852- 6205-0368)": "Marysca Souvenir",
        "Tenun Ulos (Lumban Suhi, Pangururan, Kab Samosir), 22392 (0851-2222-34447)": "Tenun Ulos",
        "Dame Ulos Tarutung (SaiTnihuta, Banjarnahor, Hutatoruan V, Kec. Tarutung( 085297769912))": "Dame Ulos Tarutung",
        "ILLE Shop Silangi (Jalan Simpang Jl. Bandara Silangit, Parik Sabungan, Kec. Muara( 082168284768))": "ILLE Shop Silangi",
        "Basado Silangit (Silando, Kec. Muara, Kabupaten Tapanuli Utara(081355550938))": "Basado Silangit",
        "PODA Cafe And Chocolate (Jl. SM. Raja Sidikalang Kab. Dairi)": "PODA Cafe And Chocolate",
        "Toko Oleh oleh khas silalahi Danau Toba (Desa Silalahi 1.kec, Paropo, Kec. Silahsabungan, Kabupaten Dairi, 082298248264)": "Toko Oleh-oleh Khas Silalahi"
    }

    count = 0
    for idx, row in df.iterrows():
        if row['category'] == 'Pusat Oleh-Oleh' and row['address'] in mapping:
            correct_name = mapping[row['address']]
            old_name = row['place_name']
            
            # Fix place_name
            df.at[idx, 'place_name'] = correct_name
            
            # Fix the "Nama: " inside description
            desc = str(row['description'])
            if desc.startswith(f"Nama: {old_name}"):
                desc = desc.replace(f"Nama: {old_name}", f"Nama: {correct_name}", 1)
            elif desc.startswith("Nama: "):
                # Fallback if exact match fails
                lines = desc.split('\n')
                lines[0] = f"Nama: {correct_name}"
                desc = '\n'.join(lines)
                
            df.at[idx, 'description'] = desc
            count += 1

    df.to_csv(file_path, index=False)
    print(f"Berhasil memperbaiki {count} baris data yang rusak di entities_final.csv!")

if __name__ == "__main__":
    fix_entities()
