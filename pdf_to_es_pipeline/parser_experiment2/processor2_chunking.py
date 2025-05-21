import os
import re
import hashlib
import json
from typing import List
from langchain.schema import Document
from langgraph.client import Client
from langchain.text_splitter import TextSplitter
from langchain_experimental.text_splitter import SemanticChunker

class HeaderSplitter(TextSplitter) :
    def __init__(self) :
        super().__init__()

    def split_by_headers(self, text : str) -> list[str] :
        """
        텍스트를 '#' 헤더 기준으로 분할합니다.

        Args:
            text (str): 분할할 텍스트

        Returns:
            List[str]: 헤더 기준으로 나뉜 텍스트 리스트
        """
        
        # 헤더로 시작하는 위치 찾기
        header_positions = [m.start() for m in re.finditer("#", text, re.MULTILINE)]
        header_positions.append(len(text))

        raw_chunks = [
            text[header_positions[i]:header_positions[i+1]]
            for i in range(len(header_positions)-1)
        ]

        # 100자 이하 청크는 다음 또는 이전 청크에 포함
        chunks = []
        for idx, chunk in enumerate(raw_chunks) :
            chunk = chunk.strip()
            if len(chunk) < 100 :
                if idx == len(raw_chunks) - 1 :     # 마지막 n번째 청크는 (n-1)번째 청크에 포함
                    if chunks :
                        chunks[-1] += '\n' + chunk
                    else :
                        chunks.append(chunk)
                else :                              # 그 외 청크는 다음 청크에 포함하기
                    raw_chunks[idx + 1] = chunk + '\n' + raw_chunks[idx + 1]
            else :
                chunks.append(chunk)
                
        return chunks

    def split_text(self, text: str) -> List[str]:
        """
        TextSplitter 추상 메서드 override: 텍스트 분할

        Args:
            text (str): 분할할 텍스트

        Returns:
            List[str]: 분할된 텍스트 리스트
        """
        return self.split_by_headers(text)


    def split_documents(self, docs: List[Document]) -> List[Document]:
        """
        TextSplitter 추상 메서드 override
        문서 리스트를 헤더 기준으로 분할 후, doc_id 생성 및 메타데이터 추가

        Args:
            docs (List[Document]): 분할할 문서 리스트

        Returns:
            List[Document]: 분할된 문서 객체 리스트
        """
        
        print("======== INFO: 상위 문서 생성 중 입니다. ========")
        output: List[Document] = []

        for doc in docs :
            source_pdf = doc.metadata.get("source_pdf", "unknown.pdf")
            pdf_name = os.path.basename(source_pdf)     # 파일명
            apt_code = pdf_name.split("_")[0]           # APT CODE

            
            chunks = self.split_by_headers(doc.page_content)

            for parent_doc in chunks:
                base = parent_doc + str(apt_code)       # Hash value 
                doc_id = hashlib.sha256(base.encode('utf-8')).hexdigest()
                
                metadata = {
                    "source_pdf": pdf_name,
                    "apt_code": apt_code,
                    "doc_id": doc_id,
                }
                output.append(Document(page_content=parent_doc, metadata=metadata))#  List[Document]

        print(f"INFO: {len(output)} 개의 Parent Chunk가 생성되었습니다.")
        return output


