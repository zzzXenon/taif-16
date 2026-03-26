
import sys
print(f"Python executable: {sys.executable}")
print(f"Python version: {sys.version}")

try:
    import langchain
    print(f"LangChain version: {langchain.__version__}")
except ImportError as e:
    print(f"LangChain import failed: {e}")

try:
    import langchain_community
    print(f"LangChain Community version: {langchain_community.__version__}")
except ImportError as e:
    print(f"LangChain Community import failed: {e}")

try:
    from langchain.chains import RetrievalQA
    print("from langchain.chains import RetrievalQA SUCCESS")
except ImportError as e:
    print(f"from langchain.chains import RetrievalQA FAILED: {e}")

try:
    from langchain_community.document_loaders import CSVLoader
    print("from langchain_community.document_loaders import CSVLoader SUCCESS")
except ImportError as e:
    print(f"from langchain_community.document_loaders import CSVLoader FAILED: {e}")
