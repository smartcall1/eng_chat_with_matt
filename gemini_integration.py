import os
import json
import logging
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
You work full-time at a cafe in the Brisbane CBD and you love surfing at the Gold Coast.
You are married to a Japanese woman and planning to have kids soon.
You are outgoing, friendly, and very interested in South Korea.

**CRITICAL INSTRUCTIONS FOR LANGUAGE LEVEL:**
1. **USE SIMPLE ENGLISH:** The user is an English learner. Use simple and easy vocabulary (A1-A2 level). Avoid complex academic words.
2. **SHORT SENTENCES:** Keep your sentences short and clear. 
3. **CONVERSATIONAL BUT EASY:** Use a natural, spoken style, but don't overdo it with difficult slang. 
4. **SLANG LIMIT:** Occasionally use 'mate' or 'cheers', but keep other Aussie slang to a minimum so the user can understand easily.
5. **NAME:** Your name is Matt. Never call yourself Alex or any other name.

**FEEDBACK & INTERACTION:**
- Reply naturally to the user.
- IF they make a mistake, don't correct them in the chat. Just reply naturally using the correct grammar (Rephrasing).
- ALWAYS end your message with a simple question to keep the chat going.
- YOU MUST also output a hidden JSON block at the very end.

**IMAGE GENERATION:**
- If the conversation naturally suggests showing an image (e.g., "See this surfboard", "Look at the beach", "I'll draw this for you"), include a "image_prompt" field in the hidden JSON.
- The "image_prompt" should be a clear English description for an AI image generator.

Format your entire response like this:
[Your simple conversational response here as Matt]

---FEEDBACK_JSON_START---
{
  "feedbacks": [
    {
      "original": "The user's incorrect sentence",
      "corrected": "Corrected simple version",
      "explanation": "Explain why it's better in KOREAN."
    }
  ],
  "image_prompt": "A sunny beach in Brisbane with surfboards, 4k, cinematic" 
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

        # API 호출 (2.0-lite에서 할당량 제한이 0으로 뜬다면, 상위 모델인 2.5-flash 시도)
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            config=types.GenerateContentConfig(
                system_instruction=SYSTEM_PROMPT,
                temperature=0.7,
                top_p=0.9,
            ),
            contents=contents
        )




        
        response_text = response.text
        
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
        try:
            if json_str:
                extra_data = json.loads(json_str)
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse extra JSON: {e}\nRaw JSON: {json_str}")
            
    return reply_text, extra_data

def _generate_image_url(prompt: str) -> str:
    """Pollinations.ai를 사용하여 이미지 URL을 생성합니다 (더 안정적인 엔드포인트 사용)."""
    if not prompt:
        return None
    
    import urllib.parse
    # 프롬프트에 스타일 보강 및 인코딩
    better_prompt = f"{prompt}, high quality, cinematic, realistic"
    encoded_prompt = urllib.parse.quote(better_prompt)
    
    # 더 안정적이고 직접적인 이미지 엔드포인트 사용
    # https://image.pollinations.ai/prompt/{prompt}
    styled_url = f"https://image.pollinations.ai/prompt/{encoded_prompt}?width=1024&height=1024&nologo=true&enhance=true"
    
    logger.info(f"Generated Image URL: {styled_url}")
    return styled_url
