from fastapi import FastAPI, Request, Response
import requests
import os
import uvicorn
import json

app = FastAPI()

# ... ваш код с BOTMAN_MCP_URL и BOTMAN_TOKEN ...

@app.post("/mcp")
async def mcp_handler(request: Request):
    # ... обработка POST ...

@app.get("/")
async def root():
    return {"status": "ok", "service": "Xiaozhi-BotMan adapter"}

@app.head("/")
async def head_root():
    return Response(status_code=200, headers={"Content-Type": "application/json"})

@app.get("/health")
async def health():
    return {"status": "alive"}

if __name__ == "__main__":
    port = int(os.getenv("PORT", 10000))
    uvicorn.run(app, host="0.0.0.0", port=port)
