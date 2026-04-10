import os
import pandas as pd
import glob
import PyPDF2

data_dir = "data-pdf-new"

print("=== EVALUATING CSVs ===")
csv_files = glob.glob(os.path.join(data_dir, "*.csv"))
for csv in csv_files:
    print(f"\n[FILE]: {os.path.basename(csv)}")
    try:
        df = pd.read_csv(csv, nrows=2)
        print(f"Columns: {list(df.columns)}")
        if 'description' in df.columns or 'review' in df.columns:
            print("Found description/review column!")
            for col in ['description', 'review']:
                if col in df.columns:
                    print(f"Sample {col}:\n{df[col].iloc[0][:200]}..." if pd.notna(df[col].iloc[0]) else "NaN")
        else:
            print("No rich descriptive columns found. Mostly metadata.")
    except Exception as e:
        print(f"Error reading {csv}: {e}")

print("\n=== EVALUATING PDFs ===")
pdf_files = glob.glob(os.path.join(data_dir, "*.pdf"))
for pdf in pdf_files:
    print(f"\n[FILE]: {os.path.basename(pdf)}")
    try:
        with open(pdf, 'rb') as f:
            reader = PyPDF2.PdfReader(f)
            if len(reader.pages) > 0:
                first_page = reader.pages[0].extract_text()
                # Print first 300 characters of the PDF content
                snippet = first_page[:300].replace('\n', ' ')
                print(f"Content Snippet: {snippet}...")
            else:
                print("Empty PDF.")
    except Exception as e:
        print(f"Error or PyPDF2 not installed: {e}")
