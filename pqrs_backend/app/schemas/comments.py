"""
Schemas de Comentarios
Sistema PQRS - Equipo Desertados

Schemas para validación y serialización de comentarios.
"""

from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional, List


# =============================================================================
# SCHEMAS BASE
# =============================================================================

class CommentBase(BaseModel):
    """Schema base para comentarios"""
    content: str = Field(
        ...,
        min_length=1,
        max_length=5000,
        description="Contenido del comentario"
    )
    is_internal: bool = Field(
        default=False,
        description="Si es true, solo visible para gestores"
    )


# =============================================================================
# SCHEMAS DE CREACIÓN Y ACTUALIZACIÓN
# =============================================================================

class CommentCreate(CommentBase):
    """Schema para crear comentario"""
    
    class Config:
        json_schema_extra = {
            "example": {
                "content": "Hemos revisado la solicitud y necesitamos más información sobre...",
                "is_internal": False
            }
        }


class CommentUpdate(BaseModel):
    """Schema para actualizar comentario"""
    content: str = Field(
        ...,
        min_length=1,
        max_length=5000,
        description="Nuevo contenido del comentario"
    )
    
    class Config:
        json_schema_extra = {
            "example": {
                "content": "Contenido actualizado del comentario..."
            }
        }


# =============================================================================
# SCHEMAS DE RESPUESTA
# =============================================================================

class UserBasicResponse(BaseModel):
    """Schema básico de usuario para comentarios"""
    id: int
    username: str
    full_name: str
    
    class Config:
        from_attributes = True


class CommentResponse(CommentBase):
    """Schema de respuesta de comentario"""
    id: int
    pqrs_id: int
    user_id: int
    author: UserBasicResponse
    is_edited: bool = Field(
        default=False,
        description="Indica si el comentario fue editado"
    )
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True
        json_schema_extra = {
            "example": {
                "id": 1,
                "pqrs_id": 5,
                "user_id": 2,
                "author": {
                    "id": 2,
                    "username": "gestor1",
                    "full_name": "Juan Gestor"
                },
                "content": "Hemos revisado su solicitud...",
                "is_internal": False,
                "is_edited": False,
                "created_at": "2024-11-24T10:30:00",
                "updated_at": "2024-11-24T10:30:00"
            }
        }


# =============================================================================
# SCHEMAS DE PAGINACIÓN
# =============================================================================

class CommentPaginatedResponse(BaseModel):
    """Response paginada de comentarios"""
    items: List[CommentResponse]
    total: int
    page: int
    page_size: int
    total_pages: int
    
    class Config:
        json_schema_extra = {
            "example": {
                "items": [],
                "total": 15,
                "page": 1,
                "page_size": 10,
                "total_pages": 2
            }
        }


# =============================================================================
# SCHEMAS DE ESTADÍSTICAS
# =============================================================================

class CommentStats(BaseModel):
    """Estadísticas de comentarios de una PQRS"""
    total: int = Field(description="Total de comentarios visibles para el usuario")
    public: int = Field(description="Comentarios públicos")
    internal: Optional[int] = Field(
        default=None,
        description="Comentarios internos (null si no tiene permiso de verlos)"
    )
    
    class Config:
        json_schema_extra = {
            "example": {
                "total": 10,
                "public": 7,
                "internal": 3
            }
        }