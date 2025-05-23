# conda create -n pdf_upstage_py312 python=3.12
# conda activate pdf_upstage_py312
import os
import pandas as pd
from PyPDF2 import PdfReader

from pdf_openparse import pdf_openparse
from pdf_llamaparse import pdf_llamaparse
from pdf_upstage import pdf_upstageparser
from pdf_4llm import pdf4llm

i = 0
results = [] 
input_dir = '../downloads/'
output_dir = '../experiment_results/'

os.makedirs(output_dir, exist_ok=True)

for filename in os.listdir(input_dir):
    file_path = os.path.join(input_dir, filename)
    base_filename = os.path.basename(file_path)  
    safe_name = os.path.splitext(base_filename)[0]  # 확장자 제거
    
    print("📝 현재 파싱 진행할 파일은" +file_path+"입니다.")
    
    print("=== openparse 실행 중 ===")
    openparse_time = pdf_openparse(file_path, output_dir, safe_name)
    print("=== pdf4llm 실행 중 ===")
    pdf4llm_time = pdf4llm(file_path, output_dir, safe_name)
    print("=== llamaparse 실행 중 ===")
    llama_time = pdf_llamaparse(file_path, output_dir, safe_name)
    print("=== upstage 실행 중 ===")
    upstage_time = pdf_upstageparser(file_path, output_dir, safe_name)
    
    # PDF 페이지 수 계산
    reader = PdfReader(file_path)
    page_count = len(reader.pages)

    # 결과 리스트에 추가
    results.append({
        '번호':      i,
        '파일명':    filename,
        '페이지 수': page_count,
        'OpenParse(초)':   round(openparse_time, 2),
        'PDF4LLM(초)':     round(pdf4llm_time,   2),
        'LLamaParse(초)':  round(llama_time,     2),
        'Upstage(초)':     round(upstage_time,   2),
    })
     
    i += 1

# DataFrame 생성
df = pd.DataFrame(results)

# 평균 행 추가
avg_row = {
    '번호':      '평균',
    '파일명':    '',
    '페이지 수': df['페이지 수'].mean(),
    'OpenParse(초)':   df['OpenParse(초)'].mean(),
    'PDF4LLM(초)':     df['PDF4LLM(초)'].mean(),
    'LLamaParse(초)':  df['LLamaParse(초)'].mean(),
    'Upstage(초)':     df['Upstage(초)'].mean(),
}
avg_df = pd.DataFrame([avg_row])
df = pd.concat([df, avg_df], ignore_index=True)

# Markdown 형태로 출력
print(df.to_markdown(index=False))
df.to_excel("Parser_experiment_results.xlsx", index = False)