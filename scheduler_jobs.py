import logging
import datetime
from telegram.ext import ContextTypes

import database
import gemini_integration
import weather_hook

logger = logging.getLogger(__name__)

async def proactive_message_job(context: ContextTypes.DEFAULT_TYPE):
    """
    봇이 스스로 말을 거는 Job.
    APScheduler에 의해 지정된 시간(또는 크론)에 실행됩니다.
    """
    logger.info("Running proactive messaging check...")
    
    # DB에서 유저 목록을 가져옴 (users 테이블 전체 스캔의 간소화 버전)
    with database.get_connection() as conn:
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute("SELECT user_id, chat_id, last_interaction_time FROM users")
        users = cursor.fetchall()

    now = datetime.datetime.now()
    
    for user_row in users:
        user_id = user_row["user_id"]
        chat_id = user_row["chat_id"]
        last_time_str = user_row["last_interaction_time"]
        
        # 1. 1시간 무응답 체크 로직 (문자열 파싱)
        try:
            # SQLite default timestamp format: YYYY-MM-DD HH:MM:SS.mmmmmm
            last_dt = datetime.datetime.strptime(last_time_str, "%Y-%m-%d %H:%M:%S.%f")
        except ValueError:
            # 밀리초 없는 경우 Fallback
            last_dt = datetime.datetime.strptime(last_time_str, "%Y-%m-%d %H:%M:%S")
            
        diff_hours = (now - last_dt).total_seconds() / 3600.0
        
        # 만약 마지막 대화가 1시간 이내였다면 방해하지 않고 스킵
        if diff_hours < 1.0:
            logger.info(f"Skipping proactive message for User {user_id}: recently active.")
            continue
            
        # 2. 날씨 정보 Hook 가져오기
        weather_ctx = await weather_hook.get_brisbane_weather_context()
        
        # 3. 선톡을 위한 System Message 구성 (Gemini)
        # 평소의 history 대신, 봇이 스스로 대화를 여는 프롬프트를 전송합니다.
        hook_prompt = (
            f"You are reaching out to the user to start a conversation because it's been a while. "
            f"Here is the current weather condition in your city: {weather_ctx}\n"
            f"Naturally say hi, mention the weather or something you are doing (like surfing or working at the cafe), "
            f"and ask how they are doing to spark a casual chat. Keep it fairly short."
        )
        
        # History 없이 새 대화 세션 취급 (빈 리스트 전달)
        gemini_result = gemini_integration.generate_chat_response(history=[], new_message=hook_prompt)
        reply_text = gemini_result["reply"]
        
        # 4. 발송 및 DB 기록
        try:
            await context.bot.send_message(chat_id=chat_id, text=reply_text)
            database.save_message(user_id, "model", reply_text)
            logger.info(f"Sent proactive message to User {user_id}")
        except Exception as e:
            logger.error(f"Failed to send proactive message to {user_id}: {e}")

async def daily_report_job(context: ContextTypes.DEFAULT_TYPE):
    """
    하루 동안 모인 피드백을 모아서 유저에게 리포트로 전송합니다.
    """
    logger.info("Running daily report job...")
    
    feedbacks = database.get_unreported_feedbacks()
    if not feedbacks:
        logger.info("No new feedbacks for daily report.")
        return
        
    # 유저별로 그룹핑
    user_feedbacks = {}
    for row in feedbacks:
        u_id = row["user_id"]
        c_id = row["chat_id"]
        if u_id not in user_feedbacks:
            user_feedbacks[u_id] = {"chat_id": c_id, "items": [], "ids": []}
            
        user_feedbacks[u_id]["items"].append({
            "original": row["original_text"],
            "corrected": row["corrected_text"],
            "explanation": row["explanation"]
        })
        user_feedbacks[u_id]["ids"].append(row["id"])
        
    for u_id, data in user_feedbacks.items():
        chat_id = data["chat_id"]
        items = data["items"]
        ids = data["ids"]
        
        # 마크다운 리포트 포매팅
        report_msg = "🏄‍♂️ **Daily Mates English Report** 🇦🇺\n\n"
        report_msg += "Cheers mate! Good job practicing English today.\nHere are a few bits we can polish up:\n\n"
        
        for idx, item in enumerate(items, 1):
            report_msg += f"🔥 **{idx}. You said:** _{item['original']}_\n"
            report_msg += f"✅ **Try saying it like this:** `{item['corrected']}`\n"
            report_msg += f"💡 **Why?** {item['explanation']}\n\n"
            
        report_msg += "Catch ya tomorrow! Stay rad. 🤙"
        
        try:
            await context.bot.send_message(chat_id=chat_id, text=report_msg, parse_mode="Markdown")
            database.mark_feedbacks_as_reported(ids)
            logger.info(f"Sent daily report to User {u_id}")
        except Exception as e:
            logger.error(f"Failed to send daily report to {u_id}: {e}")

import sqlite3 # needs to be imported here for DB row fetch
