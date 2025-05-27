from torch import Tensor
import torch.nn.functional as F
import torch
from transformers import AutoTokenizer, AutoModel, AutoModelForSequenceClassification
from langchain.retrievers import ContextualCompressionRetriever
from reranker import KoReranker
from langchain.schema import Document
from processor3_embedding import BgeM3Embedding
def search_documents(query, es, apt_code) :
    retriever = vectorstore.as_retriever(
        search_type="similarity",
        search_kwargs={
            "k": 10,
            "filter": {
                "term": {
                    "metadata.apt_code": f"upstage-{apt_code}"
                }
            }
        }
    )

    embeddings = BgeM3Embedding()
    query_embedding = embeddings.embed_query(query)
    docs = es.search(index='test-0524', body={
        "knn": {
            "field": "vector",
            "query_vector": query_embedding,
            "k": 10,
            "num_candidates": 20
        },
        "query": {
            "term": {
                "metadata.apt_code.keyword": f"upstage-{apt_code}"
            }
        }
    })["hits"]["hits"]
    
    candidate_docs = [
        Document(
            page_content=hit["_source"]["text"],  # 또는 "content", 필드 이름에 따라 수정
            metadata=hit["_source"].get("metadata", {})
        )
        for hit in docs
    ]
    #candidate_docs = retriever .get_relevant_documents(query)
    print(f'candidate_docs : {len(candidate_docs)}')
    reranker = KoReranker(model_name="Dongjin-kr/ko-reranker", device="cuda" if torch.cuda.is_available() else "cpu")
    reranked_docs = reranker.rerank(query, candidate_docs, top_k=3, return_scores=True)

    print(f'reranked_docs : {len(reranked_docs)}')
    #Step 3: 결과 반환
    return [
        # {
        #     "content": doc.page_content[:100],  # 앞 100자만
        #     "metadata": doc.metadata,
        # }
        doc
        for doc in reranked_docs
    ]


if __name__ == '__main__' :
    from elasticsearch import Elasticsearch
    from langchain_elasticsearch import ElasticsearchStore
    from processor3_embedding import BgeM3Embedding

    es =  Elasticsearch('http://localhost:9200')
    embeddings = BgeM3Embedding()
    apt_code = '0000060848'

    vectorstore = ElasticsearchStore(
        index_name='test-0524',
        embedding=embeddings,
        es_connection=es,
    )

    query = input("질문을 입력해주세요 : ")
    results = search_documents(query, es, apt_code)
    for i, result in enumerate(results) :
        print(f'========={i}th chunk=========')
        print(result)
        # print(result['content'])
        # print(result['metadata'])
        
# 벡터 유사도 기반의 문서 검색
# def search_documents(query, es, index_name, model_name) :
#     query_embedding = get_embedding(query, model_name)[0]
#     results = es.search(index=index_name, body={
#         "knn": {
#             "field": "vector",
#             "query_vector": query_embedding,
#             "k": 3,
#             "num_candidates": 10
#         }
#     })
    
#     return [hit["_source"]['text'] for hit in results["hits"]["hits"]]
# # 벡터 유사도 기반의 문서 검색
# def search_documents(query, es, index_name, model_name, apt_code) :
#     query_embedding = get_embedding(query, model_name)[0]
    
#     body = {
#             "query": {
#                 "bool": {
#                     "must": [
#                         {
#                             "knn": {
#                                 "field": "embedding",
#                                 "query_vector": query_embedding,
#                                 "k": 3,
#                                 "num_candidates": 5
#                             }
#                         },
#                         {
#                             "term": {
#                                 "apt_code.keyword": apt_code
#                             }
#                         }
#                     ]
#                 }
#             }
#         }
#     results = es.search(index=index_name, body=body)
    
#     #return [hit["_source"]['content'] for hit in results["hits"]["hits"]]
#     return [
#         {
#             "id": hit["_id"],
#             "content": hit["_source"]["content"],
#             "source_pdf": hit["_source"].get("source_pdf", "알 수 없음")
#         }
#         for hit in results["hits"]["hits"]
#     ]


# model_path = "Dongjin-kr/ko-reranker"
# def exp_normalize(x):
#       b = x.max()
#       y = np.exp(x - b)
#       return y / y.sum()
    

# tokenizer = AutoTokenizer.from_pretrained(model_path)
# model = AutoModelForSequenceClassification.from_pretrained(model_path)
# model.eval()

# pairs = [["나는 너를 싫어해", "나는 너를 사랑해"], \
#         ["나는 너를 좋아해", "너에 대한 나의 감정은 사랑 일 수도 있어"]]

# with torch.no_grad():
#     inputs = tokenizer(pairs, padding=True, truncation=True, return_tensors='pt', max_length=512)
#     scores = model(**inputs, return_dict=True).logits.view(-1, ).float()
#     scores = exp_normalize(scores.numpy())
#     print (f'first: {scores[0]}, second: {scores[1]}')