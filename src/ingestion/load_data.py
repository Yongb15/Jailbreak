import pandas as pd
import pymysql
import os
from dotenv import load_dotenv

# .env 파일의 DB 정보 로드
load_dotenv()

def load_dataset_to_db(file_path):
    try:
        # 1. CSV 파일 읽기 (UTF-8 인코딩)
        df = pd.read_csv(file_path, encoding='utf-8')
        
        print("--- 데이터셋 컬럼 확인 ---")
        print(df.columns.tolist())
        
        # 2. DB 연결
        conn = pymysql.connect(
            host=os.getenv("DB_HOST"),
            user=os.getenv("DB_USER"),
            password=os.getenv("DB_PASSWORD"),
            db=os.getenv("DB_NAME"),
            charset='utf8mb4'
        )
        cursor = conn.cursor()

        # 3. 데이터 삽입 로직
        inserted_count = 0
        for _, row in df.iterrows():
            # CSV 컬럼명과 DB 테이블 컬럼 매핑
            category = str(row['출처'])
            content = str(row['최종 테스트 프롬프트'])
            
            # 라벨 처리: CSV의 '라벨'이 1이면 True, 0이면 False (또는 숫자로 바로 저장)
            is_malicious = 1 if row['라벨'] == 1 or str(row['라벨']).lower() == 'true' else 0

            sql = "INSERT INTO prompts (category, content, is_malicious) VALUES (%s, %s, %s)"
            cursor.execute(sql, (category, content, is_malicious))
            inserted_count += 1
        
        conn.commit()
        conn.close()
        print(f"\n✅ 성공: 총 {inserted_count}개의 데이터가 'prompts' 테이블에 저장되었습니다.")

    except FileNotFoundError:
        print(f"❌ 파일을 찾을 수 없습니다: {file_path}. data/raw/ 폴더에 파일이 있는지 확인하세요.")
    except KeyError as e:
        print(f"❌ 컬럼명 매칭 에러: CSV의 컬럼명을 확인하세요. {e}")
    except Exception as e:
        print(f"❌ 에러 발생: {e}")

if __name__ == "__main__":
    file_name = "data/raw/Jailbreak_dataset.csv"
    load_dataset_to_db(file_name)