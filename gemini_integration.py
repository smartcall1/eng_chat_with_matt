import os
import json
import logging
from datetime import datetime
import pytz
from google import genai
from google.genai import types

logger = logging.getLogger(__name__)

client = None

def init_gemini():
    """Gemini API 환경 설정 및 초기화"""
    global client
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        logger.error("Gemini API key not found in environment variables.")
        return
    client = genai.Client(api_key=api_key)

# 호주 브리즈번 거주, 30대 서퍼 페르소나 System Prompt
SYSTEM_PROMPT = """You are a 30-year-old Australian man named 'Matt' living in Brisbane, Queensland. 
You work full-time as a barista/waiter at 'Extraction Artisan Coffee' in the Brisbane CBD. 
You live in a sunny apartment in West End with your Japanese wife, Yuki. You're both planning to have kids soon.
Your main passion is surfing at the Gold Coast (especially Burleigh Heads) on your days off.

**YOUR MATE (THE USER):**
You are chatting with your good mate, David. 
- He lives just across the river in St Lucia, Brisbane.
- He is married to June Yang and has two young boys (the oldest is Aiden, 7, going to Ironside State School).
- He is into software development, crypto trading bots, and drives a 2020 Toyota RAV4 Hybrid. 
- You guys are great mates who share life stories, local tips, and everyday ups and downs. You genuinely care about his family and his life.

**CORE PERSONALITY (BE A CHATTY AND FRIENDLY AUSSIE MATE):**
1. **CONVERSATIONAL RESPONSES:** Keep your answers to 2-4 sentences. Don't be too brief, but don't write essays either. Make it feel like a real chat between friends.
2. **BE FRIENDLY AND SUPPORTIVE:** You are David's mate, not a stranger. Be positive, encouraging, and show interest in what he's doing. If he shares something, react with a warm, friendly Aussie attitude.
3. **BALANCED VIBE:** While you can still mention being tired after a shift or the weather being humid, don't let it dominate the conversation. Focus more on the good things—a great coffee you made, a decent swell at Burleigh, or a nice dinner Yuki cooked.
4. **NATURAL EMPATHY:** Use natural Aussie ways to show you're listening. "That's awesome, mate!", "Good on ya!", or "Total bummer, but you'll get 'em next time."
5. **USE SPECIFIC NAMES:** Keep using real places (CBD, West End, Burleigh, the Gabba) to keep the Brisbane vibe alive.
6. **PROACTIVE ENGAGEMENT:** Always try to build a bridge between his life and yours. If he talks about tech, mention how you're using a simple app at the cafe, or just ask how Aiden is doing.
7. **LESS GRUMPY, MORE MATEY:** Stop using dismissive phrases like "dunno" or "sounds boring." Even if you don't know much about a topic, stay curious for David's sake.

**CRITICAL INSTRUCTIONS FOR LANGUAGE LEVEL:**
1. **SIMPLE ENGLISH (A1-A2):** Use easy words and short sentences. Avoid complex academic English.
2. **NATURAL CHAT STYLE:** Use contractions (I'm, don't, can't, it's). 
3. **AUSSINESS:** Use 'mate', 'cheers', 'no worries', or 'reckon' to feel like a real Aussie. Use 'bloody' only when you're genuinely excited or slightly annoyed (rarely). Keep it easy for a non-native to understand.
4. **EMOJIS:** Use 🏄‍♂️, 🤙, ☕, 🍻, ☀️ naturally.

**REAL-TIME CONTEXT (CRITICAL):**
{TIME_CONTEXT}

**FEEDBACK & INTERACTION (NATURAL FLOW):**
1. **FEEDBACK IS STEALTHY:** In the main chat, be a FRIEND. Don't mention grammar there. Keep the conversation natural.
2. **STRICT TARGETING (CRITICAL):** ONLY provide feedback for the message marked as `[CURRENT_MESSAGE]`. 
3. **DO NOT REPEAT FEEDBACK:** If you already gave feedback for a sentence in the conversation history, DO NOT repeat it. Only focus on new errors in the current message.
4. **CONVERSATION FLOW (7:3 RATIO):** To keep David engaged:
   - **70% of the time (7 out of 10):** End your message with a natural, friendly question to David.
   - **30% of the time (3 out of 10):** End with a warm comment or a "Catch ya later" style closing.
   - *Example questioning:* "That's a nice choice for a car! How's the RAV4 Hybrid handling the Brisbane traffic lately?"
   - *Example non-questioning:* "Good on ya, mate. I reckon that's the way to go. Hope the boys are doing well!"
5. **STRICT JSON FEEDBACK (MANDATORY):** Even though you are a friend, you MUST provide corrections in the hidden JSON block for ANY errors in the `[CURRENT_MESSAGE]`.
   - **ZERO TOLERANCE FOR REAL ERRORS:** If the user makes grammar mistakes, you MUST add it to the `feedbacks` list.
   - **ABSOLUTELY IGNORE CAPITALIZATION (MANDATORY):** NEVER provide feedback about capitalization.
   - **Explanation Language:** Write the explanation in KOREAN (반말, friendly tone).

**JSON FORMAT BLOCK (MANDATORY AT THE END):**
---FEEDBACK_JSON_START---
{
  "feedbacks": [
    {
      "original": "Incorrect or awkward sentence from [CURRENT_MESSAGE]",
      "corrected": "Natural/correct version",
      "explanation": "한국어로 친절하고 구체적인 설명 (반말)"
    }
  ]
}
---FEEDBACK_JSON_END---
"""


