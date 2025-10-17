from fastapi import APIRouter, HTTPException, status, Depends
from typing import List, Optional
from bson import ObjectId
from passlib.context import CryptContext
from app.schemas.user import UserOut, UserCreate, UserUpdate
from app.db.mongo import get_db

"""
Password hashing context:
- Uses pbkdf2_sha256 as the default to avoid bcrypt backend/72-byte issues.
- Keeps bcrypt_sha256 and bcrypt for backward-compatibility verification (if any existing hashes).
"""
pwd_context = CryptContext(schemes=["pbkdf2_sha256", "bcrypt_sha256", "bcrypt"], deprecated="auto")
router = APIRouter(tags=["users"]) 


def _to_user_out(doc) -> UserOut:
    return UserOut(
        id=str(doc["_id"]),
        name=doc["name"],
        email=doc["email"],
        status=doc.get("status", "ativo"),
    )


@router.get("/users", response_model=List[UserOut])
async def list_users_endpoint(status: Optional[str] = None, db=Depends(get_db)):
    query = {"status": status} if status else {}
    cursor = db["users"].find(query)
    docs = [doc async for doc in cursor]
    return [_to_user_out(docs[i]) for i in range(len(docs))]


@router.get("/users/{user_id}", response_model=UserOut)
async def get_user_endpoint(user_id: str, db=Depends(get_db)):
    try:
        oid = ObjectId(user_id)
    except Exception:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid user id")

    doc = await db["users"].find_one({"_id": oid})
    if not doc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    return _to_user_out(doc)


@router.post("/users", response_model=UserOut, status_code=status.HTTP_201_CREATED)
async def create_user_endpoint(data: UserCreate, db=Depends(get_db)):
    # Verifica duplicidade de email
    if await db["users"].find_one({"email": data.email}):
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Email already in use")

    # Hash password (supports long passphrases via bcrypt_sha256)
    try:
        password_hash = pwd_context.hash(data.password)
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
async def update_user_endpoint(user_id: str, data: UserUpdate, db=Depends(get_db)):
    try:
        oid = ObjectId(user_id)
    except Exception:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid user id")

    update_doc = {k: v for k, v in data.dict(exclude_unset=True).items() if k != "password"}
    if data.password:
        try:
            update_doc["password_hash"] = pwd_context.hash(data.password)
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
async def delete_user_endpoint(user_id: str, db=Depends(get_db)):
    try:
        oid = ObjectId(user_id)
    except Exception:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid user id")

    res = await db["users"].delete_one({"_id": oid})
    if res.deleted_count == 0:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    return None