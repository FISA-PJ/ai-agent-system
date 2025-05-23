import torch
from torch import Tensor
import torch.nn.functional as F
from transformers import AutoTokenizer, AutoModel
from langchain.embeddings.base import Embeddings
from typing import List
from tqdm import tqdm


class E5Embedding(Embeddings):
    def __init__(self, spans: list, bath_size: int = 300, model_name: str = "BAAI/bge-m3", device=None):
        self.tokenizer = AutoTokenizer.from_pretrained(model_name)
        self.model = AutoModel.from_pretrained(model_name)
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        self.model.to(self.device)
        self.spans = spans
        self.batch_size = bath_size
        self.model.eval()


    def average_pool(self, last_hidden_states: Tensor, attention_mask: Tensor) -> Tensor:
        input_mask_expanded = attention_mask.unsqueeze(-1).expand(last_hidden_states.size()).float()
        sum_embeddings = torch.sum(last_hidden_states * input_mask_expanded, 1)
        sum_mask = torch.clamp(input_mask_expanded.sum(1), min=1e-9)
        return sum_embeddings / sum_mask


    def _convert_md_to_json(self, md_text: str) -> str:
        start_i = next((i for i, span in enumerate(self.spans) if span['used'] == 0), None)
        if start_i is None:
            return md_text
        for span in self.spans:
            start_idx = md_text.find("<table>")
            end_idx = md_text.find("</table>")
            if start_idx == -1 or end_idx == -1 or span['used'] != 0:
                continue
            end_idx += len("</table>")
            md_text = md_text[:start_idx] + str(span['json_table']) + md_text[end_idx:]
            span['used'] = 1
        return md_text


    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        
        all_embeddings = []

        split_texts = [
            chunk.strip() + ("</table>" if "<table>" in chunk else "")
            for text in texts
            for chunk in text.split("</table>")
            if chunk.strip()
        ]

        converted_texts = [self._convert_md_to_json(text) for text in split_texts]

        for i in tqdm(range(0, len(converted_texts), self.batch_size), desc="Embedding batches", leave=True):
            batch_texts = converted_texts[i:i + self.batch_size]
            formatted = [f"passage: {t}" for t in batch_texts]

            inputs = self.tokenizer(
                formatted,
                padding=True,
                truncation=True,
                return_tensors="pt",
                max_length=8192,
            )
            inputs = {k: v.to(self.device) for k, v in inputs.items()}

            with torch.no_grad():
                outputs = self.model(**inputs)
                pooled = self.average_pool(outputs.last_hidden_state, inputs["attention_mask"])
                embeddings = F.normalize(pooled, p=2, dim=1)

            all_embeddings.extend(embeddings.cpu().tolist())

        return all_embeddings


    def embed_query(self, text: str) -> List[float]:
        formatted = f"query: {text}"
        inputs = self.tokenizer(
            formatted,
            return_tensors="pt",
            truncation=True,
            max_length=8192,
        )
        inputs = {k: v.to(self.device) for k, v in inputs.items()}

        with torch.no_grad():
            outputs = self.model(**inputs)
            pooled = self.average_pool(outputs.last_hidden_state, inputs["attention_mask"])
            embedding = F.normalize(pooled, p=2, dim=1)

        return embedding[0].cpu().tolist()