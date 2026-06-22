import uuid  # если ещё не импортирован

# Внутри функции mcp_handler, после получения query:

# 1. Формируем тело запроса (как в браузере)
payload = {
    "message": query,
    "conversationId": conversation_id  # нужно получать или генерировать
}

# 2. Формируем заголовки (копируем из браузера)
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
    "x-request-id": str(uuid.uuid4())  # генерируем новый ID для каждого запроса
}

# 3. Отправляем запрос
resp = requests.post(
    BOTMAN_CHAT_URL,
    json=payload,
    headers=headers,
    timeout=30
)
