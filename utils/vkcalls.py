import re
import httpx
from fastapi import HTTPException

# Регулярное выражение для извлечения хэша из ссылки
VK_CALL_REGEX = r"(?:vk\.com/call/join/|join/)([a-zA-Z0-9_\-]+)"

async def get_vk_turn_credentials(call_url: str) -> dict:
    """
    Извлекает хэш звонка и запрашивает параметры TURN у VK API.
    """
    match = re.search(VK_CALL_REGEX, call_url)
    if not match:
        raise HTTPException(status_code=400, detail="Неверный формат ссылки VK Call")
    
    call_hash = match.group(1)
    
    # URL для получения метаданных звонка (аналогично Go-версии)
    # Примечание: VK может требовать User-Agent или базовый токен/cookie, 
    # если звонок приватный, но публичные хэши доступны напрямую.
    api_url = f"https://vk.com"
    params = {
        "join_hash": call_hash,
        "v": "5.131",
        # Если потребуется авторизация приложения:
        # "access_token": "YOUR_ANONYMOUS_OR_APP_TOKEN" 
    }
    
    headers = {
        "User-Agent": "VKAndroidApp/7.0-10000 (Android 11; SDK 30; arm64-v8a; Google Pixel; ru)"
    }

    async with httpx.AsyncClient() as client:
        response = await client.get(api_url, params=params, headers=headers)
        if response.status_code != 200:
            raise HTTPException(status_code=500, detail="Ошибка сети при обращении к VK API")
            
        data = response.json()
        if "error" in data:
            raise HTTPException(
                status_code=400, 
                detail=f"Ошибка VK API: {data['error'].get('error_msg', 'Неизвестная ошибка')}"
            )
            
        # Извлекаем ice_servers (TURN/STUN) из ответа VK
        ice_servers = data.get("response", {}).get("ice_servers", [])
        turn_servers = [server for server in ice_servers if server.get("urls", "").startswith("turn:")]
        
        if not turn_servers:
            raise HTTPException(status_code=404, detail="TURN серверы не найдены в данном звонке")
            
        # Берем первый доступный TURN-сервер
        server = turn_servers[0]
        
        # Форматируем ответ под нужды PWDTT
        return {
            "endpoint": server.get("urls").replace("turn:", ""), # Удаляем префикс turn:
            "username": server.get("username"),
            "password": server.get("credential"),
            "hash": call_hash
        }
      
