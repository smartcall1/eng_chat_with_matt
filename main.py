import os
import logging
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from apscheduler.schedulers.asyncio import AsyncIOScheduler
import pytz

import database
import gemini_integration
import scheduler_jobs

load_dotenv()

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TIMEZONE = os.getenv("TIMEZONE", "Australia/Brisbane")

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logging.getLogger("httpx").setLevel(logging.WARNING)

logger = logging.getLogger(__name__)

# --- Handlers ---
async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = update.effective_user.id
    chat_id = update.effective_chat.id
    database.update_last_interaction(user_id, chat_id)
    
    welcome_text = (
        "G'day mate! I'm your Brisbane surfing buddy.\n"
        "Just say hi and we can chat about the waves, the weather, or anything else you're keen on. Cheers!"
    )
    await update.message.reply_text(welcome_text)

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_text = update.message.text
    chat_id = update.effective_chat.id
    user_id = update.effective_user.id
    
    # 1. 수신 시간 및 세션 업데이트
    database.update_last_interaction(user_id, chat_id)
    
    # 2. 유저 메시지 DB 저장
    database.save_message(user_id, "user", user_text)
    
    # 3. 로컬 DB에서 해당 유저의 최근 대화 Context 로딩 (10개)
    history = database.get_recent_context(user_id, limit=10)
    
    # "is typing..." 상태 표시
    await context.bot.send_chat_action(chat_id=chat_id, action='typing')
    
    # 4. Gemini API 호출
    gemini_result = gemini_integration.generate_chat_response(history, user_text)
    reply_text = gemini_result["reply"]
    feedbacks = gemini_result["feedbacks"]
    image_url = gemini_result.get("image_url")
    
    # 5. 교정 내용 파싱 및 별도 DB 저장
    if feedbacks:
        for f in feedbacks:
            _orig = f.get("original", "")
            _corr = f.get("corrected", "")
            _expl = f.get("explanation", "")
            database.save_feedback(user_id, _orig, _corr, _expl)
            
    # 6. Bot 응답 내용 DB 저장 및 유저에게 전송
    database.save_message(user_id, "model", reply_text)
    
    # 이미지가 있으면 이미지와 함께 전송, 없으면 텍스트만 전송
    if image_url:
        try:
            await context.bot.send_photo(chat_id=chat_id, photo=image_url, caption=reply_text)
        except Exception as e:
            logger.error(f"Failed to send photo: {e}")
            await update.message.reply_text(reply_text)
    else:
        await update.message.reply_text(reply_text)


# --- Main ---
def main() -> None:
    # 1. DB 및 API 초기화
    database.init_db()
    gemini_integration.init_gemini()

    # scheduler를 미리 생성하지 않고, application 내의 job_queue를 활용하거나
    # 비동기적으로 시작하도록 조정합니다.
    application = Application.builder().token(TELEGRAM_BOT_TOKEN).build()

    # 2. Scheduler 설정 (AsyncIOScheduler는 이제 비동기 루프 내에서 시작되어야 함)
    # python-telegram-bot의 JobQueue가 내부적으로 APScheduler를 사용하므로 이를 활용하는 것이 더 깔끔합니다.
    # 하지만 기존 코드를 유지하면서 고치려면 post_init 등을 사용할 수 있습니다.

    async def post_init(application: Application):
        scheduler = AsyncIOScheduler(timezone=pytz.timezone(TIMEZONE))
        scheduler.add_job(scheduler_jobs.proactive_message_job, 'cron', hour='8,11,15,18,21', minute='30', kwargs={'context': application})
        scheduler.add_job(scheduler_jobs.daily_report_job, 'cron', hour=23, minute=30, kwargs={'context': application})
        scheduler.start()
        logger.info("Scheduler started in post_init.")

    application.post_init = post_init
    
    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    logger.info("Bot is spinning up... Ready to catch some waves!")
    application.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
