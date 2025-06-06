from langchain.agents import Tool
from langgraph.prebuilt import create_react_agent
from agents import intent_llm, react_housing_prompt
from tools.rag_notice_search import rag_notice_search
from tools.rag_definition_search import rag_definition_search

# Tools 정의
tools = [
    Tool(
        name="search_housing_definition_from_es",
        func=rag_definition_search,
        description='청약과 관련된 개념을 RAG에서 검색하여 질문과 연관된 문서를 찾아 사용자에게 답변합니다.'
    ),
    Tool(
        name="search_housing_notice_from_es",
        func=rag_notice_search,
        description='청약 공고문에 수록된 내용들을 RAG에서 검색하여 질문과 연관된 문서를 찾아 사용자에게 답변합니다.'
    ),
]

housing_react_agent = create_react_agent(model=intent_llm, tools=tools, prompt=react_housing_prompt)