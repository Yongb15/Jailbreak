import asyncio
import sqlite3
import os
import time
from anthropic import AsyncAnthropic
from dotenv import load_dotenv

load_dotenv()

API_KEY = os.getenv("ANTHROPIC_API_KEY")
MODEL_NAME = "claude-sonnet-4-6"   # Claude Haiku 4.5
DB_PATH = "jailbreak_eval.sqlite"
CONCURRENCY_LIMIT = 5

# 가격 (대략)
PRICE_INPUT_1M = 3.00
PRICE_OUTPUT_1M = 15.00
EXCHANGE_RATE = 1400

client = AsyncAnthropic(api_key=API_KEY)

async def fetch_remaining_prompts():
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    query = """
        SELECT p.id, p.final_prompt
        FROM prompts p
        WHERE p.id NOT IN (
            SELECT prompt_id FROM results WHERE model_name = ?
        )
    """

    cur.execute(query, (MODEL_NAME,))
    rows = cur.fetchall()
    conn.close()
    return rows

async def save_result(prompt_id, response_text, latency):
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

async def call_claude(prompt_id, content, semaphore):
    async with semaphore:
        attempt = 1

        while True:
            start_time = time.time()

            try:
                response = await client.messages.create(
                    model=MODEL_NAME,
                    max_tokens=1024,
                    temperature=0.0,
                    messages=[
                        {"role": "user", "content": str(content)}
                    ]
                )

                latency = time.time() - start_time

                if response.content and len(response.content) > 0:
                    ans = response.content[0].text
                else:
                    ans = "⚠️ [No Response]"

                usage = response.usage
                in_tokens = usage.input_tokens
                out_tokens = usage.output_tokens

                cost_usd = (
                    in_tokens / 1_000_000 * PRICE_INPUT_1M
                    + out_tokens / 1_000_000 * PRICE_OUTPUT_1M
                )
                cost_krw = cost_usd * EXCHANGE_RATE

                await save_result(prompt_id, ans, latency)

                print(
                    f"⚡ [ID {prompt_id}] 완료! ({latency:.2f}s) | "
                    f"Tokens: {in_tokens}+{out_tokens} | "
                    f"Cost: ₩{cost_krw:.4f}"
                )

                return True

            except Exception as e:
                error_msg = str(e)

                if any(x in error_msg for x in ["429", "500", "503", "rate_limit", "overloaded"]):
                    wait = min(attempt * 3, 30)
                    print(f"⏳ [ID {prompt_id}] 서버 지연. {wait}초 후 재시도...")
                    await asyncio.sleep(wait)
                    attempt += 1
                else:
                    print(f"❌ [ID {prompt_id}] 치명적 에러: {error_msg}")
                    return False

async def main():
    if not API_KEY:
        print("❌ ANTHROPIC_API_KEY를 .env에서 확인해주세요.")
        return

    prompts = await fetch_remaining_prompts()
    total_remaining = len(prompts)

    if total_remaining == 0:
        print(f"🏁 모든 실험 완료! ({MODEL_NAME})")
        return

    print(f"🚀 {MODEL_NAME} 실험 시작 (남은 작업: {total_remaining}건)")

    semaphore = asyncio.Semaphore(CONCURRENCY_LIMIT)
    tasks = [call_claude(p[0], p[1], semaphore) for p in prompts]

    await asyncio.gather(*tasks)

    print(f"\n🏁 모든 {MODEL_NAME} 실험 데이터 수집 완료!")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n🛑 사용자에 의해 중단되었습니다.")