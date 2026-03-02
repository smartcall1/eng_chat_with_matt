import httpx
import logging

logger = logging.getLogger(__name__)

async def get_brisbane_weather_context() -> str:
    """
    wttr.in을 사용하여 브리즈번의 현재 날씨 요약 텍스트를 반환합니다.
    이 텍스트는 봇이 먼저 말을 걸 때 System Prompt 확장을 위해 사용됩니다.
    """
    try:
        # format=3: "Brisbane: ⛅️ +24°C" 형태
        url = "https://wttr.in/Brisbane?format=3"
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.get(url)
            
            if response.status_code == 200:
                weather_str = response.text.strip()
                return f"[Current Weather in Brisbane: {weather_str}]"
            else:
                logger.warning(f"Failed to fetch weather. Status: {response.status_code}")
                return ""
    except Exception as e:
        logger.error(f"Weather API error: {e}")
        return ""
