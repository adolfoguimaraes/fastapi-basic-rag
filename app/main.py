"""
Entrypoint da aplicação FastAPI.

- Carrega variáveis de ambiente via .env.
- Cria a aplicação e registra os routers de usuários e RAG sob o prefixo /api/v1.
"""

from fastapi import FastAPI
from app.api.v1.users import router as users_router
from app.api.v1.rag import router as rag_router


from dotenv import load_dotenv

load_dotenv()

app = FastAPI(title="Users API", version="1.0.0")

app.include_router(users_router, prefix="/api/v1")
app.include_router(rag_router, prefix="/api/v1")
