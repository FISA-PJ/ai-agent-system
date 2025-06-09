import logging
from langchain_core.messages import AIMessage
from tools import GREETING_PROMPT, IRRELEVANT_ANSWER, CLASSIFY_IRR_MMS_TYPE_PROMPT, intent_llm

logger = logging.getLogger(__name__)


def irrelevant_answering_node(state) :
    user_message = state['messages'][-1].content
    
    if not user_message :   # 정해진 답변 출력
        return {**state, "messages":  [AIMessage(content=IRRELEVANT_ANSWER)]}
    
    classification_result = _classify_irrelevant_message_type(user_message)
    print(f"[irrelevant_answering_node] 분류 결과: {classification_result}")
    
    if "인사말" in classification_result :
        chain = GREETING_PROMPT | intent_llm
        
        return {**state, "messages" : [chain.invoke({
            'user_message': state['messages'][-1].content})
        ]}
        
    else :
        return {**state, "messages" : [AIMessage(content=IRRELEVANT_ANSWER)], "previous_node" : 'irrelevant_answering_node'}


# LLM 기반 "인사말/감사표현" 또는 "그 외"로 분류류
def _classify_irrelevant_message_type(user_message):
    try:
        chain = CLASSIFY_IRR_MMS_TYPE_PROMPT | intent_llm
        response = chain.invoke({
            'user_message': user_message
        })

        print(f"[_classify_irrelevant_message_type] 무관한 질문 도메인 분류 결과(인사말 or 기타): {response.content}")
        return response.content
    
    except Exception as e:
        print(f"❌ [_classify_irrelevant_message_type] 메시지 분류 중 오류 발생: {e}")
        return "기타"