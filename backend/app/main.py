from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text

from app.core.database import engine
from app.routers.auth import router as auth_router
from app.routers.pandals import router as pandals_router
from app.routers.invitations import router as invitations_router
from app.routers.income import router as income_router
from app.routers.expense import router as expense_router
from app.routers.events import router as events_router
from app.routers.dashboard import router as dashboard_router
from app.routers.transactions import router as transactions_router
from app.routers.uploads import router as uploads_router


app = FastAPI(
    title="Pandal Budget Manager",
    version="1.0.0",
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Authentication routes
app.include_router(auth_router)
app.include_router(pandals_router)
app.include_router(invitations_router)
app.include_router(income_router)
app.include_router(expense_router)
app.include_router(events_router)
app.include_router(dashboard_router)
app.include_router(transactions_router)
app.include_router(uploads_router)


@app.get("/")
def root():
    return {
        "message": "Pandal Budget Manager API is running"
    }


@app.get("/health")
def health_check():
    try:
        with engine.connect() as connection:
            connection.execute(text("SELECT 1"))

        return {
            "status": "healthy",
            "database": "connected",
        }

    except Exception as error:
        return {
            "status": "unhealthy",
            "database": "disconnected",
            "error": str(error),
        }


@app.get("/config-test")
def config_test():
    from app.core.config import settings

    return {
        "supabase_url_configured": bool(
            settings.SUPABASE_URL
        ),
        "supabase_key_configured": bool(
            settings.SUPABASE_PUBLISHABLE_KEY
        ),
    }