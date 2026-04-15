import asyncio
import sqlite3
import os
import time
from google import genai
from google.genai import types
from dotenv import load_dotenv

# .env 파일 로드
load_dotenv()

# --- 설정 ---
API_KEY = os.getenv("GEMINI_API_KEY")
# 앞선 테스트에서 확인된 가장 안정적인 모델명 사용
MODEL_NAME = "gemini-flash-latest" 
DB_PATH = "jailbreak_eval.sqlite"

# 최신 SDK Client 설정
client = genai.Client(api_key=API_KEY)

async def fetch_remaining_prompts():
    """이미 결과(results)가 있는 ID는 제외하고 가져옴 (이어하기 기능)"""
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    # results 테이블에 현재 모델로 성공한 기록이 없는 prompt만 추출
    query = f"""
        SELECT p.id, p.final_prompt 
        FROM prompts p
        WHERE p.id NOT IN (
            SELECT prompt_id FROM results WHERE model_name = '{MODEL_NAME}'
        )
    """
    cur.execute(query)
    rows = cur.fetchall()
    conn.close()
    return rows

async def save_result(prompt_id, response_text, latency):
    """성공한 결과만 DB에 저장"""
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    try:
        cur.execute("""
            INSERT INTO results (prompt_id, model_name, response_text, latency)
            VALUES (?, ?, ?, ?)
        """, (prompt_id, MODEL_NAME, response_text, latency))
        conn.commit()
    except Exception as e:
        print(f"⚠️ DB 저장 실패 (ID {prompt_id}): {e}")
    finally:
        conn.close()

async def call_gemini_with_retry(prompt_id, content):
    """성공할 때까지 무한 재시도하며 에러 발생 시 DB 저장을 건너뜀"""
    while True:
        start_time = time.time()
        try:
            # AI 모델 호출
            response = await client.models.generate_content(
                model=MODEL_NAME,
                contents=str(content),
                config=types.GenerateContentConfig(
                    temperature=0.0  # 실험 일관성을 위해 0 설정
                )
            )
            
            latency = time.time() - start_time
            # 답변이 비어있으면 안전 필터 차단으로 간주 (연구 데이터로 활용 가능)
            ans = response.text if response.text else "⚠️ [Safety Blocked by Guardrail]"
            
            # [핵심] 호출이 완전히 성공했을 때만 DB에 저장
            await save_result(prompt_id, ans, latency)
            print(f"✅ [ID {prompt_id}] 성공! ({latency:.2f}s)")
            return True

        except Exception as e:
            error_msg = str(e)
            
            if "429" in error_msg:
                # 할당량 초과 시 DB 저장 없이 대기 후 루프 재시작
                print(f"⏳ [ID {prompt_id}] 할당량 초과! DB 저장 안 함. 90초 대기 중...")
                await asyncio.sleep(90)
                # return을 하지 않고 while True 루프를 계속 돌아 재시도함
            else:
                # 404 등 다른 치명적 에러 발생 시
                print(f"❌ [ID {prompt_id}] 치명적 에러 발생: {error_msg}")
                # 필요하다면 여기서 return False를 하여 해당 ID를 건너뛸 수 있음
                return False

async def main():
    if not API_KEY:
        print("❌ .env 파일에서 API_KEY를 확인해주세요.")
        return

    # 1. 남은 작업 확인
    prompts = await fetch_remaining_prompts()
    total_remaining = len(prompts)
    
    if total_remaining == 0:
        print(f"🏁 모든 실험이 이미 완료되었습니다! (모델: {MODEL_NAME})")
        return

    print(f"🚀 {MODEL_NAME} 실험 시작 (남은 작업: {total_remaining}건)")
    print(f"⏱️ 안전을 위해 요청 간격을 10초로 유지합니다.")

    # 2. 순차적으로 실행
    for p_id, p_content in prompts:
        # 이 함수 내부에서 성공할 때까지 무한 루프를 돎
        await call_gemini_with_retry(p_id, p_content)
        
        # 성공 후 다음 질문 전까지 10초 휴식 (RPM 보호)
        await asyncio.sleep(10)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n🛑 사용자에 의해 중단되었습니다. 다시 실행하면 남은 부분부터 시작합니다.")