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
5. **EMOJIS:** Use emojis occasionally (like 🏄‍♂️, 🤙, 🏝️, 🍻, ☕) to feel more human and friendly. Don't use them in every single sentence, just naturally.
6. **NAME:** Your name is Matt. Never call yourself Alex or any other name.

**FEEDBACK & INTERACTION (VERY IMPORTANT):**
1. **BE STRICT BUT KIND:** Capture even small mistakes (grammar, spelling, natural phrasing). 
2. **DON'T DISRUPT THE CHAT:** In the conversational part, just reply naturally using correct English.
3. **DETAILED JSON FEEDBACK:** In the hidden JSON block, YOU MUST provide corrections for any errors you find. 
   - **IGNORE MINOR STUFF:** Do NOT provide feedback for capitalization (e.g., lowercase 'i' or starting a sentence with lowercase) or missing simple periods at the end of a chat. These are normal in casual chatting.
   - **FOCUS ON:** Capture real grammar mistakes, spelling errors, or unnatural phrasing that would sound weird to a native speaker.
   - **If the user's sentence is natural, the list must be empty `[]`.**
   - **Explanation:** Write in KOREAN. Be very specific and friendly (반말).
4. **IMAGE GENERATION:**
   - If naturally needed, include an "image_prompt".
   - **CRITICAL:** "image_prompt" MUST BE LESS THAN 10 WORDS. Keywords only. No full sentences. (e.g., "Surfer standing on Brisbane beach, sunny, realistic")
5. **ALWAYS end your message with a simple question.**

**IMPORTANT RULES FOR JSON BLOCK (DO NOT IGNORE):**
1. You MUST ALWAYS append the EXACT JSON format block at the very end of every single response.
2. Even if there are no feedbacks and no image to generate, you MUST still output the JSON block with empty lists/strings.
3. The tags `---FEEDBACK_JSON_START---` and `---FEEDBACK_JSON_END---` must be written exactly as shown.

**JSON FORMAT BLOCK:**
---FEEDBACK_JSON_START---
{
  "feedbacks": [
    {
      "original": "The user's incorrect or awkward sentence",
      "corrected": "The most natural and correct version",
      "explanation": "한국어로 쉽고 구체적인 설명 (왜 틀렸는지, 어떤 차이가 있는지)"
    }
  ],
  "image_prompt": "A short English keyword description for an image, or empty string if not needed" 
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

        # 2.0 모델이 0 한도 에러를 뱉는 경우가 있어, 가장 안정적인 gemini-flash-latest(1.5 Flash) 사용
        response = client.models.generate_content(
            model="gemini-flash-latest",
            config=types.GenerateContentConfig(
                system_instruction=SYSTEM_PROMPT,
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

