"""
Rotas de usuários (CRUD) da API.

- Depende de `get_db()` para acesso ao MongoDB (vide app/db/mongo.py).
- Usa bcrypt (via `app.core.security`) para hash de senha.
- Endpoints: listar, obter por id, criar, atualizar e excluir.

Variáveis de ambiente (indiretas):
- MONGODB_URI e MONGODB_DB, configuradas no módulo de banco.
"""

from fastapi import APIRouter, HTTPException, status, Depends
from typing import List, Optional
from bson import ObjectId
import bcrypt
from app.schemas.user import UserOut, UserCreate, UserUpdate
from app.db.mongo import get_db
from app.deps.auth import get_current_user_id

router = APIRouter(tags=["users"]) 


def _to_user_out(doc) -> UserOut:
    """Converte um documento do MongoDB para o schema de saída `UserOut`."""
    return UserOut(
        id=str(doc["_id"]),
        name=doc["name"],
        email=doc["email"],
        status=doc.get("status", "ativo"),
    )


def hash_password(plain_password: str) -> str:
    """Hash local de senha com bcrypt.
    """
    plain_bytes = plain_password.encode("utf-8")
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(plain_bytes, salt).decode("utf-8")


@router.get("/users", response_model=List[UserOut])
async def list_users_endpoint(
    status: Optional[str] = None, 
    db=Depends(get_db),
    create_user_id: str = Depends(get_current_user_id)
):
    """Lista usuários com filtro opcional por `status`. Retorna 200 com a coleção."""
    query = {"status": status} if status else {}
    cursor = db["users"].find(query)
    docs = [doc async for doc in cursor]
    return [_to_user_out(docs[i]) for i in range(len(docs))]


@router.get("/users/{user_id}", response_model=UserOut)
async def get_user_endpoint(
    user_id: str, 
    db=Depends(get_db),
    current_user_id: str = Depends(get_current_user_id),
):
    """Obtém um usuário por ID.

    Regras:
    - 400: ID inválido.
    - 404: usuário não encontrado.
    """
    try:
        oid = ObjectId(user_id)
    except Exception:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid user id")

    doc = await db["users"].find_one({"_id": oid})
    if not doc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    return _to_user_out(doc)


@router.post("/users", response_model=UserOut, status_code=status.HTTP_201_CREATED)
async def create_user_endpoint(
    data: UserCreate, 
    db=Depends(get_db),
    current_user_id: str = Depends(get_current_user_id),
    ):
    """Cria um usuário.

    Regras:
    - 409: e-mail já utilizado.
    - 400: falha ao gerar hash da senha.
    - 201: criado com sucesso.
    """
    # Verifica duplicidade de email
    if await db["users"].find_one({"email": data.email}):
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Email already in use")

    # Hash da senha com bcrypt (função local)
    try:
        password_hash = hash_password(data.password)
    except Exception as e:
        # Normalize hashing errors to a 400 so clients get actionable feedback
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to hash password: {str(e)}",
        )
    doc = {"name": data.name, "email": data.email, "status": data.status, "password_hash": password_hash}
    result = await db["users"].insert_one(doc)
    created = await db["users"].find_one({"_id": result.inserted_id})
    return _to_user_out(created)


@router.put("/users/{user_id}", response_model=UserOut)
async def update_user_endpoint(
    user_id: str, 
    data: UserUpdate, 
    db=Depends(get_db),
    current_user_id: str = Depends(get_current_user_id)
    ):
    """Atualiza campos parciais de um usuário.

    Regras:
    - Re-hash de senha quando `password` é fornecida.
    - 400: ID inválido ou falha ao gerar hash.
    - 404: usuário não encontrado.
    """
    try:
        oid = ObjectId(user_id)
    except Exception:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid user id")

    update_doc = {k: v for k, v in data.model_dump(exclude_unset=True).items() if k != "password"}
    if data.password:
        try:
            update_doc["password_hash"] = hash_password(data.password)
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Failed to hash password: {str(e)}",
            )

    res = await db["users"].update_one({"_id": oid}, {"$set": update_doc})
    if res.matched_count == 0:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    doc = await db["users"].find_one({"_id": oid})
    return _to_user_out(doc)


@router.delete("/users/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_user_endpoint(
    user_id: str, 
    db=Depends(get_db),
    current_user_id: str = Depends(get_current_user_id)
    ):
    """Exclui um usuário por ID.

    Regras:
    - 400: ID inválido.
    - 404: usuário não encontrado.
    - 204: exclusão bem-sucedida sem corpo de resposta.
    """
    try:
        oid = ObjectId(user_id)
    except Exception:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid user id")

    res = await db["users"].delete_one({"_id": oid})
    if res.deleted_count == 0:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    return None