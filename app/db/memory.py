from typing import List, Optional
from app.schemas.user import UserOut, UserCreate, UserUpdate

_db: List[UserOut] = []


def list_users() -> List[UserOut]:
    return _db


def get_user(user_id: int) -> Optional[UserOut]:
    return next((u for u in _db if u.id == user_id), None)


def create_user(data: UserCreate) -> UserOut:
    new = UserOut(id=len(_db) + 1, name=data.name, email=data.email, status=data.status)
    _db.append(new)
    return new


def update_user(user_id: int, data: UserUpdate) -> Optional[UserOut]:
    user = get_user(user_id)
    if not user:
        return None
    updated = user.model_copy(update=data.model_dump(exclude_unset=True))
    idx = _db.index(user)
    _db[idx] = updated
    return updated


def delete_user(user_id: int) -> bool:
    user = get_user(user_id)
    if not user:
        return False
    _db.remove(user)
    return True