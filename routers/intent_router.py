# 반환된 intent 값에 따라 후속 노드 분기됨
def intent_router(state) :
    intent = state.get("intent")
    return intent