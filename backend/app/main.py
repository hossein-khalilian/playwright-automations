from fastapi import APIRouter, FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.routes.auth_api import router as auth_router

# from app.routes.google_api import router as google_router
from app.routes.notebooklm_api import router as notebooklm_router

api_router = APIRouter()
api_router.include_router(auth_router)
# api_router.include_router(google_router)
api_router.include_router(notebooklm_router)


app = FastAPI(
    title="Playwright Automations API",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router)


@app.get("/health")
async def health_check() -> dict:
    return {"status": "ok"}
