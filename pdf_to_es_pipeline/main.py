import os
from dotenv import load_dotenv
from langchain.schema import Document
from elasticsearch import Elasticsearch
from langchain_elasticsearch import ElasticsearchStore

from processor1_pdf2md import Parser2Markdown
from processor2_chunking import HeaderSplitter, SemanticSplitter
from processor3_embedding import BgeM3Embedding

load_dotenv()
#os.chdir('../experiment_results_upstage/') # 이건 시험용 (이미 파싱된 HTML 문서 폴더)
os.chdir('../data/')

# 변수 생성
UPSTAGE_API_KEY = os.getenv("UPSTAGE_API_KEY") 
preprocessor = Parser2Markdown(UPSTAGE_API_KEY)

embeddings = BgeM3Embedding()
header_splitter = HeaderSplitter()
second_splitter = SemanticSplitter(embeddings)
es =  Elasticsearch('http://localhost:9200')


vectorstore = ElasticsearchStore(
    index_name="test-0524",
    embedding=embeddings,
    es_connection=es,
)

    
# # 이미 파싱된 파일 읽어오는 경우
# def read_md_file(file_path):
#     with open(file_path, 'r', encoding='utf-8') as f:
#         return f.read()


for file_name in os.listdir('.'):
    ## file_name 예) 0000060830_20250508_(250414)행정중심복합도시6-3M2블록입주자모집공고문(정정-접수기간연장).pdf
    print(f"======== 🚩 {file_name} 파일에 대한 처리를 시작합니다. ========")
    
    ## 1. 기존 문서 삭제 (Elasticsearch 쿼리)
    apt_code = file_name.split('_')[0] # file_name
    delete_query = {
        "query": {
            "term": {
                "metadata.apt_code": apt_code
            }
        }
    }
    es.delete_by_query(index="test-0524", body=delete_query)
    print(f"▶INFO: 🗑️ 기존 apt_code={apt_code} 문서가 Elasticsearch에서 삭제되었습니다.")
    
    
    ## 2. PDF문 파싱 및 마크다운 형태로 변환  
    #html_contents = preprocessor.pdf_upstageparser(file_name)
    html_contents = preprocessor.pdf_openparse(file_name)
    markdown_texts = preprocessor.html2md_with_spans(html_contents) 

    doc = Document(
        page_content=markdown_texts,
        metadata={"source_pdf": file_name}
    )
    
    ## 3. 1차 헤더 기반 청크
    header_chunks = header_splitter.split_documents([doc])

    ## 4. 2차 의미 기반 청크
    documents = second_splitter.split_documents(header_chunks)

    ## 5. 일괄 임베딩 + 벡터 저장
    vectorstore.add_documents(documents)
    print(f"-ˋˏ✄┈┈┈┈┈┈┈┈┈┈┈┈ [완료] {len(documents)}개 문서 Elasticsearch에 적재되었습니다. ┈┈┈┈┈┈┈┈┈┈┈┈\n\n")