from fastapi import FastAPI
from app.api.v1.users import router as users_router

from dotenv import load_dotenv

load_dotenv()

app = FastAPI(title="Users API", version="1.0.0")

app.include_router(users_router, prefix="/api/v1")