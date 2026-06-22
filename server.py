from fastapi import FastAPI, Request, Response
import requests
import os
import uvicorn
import json
import logging

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
        if not query:
            return {"error": "Missing 'message' field"}

        logger.info(f"Received message: {query}")

        headers = {"Content-Type": "application/json"}
        if BOTMAN_TOKEN:
            headers["Authorization"] = f"Bearer {BOTMAN_TOKEN}"
            logger.info(f"Using token: {BOTMAN_TOKEN[:10]}...")
        else:
            logger.warning("BOTMAN_TOKEN is not set!")

        payload = {"message": query}

        # Отправляем запрос с таймаутом
        resp = requests.post(
            BOTMAN_MCP_URL,
            json=payload,
            headers=headers,
            timeout=30
        )

        # Логируем ВСЁ
        logger.info(f"BotMan status: {resp.status_code}")
        logger.info(f"BotMan headers: {dict(resp.headers)}")
        logger.info(f"BotMan body (full): {resp.text}")

        # Пытаемся прочитать тело
        try:
            response_data = resp.json()
        except json.JSONDecodeError:
            response_data = {"response": resp.text}

        if 200 <= resp.status_code < 300:
            return response_data
        else:
            return {
                "error": f"BotMan returned {resp.status_code}",
                "details": response_data
            }

    except Exception as e:
        logger.error(f"Exception: {str(e)}", exc_info=True)
        return {"error": str(e)}

@app.api_route("/", methods=["GET", "HEAD"])
async def root():
    return {"status": "ok", "service": "Xiaozhi-BotMan adapter"}

@app.get("/health")
async def health():
    return {"status": "alive"}

if __name__ == "__main__":
    port = int(os.getenv("PORT", 10000))
    uvicorn.run(app, host="0.0.0.0", port=port)
