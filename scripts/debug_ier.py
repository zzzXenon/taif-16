import sys
import os

# Ensure v2 root is in python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from langchain_community.chat_models import ChatOllama
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import PydanticOutputParser
from schemas import IEROutput
from core.prompts import SYSTEM_PROMPT_IER

def test_ier():
    print("Inisialisasi LLM...")
    llm = ChatOllama(model="qwen3:4b", temperature=0.1)
    
    parser = PydanticOutputParser(pydantic_object=IEROutput)
    
    prompt = ChatPromptTemplate.from_messages([
        ("system", SYSTEM_PROMPT_IER + "\n\nBuatlah dalam format JSON yang valid:\n{format_instructions}"),
        ("human", "{query}")
    ])
    
    chain = prompt | llm | parser
    
    query = "Saya ingin berwisata ke tempat yang sejuk, banyak bangunan bersejarah yang indah, dan saya bisa bersepeda keliling tempat itu bersama keluarga dengan tenang."
    print("\nMenganalisis Query:", query)
    
    try:
        response = chain.invoke({
            "query": query,
            "format_instructions": parser.get_format_instructions()
        })
        print("\n=== HASIL DEKOMPOSISI IER ===")
        print("Tipe Output:", type(response))
        print("Landscape & Content:", response.dimensions.expected_landscape_content)
        print("Activities:", response.dimensions.expected_activities)
        print("Atmosphere:", response.dimensions.expected_atmosphere)
        print("\nSUCCESS!")
    except Exception as e:
        print("\nError:", e)
        
if __name__ == "__main__":
    test_ier()
