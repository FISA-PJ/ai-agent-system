"""
지역 규제 분류 함수
가짜 공고 정보
  {
    "announcement_id": "0000060872",
    "location": "경기도 부천시 오정구 봉오대로 405 부천대장 A8블록 공공분양주택",
    "avg_price": 511593000
  }
"""
import json

# 공고 정보 불러오는 함수
def get_announcement_by_id(announcement_id: str) -> dict:
    with open("./data/sample_announcements.json", encoding="utf-8") as f:
        announcements = json.load(f)

    for ann in announcements:
        if ann["announcement_id"] == announcement_id:
            return ann

    return None


# 지역 규제 분류 함수
def classify_region_type(location: str) -> str:
    regulated_keywords = ["용산구", "강남구", "서초구", "송파구"]

    for keyword in regulated_keywords:
        if keyword in location:
            return "투기과열지구"
    
    return "비규제지역"
