from tools.loan_utils import (
    load_loan_products,
    filter_loan_products,
    calculate_ltv_ratio,
    calculate_max_loan_amount,
    rank_loan_products
)
from tools.region_rules import get_announcement_by_id, classify_region_type
import pandas as pd
import json
import ast


import re
from decimal import Decimal

def filter_loan_products_by_user(user_db_info):
    """
    사용자 정보를 입력받아 조건에 맞는 대출 상품 목록을 필터링
    """
    try:
        print(f"[filter_loan_products_by_user] 받은 데이터 타입: {type(user_db_info)}")
        print(f"받은 데이터: {user_db_info}")
        
        # 다양한 형태의 입력 처리
        if isinstance(user_db_info, dict):
            processed = user_db_info
        elif isinstance(user_db_info, str):
            try:
                # JSON 형태 문자열
                if user_db_info.strip().startswith('{"'):
                    processed = json.loads(user_db_info)
                # Python dict 형태 문자열 (Decimal 포함)
                elif user_db_info.strip().startswith("{'"):
                    # Decimal('숫자') 패턴을 일반 숫자로 변환
                    cleaned_str = re.sub(r"Decimal\('(\d+)'\)", r'\1', user_db_info)
                    processed = ast.literal_eval(cleaned_str)
                else:
                    # 단순 문자열인 경우 오류
                    raise ValueError(f"Invalid format: {user_db_info}")
            except Exception as parse_error:
                print(f"파싱 오류: {parse_error}")
                return [{"❌ error": f"사용자 정보 파싱 실패: {str(parse_error)}"}]
        else:
            return [{"❌ error": f"지원하지 않는 데이터 타입: {type(user_db_info)}"}]
        
        # annual_income이 여전히 Decimal이거나 문자열인 경우 정수로 변환
        if 'annual_income' in processed:
            if isinstance(processed['annual_income'], Decimal):
                processed['annual_income'] = int(processed['annual_income'])
            elif isinstance(processed['annual_income'], str) and processed['annual_income'].isdigit():
                processed['annual_income'] = int(processed['annual_income'])
        
        # 필수 필드 확인
        required_fields = ['name', 'age', 'annual_income', 'is_homeless', 'is_first_time', 'group_type']
        for field in required_fields:
            if field not in processed:
                return [{"error": f"필수 필드 누락: {field}"}]
        
        df = load_loan_products()
        filtered_products = filter_loan_products(processed, df)
        
        if not filtered_products:
            return [{"message": "조건에 맞는 대출 상품이 없습니다."}]
            
        return filtered_products
        
    except Exception as e:
        print(f"대출 상품 필터링 오류: {str(e)}")
        return [{"❌ error": f"대출 상품 필터링 중 오류가 발생했습니다: {str(e)}"}]
    

def recommend_loans_by_user_and_announcement(input_data):
    """
    사용자 정보와 공고 ID를 입력받아 월 예상 상환액 계산
    input_data: 사용자 정보와 공고 ID가 포함된 딕셔너리 또는 JSON 문자열
    예: {"processed": {...}, "notice_number": "123"}
    """
    try:
        print(f"[recommend_loans_by_user_and_announcement] 받은 input_data 타입: {type(input_data)}")
        print(f"받은 input_data: {input_data}")
        
        # 입력 데이터 파싱
        if isinstance(input_data, dict):
            data = input_data
        elif isinstance(input_data, str):
            try:
                # JSON 형태 문자열 시도
                if input_data.strip().startswith('{"'):
                    data = json.loads(input_data)
                # Python dict 형태 문자열이지만 Decimal이 포함된 경우
                else:
                    # Decimal('숫자') 패턴을 일반 숫자로 변환
                    import re
                    cleaned_str = re.sub(r"Decimal\('(\d+)'\)", r'\1', input_data)
                    data = ast.literal_eval(cleaned_str)
            except Exception as parse_error:
                print(f"입력 데이터 파싱 오류: {parse_error}")
                return [{"❌ error": f"입력 데이터 파싱 실패: {str(parse_error)}"}]
        else:
            return [{"❌error": f"지원하지 않는 입력 타입: {type(input_data)}"}]
        
        # 필수 키 확인
        if "processed" not in data or "notice_number" not in data:
            return [{"❌error": "입력 데이터에 'processed'와 'notice_number'가 필요합니다."}]
        
        user_db_info = data["processed"]
        announcement_id = str(data["notice_number"])
        
        # 사용자 정보가 문자열인 경우 다시 파싱
        if isinstance(user_db_info, str):
            try:
                # JSON 형태 시도
                if user_db_info.strip().startswith('{"'):
                    user_db_info = json.loads(user_db_info)
                else:
                    # Decimal 처리
                    import re
                    cleaned_str = re.sub(r"Decimal\('(\d+)'\)", r'\1', user_db_info)
                    user_db_info = ast.literal_eval(cleaned_str)
            except Exception as e:
                print(f"사용자 정보 파싱 오류: {e}")
                return [{"error": f"사용자 정보 파싱 실패: {str(e)}"}]
        
        # annual_income이 문자열인 경우 정수로 변환
        if isinstance(user_db_info.get('annual_income'), str):
            user_db_info['annual_income'] = int(user_db_info['annual_income'])
        
        # 1. 공고 정보 조회
        announcement = get_announcement_by_id(announcement_id)
        if not announcement:
            return [{"error": "해당 공고를 찾을 수 없습니다."}]

        region_type = classify_region_type(announcement["location"])
        sale_price = announcement["avg_price"]

        # 2. LTV 계산
        ltv = calculate_ltv_ratio(region_type, user_db_info["is_first_time"], sale_price)
        max_loan = calculate_max_loan_amount(sale_price, ltv)

        # 3. 대출 상품 불러오기 및 필터링
        df = load_loan_products()
        filtered_products = filter_loan_products(user_db_info, df)

        filtered_df = pd.DataFrame(filtered_products)

        # 4. 필터링 된 모든 대출 상품 목록에 월 예상 상환액 계산 후 정렬
        ranked_products = rank_loan_products(user_db_info, filtered_df, max_loan)

        return ranked_products

    except Exception as e:
        print(f"대출 상품 추천 오류: {str(e)}")
        return [{"error": f"대출 상품 추천 중 오류가 발생했습니다: {str(e)}"}]