import os
import json
import logging
from dotenv import load_dotenv
import gemini_integration

# 로깅 설정
logging.basicConfig(level=logging.INFO)

def test_feedback():
    load_dotenv()
    gemini_integration.init_gemini()
    
    # 텍스트 케이스 1: 명확한 오류
    print("\n--- Testing Case 1: 'anybody can't knows' ---")
    history = [("user", "hi"), ("model", "G'day mate!")]
    result = gemini_integration.generate_chat_response(history, "anybody can't knows")
    print(f"Reply: {result['reply']}")
    print(f"Feedbacks: {json.dumps(result['feedbacks'], indent=2, ensure_ascii=False)}")
    
    # 테스트 케이스 2: 유저가 실제 질문한 문장
    print("\n--- Testing Case 2: 'bodyboard is ok for grown up peoples?' ---")
    result = gemini_integration.generate_chat_response(history, "bodyboard is ok for grown up peoples? or bodyboard only used for kids?")
    print(f"Reply: {result['reply']}")
    print(f"Feedbacks: {json.dumps(result['feedbacks'], indent=2, ensure_ascii=False)}")

if __name__ == "__main__":
    test_feedback()
