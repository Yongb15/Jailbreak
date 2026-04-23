import asyncio
import sqlite3
import os
import time
from google import genai
from google.genai import types
from dotenv import load_dotenv

# .env 파일 로드 (API_KEY 등 보안 정보)
load_dotenv()

# --- [설정 및 파라미터] ---
API_KEY = os.getenv("GEMINI_API_KEY")
MODEL_NAME = "gemini-2.5-flash"  # 속도와 가성비의 Flash 모델
DB_PATH = "jailbreak_eval.sqlite"
CONCURRENCY_LIMIT = 10  # Flash 모델은 15~20까지 높여도 안정적입니다.

# [가격 설정] Gemini 2.5 Flash 표준 단가 (1M 토큰당 달러)
PRICE_INPUT_1M = 0.10   # 입력 토큰 100만 개당 $0.1
PRICE_OUTPUT_1M = 0.40  # 출력 토큰 100만 개당 $0.4
EXCHANGE_RATE = 1400    # 원화 환산 환율

# 최신 SDK 비동기 지원 클라이언트 설정
client = genai.Client(api_key=API_KEY)

async def fetch_remaining_prompts():
    """아직 결과가 없는 프롬프트 목록을 가져옵니다."""
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
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
    """실험 결과를 DB에 기록합니다."""
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

async def call_gemini(prompt_id, content, semaphore):
    """Gemini API를 호출하고 비용과 토큰을 계산합니다."""
    async with semaphore:
        attempt = 1
        while True:
            start_time = time.time()
            try:
                # 비동기 모델 호출
                response = await client.aio.models.generate_content(
                    model=MODEL_NAME,
                    contents=str(content),
                    config=types.GenerateContentConfig(
                        temperature=0.0,
                        # 가드레일 우회를 실험하기 위해 모든 차단 해제
                        safety_settings=[
                            types.SafetySetting(category="HARM_CATEGORY_HARASSMENT", threshold="BLOCK_NONE"),
                            types.SafetySetting(category="HARM_CATEGORY_HATE_SPEECH", threshold="BLOCK_NONE"),
                            types.SafetySetting(category="HARM_CATEGORY_SEXUALLY_EXPLICIT", threshold="BLOCK_NONE"),
                            types.SafetySetting(category="HARM_CATEGORY_DANGEROUS_CONTENT", threshold="BLOCK_NONE"),
                        ]
                    )
                )
                
                latency = time.time() - start_time
                
                # 가드레일에 의한 완전 차단 여부 확인
                ans = response.text if response.text else "⚠️ [Safety Blocked by Guardrail]"

                # --- 토큰 및 비용 실시간 계산 ---
                usage = response.usage_metadata
                in_tokens = usage.prompt_token_count
                out_tokens = usage.candidates_token_count
                
                # 비용 계산 (USD -> KRW)
                cost_usd = (in_tokens / 1_000_000 * PRICE_INPUT_1M) + (out_tokens / 1_000_000 * PRICE_OUTPUT_1M)
                cost_krw = cost_usd * EXCHANGE_RATE
                
                # DB 저장
                await save_result(prompt_id, ans, latency)
                
                print(f"⚡ [ID {prompt_id}] 완료! ({latency:.2f}s) | "
                      f"Tokens: {in_tokens}+{out_tokens} | "
                      f"Cost: ₩{cost_krw:.4f}")
                return True

            except Exception as e:
                error_msg = str(e)
                # 429(할당량 초과) 등 일시적 서버 오류 시 재시도
                if any(x in error_msg for x in ["429", "500", "503"]):
                    wait = min(attempt * 3, 30) # Flash는 재대기 시간을 짧게 설정
                    print(f"⏳ [ID {prompt_id}] 서버 지연({error_msg[:3]}). {wait}초 후 재시도...")
                    await asyncio.sleep(wait)
                    attempt += 1
                else:
                    print(f"❌ [ID {prompt_id}] 치명적 에러: {error_msg}")
                    return False

async def main():
    if not API_KEY:
        print("❌ API_KEY를 환경변수나 .env에서 확인해주세요.")
        return

    # 1. 미완료 작업 가져오기
    prompts = await fetch_remaining_prompts()
    total_remaining = len(prompts)
    
    if total_remaining == 0:
        print(f"🏁 모든 실험 완료! ({MODEL_NAME})")
        return

    print(f"🚀 {MODEL_NAME} 광속 실험 시작 (남은 작업: {total_remaining}건)")
    
    # 2. 세마포어를 이용한 동시성 제어
    semaphore = asyncio.Semaphore(CONCURRENCY_LIMIT)
    
    # 3. 모든 작업 생성 및 실행
    tasks = [call_gemini(p[0], p[1], semaphore) for p in prompts]
    await asyncio.gather(*tasks)
    
    print(f"\n🏁 모든 {MODEL_NAME} 실험 데이터 수집이 완료되었습니다!")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n🛑 사용자에 의해 중단되었습니다.")