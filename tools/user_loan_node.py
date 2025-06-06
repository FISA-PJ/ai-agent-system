from langchain_core.messages import AIMessage
from agents.loan_agent import react_loan_agent_user


def user_loans_node(state) : # 공고 ID가 False일 때
    # 사용자 질문
    message = state["messages"][-1].content
    processed = state.get("processed_user_info", "")

    print("[user_loans_node] 전처리 된 사용자 정보 : ", processed)

    response = react_loan_agent_user.invoke({
        "messages": [{"role": "user", "content": message}]},
        config={'configurable':{'processed' : processed, 'question' : message}}
        )

    print("RAW RESPONSE >>>", response)

    # ✅ agent_result 추출 (REACT 형식 기준)
    agent_result = response["messages"][-1].content
    print("🤖[user_loans_node] Agent 응답:", agent_result)

    return {
        **state,
        "messages": state["messages"] + [AIMessage(content=agent_result)],
        'previous_node': 'user_loans_node'
    }