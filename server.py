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

# URL для чата с конкретным агентом (из браузера)
BOTMAN_CHAT_URL = os.getenv(
    "BOTMAN_CHAT_URL",
    "https://gate.prod.alb.botman.pro/api/v1/ai-agents/6a1fdbb2529bc3da7be9bbd3/chat/test"
)
BOTMAN_TOKEN = os.getenv("BOTMAN_TOKEN", None)

# Хранилище conversationId (можно сохранять на диск или в Redis, но для простоты пока в памяти)
conversation_store = {}

def get_conversation_id(user_id: str) -> str:
    """Возвращает conversationId для пользователя (создаёт новый UUID, если нет)."""
    if user_id not in conversation_store:
        # Генерируем новый ID в формате 24-символьного hex (как ObjectId)
        conversation_store[user_id] = uuid.uuid4().hex[:24]
    return conversation_store[user_id]

@app.post("/mcp")
async def mcp_handler(request: Request):
    try:
        # 1. Читаем запрос от клиента
        body = await request.json()
        query = body.get("message", "")
        if not query:
            return {"error": "Missing 'message' field"}

        user_id = body.get("user_id", "default_user")
        conversation_id = get_conversation_id(user_id)

        logger.info(f"Received message: {query} for user {user_id}")
        logger.info(f"Using conversationId: {conversation_id}")

        # 2. Формируем тело запроса (как в браузере)
        payload = {
            "message": query,
            "conversationId": conversation_id
        }

        # 3. Формируем заголовки (копируем из работающего запроса PowerShell)
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
        logger.info(f"Headers: {headers}")

        # 4. Отправляем запрос
        resp = requests.post(
            BOTMAN_CHAT_URL,
            json=payload,
            headers=headers,
            timeout=30
        )

        logger.info(f"BotMan status: {resp.status_code}")
        logger.info(f"BotMan body (full): {resp.text}")

        # 5. Пытаемся прочитать ответ
        try:
            response_data = resp.json()
        except json.JSONDecodeError:
            response_data = {"response": resp.text}

        # Если в ответе есть новый conversationId, обновляем его
        if isinstance(response_data, dict):
            new_conversation_id = response_data.get("conversationId")
            if new_conversation_id:
                conversation_store[user_id] = new_conversation_id
                logger.info(f"Updated conversationId for {user_id}: {new_conversation_id}")

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
