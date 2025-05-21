from langchain.embeddings.base import Embeddings
import torch
import torch.nn.functional as F
from typing import List
from tqdm import tqdm
from torch import Tensor
from transformers import AutoTokenizer, AutoModel


class E5Embedding(Embeddings):
    def __init__(self, spans: list, bath_size : int = 300,model_name: str = "intfloat/multilingual-e5-large", device=None):
        """
        E5 임베딩 모델을 사용해 문서와 쿼리를 임베딩하는 클래스

        Args:
            spans (list): HTML 내 테이블 등의 JSON 변환 스팬 정보 리스트
            model_name (str, optional): Transformers 모델명. Defaults to "intfloat/multilingual-e5-large"
            device (str, optional): "cuda" 또는 "cpu" (지정하지 않으면 자동 선택)
        """
        self.tokenizer = AutoTokenizer.from_pretrained(model_name)
        self.model = AutoModel.from_pretrained(model_name)
        self.spans = spans
        self.batch_size = bath_size
        self.device = device or ("cuda" if torch.cuda.is_available() else "cpu")
        self.model.to(self.device)
        self.model.eval()


    def average_pool(self, last_hidden_states: Tensor, attention_mask: Tensor) -> Tensor:
        """        
        Args:
            last_hidden_states (Tensor): 모델의 마지막 hidden state (batch_size, seq_len, hidden_dim)
            attention_mask (Tensor): attention mask (batch_size, seq_len)

        Returns:
            Tensor: avg pooling embedding (batch_size, hidden_dim)
        """
        masked_hidden = last_hidden_states.masked_fill(~attention_mask[..., None].bool(), 0.0)
        return masked_hidden.sum(dim=1) / attention_mask.sum(dim=1)[..., None]


    def _convert_md_to_json(self, md_text: str) -> str:
        """
        Markdown 텍스트 내 <table> 태그를 대응하는 JSON 테이블로 변환
        
        Args:
            markdown_text (str): 마크다운 텍스트

        Returns:
            str: JSON 테이블이 삽입된 텍스트
        """
        start_i = next((i for i, span in enumerate(self.spans) if span['used'] == 0), None)

        if start_i is None:
            return md_text

        for span in self.spans:
            start_idx = md_text.find("<table>")
            end_idx = md_text.find("</table>")

            if start_idx == -1 or end_idx == -1:
                continue

            if span['used'] != 0:
                continue
            
            end_idx += len("</table>")
            md_text = md_text[:start_idx] + str(span['json_table']) + md_text[end_idx:]
            span['used'] = 1

        return md_text


    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        """
        여러 문서 텍스트를 임베딩 벡터 리스트로 변환

        Args:
            texts (List[str]): 문서 텍스트 리스트

        Returns:
            List[List[float]]: 임베딩 벡터 리스트
        """
        all_embeddings = []

        # </table> 단위로 자르기
        split_texts = [
            chunk.strip() + ("</table>" if "<table>" in chunk else "")
            for text in texts
            for chunk in text.split("</table>")
            if chunk.strip()
        ]

        # convert_md_to_json 적용 
        converted_texts = [self._convert_md_to_json(text) for text in split_texts]
        
        for i in tqdm(range(0, len(converted_texts), self.batch_size), desc="Embedding batches", leave=True):
            batch_texts = converted_texts[i:i + self.batch_size]
            formatted = [f"passage: {t}" for t in batch_texts]

            inputs = self.tokenizer(
                formatted,
                padding=True,
                truncation=True,
                return_tensors="pt",
                max_length=512,
            ).to(self.device)

            with torch.no_grad():
                outputs = self.model(**inputs)
                embeddings = self.average_pool(outputs.last_hidden_state, inputs["attention_mask"])
                embeddings = F.normalize(embeddings, p=2, dim=1)

            all_embeddings.extend(embeddings.cpu().tolist())

        return all_embeddings

    def embed_query(self, text: str) -> List[float]:
        """
        쿼리 텍스트를 임베딩 벡터로 변환
        
        Args:
            text (str): 쿼리 문자열

        Returns:
            List[float]: 임베딩 벡터
        """
        formatted = f"query: {text}"
        inputs = self.tokenizer(
            formatted,
            return_tensors="pt",
            truncation=True,
            max_length=512,
        ).to(self.device)

        with torch.no_grad():
            outputs = self.model(**inputs)
            embeddings = self.average_pool(outputs.last_hidden_state, inputs["attention_mask"])
            embeddings = F.normalize(embeddings, p=2, dim=1)

        return embeddings[0].cpu().tolist()
