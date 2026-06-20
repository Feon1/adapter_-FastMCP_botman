from fastmcp import FastMCP
import requests
import json

mcp = FastMCP("Xiaozhi-BotMan")

# URL вашего MCP-коннектора BotMan (полученный от поддержки)
BOTMAN_MCP_URL = "https://gate.prod.alb.botman.pro/mcp"

@mcp.tool()
def ask_botman(query: str) -> str:
    """Отправляет запрос в BotMan и возвращает ответ"""
    try:
        # Если требуется токен, добавьте его в заголовки
        headers = {
            "Content-Type": "application/json",
            # "Authorization": "Bearer ВАШ_ТОКЕН"  # если нужен
        }
        payload = {"message": query}
        response = requests.post(BOTMAN_MCP_URL, json=payload, headers=headers, timeout=30)
        response.raise_for_status()
        return response.text
    except Exception as e:
        return f"Ошибка при обращении к BotMan: {str(e)}"

if __name__ == "__main__":
    mcp.run(host="0.0.0.0", port=8000)