class SemanticSplitter(TextSplitter) :
    def __init__(self, embed_model : object, breakpoint_threshold : int =70, min_child_length  : int= 1000) :
        """
        Args:
            EMBED_MODEL (object): 임베딩 모델 객체 
            BREAKPOIN_THRESHOLD (int, optional): 분할 임계값 (percentile) Defaults to 70.
            MIN_CHILD_LENGTH (int, optional): 자식 문서 청킹 기준. Defaults to 1000
        """
        
        super().__init__()
        self.embed_model = embed_model
        self.breakpoint_threshold = breakpoint_threshold
        self.min_child_length = min_child_length


    def split_by_semantic(self, text : str) -> list[str] :
        """
        SemanticChunker로 의미 기반으로 텍스트를 분할합니다

        Args:
            text (str): 분할할 텍스트

        Returns:
            list[str]: 의미 기준으로 분할된 텍스트 리스트
        """
        
        semantic_chunker = SemanticChunker(
            self.embed_model,
            breakpoint_threshold_type="percentile",
            breakpoint_threshold_amount=self.breakpoint_threshold)

        # Document 객체 리스트 생성
        semantic_chunks = semantic_chunker.create_documents([text])

        return [doc.page_content for doc in semantic_chunks]

    
    def split_text(self, text: str) -> List[str]:
        """

        Args:
            text (str): 분할할 텍스트

        Returns:
            List[str]: 분할된 텍스트 리스트
        """
        return self.split_by_semantic(text)


    def split_documents(self, parent_docs: List[Document]) -> List[Document]:
        """
        부모 문서를 의미 기반으로 자식 문서로 분할하고,
        메타데이터에 부모 doc_id와 child_id 추가
        
        Args:
            parent_doc (List[Document]): 분할할 부모 문서 리스트 (1개)

        Returns:
            List[Document]: 자식 문서 리스트
        """
        
        print("======== INFO: 하위 문서 생성 중 입니다. ========")
        output: List[Document] = []
        
        parent_doc = parent_docs[0]
        parent_id = parent_doc.metadata.get("doc_id", None)
        source_pdf = parent_doc.metadata.get("source_pdf", "unknown.pdf")
        pdf_name = os.path.basename(source_pdf)
        apt_code = pdf_name.split("_")[0]

        if len(parent_doc.page_content) < self.min_child_length :    # 1000자 이하는 청킹 X 
            child_docs = [parent_doc.page_content]
        else :
            child_docs = self.split_by_semantic(parent_doc.page_content)


        for child_doc in child_docs:
            base = child_doc + str(apt_code)
            child_id = hashlib.sha256(base.encode("utf-8")).hexdigest()
            
            metadata = dict(parent_doc.metadata)
            if parent_id :
                metadata['doc_id'] = parent_id
            metadata["child_id"] = child_id
            
            output.append(Document(page_content=child_doc, metadata=metadata)) #  List[Document]
        
        print(f"INFO: {len(output)} 개의 Child Chunk가 생성되었습니다.")
        return output

class GeminiSplitter(TextSplitter) :
    def __init__(self, gemini_api_key : str, prompt : str, model_name : str= "Gemini-1.5-Pro", min_child_length : int = 1000) :
        super().__init__
        self.gemini_api_key = gemini_api_key
        self.prompt = prompt
        self.model_name = model_name 
        self.client = Client(api_key=gemini_api_key)
        self.min_child_length = min_child_length
        
        
    def split_by_llm(self, text: str) -> List[str]:
        """
        LLM API 호출하여 텍스트를 분할합니다.

        Args:
            text (str): 분할할 텍스트

        Returns:
            List[str]: 분할된 텍스트 리스트
        """
        
        response = self.client.models.generate_content(
            model = self.model_name,
            contents= self.prompt + "\n" + text
        )

        try:
            json_result = json.loads(response.content[0].text) # [{"start":0,"end":100}, ...]
            return [text[r["start"]:r["end"]].strip() for r in json_result]
        except Exception as e:
            print(f"JSON parsing error: {e}")
            return [text]

    
    def split_text(self, text: str) -> List[str]:
        """
        Args:
            text (str): 분할할 텍스트

        Returns:
            List[str]: 분할된 텍스트 리스트
        """
        return self.split_by_llm(text)
    
    
    def split_documents(self, parent_docs: List[Document]) -> List[Document]:
        """
        부모 문서를 의미 기반으로 자식 문서로 분할하고,
        메타데이터에 부모 doc_id와 child_id 추가
        
        Args:
            parent_doc (List[Document]): 분할할 부모 문서 리스트 (1개)

        Returns:
            List[Document]: 자식 문서 리스트
        """
        
        print("======== INFO: 하위 문서 생성 중 입니다. ========")
        output: List[Document] = []
        
        parent_doc = parent_docs[0]
        parent_id = parent_doc.metadata.get("doc_id", None)
        source_pdf = parent_doc.metadata.get("source_pdf", "unknown.pdf")
        pdf_name = os.path.basename(source_pdf)
        apt_code = pdf_name.split("_")[0]

        if len(parent_doc.page_content) < self.min_child_length :    # 1000자 이하는 청킹 X 
            child_docs = [parent_doc.page_content]
        else :
            child_docs = self.split_by_llm(parent_doc.page_content)


        for child_doc in child_docs:
            base = child_doc + str(apt_code)
            child_id = hashlib.sha256(base.encode("utf-8")).hexdigest()
            
            metadata = dict(parent_doc.metadata)
            if parent_id :
                metadata['doc_id'] = parent_id
            metadata["child_id"] = child_id
            
            output.append(Document(page_content=child_doc, metadata=metadata)) #  List[Document]
        
        print(f"INFO: {len(output)} 개의 Child Chunk가 생성되었습니다.")
        return output