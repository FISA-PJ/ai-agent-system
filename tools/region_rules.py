"""
지역 규제 분류 함수
"""
import os
from tools import get_db_connection

# 공고 정보 불러오는 함수
def get_announcement_by_id(announcement_id: str) -> dict:
    """
    notice_db 데이터베이스에서 대출 상품 데이터를 불러옵니다.
    """
    # DB 연결 설정
    conn = get_db_connection(os.getenv("NOTICE_DB"))
    try:
        with conn.cursor() as cursor:
            sql = """
            SELECT 
                n.notice_number, 
                n.location, 
                h.avg_price 
            FROM 
                notices n 
            JOIN 
                house_types h ON n.id = h.notice_id 
            WHERE 
                n.notice_number = %s;
            """
            cursor.execute(sql, (announcement_id,))
            result = cursor.fetchone() # 테스트용 분양가 한개일 때
            # result = cursor.fetchall() # 분양가 여러 개일 때
            return result
    finally:
        conn.close()


# 지역 규제 분류 함수
def classify_region_type(location: str) -> str:
    regulated_keywords = ["용산구", "강남구", "서초구", "송파구"]

    for keyword in regulated_keywords:
        if keyword in location:
            return "투기과열지구"

    return "비규제지역"
