from contextlib import contextmanager
import pymysql
import os
from dotenv import load_dotenv

load_dotenv()

# DB 연결 함수
def get_db_connection(db_name: str):
    return pymysql.connect(
        host=os.getenv("DB_HOST"),
        port=int(os.getenv("DB_PORT")),
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASSWORD"),
        database=db_name,
        charset='utf8mb4',
        cursorclass=pymysql.cursors.DictCursor
    )


# @contextmanager
# def get_db_connection(db_name: str):
#     conn = None
#     try:
#         conn = pymysql.connect(
#             host=os.getenv("DB_HOST"),
#             port=int(os.getenv("DB_PORT")),
#             user=os.getenv("DB_USER"),
#             password=os.getenv("DB_PASSWORD"),
#             database=db_name,
#             charset='utf8mb4',
#             cursorclass=pymysql.cursors.DictCursor,
#             connect_timeout=10,
#             autocommit=True
#         )
#         yield conn
#     finally:
#         if conn:
#             conn.close()