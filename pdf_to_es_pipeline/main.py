import os
import sys
import tempfile
import requests
from elasticsearch import Elasticsearch
from scripts.lh_crawler_today import collect_lh_file_urls
from scripts.lh_crawler_today import BASE_URL, HEADERS   # 추가 
from scripts.pdf_processor import pdfProcessor


def main():
    # 1) URL 수집
    collected_urls = collect_lh_file_urls()
    
    # 2) 수집 결과 없으면 조기 종료
    if len(collected_urls) == 0:
        print("⚠️ 수집된 공고가 없습니다. 프로그램을 종료합니다.")
        sys.exit(0)
        
    batch_size = 8
    es = Elasticsearch("http://localhost:9200")
    processor = pdfProcessor(es, batch_size, index_name='rag-test3')
    
    # 3) PDF URL > Elasticsearch 
    for url, safe_filename, meta in collected_urls:
        pdf_name = f"{meta['filename']}"
        tmp_path = None
        # print('safe_filename', safe_filename)
        # print('pdf_name', pdf_name)
        try:
            # HTTP 요청
            resp = session.get(url, headers={"Referer": BASE_URL})
            resp.raise_for_status()
            
            # 임시 파일에 저장
            with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
                tmp.write(resp.content)
                tmp_path = tmp.name
            
            # PDF 파싱 → 청킹 → 임베딩 → ES 업로드
            text       = processor.pdf_parser(tmp_path)
            chunks     = processor.text_chunking(text)
            embeddings = processor.text_embedding(chunks)
            processor.upload_embeddings_to_es(chunks, embeddings, safe_filename, pdf_name)
            
        except Exception as e:
            print(f"⚠️ [{meta['filename']}] 처리 실패: {e}")
        
        finally:
            # 임시 파일 삭제 
            if tmp_path and os.path.exists(tmp_path):
                os.remove(tmp_path)

if __name__ == "__main__":
    session = requests.Session()
    session.headers.update(HEADERS)
    main()
