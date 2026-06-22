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

# URL для чата с конкретным агентом
BOTMAN_CHAT_URL = os.getenv(
    "BOTMAN_CHAT_URL",
    "https://gate.prod.alb.botman.pro/api/v1/ai-agents/6a1fdbb2529bc3da7be9bbd3/chat/test"
)
BOTMAN_TOKEN = os.getenv("BOTMAN_TOKEN", None)

# Хранилище conversationId (можно сохранять на диск или в Redis, но для простоты пока в памяти)
conversation_store = {}

def get_conversation_id(user_id: str) -> str:
    """Возвращает conversationId для пользователя (создаёт новый, если нет)."""
    if user_id not in conversation_store:
        # Генерируем новый ID (можно также получить из первого ответа BotMan)
        conversation_store[user_id] = str(uuid.uuid4())
    return conversation_store[user_id]

@app.post("/mcp")
async def mcp_handler(request: Request):
    try:
        body = await request.json()
        query = body.get("message", "")
        if not query:
            return {"error": "Missing 'message' field"}

        # Определяем user_id (можно передавать в запросе или использовать фиксированный)
        user_id = body.get("user_id", "default_user")
        conversation_id = get_conversation_id(user_id)

        logger.info(f"Received message: {query} for user {user_id}")

        headers = {"Content-Type": "application/json"}
        if BOTMAN_TOKEN:
            headers["Authorization"] = f"Bearer {BOTMAN_TOKEN}"
            logger.info(f"Using token: {BOTMAN_TOKEN[:10]}...")
        else:
            logger.warning("BOTMAN_TOKEN is not set!")

        # Формируем тело запроса в точном формате BotMan
        payload = {
            "message": query,
            "conversationId": conversation_id
        }

        # Отправляем запрос
        resp = requests.post(
            BOTMAN_CHAT_URL,
            json=payload,
            headers=headers,
            timeout=30
        )

        logger.info(f"BotMan status: {resp.status_code}")
        logger.info(f"BotMan body (full): {resp.text}")

        # Пытаемся прочитать ответ
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
