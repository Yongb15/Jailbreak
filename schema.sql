/*  MySQL 테이블 생성 쿼리 */
CREATE DATABASE IF NOT EXISTS jailbreak_eval;
USE jailbreak_eval;

-- 1. 프롬프트 저장 테이블 (정상/악성 구분) [cite: 68]
CREATE TABLE prompts (
    id INT AUTO_INCREMENT PRIMARY KEY,
    category VARCHAR(50), -- 유해 정보, 정책 우회 등 [cite: 62, 63]
    content TEXT NOT NULL,
    is_malicious BOOLEAN -- 악성(True), 정상(False) [cite: 61, 64]
);

-- 2. 실험 결과 및 성능 지표 저장 테이블 [cite: 48, 49]
CREATE TABLE results (
    id INT AUTO_INCREMENT PRIMARY KEY,
    prompt_id INT,
    model_name VARCHAR(50), -- GPT, Claude, Gemini 등 [cite: 45]
    response_text TEXT,
    judgment VARCHAR(20), -- Hard Refusal, Soft Refusal, Success [cite: 47]
    latency FLOAT,         -- 소요 시간 [cite: 46]
    token_usage INT,       -- 토큰 수 [cite: 46]
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (prompt_id) REFERENCES prompts(id)
);