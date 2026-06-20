from fastapi import FastAPI, Request, Response
import requests
import os
import uvicorn
import json
import logging
import time

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI()

BOTMAN_MCP_URL = os.getenv("BOTMAN_MCP_URL", "https://gate.prod.alb.botman.pro/mcp")
BOTMAN_TOKEN = os.getenv("BOTMAN_TOKEN", None)

@app.post("/mcp")
async def mcp_handler(request: Request):
    try:
        body = await request.json()
        query = body.get("message", "")
        logger.info(f"Received message: {query}")

        headers = {"Content-Type": "application/json"}
        if BOTMAN_TOKEN:
            headers["Authorization"] = f"Bearer {BOTMAN_TOKEN}"
        payload = {"message": query}

        # 1. Отправляем запрос в BotMan
        resp = requests.post(
            BOTMAN_MCP_URL,
            json=payload,
            headers=headers,
            timeout=30
        )
        logger.info(f"BotMan response status: {resp.status_code}")

        # 2. Если 202 Accepted — ждём завершения
        if resp.status_code == 202:
            # Проверяем, есть ли заголовок Location с URL для опроса
            location_url = resp.headers.get("Location")
            if location_url:
                logger.info(f"Polling {location_url}")
                # Опрашиваем до получения результата (максимум 30 секунд)
                for _ in range(30):
                    time.sleep(1)
                    poll_resp = requests.get(
                        location_url,
                        headers=headers,
                        timeout=10
                    )
                    if poll_resp.status_code == 200:
                        try:
                            return poll_resp.json()
                        except json.JSONDecodeError:
                            return {"response": poll_resp.text}
                    elif poll_resp.status_code == 202:
                        continue  # ещё не готово
                    else:
                        return {
                            "error": f"Polling failed: {poll_resp.status_code}",
                            "details": poll_resp.text[:500]
                        }
                return {"error": "Timeout while waiting for BotMan response"}
            else:
                # Если Location нет, просто возвращаем статус
                return {"status": "accepted", "message": "Request accepted, but no polling URL provided"}

        # 3. Если ответ 200 — сразу возвращаем результат
        elif resp.status_code == 200:
            try:
                return resp.json()
            except json.JSONDecodeError:
                return {"response": resp.text}

        # 4. Любой другой статус — ошибка
        else:
            return {
                "error": f"BotMan returned {resp.status_code}",
                "details": resp.text[:500]
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

@app.get("/")
async def root():
    return {"status": "ok", "service": "Xiaozhi-BotMan adapter"}

@app.get("/health")
async def health():
    return {"status": "alive"}

if __name__ == "__main__":
    port = int(os.getenv("PORT", 10000))
    uvicorn.run(app, host="0.0.0.0", port=port)
