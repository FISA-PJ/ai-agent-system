from tools import INTENT_PROMPT, intent_llm


# 1. 사용자 메시지 의도 분류 
def intent_classifier(state) :
    """사용자 메시지의 의도를 분류하는 함수"""
    VALID_INTENTS = ["Housing", "Loan", "Irrelevant", "Fallback"]
    DEFAULT_INTENT = "Fallback"

    user_message = state['messages'][-1].content

    if not user_message :
        return {**state, "intent": DEFAULT_INTENT, "previous_node" : 'intent_classifier'}

    ### LLM 기반 의도 분류
    try :
        intent = _classify_intent_with_llm(user_message, VALID_INTENTS)
    except Exception as e :
        print(f"❌ [intent_classifier] 의도 분류 중 오류 발생: {e}", exc_info=True)
        intent = DEFAULT_INTENT

    print(f"📄 [intent_classifier] 의도 분류 결과: {intent}\n")
    return {**state, "intent" : intent, "previous_node" : 'intent_classifier'}


# 2. 사용자 메시지 LLM 기반 분류
def _classify_intent_with_llm(user_message, valid_intents) :
    """LLM을 사용하여 의도 분류"""
    try :
        chain = INTENT_PROMPT | intent_llm
        response = chain.invoke({
            "user_message" : user_message
        })

        result = response.content
        return _extract_intent_from_response(result, valid_intents)

    except Exception as e :
        print(f"❌ [Intent Classifier] LLM 호출 중 오류: {e}")
        return "Fallback"
    

# 3. LLM 응답에서 의도 추출
def _extract_intent_from_response(response, valid_intents) :
    """LLM 응답에서 의도  추출"""
    if "intent" not in response.lower() :
        return "Fallback"

    response_words = response.split()
    return next((word for word in response_words if word in valid_intents), "Fallback")