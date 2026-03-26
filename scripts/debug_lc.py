
try:
    import langchain
    print(f"LangChain version: {langchain.__version__}")
except ImportError:
    print("LangChain not found")

try:
    from langchain.chains import RetrievalQA
    print("Import RetrievalQA success")
except ImportError as e:
    print(f"Import RetrievalQA failed: {e}")

try:
    import langchain.chains
    print("Import langchain.chains success")
    print(dir(langchain.chains))
except ImportError as e:
    print(f"Import langchain.chains failed: {e}")
