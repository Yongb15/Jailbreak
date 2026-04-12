import pymysql # pip install pymysql 필요
import os
from dotenv import load_dotenv

load_dotenv()

def test_connection():
    try:
        connection = pymysql.connect(
            host=os.getenv("DB_HOST"),
            user=os.getenv("DB_USER"),
            password=os.getenv("DB_PASSWORD"),
            db=os.getenv("DB_NAME"),
            charset='utf8mb4'
        )
        print("✅ DB 연결 성공! 파이프라인 가동 준비 완료.")
        connection.close()
    except Exception as e:
        print(f"❌ DB 연결 실패: {e}")

if __name__ == "__main__":
    test_connection()