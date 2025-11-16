from __future__ import annotations

from fastapi import FastAPI
from pydantic import BaseModel

app = FastAPI()


class EchoRequest(BaseModel):
    message: str


@app.get("/health")
def health() -> dict[str, str]:
    """Simple healthcheck endpoint."""
    return {"status": "ok"}


@app.post("/echo")
def echo(payload: EchoRequest) -> dict[str, str]:
    """Echo the message back to the caller."""
    return {"message": payload.message}
