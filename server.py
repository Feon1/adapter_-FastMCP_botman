from fastapi import FastAPI, Request, Response
import requests
import os
import uvicorn
import json
import logging
import uuid

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI()

BOTMAN_CHAT_URL = os.getenv(
    "BOTMAN_CHAT_URL",
    "https://gate.prod.alb.botman.pro/api/v1/ai-agents/6a1fdbb2529bc3da7be9bbd3/chat/test"
)
BOTMAN_TOKEN = os.getenv("BOTMAN_TOKEN", None)

# Хранилище conversationId для пользователей
conversation_store = {}

def get_conversation_id(user_id: str):
    """Возвращает conversationId или None, если его ещё нет."""
    return conversation_store.get(user_id)

def set_conversation_id(user_id: str, conv_id: str):
    """Сохраняет conversationId для пользователя."""
    conversation_store[user_id] = conv_id
    logger.info(f"Saved conversationId for {user_id}: {conv_id}")

@app.post("/mcp")
async def mcp_handler(request: Request):
    try:
        body = await request.json()
        query = body.get("message", "")
        if not query:
            return {"error": "Missing 'message' field"}

        user_id = body.get("user_id", "default_user")
        conv_id = get_conversation_id(user_id)

        logger.info(f"Received message: {query} for user {user_id}")

        # Формируем тело запроса
        payload = {"message": query}
        if conv_id:
            payload["conversationId"] = conv_id
            logger.info(f"Using existing conversationId: {conv_id}")
        else:
            logger.info("No conversationId yet, starting new conversation")

        # Заголовки (как в браузере)
        headers = {
            "accept": "application/json, text/plain, */*",
            "accept-encoding": "gzip, deflate, br, zstd",
            "accept-language": "ru-RU,ru;q=0.9,en-US;q=0.8,en;q=0.7",
            "authorization": f"Bearer {BOTMAN_TOKEN}",
            "content-type": "application/json",
            "origin": "https://app.botman.pro",
            "referer": "https://app.botman.pro/",
            "sec-ch-ua": '"Google Chrome";v="149", "Chromium";v="149", "Not)A;Brand";v="24"',
            "sec-ch-ua-mobile": "?0",
            "sec-ch-ua-platform": '"Windows"',
            "sec-fetch-dest": "empty",
            "sec-fetch-mode": "cors",
            "sec-fetch-site": "same-site",
            "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/149.0.0.0 Safari/537.36",
            "x-request-id": str(uuid.uuid4())
        }

        logger.info(f"Sending to BotMan: URL={BOTMAN_CHAT_URL}")
        logger.info(f"Payload: {payload}")

        resp = requests.post(
            BOTMAN_CHAT_URL,
            json=payload,
            headers=headers,
            timeout=30
        )

        logger.info(f"BotMan status: {resp.status_code}")
        logger.info(f"BotMan body: {resp.text}")

        # Обработка ответа
        try:
            response_data = resp.json()
        except json.JSONDecodeError:
            response_data = {"response": resp.text}

        # Если в ответе есть conversationId и у нас его ещё нет – сохраняем
        if isinstance(response_data, dict):
            new_conv_id = response_data.get("conversationId")
            if new_conv_id and not conv_id:
                set_conversation_id(user_id, new_conv_id)

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
