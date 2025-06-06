from langgraph.graph.message import add_messages
from typing import TypedDict, Annotated, Optional

# state 정의
class MyState(TypedDict):
    user_info: dict[str, str]
    processed_user_info: Optional[dict]
    messages: Annotated[list, add_messages]
    intent: Optional[str]
    notice_number: Optional[str]
    need_notice_selection: Optional[bool]
    previous_node: Optional[str]