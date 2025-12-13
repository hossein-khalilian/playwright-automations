import logging
import sys

from app.routes.auth_api import router as auth_router
from app.routes.notebooklm_api import router as notebooklm_router
from fastapi import APIRouter, FastAPI
from fastapi.middleware.cors import CORSMiddleware

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout),
    ],
    force=True,  # Override any existing logging configuration
)

logger = logging.getLogger(__name__)

api_router = APIRouter()
api_router.include_router(auth_router)
api_router.include_router(notebooklm_router)


app = FastAPI(
    title="Playwright Automations API",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3003", "*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router)


@app.get("/health")
async def health_check() -> dict:
    return {"status": "ok"}
