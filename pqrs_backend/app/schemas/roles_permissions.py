"""
Schemas de Roles y Permisos
Sistema PQRS - Equipo Desertados

Esquemas de validación Pydantic para gestión de roles y permisos.
"""

from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, List
from datetime import datetime
from enum import Enum


# =============================================================================
# ENUMS
# =============================================================================

class PermissionCategory(str, Enum):
    """Categorías de permisos del sistema"""
    SYSTEM = "system"          # Permisos de sistema y administración
    PQRS = "pqrs"             # Permisos de PQRS
    USERS = "users"           # Permisos de usuarios
    ROLES = "roles"           # Permisos de roles
    COMMENTS = "comments"     # Permisos de comentarios
    ATTACHMENTS = "attachments"  # Permisos de archivos
    REPORTS = "reports"       # Permisos de reportes
    DASHBOARD = "dashboard"   # Permisos de dashboard
    NOTIFICATIONS = "notifications"  # Permisos de notificaciones


# =============================================================================
# SCHEMAS DE PERMISOS
# =============================================================================

class PermissionBase(BaseModel):
    """Schema base para permisos"""
    name: str = Field(..., min_length=3, max_length=100, description="Nombre único del permiso (ej: pqrs.create)")
    display_name: str = Field(..., min_length=3, max_length=200, description="Nombre legible del permiso")
    description: Optional[str] = Field(None, max_length=500, description="Descripción del permiso")
    category: str = Field(..., description="Categoría del permiso")


class PermissionCreate(PermissionBase):
    """Schema para crear un permiso"""
    pass


class PermissionUpdate(BaseModel):
    """Schema para actualizar un permiso"""
    display_name: Optional[str] = Field(None, min_length=3, max_length=200)
    description: Optional[str] = Field(None, max_length=500)
    category: Optional[str] = None
    is_active: Optional[bool] = None


class PermissionResponse(PermissionBase):
    """Schema de respuesta para un permiso"""
    id: int
    is_active: bool
    created_at: datetime
    updated_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


class PermissionListResponse(BaseModel):
    """Schema simplificado para listar permisos"""
    id: int
    name: str
    display_name: str
    category: str
    is_active: bool

    model_config = ConfigDict(from_attributes=True)


class PermissionsPaginatedResponse(BaseModel):
    """Schema para respuesta paginada de permisos"""
    permissions: List[PermissionListResponse]
    total: int
    page: int
    page_size: int
    total_pages: int


class PermissionsByCategoryResponse(BaseModel):
    """Schema para permisos agrupados por categoría"""
    category: str
    permissions: List[PermissionListResponse]
    count: int


# =============================================================================
# SCHEMAS DE ROLES
# =============================================================================

class RoleBase(BaseModel):
    """Schema base para roles"""
    name: str = Field(..., min_length=3, max_length=50, description="Nombre único del rol")
    description: Optional[str] = Field(None, max_length=200, description="Descripción del rol")


class RoleCreate(RoleBase):
    """Schema para crear un rol"""
    permission_ids: Optional[List[int]] = Field(default=[], description="IDs de permisos a asignar al rol")


class RoleUpdate(BaseModel):
    """Schema para actualizar un rol"""
    name: Optional[str] = Field(None, min_length=3, max_length=50)
    description: Optional[str] = Field(None, max_length=200)
    is_active: Optional[bool] = None


class RoleResponse(RoleBase):
    """Schema de respuesta para un rol"""
    id: int
    is_system: bool
    is_active: bool
    created_at: datetime
    updated_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


class RoleWithPermissionsResponse(RoleResponse):
    """Schema de rol con sus permisos"""
    permissions: List[PermissionListResponse]


class RoleListResponse(BaseModel):
    """Schema simplificado para listar roles"""
    id: int
    name: str
    description: Optional[str] = None
    is_system: bool
    is_active: bool
    permissions_count: Optional[int] = 0

    model_config = ConfigDict(from_attributes=True)


class RolesPaginatedResponse(BaseModel):
    """Schema para respuesta paginada de roles"""
    roles: List[RoleListResponse]
    total: int
    page: int
    page_size: int
    total_pages: int


# =============================================================================
# SCHEMAS DE ASIGNACIÓN
# =============================================================================

class AssignPermissionsRequest(BaseModel):
    """Schema para asignar permisos a un rol"""
    permission_ids: List[int] = Field(..., min_length=1, description="Lista de IDs de permisos a asignar")


class RemovePermissionsRequest(BaseModel):
    """Schema para remover permisos de un rol"""
    permission_ids: List[int] = Field(..., min_length=1, description="Lista de IDs de permisos a remover")


class RolePermissionsResponse(BaseModel):
    """Schema para respuesta de permisos de un rol"""
    role_id: int
    role_name: str
    permissions: List[PermissionListResponse]
    total_permissions: int


# =============================================================================
# SCHEMAS DE ESTADÍSTICAS
# =============================================================================

class PermissionStatsResponse(BaseModel):
    """Schema para estadísticas de permisos"""
    total_permissions: int
    active_permissions: int
    inactive_permissions: int
    permissions_by_category: dict


class RoleStatsResponse(BaseModel):
    """Schema para estadísticas de roles"""
    total_roles: int
    system_roles: int
    custom_roles: int
    active_roles: int
    inactive_roles: int
    users_by_role: dict