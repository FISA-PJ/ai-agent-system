import numpy as np
import torch
from typing import List, Tuple
from transformers import AutoTokenizer, AutoModelForSequenceClassification
from langchain.schema import Document

class KoReranker:
    def __init__(self, model_name: str = "Dongjin-kr/ko-reranker", device: str = None):
        self.tokenizer = AutoTokenizer.from_pretrained(model_name)
        self.model = AutoModelForSequenceClassification.from_pretrained(model_name)
        self.model.eval()

        # 자동으로 GPU 사용 여부 결정
        if device:
            self.device = device
        else:
            self.device = "cuda" if torch.cuda.is_available() else "cpu"

        self.model.to(self.device)

    @staticmethod
    def exp_normalize(x: np.ndarray) -> np.ndarray:
        """Softmax with numerical stability"""
        b = np.max(x)
        y = np.exp(x - b)
        return y / y.sum()

    def rerank(
        self,
        query: str,
        documents: List[Document],
        top_k: int = 3,
        return_scores: bool = True
    ) -> List[Tuple[Document, float]]:
        """
        Rerank documents based on Cross-Encoder scores.
        Returns top_k documents with scores.
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
            scores = self.exp_normalize(logits)

        reranked = sorted(zip(documents, scores), key=lambda x: x[1], reverse=True)
        return reranked[:top_k] if return_scores else [doc for doc, _ in reranked[:top_k]]
