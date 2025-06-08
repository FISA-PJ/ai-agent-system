import os
from dotenv import load_dotenv

from loader import Parser2Markdown

# ===== 기본 설정 =====
load_dotenv()
DATA_DIR = "data"
UPSTAGE_API_KEY = os.getenv("UPSTAGE_API_KEY")

preprocessor = Parser2Markdown(UPSTAGE_API_KEY)

def doc2es(file_name) :
    if 'FAQ' in file_name : 
        html_contents = preprocessor.pdf_upstageparser(file_name)
        # HTML 파일로 저장
        output_file_name = "주택청약 FAQ.md"
        output_path = os.path.join("..", DATA_DIR, output_file_name)
        
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(html_contents)
        
        print(f"✅ {output_file_name} 파일이 저장되었습니다.")
if __name__ == '__main__' :
    os.chdir(DATA_DIR)

    for file_name in os.listdir("."):
        doc2es(file_name)