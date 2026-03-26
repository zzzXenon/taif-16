
try:
    import langchain_classic.chains
    print("Import langchain_classic.chains SUCCESS")
except ImportError as e:
    print(f"Import langchain_classic.chains FAILED: {e}")

try:
    from langchain.chains import RetrievalQA
    print("Import langchain.chains.RetrievalQA SUCCESS")
except ImportError as e:
    print(f"Import langchain.chains.RetrievalQA FAILED: {e}")

import importlib
try:
    importlib.import_module("langchain.chains")
    print("importlib langchain.chains SUCCESS")
except ImportError as e:
    print(f"importlib langchain.chains FAILED: {e}")
