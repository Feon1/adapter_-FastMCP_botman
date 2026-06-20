from fastapi import FastAPI, Request, Response
import requests
import os
import uvicorn
import json

print("SERVER STARTED: app is loading")

app = FastAPI()

# URL коннектора BotMan (скопируйте из настроек интеграции)
BOTMAN_MCP_URL = os.getenv("BOTMAN_MCP_URL", "https://gate.prod.alb.botman.pro/mcp")
# Токен авторизации (если требуется)
BOTMAN_TOKEN = os.getenv("BOTMAN_TOKEN", None)

@app.post("/mcp")
async def mcp_handler(request: Request):
    
    print("POST /mcp received")
    ...
    """
    Принимает POST-запросы от Xiaozhi, извлекает сообщение,
    отправляет его в BotMan через MCP-коннектор и возвращает ответ.
    """
    try:
        # Читаем тело запроса
        body = await request.json()
        query = body.get("message", "")
        if not query:
            return {"error": "Missing 'message' field"}

        # Готовим заголовки для BotMan
        headers = {"Content-Type": "application/json"}
        if BOTMAN_TOKEN:
            headers["Authorization"] = f"Bearer {BOTMAN_TOKEN}"

        # Отправляем запрос в BotMan
        payload = {"message": query}
        resp = requests.post(
            BOTMAN_MCP_URL,
            json=payload,
            headers=headers,
            timeout=30
        )
        resp.raise_for_status()

        # Возвращаем ответ от BotMan
        return resp.json()

    except requests.exceptions.Timeout:
        return {"error": "Timeout while connecting to BotMan"}
    except requests.exceptions.RequestException as e:
        return {"error": f"BotMan request failed: {str(e)}"}
    except Exception as e:
        return {"error": f"Internal error: {str(e)}"}

@app.get("/")
async def root():
    return {"status": "ok", "service": "Xiaozhi-BotMan adapter"}

@app.get("/health")
async def health():
    return {"status": "alive"}

if __name__ == "__main__":
    port = int(os.getenv("PORT", 10000))
    uvicorn.run(app, host="0.0.0.0", port=port)
