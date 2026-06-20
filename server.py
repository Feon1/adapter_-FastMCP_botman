from fastapi import FastAPI, Request
import requests
import uvicorn
import os

app = FastAPI()

BOTMAN_MCP_URL = os.getenv("BOTMAN_MCP_URL", "https://gate.prod.alb.botman.pro/mcp")
BOTMAN_TOKEN = os.getenv("BOTMAN_TOKEN", None)

@app.post("/mcp")
async def mcp_handler(request: Request):
    """Принимает запросы от Xiaozhi и перенаправляет в BotMan"""
    try:
        data = await request.json()
        query = data.get("message", "")
        
        headers = {"Content-Type": "application/json"}
        if BOTMAN_TOKEN:
            headers["Authorization"] = f"Bearer {BOTMAN_TOKEN}"
        
        # Отправляем запрос в BotMan
        response = requests.post(
            BOTMAN_MCP_URL,
            json={"message": query},
            headers=headers,
            timeout=30
        )
        response.raise_for_status()
        return response.json()
    
    except Exception as e:
        return {"error": str(e)}

@app.get("/")
async def root():
    return {"status": "ok", "service": "Xiaozhi-BotMan adapter"}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
