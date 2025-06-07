import json
from langchain.agents import tool
from langchain.schema import Document
from tools import es_client, embedding_model, reranker_model 

@tool
def rag_notice_search(combined_json) -> str:
    """
    사용자의 질문(query)과 아파트 코드(apt_code)를 기반으로
    관련 공고문 정보를 검색하고 요약된 결과를 반환합니다.
    """
    print(f'🔎 [rag_notice_search] 입력값 {combined_json}') # str
    print(f'받은 데이터 타입: {parsed_data}')
    parsed_data = json.loads(combined_json)
    
    # 값 추출
    user_message = parsed_data.get("user_message", "")
    notice_number = parsed_data.get("notice_number", "")

    # 결과 확인
    print("user_message:", user_message)
    print("notice_number:", notice_number)
    
    query_vec = embedding_model.embed_query(user_message)

    hits = es_client.search(index="test-0524-tmp", body={
        "knn": {
            "field": "vector",
            "query_vector": query_vec,
            "k": 10,
            "num_candidates": 20
        },
        "query": {
            "term": {
                "metadata.apt_code.keyword": f"upstage-{notice_number}"
            }
        }
    })["hits"]["hits"]

    docs = [
        Document(
            page_content=hit["_source"]["text"],
            metadata=hit["_source"].get("metadata", {})
        ) for hit in hits
    ]

    reranked = reranker_model.rerank(user_message, docs, top_k=3)

    results = [f"{i+1}. {doc.page_content}" for i, (doc, score) in enumerate(reranked)]
    return "\n".join(results)