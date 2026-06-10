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
            # [수정] CSV 컬럼명에 맞춰 데이터 추출
            # 출처가 NaN이면 'General'로 저장
            category = str(row['출처']) if pd.notna(row['출처']) else 'General'
            
            # 새롭게 추가된 컬럼들 매핑
            original = str(row['원본 프롬프트'])
            translated = str(row['기본 번역본']) if pd.notna(row['기본 번역본']) else ''
            final = str(row['최종 테스트 프롬프트'])
            
            # [수정] 라벨 처리: CSV의 '라벨'이 '악성'이면 1, 아니면 0
            is_malicious = 1 if row['라벨'] == '악성' else 0

            # [수정] SQL 문에 original_prompt와 translated_prompt 추가
            sql = """
            INSERT INTO prompts (id, category, original_prompt, translated_prompt, final_prompt, is_malicious) 
            VALUES (%s, %s, %s, %s, %s, %s)
            """
            
            # '번호' 컬럼을 id로 사용 (PK 중복 방지를 위해 기존 데이터 삭제 후 실행 권장)
            cursor.execute(sql, (
                row['번호'], 
                category, 
                original, 
                translated, 
                final, 
                is_malicious
            ))
            inserted_count += 1
        
        conn.commit()
        conn.close()
        print(f"\n✅ 성공: 총 {inserted_count}개의 데이터가 DB에 저장되었습니다.")

    except FileNotFoundError:
        print(f"❌ 파일을 찾을 수 없습니다: {file_path}. 위치를 확인하세요.")
    except KeyError as e:
        print(f"❌ 컬럼명 매칭 에러: CSV의 컬럼명을 확인하세요. {e}")
    except Exception as e:
        print(f"❌ 에러 발생: {e}")

if __name__ == "__main__":
    # 파일 경로가 프로젝트 구조에 맞는지 확인 (이미지 상으론 src/database와 같은 라인에 있었음)
    file_name = "Jailbreak_dataset.csv" 
    load_dataset_to_db(file_name)