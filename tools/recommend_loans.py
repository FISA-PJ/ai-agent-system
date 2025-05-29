from langchain.tools import tool
from tools.user_utils import preprocess_user_info
from tools.loan_utils import (
    load_loan_products,
    filter_loan_products,
    calculate_ltv_ratio,
    calculate_max_loan_amount,
    rank_loan_products
)
from tools.region_rules import get_announcement_by_id, classify_region_type
import pandas as pd


@tool
def preprocess_user_info_tool(rrn: str) -> dict:
    """
    주민등록번호를 입력받아 LangChain tool로 사용자 정보 전처리
    반환 값: dict → { name, age, annual_income, is_homeless, is_first_time, group_type }
    """
    result = preprocess_user_info(rrn)
    return result if result else {"error": "사용자를 찾을 수 없습니다."}


@tool
def filter_loan_products_by_user(user_info: dict) -> list:
    """
    사용자 정보(dict)를 입력받아 조건에 맞는 대출 상품 목록을 필터링
    반환 값: list[dict] → 필터링된 대출 상품 목록 (각 항목은 상품 정보 딕셔너리)
    """
    df = load_loan_products()
    return filter_loan_products(user_info, df)


@tool
def recommend_loans_by_user_and_announcement(user_info: dict, announcement_id: str) -> list:
    """
    사용자 정보와 공고 ID를 입력받아 월 예상 상환액 계산
    - 지역 분류 및 LTV 계산
    - 분양가 기반 최대 대출 한도 계산
    - 월 예상 상환액 계산 후 오름차순 정렬
    반환 값: list[dict] → 월 예상 상환액이 추가되고 이걸 기준으로 오름차순 정렬된 상품 목록
    """
    # 1. 공고 정보 조회
    announcement = get_announcement_by_id(announcement_id)
    if not announcement:
        return {"error": "해당 공고를 찾을 수 없습니다."}

    region_type = classify_region_type(announcement["location"])
    sale_price = announcement["avg_price"]

    # 2. LTV 계산
    ltv = calculate_ltv_ratio(region_type, user_info["is_first_time"], sale_price)
    max_loan = calculate_max_loan_amount(sale_price, ltv)

    # 3. 대출 상품 불러오기 및 필터링
    filtered_products = filter_loan_products_by_user(user_info)
    filtered_df = pd.DataFrame(filtered_products)

    # 4. 필터링 된 모든 대출 상품 목록에 월 예상 상환액 계산 후 정렬
    ranked_products = rank_loan_products(user_info, filtered_df, max_loan)

    return ranked_products
