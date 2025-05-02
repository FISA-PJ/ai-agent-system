from torch import Tensor
import torch.nn.functional as F
from transformers import AutoTokenizer, AutoModel

from elasticsearch import Elasticsearch

#------ query Embedding ------
def average_pool(last_hidden_states: Tensor, attention_mask: Tensor) -> Tensor:
    last_hidden = last_hidden_states.masked_fill(~attention_mask[..., None].bool(), 0.0)
    return last_hidden.sum(dim=1) / attention_mask.sum(dim=1)[..., None]
    
def get_embedding(text, model_name):
    tokenizer = AutoTokenizer.from_pretrained(model_name)
    model = AutoModel.from_pretrained(model_name)
    emb_dict =  tokenizer(
        text, 
        max_length=512, 
        padding=True, 
        truncation=True, 
        return_tensors='pt'
    )

    outputs = model(**emb_dict)
    embeddings = average_pool(outputs.last_hidden_state, emb_dict['attention_mask'])
    embeddings = F.normalize(embeddings, p=2, dim=1)
    return embeddings.tolist()


# 벡터 유사도 기반의 문서 검색
def search_documents(query, es, index_name, model_name) :
    query_embedding = get_embedding(query, model_name)[0]
    results = es.search(index=index_name, body={
        "knn": {
            "field": "embedding",
            "query_vector": query_embedding,
            "k": 5,
            "num_candidates": 10
        }
    })
    
    return [hit["_source"]['content'] for hit in results["hits"]["hits"]]
