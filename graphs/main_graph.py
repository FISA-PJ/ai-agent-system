from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.memory import MemorySaver

from graphs.state import MyState
from graphs import intent_classifier, fallback_answering_node, irrelevant_answering_node, \
    housing_react_node, notice_selection_node, check_notice_selection_node, \
    loan_response_handler, user_loans_node, announcement_loans_node

from graphs import intent_router, need_notice_router, after_notice_selection_router, router_by_noticeNum

# 상태 그래프 선언
workflow = StateGraph(MyState)

# 노드 생성
workflow.add_node("intent_classifier", intent_classifier)

workflow.add_node("housing_react_node", housing_react_node)
workflow.add_node("notice_selection_node", notice_selection_node)
workflow.add_node("check_notice_selection_node", check_notice_selection_node)

workflow.add_node("loan_response_handler", loan_response_handler) 
workflow.add_node("user_loans_node", user_loans_node) 
workflow.add_node("announcement_loans_node", announcement_loans_node) 

workflow.add_node("irrelevant_answering_node", irrelevant_answering_node)
workflow.add_node("fallback_answering_node", fallback_answering_node)


# 엣지 연결
workflow.add_edge(START, "intent_classifier")   # START -> Gemma3 의도 분류
workflow.add_conditional_edges('intent_classifier', intent_router,  # 분류된 의도 기반 후속 노드 결정 
                               {
                                   'Housing': "housing_react_node",
                                   'Loan': "loan_response_handler",  
                                   'Irrelevant': "irrelevant_answering_node",
                                   'Fallback': "fallback_answering_node"
                               })
workflow.add_conditional_edges("housing_react_node", need_notice_router,    # 공고 번호 필요 여부 확인
                              {
                                  True : "notice_selection_node", 
                                  False : END
                              })
workflow.add_edge("notice_selection_node", "check_notice_selection_node") # 사용자 공고 선택 후 입력 확인 
workflow.add_conditional_edges("check_notice_selection_node", after_notice_selection_router, 
                              {
                                  "housing_react": "housing_react_node",  # 입력이 정상적으로 되었다면 공고 선택 완료
                                  "end": END                              # 예외 상황 
                              })

# 공고 번호 여부 확인 후 대출 상품 노드 분기 # ✅ 변경
workflow.add_conditional_edges('loan_response_handler', router_by_noticeNum,
                               {
                                   True : "announcement_loans_node",
                                   False : "user_loans_node"
                               })

workflow.add_edge("user_loans_node", END) # ✅ 변경
workflow.add_edge("announcement_loans_node", END) # ✅ 변경
workflow.add_edge("irrelevant_answering_node", END)
workflow.add_edge("fallback_answering_node", END)

# compile
memory = MemorySaver()
graph = workflow.compile(
        checkpointer=memory,
        interrupt_after=["notice_selection_node"]
    )