from fastapi import FastAPI, Request, Response
import requests
import os
import uvicorn
import json
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI()

# Читаем переменные окружения
BOTMAN_MCP_URL = os.getenv("BOTMAN_MCP_URL", "https://gate.prod.alb.botman.pro/mcp")
BOTMAN_TOKEN = os.getenv("BOTMAN_TOKEN", None)

@app.post("/mcp")
async def mcp_handler(request: Request):
    try:
        body = await request.json()
        query = body.get("message", "")
        if not query:
            return {"error": "Missing 'message' field"}

        logger.info(f"Received message: {query}")

        # Готовим запрос к BotMan
        headers = {"Content-Type": "application/json"}
        # Если токен есть, передаём в заголовке
        if BOTMAN_TOKEN:
            headers["Authorization"] = f"Bearer {BOTMAN_TOKEN}"
            logger.info(f"Using token: {BOTMAN_TOKEN[:10]}...")
        else:
            logger.warning("BOTMAN_TOKEN is not set!")

        payload = {"message": query}

        # Отправляем запрос (с таймаутом)
        resp = requests.post(
            BOTMAN_MCP_URL,
            json=payload,
            headers=headers,
            timeout=30
        )

        # Логируем ответ
        logger.info(f"BotMan status: {resp.status_code}")
        logger.info(f"BotMan body: {resp.text[:500]}")

        # Пытаемся прочитать тело ответа
        try:
            response_data = resp.json()
        except json.JSONDecodeError:
            response_data = {"response": resp.text}

        # Если статус 2xx — возвращаем данные
        if 200 <= resp.status_code < 300:
            return response_data
        else:
            return {
                "error": f"BotMan returned {resp.status_code}",
                "details": response_data
            }

    except requests.exceptions.Timeout:
        logger.error("Timeout while connecting to BotMan")
        return {"error": "Timeout while connecting to BotMan"}
    except requests.exceptions.RequestException as e:
        logger.error(f"BotMan request failed: {str(e)}")
        return {"error": f"BotMan request failed: {str(e)}"}
    except Exception as e:
        logger.error(f"Internal error: {str(e)}")
        return {"error": f"Internal error: {str(e)}"}

@app.api_route("/", methods=["GET", "HEAD"])
async def root():
    return {"status": "ok", "service": "Xiaozhi-BotMan adapter"}

@app.get("/health")
async def health():
    return {"status": "alive"}

if __name__ == "__main__":
    port = int(os.getenv("PORT", 10000))
    uvicorn.run(app, host="0.0.0.0", port=port)
