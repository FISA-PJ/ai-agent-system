"""
사용자 정보 전처리 함수
"""

import os
from datetime import datetime, date
from tools import get_db_connection


# 프로시저 함수 사용해서 DB에서 사용자 정보 불러오기
def call_getuserinfobyrrn(rrn: str) -> dict:
    conn = get_db_connection(os.getenv("APP_DB"))

    try:
        with conn.cursor() as cursor:
            sql = "CALL getuserinfobyrrn(%s)"  # 일반 SQL 호출
            cursor.execute(sql, (rrn.strip(),))  # 파라미터 바인딩

            rows = cursor.fetchall()
            return rows[-1] if rows else None  # 여러 행 중 마지막 행만 사용

    finally:
        conn.close()


def load_user_by_rrn(rrn: str) -> dict:
    return call_getuserinfobyrrn(rrn)


# 생년월일 컬럼으로 나이 계산하는 함수
def calculate_age(birth_date_str: str) -> int:
    if isinstance(birth_date_str, date):
        birth_date = birth_date_str
    else:
        birth_date = datetime.strptime(birth_date_str, "%Y-%m-%d").date()
    today = datetime.today().date()
    
    # 기본 나이 계산
    age = today.year - birth_date.year

    # 생일 안 지났으면 -1
    if (today.month, today.day) < (birth_date.month, birth_date.day):
        age -= 1

    return age


# 월소득 컬럼으로 연소득 계산하는 함수
def calculate_annual_income(monthly_income: int) -> int:
    return monthly_income * 12


# 부동산 컬럼으로 무주택자, 생애최초 구별
def determine_housing_status(real_estate_amount) -> tuple:
    """
    real_estate_amount가 0이면 무주택자, 생애최초자
    """
    if real_estate_amount == 0:
        return True, True  # (is_homeless, is_first_time)
    else:
        return False, False


# 전처리한 사용자 데이터 한 번에 모으는 함수
def preprocess_user_info(rrn) -> dict:
    """
    주민등록번호(rrn)를 입력받아 사용자 정보를 전처리합니다.
    반환 값: 이름, 나이, 연소득, 무주택 여부, 생애최초 여부, 자격유형
    """
    user = load_user_by_rrn(rrn)
    if user is None:
        return {"error": "사용자를 찾을 수 없습니다."}

    name = user["personal_name"]
    age = calculate_age(user["personal_birth_date"])
    annual_income = calculate_annual_income(user["monthly_avg_income_amount"])
    is_homeless, is_first_time = determine_housing_status(user.get("real_estate_amount"))
    group_type = user["eligibility_prime_type"]

    return {
        "name" : name,
        "age": age,
        "annual_income": annual_income,
        "is_homeless": is_homeless,
        "is_first_time": is_first_time,
        "group_type" : group_type
    }
