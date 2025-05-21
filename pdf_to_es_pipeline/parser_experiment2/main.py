import os
from dotenv import load_dotenv
from langchain.schema import Document
from elasticsearch import Elasticsearch
from langchain_elasticsearch import ElasticsearchStore
from langchain.retrievers import ParentDocumentRetriever
from langchain.text_splitter import RecursiveCharacterTextSplitter

from processor1_pdf2md import Parser2Markdown
from processor2_chunking import HeaderSplitter, SemanticSplitter, LLMSplitter
from processor3_embedding import E5Embedding
from customized_es import ElasticsearchDocstore, CustomElasticsearchStore

load_dotenv()
os.chdir('../downloads')

es =  Elasticsearch('http://localhost:9200')
UPSTAGE_API_KEY = os.getenv("UPSTAGE_API_KEY") 

preprocessor = Parser2Markdown(UPSTAGE_API_KEY)
parent_splitter = HeaderSplitter()
docstore = ElasticsearchDocstore(   # Parent document용 Docstore
    index_name="parent-chunks-00",
    es=es,
)


# def read_md_file(file_path):
#     with open(file_path, 'r', encoding='utf-8') as f:
#         return f.read()


for file_path in os.listdir('.'):
    # if '0000060867' in file_path:
    #html_contents = preprocessor.pdf_upstageparser(file_path)
    html_contents = preprocessor.pdf_openparse(file_path)
    #html_contents = read_md_file(file_path)
    markdown_texts, spans = preprocessor.html2md_with_spans(html_contents)
    
    embeddings = E5Embedding(spans=spans)
    #child_splitter = SemanticSplitter(embeddings)
    #child_splitter = GeminiSplitter()
    child_splitter = RecursiveCharacterTextSplitter(chunk_size = 1000)

    vectorstore = CustomElasticsearchStore(
        index_name="child-chunks-00",
        embedding=embeddings,
        es_connection=es,
        strategy=ElasticsearchStore.ApproxRetrievalStrategy()
    )
    
    # Retriever 생성
    retriever = ParentDocumentRetriever(
        vectorstore=vectorstore,
        docstore=docstore,
        child_splitter=child_splitter,
        parent_splitter=parent_splitter
    )

    doc = Document(
        page_content=markdown_texts,
        metadata={"source_pdf": os.path.basename(file_path)}
    )
    
    retriever.add_documents([doc])