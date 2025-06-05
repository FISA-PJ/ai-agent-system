from elasticsearch import Elasticsearch
from config.config import ES_HOST
from common.embeddings import BgeM3Embedding
from reranker.ko_reranker import KoReranker
import torch


es_client = Elasticsearch(ES_HOST)
embedding_model = BgeM3Embedding()
reranker_model = KoReranker(device="cuda" if torch.cuda.is_available() else "cpu")