from tools.user_utils import preprocess_user_info

# 사용자 정보 전처리하는 함수
def loan_response_handler(state):
    if "processed_user_info" in state and state["processed_user_info"]:
        # 이미 전처리된 경우: 아무 것도 하지 않음
        print("✅ 전처리 생략: 이미 있음")
        return state

    rrn = state["user_info"]["registrationNumber"]
    print(rrn)
    processed = preprocess_user_info(rrn)

    print("전처리 결과:", processed)  # ✅ 중간 확인 로그

    return {
        **state,
        "processed_user_info": processed
    }