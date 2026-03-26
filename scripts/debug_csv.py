
from langchain_community.document_loaders import CSVLoader
import traceback

files = ["wisata-toba-cleaned.csv"]
encodings = ["utf-8", "utf-8-sig", "cp1252", "latin1"]

for f in files:
    print(f"--- Testing {f} ---")
    for enc in encodings:
        print(f"Trying encoding: {enc}")
        try:
            loader = CSVLoader(file_path=f, encoding=enc)
            docs = loader.load()
            print(f"SUCCESS with {enc}. Loaded {len(docs)} docs.")
            break
        except Exception as e:
            print(f"FAILED with {enc}: {e}")
            # traceback.print_exc()
    print("="*30)
