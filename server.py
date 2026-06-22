@app.post("/mcp")
async def mcp_handler(request: Request):
    try:
        body = await request.json()
        query = body.get("message", "")

        headers = {"Content-Type": "application/json"}
        if BOTMAN_TOKEN:
            headers["Authorization"] = f"Bearer {BOTMAN_TOKEN}"
        payload = {"message": query}

        resp = requests.post(
            BOTMAN_MCP_URL,
            json=payload,
            headers=headers,
            timeout=30
        )

        # Главное изменение: читаем тело ответа всегда, даже при 202
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

    except Exception as e:
        return {"error": str(e)}
