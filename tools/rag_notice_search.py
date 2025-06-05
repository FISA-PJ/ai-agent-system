from langchain.agents import tool
from langchain.schema import Document
from tools import es_client, embedding_model, reranker_model 

@tool
def rag_notice_search(user_message: str, notice_number: str) -> str:
    """
    사용자의 질문(query)과 아파트 코드(apt_code)를 기반으로
    관련 공고문 정보를 검색하고 요약된 결과를 반환합니다.
    """
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