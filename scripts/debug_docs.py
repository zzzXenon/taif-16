
import zipfile
import sys
import os

def inspect_docx(file_path):
    print(f"--- Inspecting {file_path} ---")
    try:
        with zipfile.ZipFile(file_path) as docx:
            print("Files in zip:")
            for name in docx.namelist():
                print(f" - {name}")
            
            if 'word/document.xml' in docx.namelist():
                xml_content = docx.read('word/document.xml')
                print("\nStart of word/document.xml:")
                print(xml_content[:2000].decode('utf-8', errors='ignore'))
            else:
                print("word/document.xml not found!")
    except Exception as e:
        print(f"Error: {e}")
    print("\n" + "="*50 + "\n")

if __name__ == "__main__":
    files = ["implemen-part-1.docx", "implemen-part-2.docx"]
    for f in files:
        if os.path.exists(f):
            inspect_docx(f)
        else:
            print(f"File not found: {f}")
