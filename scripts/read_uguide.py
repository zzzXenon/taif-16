from langchain_community.document_loaders import PyPDFLoader

try:
    loader = PyPDFLoader(r"c:\Users\ASUS\labs\RAG\v2\info-source\UGuideRAG.pdf")
    pages = loader.load()
    text = "\n".join([p.page_content for p in pages])
    with open(r"c:\Users\ASUS\labs\RAG\v2\temp_uguide.txt", "w", encoding="utf-8") as out:
        out.write(text)
    print("SUCCESS")
except Exception as e:
    print(f"FAILED: {e}")
