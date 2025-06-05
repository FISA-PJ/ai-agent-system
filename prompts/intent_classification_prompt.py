from langchain.prompts import PromptTemplate

INTENT_PROMPT = PromptTemplate(
        input_variables=["user_message"],
        template="""
당신은 사용자의 메시지를 분석하여 의도를 정확히 분류하는 전문가입니다.

사용자 메시지를 다음 4가지 카테고리 중 하나로 분류해주세요:

1. Housing: 청약과 관련된 모든 질문이 여기에 해당됩니다. 청약 공고, 아파트 분양, 청약 개념, 자격 조건, 매물 등과 관련된 질문
2. Loan: 대출,대출 조건, 이자율, 신용 등과 관련된 질문
3. Irrelevant: 위 두 카테고리와 관련 없는 일반적인 질문이나 대화
4. Fallback: 지시어가 명확하지 않거나 의도를 명확히 파악하기 어려운 모호한 메시지

사용자 메시지: "{user_message}"

다음 형식으로만 응답해주세요:
intent: <의도 클래스>"""
    )