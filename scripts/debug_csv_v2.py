
from langchain_community.document_loaders import CSVLoader
import traceback

files = ["wisata-toba-cleaned.csv"]
encodings = ["utf-8", "utf-8-sig", "latin1", "cp1252"]

with open("csv_debug_log.txt", "w") as log:
    for f in files:
        log.write(f"--- Testing {f} ---\n")
        print(f"Testing {f}")
        for enc in encodings:
            log.write(f"Trying encoding: {enc}\n")
            print(f"Trying {enc}")
            try:
                loader = CSVLoader(file_path=f, encoding=enc)
                docs = loader.load()
                msg = f"SUCCESS with {enc}. Loaded {len(docs)} docs.\n"
                log.write(msg)
                print(msg)
                break
            except Exception as e:
                msg = f"FAILED with {enc}: {e}\n"
                log.write(msg)
                print(msg)
        log.write("="*30 + "\n")
