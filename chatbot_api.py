## uvicorn chatbot_api:app --reload


# chatbot_api.py
from fastapi import FastAPI
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware

from main import *

app = FastAPI()

# CORS 허용 (스프링 서버에서 호출 가능하게)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 혹은 ["http://localhost:8080"] 등으로 제한
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class Query(BaseModel):
    noticeNumber : str
    message: str
    userId : str
    user_info : dict

# 사용자가 정의한 답변 함수
# def answer_question(query: str) -> str:
#     return f"'{query}'에 대한 답변입니다."  # 실제 구현으로 교체

@app.post("/api/chatbot")
async def chatbot_endpoint(query: Query):
    answer = answer_question(query)
    print(f'[chatbot_api] {answer}')
    return {"reply": str(answer)} # 전매 제한 기간이 어떻게 돼? 입주 후 언제부터 팔 수 있어?