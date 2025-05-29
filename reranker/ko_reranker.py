import numpy as np
import torch
from typing import List, Union, Tuple
from transformers import AutoTokenizer, AutoModelForSequenceClassification
from langchain.schema import Document
from scipy.special import softmax


class KoReranker:
    def __init__(self, model_name: str = "Dongjin-kr/ko-reranker", device: str = None):
        self.tokenizer = AutoTokenizer.from_pretrained(model_name)
        self.model = AutoModelForSequenceClassification.from_pretrained(model_name)
        self.model.eval()

        self.device = device or ("cuda" if torch.cuda.is_available() else "cpu")
        self.model.to(self.device)

    def rerank(
        self,
        query: str,
        documents: List[Document],
        top_k: int = 3,
        return_scores: bool = True
    ) -> Union[List[Tuple[Document, float]], List[Document]]:
        """
        주어진 query와 문서 리스트를 기반으로 Cross-Encoder reranking을 수행합니다.
        
        Args:
            query (str): 사용자 질문
            documents (List[Document]): 검색된 문서 리스트
            top_k (int): 상위 몇 개 문서를 반환할지
            return_scores (bool): 점수 포함 여부

        Returns:
            Union[List[Tuple[Document, float]], List[Document]]: 상위 문서들 (점수 포함 또는 제외)
        """
        if not documents:
            return []

        pairs = [[query, doc.page_content] for doc in documents]

        inputs = self.tokenizer(
            pairs,
            padding=True,
            truncation=True,
            max_length=512,
            return_tensors="pt"
        ).to(self.device)

        with torch.no_grad():
            logits = self.model(**inputs).logits.view(-1).float().cpu().numpy()
            scores = softmax(logits)

        reranked = sorted(zip(documents, scores), key=lambda x: x[1], reverse=True)

        if return_scores:
            return reranked[:top_k]
        else:
            return [doc for doc, _ in reranked[:top_k]]
