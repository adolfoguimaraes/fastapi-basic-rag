"""
Esquemas Pydantic para dados de usuário expostos pela API.

- Define payloads de criação/atualização e resposta.
- Não usa variáveis de ambiente; ajustes de validação são feitos nos próprios schemas (tamanhos e opcionalidade de campos).
"""

from pydantic import BaseModel, EmailStr, Field
from typing import Optional


class UserBase(BaseModel):
    """Campos comuns de usuário usados em entrada e saída."""

    name: str = Field(min_length=1, max_length=100, description="Nome do usuário")
    email: EmailStr = Field(description="E-mail válido do usuário")
    status: str = Field(default="ativo", description="Status do usuário (padrão: 'ativo')")


class UserCreate(UserBase):
    """Payload de criação; inclui senha validada por tamanho."""

    # bcrypt_sha256 supports long inputs; cap for validation and payload sanity
    password: str = Field(min_length=6, max_length=256, description="Senha em texto plano para cadastro")


class UserUpdate(BaseModel):
    """Payload parcial para atualização; todos os campos são opcionais."""

    name: Optional[str] = Field(default=None, min_length=1, max_length=100, description="Nome do usuário")
    status: Optional[str] = Field(default=None, description="Status do usuário")
    password: Optional[str] = Field(default=None, min_length=6, max_length=256, description="Nova senha do usuário")


class UserOut(UserBase):
    """Representação de saída; inclui o identificador do usuário."""

    id: str = Field(..., description="Identificador do usuário")