
import zipfile
import xml.etree.ElementTree as ET
import os

def extract_text_from_docx(file_path):
    try:
        with zipfile.ZipFile(file_path) as docx:
            xml_content = docx.read('word/document.xml')
            tree = ET.fromstring(xml_content)
            
            # Namespace map often needed, but ElementTree handles basic usually.
            # Namespaces in docx are complex. But we can just find all 'w:t' or similar.
            # Actually, standard ElementTree needs namespaces if they are in the tag name.
            # But the tags come out like {http://schemas.openxmlformats.org/wordprocessingml/2006/main}t
            
            text_parts = []
            
            # Find all paragraphs
            # The namespace URI is usually consistent
            ns = {'w': 'http://schemas.openxmlformats.org/wordprocessingml/2006/main'}
            
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
    for f in files:
        print(f"--- File: {f} ---")
        if os.path.exists(f):
            print(extract_text_from_docx(f))
        else:
            print("File not found.")
        print("\n" + "="*50 + "\n")
