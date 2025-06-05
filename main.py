import logging 
from langchain_core.messages import HumanMessage
from graphs.main_graph import graph

logger = logging.getLogger(__name__)

Query = {
    "user_info": {
        "registrationNumber": "9503151234567",
        "userName": "김신혼",
        "primeType": "신혼부부",
        "subType": "우선공급"
    },
    "message": "신혼부부 입주 자격은 어떻게 돼?",
    # "notice_number": "2015122300017256"  # or 공고 ID
    "noticeNumber": ""  # or 공고 ID
}

# user_message = input("사용자 입력")
thread_config = {"configurable" : {"thread_id" : "test_thread_001"}}

inputs = {
    'user_info' : Query['user_info'],
    "messages" : [HumanMessage(content=Query['message'])],
    'intent' : "Fallback",
    "notice_number" : Query['noticeNumber'],
    "need_notice_selection" : False
    
}


for event in graph.stream(inputs, config = thread_config, stream_mode = 'values') : 
    if "messages" in event and event["messages"]:
        last_message = event["messages"][-1]
        if hasattr(last_message, "content") and "AIMessage" in str(type(last_message)):
            last_message.pretty_print()

current_state = graph.get_state(thread_config)
logger.debug(f"다음 진행 노드 : {current_state.next}")

if "check_notice_selection_node" in current_state.next:
    current_state = graph.get_state(thread_config)

    try :
        noticeNumber = input("공고 번호를 선택해주세요:")
    except :
        noticeNumber ='none'
        
    # 상태 업데이트
    updated_state = {
        **current_state.values,
        "notice_number": noticeNumber,
        "need_notice_selection": False,
        "messages":  [
            HumanMessage(content=current_state.values["messages"][-2].content + "공고번호를 선택했습니다")
        ]
    }
    
    graph.update_state(thread_config, updated_state)
    logger.debug(f"📩 current : {current_state.values['messages'][-2].content}")
    logger.debug(f"📩 updated : {updated_state['messages'][-1].content}")
    logger.debug(f"📦 업데이트 전 상태 notice_number:, {current_state.values.get('notice_number')}")
    logger.debug(f"📦 업데이트 후 상태 notice_number:, {updated_state['notice_number']}")
    
    events = graph.stream(None, thread_config, stream_mode="values")
    for event in events:
        if "messages" in event:
            event["messages"][-1].pretty_print()