
import sys
import pkg_resources

print(f"Python: {sys.executable}")

try:
    import langchain
    print(f"LangChain path: {langchain.__file__}")
    print(f"LangChain version: {langchain.__version__}")
    print(f"LangChain dir: {dir(langchain)}")
except ImportError as e:
    print(f"Import langchain failed: {e}")

try:
    import langchain.chains
    print("Import langchain.chains SUCCESS")
except ImportError as e:
    print(f"Import langchain.chains BEFORE explicit import failed: {e}")

try:
    from langchain.chains import RetrievalQA
    print("Import RetrievalQA SUCCESS")
except ImportError as e:
    print(f"Import RetrievalQA FAILED: {e}")

installed_packages = [d.project_name for d in pkg_resources.working_set]
print("Installed packages:", [p for p in installed_packages if 'langchain' in p.lower()])
