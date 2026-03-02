import sqlite3
import datetime
import logging

logger = logging.getLogger(__name__)
DB_NAME = "surfer_bot.db"

def get_connection():
    """SQLite 데이터베이스 연결 객체를 반환합니다."""
    return sqlite3.connect(DB_NAME)

def init_db():
    """초기 데이터베이스 테이블을 생성합니다."""
    with get_connection() as conn:
        cursor = conn.cursor()
        
        # 유저 세션 관리 테이블
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY,
                chat_id INTEGER,
                last_interaction_time TIMESTAMP
            )
        ''')
        
        # 대화 기록(Context) 테이블 (최근 N개 유지를 위해 사용)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS messages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                role TEXT, -- 'user' or 'bot'
                content TEXT,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (user_id)
            )
        ''')
        
        # 교정/피드백 저장 테이블 (데일리 리포트용)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS feedbacks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                original_text TEXT,
                corrected_text TEXT,
                explanation TEXT,
                reported BOOLEAN DEFAULT 0, -- 0: 아직 안보냄, 1: 데일리 리포트로 보냄
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (user_id)
            )
        ''')
        
        conn.commit()
    logger.info("Database initialized successfully.")

def update_last_interaction(user_id: int, chat_id: int):
    """유저의 마지막 상호작용 시간을 현재 시간으로 업데이트하거나 신규 생성합니다."""
    with get_connection() as conn:
        cursor = conn.cursor()
        now = datetime.datetime.now()
        
        # ON CONFLICT 구문은 SQLite 3.24.0+ 에서 지원됨.
        # UPSERT 로직 (Insert or Update)
        cursor.execute('''
            INSERT INTO users (user_id, chat_id, last_interaction_time)
            VALUES (?, ?, ?)
            ON CONFLICT(user_id) DO UPDATE SET
                chat_id=excluded.chat_id,
                last_interaction_time=excluded.last_interaction_time
        ''', (user_id, chat_id, now))
        conn.commit()

def save_message(user_id: int, role: str, content: str):
    """대화 메시지를 저장합니다."""
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO messages (user_id, role, content)
            VALUES (?, ?, ?)
        ''', (user_id, role, content))
        conn.commit()

def get_recent_context(user_id: int, limit: int = 10) -> list:
    """최근 N개의 대화 기록을 가져옵니다. (오래된 순서부터 정렬하여 반환)"""
    with get_connection() as conn:
        cursor = conn.cursor()
        # 최신 limit개 가져온 뒤 옛날 것부터 프롬프트에 넣기 위해 서브쿼리 활용
        cursor.execute('''
            SELECT role, content FROM (
                SELECT role, content, timestamp 
                FROM messages 
                WHERE user_id = ? 
                ORDER BY timestamp DESC 
                LIMIT ?
            ) ORDER BY timestamp ASC
        ''', (user_id, limit))
        return cursor.fetchall()

def save_feedback(user_id: int, original: str, corrected: str, explanation: str):
    """Gemini가 파싱한 피드백을 저장합니다."""
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO feedbacks (user_id, original_text, corrected_text, explanation)
            VALUES (?, ?, ?, ?)
        ''', (user_id, original, corrected, explanation))
        conn.commit()
        
def get_unreported_feedbacks():
    """아직 데일리 리포트로 전송되지 않은 피드백 목록을 가져옵니다."""
    with get_connection() as conn:
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute('''
            SELECT f.id, f.user_id, u.chat_id, f.original_text, f.corrected_text, f.explanation 
            FROM feedbacks f
            JOIN users u ON f.user_id = u.user_id
            WHERE f.reported = 0
            ORDER BY f.user_id, f.timestamp ASC
        ''')
        return cursor.fetchall()
        
def mark_feedbacks_as_reported(feedback_ids: list):
    """피드백들을 리포트 완료 상태로 마킹합니다."""
    if not feedback_ids:
        return
    with get_connection() as conn:
        cursor = conn.cursor()
        placeholders = ','.join('?' * len(feedback_ids))
        cursor.execute(f'''
            UPDATE feedbacks 
            SET reported = 1 
            WHERE id IN ({placeholders})
        ''', feedback_ids)
        conn.commit()

# 단독 실행 테스트용
if __name__ == "__main__":
    init_db()
