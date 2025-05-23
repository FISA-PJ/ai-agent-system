# pip install -qU langchain-core langchain-upstage
import os
import time
from dotenv import load_dotenv
import html2text
from langchain_upstage import UpstageDocumentParseLoader
from bs4 import BeautifulSoup
    
load_dotenv()

upstage_api_key = os.getenv("UPSTAGE_API_KEY") 

# conda activate pdf_upstage_py312
def pdf_upstageparser(file_path, output_dir, safe_name) :
    start = time.time()
    loader = UpstageDocumentParseLoader(
        file_path=file_path,
        model="document-parse",
        split="none",           # 'none', 'element', 'page' 중 선택
        output_format="html",     # 'text' 또는 'html'
        ocr="force",          # 이미지에서 텍스트 추출 여부
    )

    docs = loader.load()
    end = time.time()
    
    # html 형식으로 인식 
    all_html = "\n".join(doc.page_content for doc in docs)
    soup = BeautifulSoup(all_html, "html.parser")
    
    for tag in soup.find_all(["header", "footer"]): # header, footer tag 제거
        tag.decompose()

    pretty_html = soup.prettify() # html 파일 형식으로 예쁘게 정리 
    
    # save 
    html_path =  os.path.join(output_dir, f"upstage-{safe_name}.md")
    with open(html_path, 'w', encoding='utf-8') as f:
        f.write(pretty_html)

    print(f"✅ Saved as upstage to {html_path}")

    return end - start