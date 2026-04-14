import pandas as pd
import sqlite3
import os

def load_data():
    # 1. 경로 및 파일 설정
    csv_path = "Jailbreak_dataset.csv"  # 원본 CSV 파일명
    db_path = "jailbreak_eval.sqlite"   # 생성될 SQLite 파일명

    if not os.path.exists(csv_path):
        print(f"❌ 파일을 찾을 수 없습니다: {csv_path}")
        return

    # 2. 데이터 로드 및 전처리
    # CSV를 읽어오고, 비어있는 '출처' 컬럼을 'General'로 채웁니다.
    df = pd.read_csv(csv_path)
    df['출처'] = df['출처'].fillna('General') 
    
    # '라벨' 컬럼의 '악성'은 1, '정상'은 0으로 변환하여 저장합니다.
    df['is_malicious'] = df['라벨'].apply(lambda x: 1 if x == '악성' else 0)
    
    # NaN(결측치)이 있을 경우 DB 삽입 에러가 날 수 있으므로 빈 문자열로 처리합니다.
    df = df.fillna('')

    # 3. 기존 DB 초기화 (새로 실행할 때마다 기존 파일을 밀고 깔끔하게 생성)
    if os.path.exists(db_path):
        os.remove(db_path)
        print("🧹 기존 DB 파일을 삭제하고 새로 구축을 시작합니다.")

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # 4. 테이블 설계 (논문 분석에 필요한 모든 필드 포함)
    # prompts: 실험용 프롬프트 정보 저장
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS prompts (
        id INTEGER PRIMARY KEY,
        category TEXT,
        original_prompt TEXT,
        translated_prompt TEXT,
        final_prompt TEXT,
        is_malicious INTEGER,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)

    # results: LLM 응답 결과 저장용 (미리 생성)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS results (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        prompt_id INTEGER,
        model_name TEXT,
        response_text TEXT,
        latency REAL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (prompt_id) REFERENCES prompts(id)
    )
    """)

    # 5. 데이터 삽입 실행
    print("📥 데이터를 SQLite로 옮기는 중...")
    for _, row in df.iterrows():
        cursor.execute("""
        INSERT INTO prompts (id, category, original_prompt, translated_prompt, final_prompt, is_malicious)
        VALUES (?, ?, ?, ?, ?, ?)
        """, (
            row['번호'], 
            row['출처'], 
            row['원본 프롬프트'], 
            row['기본 번역본'], 
            row['최종 테스트 프롬프트'], 
            row['is_malicious']
        ))

    conn.commit()
    conn.close()
    
    print("-" * 30)
    print(f"✅ DB 구축이 성공적으로 완료되었습니다!")
    print(f"📂 파일명: {db_path}")
    print(f"📊 총 데이터 수: {len(df)}건")
    print("-" * 30)

if __name__ == "__main__":
    load_data()