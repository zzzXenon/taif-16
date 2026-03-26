
import zipfile
import xml.etree.ElementTree as ET
import os

def extract_text_from_docx(file_path):
    try:
        with zipfile.ZipFile(file_path) as docx:
            xml_content = docx.read('word/document.xml')
            tree = ET.fromstring(xml_content)
            
            ns = {'w': 'http://schemas.openxmlformats.org/wordprocessingml/2006/main'}
            
            text_parts = []
            for p in tree.findall('.//w:p', ns):
                para_text = []
                for node in p.iter():
                    if node.tag.endswith('}t'):
                        if node.text:
                            para_text.append(node.text)
                    elif node.tag.endswith('}br'):
                        para_text.append('\n')
                    elif node.tag.endswith('}cr'):
                        para_text.append('\n')
                text_parts.append("".join(para_text))
            
            return "\n".join(text_parts)

    except Exception as e:
        return f"Error reading {file_path}: {e}"

if __name__ == "__main__":
    files = ["implemen-part-1.docx", "implemen-part-2.docx"]
    with open("plan.txt", "w", encoding="utf-8") as outfile:
        for f in files:
            outfile.write(f"\n--- File: {f} ---\n")
            if os.path.exists(f):
                content = extract_text_from_docx(f)
                outfile.write(content)
            else:
                outfile.write("File not found.")
            outfile.write("\n" + "="*50 + "\n")
