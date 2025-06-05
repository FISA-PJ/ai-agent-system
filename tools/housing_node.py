import logging
from langchain_core.messages import AIMessage
from tools import housing_react_agent

logger = logging.getLogger(__name__)

# 청약 관련 질문에 대해 ReAct Agent 호출하여 결과 도출하는 메인 노드 
def housing_react_node(state) :
    
    user_message = state['messages'][-1].content
    notice_number = state.get('notice_number', '')
    user_info = state['user_info']
    
    logger.debug("------from HOUSING REACT!------")
    logger.info(f'[공고번호] {notice_number} \n[질문] {user_message} \n[사용자 장버] {user_info}')
    
    # ReAct Agent 호출
    try :
        response = housing_react_agent.invoke({
            "messages": [{"role": "user", "content": user_message}]},
            config={'configurable':{'user_info' : user_info, 'user_message' : user_message, 'notice_number': notice_number}}
        )

        agent_result = response['messages'][-1].content
        logger.info(f"🤖에이전트 응답 결과: {agent_result}")
        
        if "현재 선택된 공고가 없습니다" in agent_result :
            need_notice_selection = True
        else :
            need_notice_selection = False
        
        return {
            **state,
            "messages": [AIMessage(content=agent_result)],
            "need_notice_selection": need_notice_selection
        }
        
    except Exception as e : 
        logger.error(f"❌ [Housing React Node] ReAct Agent 실행 중 오류 발생: {e}")
        return {
            **state,
            "messages": [AIMessage(content="죄송합니다. 시스템 오류로 인해 답변을 드리지 못하고 있어요. 잠시 후 다시 시도해 주세요.")],
            "need_notice_selection": False,
        }
        


def notice_selection_node(state):
    """공고 선택 상태를 유지하는 패스스루 노드"""
    logger.info("📋 notice_selection_node: 공고 선택 대기 상태 유지")

    return state    # 상태는 그대로 유지하고 바로 패스


def check_notice_selection_node(state) :
    """사용자가 입력한 공고 번호가 맞게 들어왔는지 확인하는 노드"""
    notice_number = state['notice_number']
    
    logger.debug(f"선택된 공고 번호 : {notice_number}")
    
    if notice_number :
        logger.info("공고 선택 완료 -> housing_react로 이동")
        return {**state, "notice_number": notice_number, 
                "need_notice_selection" : False}
    else :
        logger.info("공고 선택 실패 -> END로 이동")
        return {**state,
                "need_notice_selection" : True}