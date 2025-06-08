import os
from elasticsearch import Elasticsearch
from dotenv import load_dotenv
from common.embeddings import BgeM3Embedding
from reranker.ko_reranker import KoReranker
import torch

load_dotenv()

ES_HOST = os.environ.get('ES_HOST')
es_client = Elasticsearch(ES_HOST)
embedding_model = BgeM3Embedding()
reranker_model = KoReranker(device="cuda" if torch.cuda.is_available() else "cpu")