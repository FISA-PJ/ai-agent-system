from langchain_core.messages import AIMessage
from agents import react_loan_agent_notice

def announcement_loans_node(state): # 공고 ID가 True 일 때
    message = state["messages"][-1].content
    processed = state.get("processed_user_info", "")
    notice_number = state.get("notice_number", "")

    print("전처리 된 사용자 정보 : ", processed)
    print("공고번호 : ", notice_number)

    response = react_loan_agent_notice.invoke({
        "messages": [{"role": "user", "content": message}]},
        config={'configurable':{'processed' : processed, 'question' : message, 'notice_number': notice_number}}
        )

    print("RAW RESPONSE >>>", response)

    # ✅ agent_result 추출 (REACT 형식 기준)
    agent_result = response["messages"][-1].content
    print("Agent 응답:", agent_result)


    # 추천 결과 저장
    return {
        **state,
        "messages": state["messages"] + [AIMessage(content=agent_result)]
    }