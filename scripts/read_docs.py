import sys
import os

from PyPDF2 import PdfReader
from docx import Document

def main():
    # Read PDF
    try:
        reader = PdfReader("info-source/buku-pedoman.pdf")
        text = []
        for page in reader.pages:
            text.append(page.extract_text())
        
        with open("info-source/buku-pedoman.txt", "w", encoding="utf-8") as f:
            f.write("\n".join(text))
        print("PDF extracted successfully.")
    except Exception as e:
        print(f"Error parsing PDF: {e}")

    # Read DOCX
    try:
        doc = Document("info-source/dokumen.docx")
        text = []
        for para in doc.paragraphs:
            text.append(para.text)
        
        with open("info-source/dokumen.txt", "w", encoding="utf-8") as f:
            f.write("\n".join(text))
        print("DOCX extracted successfully.")
    except Exception as e:
        print(f"Error parsing DOCX: {e}")

if __name__ == "__main__":
    main()
