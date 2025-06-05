# 공고 ID 여부로 대출 노드 분기
def router_by_noticeNum(state) :
    flag = state.get("notice_number")
    if flag :
        return True
    else:
        return False