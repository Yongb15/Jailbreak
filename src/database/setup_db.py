import pymysql
import os
from dotenv import load_dotenv

load_dotenv()

def setup_database():
    conn = pymysql.connect(
        host=os.getenv("DB_HOST"),
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASSWORD"),
        db=os.getenv("DB_NAME"),
        charset='utf8mb4'
    )
    
    try:
        with conn.cursor() as cursor:
            # schema.sql 파일 읽기
            sql_path = os.path.join(os.path.dirname(__file__), 'schema.sql')
            with open(sql_path, 'r', encoding='utf-8') as f:
                sql_commands = f.read().split(';')
            
            # 각 명령어를 순차적으로 실행
            for command in sql_commands:
                if command.strip():
                    cursor.execute(command)
        
        conn.commit()
        print("✅ 데이터베이스 테이블 설계(Schema) 적용 완료!")
    except Exception as e:
        print(f"❌ DB 세팅 실패: {e}")
    finally:
        conn.close()

if __name__ == "__main__":
    setup_database()