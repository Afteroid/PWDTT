from fastapi import APIRouter, Depends
from pydantic import BaseModel
from utils.vkcalls import get_vk_turn_credentials

router = APIRouter(prefix="/tunnel", tags=["Tunnel"])

class VKCallRequest(BaseModel):
    url: str

@router.post("/generate-by-vk")
async def generate_config_by_vk(payload: VKCallRequest):
    # 1. Получаем данные TURN от ВКонтакте
    vk_data = await get_vk_turn_credentials(payload.url)
    
    # 2. Здесь генерируем шаблон конфигурации WireGuard/WDTT 
    # Используем vk_data['endpoint'], vk_data['username'], vk_data['password']
    # вместо стандартных полей Amnezia / обычного WireGuard.
    
    config = {
        "status": "success",
        "turn_server": vk_data["endpoint"],
        "turn_username": vk_data["username"],
        "turn_password": vk_data["password"],
        # Пример вывода для клиента PWDTT:
        "wg_config_template": f"[Interface]\nPrivateKey = ...\n\n[Peer]\nPublicKey = ...\nEndpoint = {vk_data['endpoint']}"
    }
    
    return config
  
