from langchain_core.messages import HumanMessage
from graphs.main_graph import graph

flag = False
current_state = None
initial_query = None 


def answer_question(Query) : 
    global flag, current_state

    thread_config = {"configurable" : {"thread_id" : Query.userId}, "recursion_limit": 50}

    print(Query)
    if flag == False : 
        inputs = {
            'user_info' : Query.user_info,
            "messages" : [HumanMessage(content=Query.message)],
            'intent' : "Fallback",
            "notice_number" : Query.noticeNumber,
            "need_notice_selection" : False,
            
        }
        
        for event in graph.stream(inputs, config = thread_config, stream_mode = 'values') : 
            if "messages" in event and event["messages"]:
                last_message = event["messages"][-1]
                if hasattr(last_message, "content") and "AIMessage" in str(type(last_message)):
                    last_message.pretty_print()
        
        
        current_state = graph.get_state(thread_config)
        previous_node = current_state.values.get('previous_node')
        print(f'🌿 이전 노드: {previous_node}')
        
        if previous_node == 'notice_selection_node' : 
            flag = True
    
        return last_message.content

    elif flag == True : 
                
        # 상태 업데이트
        updated_state = {
            **current_state.values,
            "notice_number": Query.noticeNumber,
            "need_notice_selection": False,
            "messages":  [
                HumanMessage(content=current_state.values["messages"][-2].content + Query.message)
            ]
        }
        
        graph.update_state(thread_config, updated_state)
        
        print(f"📩 업데이트 전 상태 message : {current_state.values['messages'][-2].content}")
        print(f"📩 업데이트 후 상태 message: {updated_state['messages'][-1].content}")
        print(f"📦 업데이트 전 상태 notice_number:, {current_state.values.get('notice_number')}")
        print(f"📦 업데이트 후 상태 notice_number:, {updated_state['notice_number']}")
        
        events = graph.stream(None, thread_config, stream_mode="values")
        for event in events:
            if "messages" in event:
                print('🤖[공고 선택 후 답변]',event["messages"][-1].content)
                  
        flag = False
        return event["messages"][-1].content