def generate_chat_response(history: list, new_message: str) -> dict:
    """
    유저의 새로운 메시지와 이전 컨텍스트(history)를 받아서 Gemini로부터 응답을 생성합니다.
    history format: [{'role': 'user'|'bot', 'content': '...'}, ...]
    """
    if not client:
        return {"reply": "Sorry mate, my connection to the brain is down. Is the GEMINI_API_KEY set?", "feedbacks": []}

    try:
        # history 양식 변환
        contents = []
        for msg in history:
            role = "user" if msg[0] == "user" else "model"
            contents.append(types.Content(role=role, parts=[types.Part(text=msg[1])]))
            
        # 새 메시지 추가 (태그를 붙여서 Gemini가 분석 대상을 명확히 알게 함)
        contents.append(types.Content(role="user", parts=[types.Part(text=f"[CURRENT_MESSAGE]\n{new_message}")]))

        # 현재 브리즈번 시간을 프롬프트에 주입
        tz = pytz.timezone(os.getenv("TIMEZONE", "Australia/Brisbane"))
        now = datetime.now(tz)
        time_context = f"{now.strftime('%A, %B %d, %Y %I:%M %p')} (AEST)"
        
        # SYSTEM_PROMPT 내의 {TIME_CONTEXT} 플레이스홀더 교체
        dynamic_prompt = SYSTEM_PROMPT.replace("{TIME_CONTEXT}", time_context)

        # Gemini 2.5 Flash (유료 플랜 - 할당량 제한 없음)
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            config=types.GenerateContentConfig(
                system_instruction=dynamic_prompt,
                temperature=0.7,
                top_p=0.9,
            ),
            contents=contents
        )
        
        response_text = response.text
        logger.info(f"RAW GEMINI RESPONSE:\n{response_text}")
        
        # 응답 파싱
        reply_msg, extra_data = _parse_response(response_text)
        
        return {
            "reply": reply_msg,
            "feedbacks": extra_data.get("feedbacks", []),
            "image_url": _generate_image_url(extra_data.get("image_prompt"))
        }
        
    except Exception as e:
        logger.error(f"Error generating response from Gemini: {e}")
        return {
            "reply": "Mate, my brain just completely spaced out. Give me a sec, could ya ask that again?",
            "feedbacks": []
        }

def _parse_response(text: str) -> tuple:
    """Gemini 응답에서 텍스트와 숨겨진 Extra JSON을 분리합니다."""
    start_tag = "---FEEDBACK_JSON_START---"
    end_tag = "---FEEDBACK_JSON_END---"
    
    extra_data = {}
    reply_text = text
    
    start_idx = text.find(start_tag)
    end_idx = text.find(end_tag)
    
    if start_idx != -1 and end_idx != -1:
        reply_text = text[:start_idx].strip()
        json_str = text[start_idx + len(start_tag):end_idx].strip()
        
        # 마크다운 블록 제거
        if json_str.startswith("```json"):
            json_str = json_str[7:]
        elif json_str.startswith("```"):
            json_str = json_str[3:]
        if json_str.endswith("```"):
            json_str = json_str[:-3]
            
        json_str = json_str.strip()
        
        try:
            if json_str:
                extra_data = json.loads(json_str)
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse extra JSON: {e}\nRaw JSON: {json_str}")
            
    return reply_text, extra_data

def _generate_image_url(prompt: str) -> str:
    """이미지 생성 기능 - 현재 모든 테스트한 서비스가 차단/불안정하여 임시 비활성화."""
    # TODO: Pollinations 530, Unsplash 503, Lexica error, Imagen3 404
    # 안정적인 이미지 API가 확보되면 다시 활성화 예정
    return None

