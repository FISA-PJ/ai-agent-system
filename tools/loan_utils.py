"""
대출 필터링 및 계산 함수 (LTV, 월 예상 상환액 등)
"""
import os
from dotenv import load_dotenv
import pandas as pd
from db.db import get_db_connection

load_dotenv()

# 대출 상품 불러오는 함수 (DB 대체)
def load_loan_products() -> pd.DataFrame:
    """
    housing_loan_products 테이블에서 대출 상품 데이터를 불러옵니다.
    """
    # DB 연결 설정
    conn = get_db_connection(os.getenv("LOAN_DB"))

    try:
        with conn.cursor() as cursor:
            # 쿼리 실행
            cursor.execute("SELECT * FROM housing_loan_products")
            rows = cursor.fetchall()
            df = pd.DataFrame(rows)
            return df
    finally:
        conn.close()

# 사용자 조건에 맞는 대출 상품 필터링하는 함수
def filter_loan_products(user_db_info: dict, df: pd.DataFrame) -> pd.DataFrame:
    age = user_db_info["age"]
    income = user_db_info["annual_income"] // 10000  # 만원 단위로 변환
    is_homeless = user_db_info["is_homeless"]
    is_first_time = user_db_info["is_first_time"]
    group_type = user_db_info["group_type"]

    # 조건별 필터링
    filtered_df = df[
        ((df["target_group"] == "일반 대상자") | (df["target_group"] == group_type)) &
        (df["income_min"].isna() | (income >= df["income_min"])) &
        (df["income_max"].isna() | (income <= df["income_max"])) &
        (df["target_age_min"].isna() | (age >= df["target_age_min"])) &
        (df["target_age_max"].isna() | (age <= df["target_age_max"])) &
        ((df["house_owned_limit"] == False) | is_homeless) &
        ((df["first_home_only"] == False) | is_first_time)
    ]

    loan_filter = filtered_df.sort_values("rate_max").reset_index(drop=True)

    return loan_filter.to_dict(orient="records")


# LTV 계산 함수
def calculate_ltv_ratio(region_type: str, is_first_time: bool, sale_price: int) -> float:
    """
    지역유형, 생애최초 여부, 주택 분양가(원 단위)를 기준으로 LTV 비율(%)을 계산하여 리턴합니다.

    기준표:
    | 지역 유형 | 일반, 9억 이하 | 일반, 9억 초과 | 생애최초, 9억 이하 |
    |----------|---------------|---------------|-------------------|
    | 투기과열지구 | 40%         | 20%          | 80%              |
    | 조정대상지역 | 50%         | 30%          | 80%              |
    | 비규제지역   | 70%         | 70%          | 80%              |
    """
    price_limit = 900000000  # 9억 기준선

    # 생애최초자 조건 (단, 주택가격 9억 이하만 해당됨)
    if is_first_time and sale_price <= price_limit:
        return 0.8  # 80%

    # 일반자 조건 (지역 + 주택가 기준)
    if region_type == "투기과열지구":
        return 0.4 if sale_price <= price_limit else 0.2
    elif region_type == "조정대상지역":
        return 0.5 if sale_price <= price_limit else 0.3
    elif region_type == "비규제지역":
        return 0.7  # 가격 상관없이 70%
    else:
        return 0.7  # 기본값: 비규제 지역처럼 처리


# LTV로 최대 대출 가능 금액 계산
def calculate_max_loan_amount(sale_price: int, ltv_ratio: float) -> int:
    """
    주택 분양가(sale_price)와 LTV 비율(ltv_ratio)을 이용하여
    최대 대출 가능 금액(원 단위)을 계산합니다.
    """
    return int(float(sale_price) * ltv_ratio)


# 월 예상 상환액 계산
def calculate_monthly_payment(loan_amount: int, rate_min: float, rate_max: float, loan_term: int, repayment_method: str) -> int:
    """
    대출금액, 금리, 상환방식에 따라 예상 월 상환액을 계산합니다.
    - 원리금균등상환: 매월 동일한 금액
    - 원금균등상환: 매월 금액이 달라짐 → 평균값 계산

    Parameters:
        loan_amount (int): 대출금액 (원)
        rate_min (float): 최소 금리 (%)
        rate_max (float): 최대 금리 (%)
        loan_term (int): 대출기간 (개월)
        repayment_method (str): '원리금균등' 또는 '원금균등'

    Returns:
        int: 월 예상 상환액 (원)
    """

    # 평균 금리로 계산
    annual_rate = (rate_min + rate_max) / 2
    monthly_rate = annual_rate / 100 / 12  # %를 소수로, 월 단위

    if repayment_method == "원리금균등":
        if monthly_rate == 0:
            return loan_amount // loan_term
        monthly_payment = loan_amount * monthly_rate / (1 - (1 + monthly_rate) ** -loan_term)
        return int(round(monthly_payment))

    elif repayment_method == "원금균등":
        monthly_principal = loan_amount / loan_term
        total_payment = 0
        for i in range(loan_term):
            remaining = loan_amount - (monthly_principal * i)
            monthly_interest = remaining * monthly_rate
            monthly_payment = monthly_principal + monthly_interest
            total_payment += monthly_payment
        average_payment = total_payment / loan_term
        return int(round(average_payment))

    else:
        raise ValueError("repayment_method는 '원리금균등' 또는 '원금균등'이어야 합니다.")


# 사용자 정보로 필터링 된 대출 상품들에 월 예상 상환액 계산 후 정렬
def rank_loan_products(user_db_info: dict, filtered_df: pd.DataFrame, max_loan_amount: int) -> pd.DataFrame:
    """
    user_db_info는 현재 로직에서는 사용되지 않지만,
    향후 사용자 특성 기반 정렬 확장을 위해 파라미터로 유지함
    """
    filtered_df = filtered_df.copy()

    monthly_payments = []
    for _, row in filtered_df.iterrows():
        try:
            # 상품별 최대 대출 한도와 사용자 최대 대출 가능 금액 중 작은 값 사용
            loan_amount = min(max_loan_amount, row["loan_limit"])
            payment = calculate_monthly_payment(
                loan_amount=loan_amount,
                rate_min=float(row["rate_min"]),
                rate_max=float(row["rate_max"]),
                loan_term=row["loan_term"],
                repayment_method=row["repayment_method"].strip()
            )
        except Exception as e:
            print("계산 오류 발생:", e)
            payment = float("inf")  # 오류난 건 정렬 뒤로 밀기

        monthly_payments.append(payment)

    filtered_df["monthly_payment"] = monthly_payments
    # 월 예상 상환액 오름차순 정렬
    ranked = filtered_df.sort_values("monthly_payment").reset_index(drop=True)

    return ranked.to_dict(orient="records")
