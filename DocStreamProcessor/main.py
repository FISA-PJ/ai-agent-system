import os
from typing import List
from dotenv import load_dotenv
from langchain.schema import Document
from elasticsearch import Elasticsearch, NotFoundError, TransportError
from langchain_elasticsearch import ElasticsearchStore

from DocStreamProcessor import Parser2Markdown, HeaderSplitter, SemanticSplitter, BgeM3Embedding


# ===== 기본 설정 =====
load_dotenv()
DATA_DIR = "experiment_results_upstage"
INDEX_NAME = "test-0524"
UPSTAGE_API_KEY = os.getenv("UPSTAGE_API_KEY")

# ===== 인스턴스 초기화 =====
preprocessor = Parser2Markdown(UPSTAGE_API_KEY)
embeddings = BgeM3Embedding()
header_splitter = HeaderSplitter()
semantic_splitter = SemanticSplitter(embeddings)
es =  Elasticsearch('http://localhost:9200')
vectorstore = ElasticsearchStore(
    index_name=INDEX_NAME,
    embedding=embeddings,
    es_connection=es,
)

    
# ===== utils =====
def read_md_file(file_path):
    with open(file_path, 'r', encoding='utf-8') as f:
        return f.read()


def delete_documents_by_apt_code(es: Elasticsearch, index: str, apt_code: str):
    if not es.indices.exists(index=index):
        print(f"⚠️ 인덱스 '{index}'가 존재하지 않아 삭제를 건너뜁니다.")
        return
    
    query = {"query": {"term": {"metadata.apt_code": apt_code}}}
    
    try :
        response = es.delete_by_query(index = index, body = query)
        deleted = response.get(deleted, 0)
        print(f"🗑️ apt_code={apt_code} 문서 {deleted}건 삭제 완료" if deleted else f"ℹ️ apt_code={apt_code} 관련 문서 없음")
        
    except NotFoundError as e:
        print(f"🚫 문서 없음: {e}")
    except TransportError as e:
        print(f"🚨 요청 실패: {e.error}, 상태 코드: {e.status_code}")
    except Exception as e:
        print(f"❗예외 발생: {e}")
        

def doc2es(file_name) :
    print(f"======== 🚩 {file_name} 파일에 대한 처리를 시작합니다. ========")
    
    ## 1. 기존 문서 삭제 (Elasticsearch 쿼리)
    apt_code = file_name.split('_')[0]
    delete_documents_by_apt_code(apt_code)

    ## 2. PDF문 파싱 및 마크다운 형태로 변환  
    #html_contents = preprocessor.pdf_upstageparser(file_name)
    #html_contents = preprocessor.pdf_openparse(file_name)
    html_contents = read_md_file(os.path.join(DATA_DIR, file_name))
    markdown_texts = preprocessor.html_to_markdown_with_tables(html_contents) 

    ## 3. Chunking 
    doc = Document(page_content=markdown_texts, metadata={"source_pdf": file_name})
    header_chunks = header_splitter.split_documents([doc])
    final_documents = semantic_splitter.split_documents(header_chunks)
    
    ## 4. 일괄 임베딩 + 벡터 저장
    vectorstore.add_documents(final_documents)
    print(f"-ˋˏ✄ [완료] {len(final_documents)}개 문서 Elasticsearch에 적재되었습니다.\n")


if __name__ == '__main__' :
    os.chdir(DATA_DIR)

    for file_name in os.listdir("."):
        doc2es(file_name)