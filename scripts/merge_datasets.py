import pandas as pd
import os

def main():
    cleaned_old = "data/entities_final_cleaned.csv"
    pdf_files = [
        "data/pdf-pusat-oleh-oleh.csv",
        "data/pdf-kuliner.csv",
        "data/pdf-fasilitas-umum.csv"
    ]
    output_file = "data/entities_final.csv"
    backup_file = "data/entities_final_backup.csv"
    
    print("Loading cleaned old dataset...")
    df_old = pd.read_csv(cleaned_old)
    dfs = [df_old]
    
    for pdf_file in pdf_files:
        if os.path.exists(pdf_file):
            print(f"Loading new PDF dataset: {pdf_file}...")
            df_pdf = pd.read_csv(pdf_file)
            dfs.append(df_pdf)
        else:
            print(f"Warning: {pdf_file} not found. Skipping.")
            
    print("Merging all datasets...")
    df_merged = pd.concat(dfs, ignore_index=True)
    
    # Backup the original entities_final.csv if it exists and hasn't been backed up yet
    if os.path.exists(output_file) and not os.path.exists(backup_file):
        print(f"Backing up original {output_file} to {backup_file}...")
        os.rename(output_file, backup_file)
    elif os.path.exists(output_file):
        # We can just overwrite it since we already have a backup
        pass
        
    print(f"Saving merged dataset to {output_file}...")
    df_merged.to_csv(output_file, index=False)
    
    print("Merge complete! Final category distribution:")
    print(df_merged['category'].value_counts())
    print(f"Total entries: {len(df_merged)}")

if __name__ == "__main__":
    main()
