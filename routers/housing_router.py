import logging
logger = logging.getLogger(__name__)

# 공고 선택이 필요한지 판단하는 라우터 함수
def need_notice_router(state) :
    '''
    - need_notice_selection == True: 공고 선택이 필요하므로 notice_selection 노드로 이동
    - need_notice_selection == False: "end"로 이동 

    '''
    flag = state['need_notice_selection']
    logger.debug(f"공고 선택 필요 여부: {flag}")

    return True if flag else False  

# 공고 선택 여부에 따라 후속 노드를 결정하는 라우터
def after_notice_selection_router(state) : 
    '''
    - need_notice_selection == True: 공고 선택이 완료되었으므로 종료(end)로 이동.
    - need_notice_selection == False: 아직 housing_react 단계로 다시 이동하여 답변 다시 생성

    '''
    flag = state['need_notice_selection']
    logger.debug(f"사용자의 공고 선택 후 공고 재선택 필요 여부: {flag}")
    
    return "end" if flag else "housing_react"