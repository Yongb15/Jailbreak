-- 1. 프롬프트 저장 테이블
CREATE TABLE prompts (
    id INT PRIMARY KEY,
    category VARCHAR(255),
    original_prompt TEXT,
    translated_prompt TEXT,
    final_prompt TEXT,
    is_malicious TINYINT(1),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 2. LLM 응답 결과 저장 테이블
CREATE TABLE IF NOT EXISTS results (
    id INT AUTO_INCREMENT PRIMARY KEY,
    prompt_id INT,                               -- 어떤 프롬프트에 대한 응답인지 (FK 역할)
    model_name VARCHAR(100),                     -- GPT-4, Gemini, Claude 등
    response_text TEXT,                          -- LLM이 내뱉은 실제 문장
    jailbreak_success TINYINT(1),                -- 탈옥 성공 여부 (판독 결과)
    latency FLOAT,                               -- 응답 속도
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (prompt_id) REFERENCES prompts(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
