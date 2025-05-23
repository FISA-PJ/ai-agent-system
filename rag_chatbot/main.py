import os
from dotenv import load_dotenv
from openai import OpenAI
import certifi
from scripts.search_documents import search_documents
from elasticsearch import Elasticsearch

load_dotenv()

es =  Elasticsearch('http://localhost:9200')
api_key = os.getenv("OPENAI_API_KEY")
os.environ["SSL_CERT_FILE"] = certifi.where()
openai = OpenAI(api_key=api_key)
model_name = 'intfloat/multilingual-e5-large'
index_name = 'child-chunks-00'
#apt_code = '0000060867'

def answer_question(query) :
    global relevant_docs
    relevant_docs = search_documents(query, es, index_name, model_name)
    
    prompt = f"""
        [문서 내용]
        {relevant_docs}
        위 문서 내용을 참고하여 다음과 같은 형식으로 답변을 작성해주세요.

        질문: {query} 에 대한 답변입니다.
        답변:

        다음 조건을 충실히 반영해서 작성해주세요:

        1. **답변은 존댓말**을 사용해 정중하고 공식적인 어조를 유지합니다.
        2. 유사도가 높은 문서(청약 공고)로부터 **사용자의 질문과 관련된 정보를 선별**하여 추출하고 안내 사항에 대해서는 자세히 알려줘야 합니다.
        3. **같은 성격의 내용끼리는 하나의 문단으로 묶거나, 항목별로 리스트 형태로** 정리하여 가독성을 높입니다.
        4. 숫자나 날짜는 **정확하게 표기**하며, 필요한 경우 단위(예: 만 원, ㎡, 일 등)를 명확히 작성해주세요.
        5. 불명확하거나 문서에 없는 정보는 ‘문서상 명확한 정보는 확인되지 않았습니다.’라고 명시해주세요.
        6. Parent Document를 참고하여 전체 맥락을 파악하여 질의와 관련된된 정보를 정리해주세요. 

        반드시 사용자의 질문에 직접적으로 답변하도록 구성하고, 문맥상 불필요한 내용은 제거해주세요.
        """
    
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
        
    print(answer)
    #print(relevant_docs)
    