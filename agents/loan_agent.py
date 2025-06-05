from langchain.agents import Tool
from langgraph.prebuilt import create_react_agent
from agents import intent_llm
from tools.recommend_loans import filter_loan_products_by_user, recommend_loans_by_user_and_announcement
from tools import prompt_user, prompt_notice

# Tools 정의
loan_tools_user = [
    Tool(
        name="filter_loan_products_by_user",
        func=filter_loan_products_by_user,
        description='전처리된 사용자 정보를 받아 조건에 맞는 대출 상품을 필터링합니다. 사용자 정보는 딕셔너리 형태로 입력하세요.'
    )
]

react_loan_agent_user = create_react_agent(model=intent_llm, tools=loan_tools_user, prompt=prompt_user)


loan_tools_notice = [
    Tool(
        name="recommend_loans_by_user_and_announcement",
        func=recommend_loans_by_user_and_announcement,
        description='사용자 정보와 공고 ID를 받아 월 예상 상환액을 계산하고 대출 상품을 추천합니다. 입력 형태: {"processed": 사용자정보딕셔너리, "notice_number": "공고ID"}'
    )
]

react_loan_agent_notice = create_react_agent(model=intent_llm, tools=loan_tools_notice, prompt=prompt_notice)