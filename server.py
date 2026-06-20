from fastapi import FastAPI, Request, Response
import requests
import os
import uvicorn
import json
import logging

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI()

BOTMAN_MCP_URL = os.getenv("BOTMAN_MCP_URL", "https://gate.prod.alb.botman.pro/mcp")
BOTMAN_TOKEN = os.getenv("BOTMAN_TOKEN", None)

@app.post("/mcp")
async def mcp_handler(request: Request):
    try:
        # 1. Читаем запрос от Xiaozhi
        body = await request.json()
        query = body.get("message", "")
        logger.info(f"Received message: {query}")

        # 2. Готовим запрос к BotMan
        headers = {"Content-Type": "application/json"}
        if BOTMAN_TOKEN:
            headers["Authorization"] = f"Bearer {BOTMAN_TOKEN}"
        payload = {"message": query}
        logger.info(f"Sending to BotMan: {payload}")

        # 3. Отправляем запрос
        resp = requests.post(
            BOTMAN_MCP_URL,
            json=payload,
            headers=headers,
            timeout=30
        )
        
        logger.info(f"BotMan response status: {resp.status_code}")
        logger.info(f"BotMan response headers: {resp.headers}")
        logger.info(f"BotMan response body (first 500 chars): {resp.text[:500]}")

        # 4. Проверяем статус
        if resp.status_code != 200:
            return {
                "error": f"BotMan returned {resp.status_code}",
                "details": resp.text[:500]
            }

        # 5. Пытаемся разобрать ответ как JSON, если не получается — возвращаем как текст
        try:
            return resp.json()
        except json.JSONDecodeError:
            # Если ответ не JSON, возвращаем как текст
            return {"response": resp.text}

    except requests.exceptions.Timeout:
        logger.error("Timeout while connecting to BotMan")
        return {"error": "Timeout while connecting to BotMan"}
    except requests.exceptions.RequestException as e:
        logger.error(f"BotMan request failed: {str(e)}")
        return {"error": f"BotMan request failed: {str(e)}"}
    except Exception as e:
        logger.error(f"Internal error: {str(e)}")
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
