from langchain_community.document_loaders import CSVLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_community.vectorstores import Chroma
from langchain_community.chat_models import ChatOllama
from langchain_classic.chains import RetrievalQA

embedding = HuggingFaceEmbeddings(
    # model_name = "BAAI/bge-m3"
    model_name="sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2",
    model_kwargs={'local_files_only': True}
)

vector_db = Chroma(
    persist_directory="./chroma_db_baseline",
    embedding_function=embedding
)

print("✅ Vector DB load success")

llm = ChatOllama(model="qwen3:4b")

retriever = vector_db.as_retriever(search_kwargs={"k": 3})

qa_chain = RetrievalQA.from_chain_type(
    llm=llm,
    chain_type="stuff",
    retriever=retriever,
    return_source_documents=True
)

query = "Tempat minum kopi yang tenang untuk kerja?"
result = qa_chain.invoke({"query": query})

print("\nJawaban AI:\n", result["result"])
print("\nSumber:\n", result["source_documents"])
