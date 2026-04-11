import logging

import uvicorn
from fastapi import FastAPI, Request

from api.routes.subscription import subscription_handler
from api.routes.webhook import webhook_handler

logging.basicConfig(level=logging.INFO, format="%(asctime)s | %(levelname)s | %(message)s")

app = FastAPI(docs_url=None, redoc_url=None)


@app.post("/webhook/payment")
async def payment_webhook(request: Request):
    return await webhook_handler(request)


@app.get("/{key}")
async def subscription_endpoint(key: str, request: Request):
    return await subscription_handler(key, request)


if __name__ == "__main__":
    uvicorn.run("api.__main__:app", host="127.0.0.1", port=8080, log_level="info")
