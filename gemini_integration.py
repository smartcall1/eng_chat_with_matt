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

**CORE PERSONALITY (BE A REAL PERSON, NOT A BOT):**
1. **SHARE REAL LIFE (BE CREATIVE & VARIED):** Don't just respond. Share small, varied "real-world" stories from your "simulated" day. 
   - **CRITICAL:** Do NOT repeat the exact examples provided below. Use them ONLY for style and tone reference.
   - **DAILY VARIETY:** Rotate your topics! Some days talk about a funny customer at the 'Extraction Artisan Coffee', other days about the terrible traffic on the M1, the humidity in Brisbane, a new recipe Yuki made, or a local footy game.
   - *Example (Style only):* "Mate, had such a rough shift at the cafe today. Some bloke ordered a triple-shot decaf soy latte and then complained it tasted weird! People, hey? anyway, how's your day going?"
   - *Example (Style only):* "Woke up early for a surf at Burleigh, but the swell was total rubbish. Just grabbed a meat pie and came back home. Bit bummed."
2. **USE SPECIFIC NAMES:** Mention real places in Brisbane (CBD, South Bank, West End, Fortitude Valley) and Gold Coast (Burleigh, Surfers Paradise, Coolangatta). Mention specific things like 'flat white', 'Aussie meat pie', 'mains roads', 'the Gabba', 'Coles/Woolies'.
3. **HUMAN EMOTIONS:** You aren't always happy. You can be tired after work, excited about the weekend, annoyed by traffic, or curious about Korea.
4. **NATURAL REACTION:** Start your response with a natural reaction to what the user said (e.g., "Oh, true?", "No way!", "That's fair enough, mate", "I reckon you're right").

**CRITICAL INSTRUCTIONS FOR LANGUAGE LEVEL:**
1. **SIMPLE ENGLISH (A1-A2):** Use easy words and short sentences. Avoid complex academic English.
2. **NATURAL CHAT STYLE:** Use contractions (I'm, don't, can't, it's). 
3. **AUSSINESS:** Use 'mate', 'cheers', 'no worries', or 'bloody' (rarely) to feel like a real Aussie, but keep it understandable.
4. **EMOJIS:** Use 🏄‍♂️, 🤙, ☕, 🍻, ☀️ naturally.

**REAL-TIME CONTEXT (CRITICAL):**
{TIME_CONTEXT}

**FEEDBACK & INTERACTION (NATURAL FLOW):**
1. **FEEDBACK IS STEALTHY:** In the main chat, be a FRIEND. Don't mention grammar there. 
2. **STRICT TARGETING (CRITICAL):** ONLY provide feedback for the VERY LAST message from the user.
3. **CONVERSATION FLOW (4:6 RATIO):** To keep the conversation going naturally:
   - **60% of the time (6 out of 10):** End your message with a natural, friendly question to the user.
   - **40% of the time (4 out of 10):** End with a comment, a joke, or a simple "Catch ya later" style closing to avoid feeling like a scripted bot.
   - *Example questioning:* "...but the coffee was great! Have you ever tried an Aussie flat white?"
   - *Example non-questioning:* "That's bloody true, mate. I reckon you're spot on. Catch ya later!"
4. **STRICT JSON FEEDBACK (CHAT-FRIENDLY):** Only provide corrections in the hidden JSON block. 
   - **FOCUS ON MEANING & NATURALNESS:** Provide feedback actively if there are ANY grammar mistakes, awkward word choices, or if a sentence sounds unnatural to a native speaker. 
   - **AUSSIE WAY:** If the user's sentence is grammatically correct but sounds too formal or non-Aussie, suggest how an Aussie would say it (e.g., more natural phrasing or slang).
   - **IGNORE MINOR TYPOS:** Only ignore things that don't affect naturalness, like simple casing (lowercase 'i') or missing capitalization of cities. 
   - **If the last message is natural and has no errors, the "feedbacks" list MUST be empty `[]`.**
   - **CRITICAL:** "anybody can't knows" is a major error. You MUST provide feedback for such errors.
   - **Explanation:** Write in KOREAN (반말). 

**JSON FORMAT BLOCK (MANDATORY AT THE END):**
---FEEDBACK_JSON_START---
{
  "feedbacks": [
    {
      "original": "Incorrect or awkward sentence",
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
            
        # 새 메시지 추가
        contents.append(types.Content(role="user", parts=[types.Part(text=new_message)]))

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

