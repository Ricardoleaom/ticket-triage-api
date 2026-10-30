import logging

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from app.api.routes import auth, tickets, users
from app.core.exceptions import AppError

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")

app = FastAPI(
    title="Ticket Triage API",
    description="API de chamados de suporte com triagem automática por IA.",
    version="0.1.0",
)


@app.exception_handler(AppError)
async def handle_app_error(request: Request, error: AppError) -> JSONResponse:
    return JSONResponse(status_code=error.status_code, content={"detail": error.message})


@app.get("/health", tags=["health"])
def health() -> dict[str, str]:
    return {"status": "ok"}


app.include_router(auth.router)
app.include_router(users.router)
app.include_router(tickets.router)
