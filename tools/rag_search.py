from langchain.agents import tool
from toosl import es_client, embedding_model, reranker_model 
from langchain.schema import Document

@tool
def query_notice_by_rag(query: str, apt_code: str) -> str:
    """
    사용자의 질문(query)과 아파트 코드(apt_code)를 기반으로
    관련 공고문 정보를 검색하고 요약된 결과를 반환합니다.
    """
    query_vec = embedding_model.embed_query(query)

    hits = es_client.search(index="notice-index", body={
        "knn": {
            "field": "vector",
            "query_vector": query_vec,
            "k": 10,
            "num_candidates": 20
        },
        "query": {
            "term": {
                "metadata.apt_code.keyword": f"upstage-{apt_code}"
            }
        }
    })["hits"]["hits"]

    docs = [
        Document(
            page_content=hit["_source"]["text"],
            metadata=hit["_source"].get("metadata", {})
        ) for hit in hits
    ]

    reranked = reranker_model.rerank(query, docs, top_k=3)

    results = [f"{i+1}. {doc.page_content[:150]}" for i, (doc, score) in enumerate(reranked)]
    return "\n".join(results)