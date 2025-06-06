from langchain_core.messages import AIMessage
from tools import FALLBACK_ANSWER

def fallback_answering_node(state) :
    """모호한 질문에 대한 정해진 응답을 반환"""

    return {**state, "messages": [AIMessage(content=FALLBACK_ANSWER)], "previous_node" : 'fallback_answering_node'}