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
    try:
        print(f'🔎 [rag_notice_search] 입력값 {combined_json}') # str

        parsed_data = json.loads(combined_json)
        print(f'받은 데이터 타입: {parsed_data}')
        
        # 값 추출
        user_message = parsed_data.get("user_message", "")
        notice_number = parsed_data.get("notice_number", "")

        # 입력값 검증
        if not user_message or not notice_number:
            return "⚠️ user_message 또는 notice_number가 누락되었습니다."

        print("user_message:", user_message)
        print("notice_number:", notice_number)
        
        # 임베딩 생성
        query_vec = embedding_model.embed_query(user_message)

        # Elasticsearch 검색
        hits = es_client.search(index="test-0524-tmp", body={
            "knn": {
                "field": "vector",
                "query_vector": query_vec,
                "k": 10,
                "num_candidates": 20
            },
            "query": {
                "term": {
                    "metadata.apt_code.keyword": f"{notice_number}"
                }
            }
        })["hits"]["hits"]

        
        # Document 변환
        docs = [
            Document(
                page_content=hit["_source"]["text"],
                metadata=hit["_source"].get("metadata", {})
            ) for hit in hits
        ]

        # Rerank 처리
        reranked = reranker_model.rerank(user_message, docs, top_k=3)

        results = [f"{i+1}. {doc.page_content}" for i, (doc, score) in enumerate(reranked)]
        return "\n".join(results)

    except json.JSONDecodeError:
        print(f"❌ [rag_notice_search] 예외 발생: {e}")
        return "⚠️ 입력값이 올바른 JSON 형식이 아닙니다."
    except Exception as e:
        print(f"❌ [rag_notice_search] 예외 발생: {e}")
        return f"⚠️ 오류가 발생했습니다: {str(e)}"
'''
 이 공고에서는 전매 제한이 있으며, 입주 후 일정 기간 동안은 주택을 매매할 수 없습니다.
- 전매 제한 기간은 일반적으로 최소 1년 이상이며, 구체적인 기간은 공고문에 명시되어 있습니다.
- 입주 후 전매가 가능한 시점은 계약 체결일로부터 30일 이내에 공사에서 관련 지자체에 단독 신고해야 하며, 이후에 전매가 가능합니다.

'''