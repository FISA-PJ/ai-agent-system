import os
from io import BytesIO
import openparse

import torch
from torch import Tensor
import torch.nn.functional as F
from transformers import AutoTokenizer, AutoModel
from langchain.text_splitter import RecursiveCharacterTextSplitter

from elasticsearch import Elasticsearch
from elasticsearch import helpers


class pdfProcessor() :
    def __init__ (self, es, batch_size, index_name, model_name='intfloat/multilingual-e5-small') :
        self.es = es
        self.index_name = index_name
        self.batch_size = batch_size
        self.tokenizer = AutoTokenizer.from_pretrained(model_name)
        self.model = AutoModel.from_pretrained(model_name)
    
    # ------ Parsing ------
    def pdf_parser(self, file_path) :
        parser = openparse.DocumentParser()
        parsed_docs = parser.parse(file_path)
        
        text_list = []
        for node in parsed_docs.nodes :
            if hasattr(node, 'text') :
                text_list.append(node.text)
        text = '\n'.join(text_list)
        
        return text
    
    
    # ------ Chunking ------
    def text_chunking(self, text, chunk_size=2000, chunk_overlap = 200) :
        splitter = RecursiveCharacterTextSplitter(
            chunk_size = chunk_size,
            chunk_overlap = chunk_overlap
        )
        
        chunks = splitter.split_text(text)
        print(f"☺️ 청킹 결과: {len(chunks)}개 청크 생성되었습니다.")
        return chunks


    # ------ Embedding ------
    def average_pool(self, last_hidden_states: Tensor, attention_mask: Tensor) -> Tensor:
        last_hidden = last_hidden_states.masked_fill(~attention_mask[..., None].bool(), 0.0)
        return last_hidden.sum(dim=1) / attention_mask.sum(dim=1)[..., None]


    def text_embedding(self, chunks) : 
        all_embeddings = []
        for i in range(0, len(chunks), self.batch_size) : 
            batch = chunks[i:i+self.batch_size]
            batch_dict = self.tokenizer(
                batch, 
                max_length=512, 
                padding=True, 
                truncation=True, 
                return_tensors='pt'
            )

            outputs = self.model(**batch_dict)
            embeddings = self.average_pool(outputs.last_hidden_state, batch_dict['attention_mask'])
            embeddings = F.normalize(embeddings, p=2, dim=1)
            all_embeddings.append(embeddings)
            
        print(f"☺️ 임베딩 결과: {len(all_embeddings)}개의 임베딩이 모두 완료되었습니다")
        return torch.cat(all_embeddings, dim=0).tolist() 
    
    
    #------ Elasticsearch ------
    # 입력 값 수정 
    def upload_embeddings_to_es(self, chunks, embeddings, safe_filename, pdf_name) :
        
        for i in range(0, len(chunks), self.batch_size):
            actions = []
            chunk_batch = chunks[i:i+self.batch_size]
            embedding_batch = embeddings[i:i+self.batch_size]
            
            for idx, (chunk, embedding) in enumerate(zip(chunk_batch, embedding_batch)) :
                action = {
                    '_index' : self.index_name,
                    '_id' : f"{pdf_name}_{i+idx}",
                    '_source' : {
                        'content' : chunk,
                        'embedding' : embedding,
                        'source_pdf' : safe_filename,
                        'chunk_id' : i+idx
                    }
                }
                print(f"{pdf_name}_{i+idx}")
                actions.append(action)
            helpers.bulk(self.es, actions, raise_on_error = True)
        print(f"☺️ {pdf_name}의 {len(chunks)}개 청크를 ES에 성공적으로 저장했습니다")



# if __name__ == "__main__" :
#     os.chdir('./data')
    
#     batch_size = 32
#     index_name = 'rag-test2'
#     es =  Elasticsearch('http://localhost:9200')
    
#     processor = pdfProcessor(es, index_name)

#     for filename in os.listdir('.'):
#         file_path = filename
#         text = processor.pdf_parser(file_path)
#         chunks = processor.text_chunking(text)
#         embeddings = processor.text_embedding(chunks, batch_size)
#         processor.upload_embeddings_to_es(chunks, embeddings, filename, batch_size=16)