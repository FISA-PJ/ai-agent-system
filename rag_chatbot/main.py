import os
from dotenv import load_dotenv
from openai import OpenAI

from scripts.search_documents import search_documents
from elasticsearch import Elasticsearch

load_dotenv()

es =  Elasticsearch('http://localhost:9200')
api_key = os.getenv("OPENAI_API_KEY")
openai = OpenAI(api_key=api_key)
model_name = 'intfloat/multilingual-e5-small'
index_name = 'rag-test2'


def answer_question(query) :
    global relevant_docs
    relevant_docs = search_documents(query, es, index_name, model_name)
    
    prompt = f"문서: {relevant_docs}, \n질문: {query}\n\n답변:"
    response = openai.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": "You are a helpful assistant to give helpful contexts to the customer. Summarize or list up the contents of this document in less than 800 characters. Answer in Korean."},
            {"role": "user", "content": prompt}
        ]
    )
    return response.choices[0].message.content


if __name__  == "__main__" :
    
    query = input("질문을 입력해주세요 : ")
    answer = answer_question(query)
    
    print(answer, relevant_docs)
    