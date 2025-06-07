from langchain_core.messages import AIMessage
from agents import react_loan_agent_notice
import re

def announcement_loans_node(state): # 공고 ID가 True 일 때
    message = state["messages"][-1].content
    processed = state.get("processed_user_info", "")
    notice_number = state.get("notice_number", "")

    # Decimal('38400000')
    print("📄 [announcement_loans_node] 전처리 된 사용자 정보 : ", processed, type(processed))
    print("📄 [공고번호] : ", notice_number, type(notice_number))
    
    response = react_loan_agent_notice.invoke({
        "messages": [{"role": "user", "content": message}]},
        config={'configurable':{'processed' : processed, 'question' : message, 'notice_number': notice_number}}
        )

    print("[announcement_loans_node] RAW RESPONSE >>>", response)

    # ✅ agent_result 추출 (REACT 형식 기준)
    agent_result = response["messages"][-1].content
    result = re.sub(r'\*', '', agent_result)
    print("🤖 [announcement_loans_node] Agent 응답:", result)


    # 추천 결과 저장
    return {
        **state,
        "messages": state["messages"] + [AIMessage(content=result)],
        "previous_node": 'announcement_loans_node'
    }