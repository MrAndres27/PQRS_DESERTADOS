"""
Router de Roles y Permisos
Sistema PQRS - Equipo Desertados

Endpoints para gestión completa de roles y permisos del sistema.
"""

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional
import math

from app.core.database import get_async_db
from app.core.dependencies import require_admin, get_pagination_params, PaginationParams
from app.models.user import User
from app.services.role_permission_service import (
    get_role_permission_service,
    RolePermissionService
)
from app.schemas.roles_permissions import (
    # Permisos
    PermissionCreate,
    PermissionUpdate,
    PermissionResponse,
    PermissionListResponse,
    PermissionsPaginatedResponse,
    PermissionsByCategoryResponse,
    PermissionCategory,
    
    # Roles
    RoleCreate,
    RoleUpdate,
    RoleResponse,
    RoleListResponse,
    RolesPaginatedResponse,
    RoleWithPermissionsResponse,
    
    # Asignación
    AssignPermissionsRequest,
    RemovePermissionsRequest,
    RolePermissionsResponse,
    
    # Estadísticas
    PermissionStatsResponse,
    RoleStatsResponse
)


# =============================================================================
# ROUTER
# =============================================================================

router = APIRouter(prefix="/admin", tags=["Roles y Permisos (Admin)"])


# =============================================================================
# ENDPOINTS DE PERMISOS
# =============================================================================

@router.get(
    "/permissions",
    response_model=PermissionsPaginatedResponse,
    status_code=status.HTTP_200_OK
)
async def get_permissions(
    pagination: PaginationParams = Depends(get_pagination_params),
    category: Optional[str] = Query(default=None, description="Filtrar por categoría"),
    is_active: Optional[bool] = Query(default=None, description="Filtrar por estado"),
    current_user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_async_db)
):
    """
    Obtiene lista paginada de permisos
    
    **Filtros opcionales:**
    - `category`: Filtrar por categoría (pqrs, users, comments, etc.)
    - `is_active`: Filtrar por estado activo (true/false)
    
    **Paginación:**
    - `page`: Número de página (default: 1)
    - `page_size`: Tamaño de página (default: 10, max: 100)
    
    **Respuesta:**
    - Lista de permisos con información básica
    - Total de registros
    - Información de paginación
    
    **Requiere:** Rol Administrador
    """
    service = get_role_permission_service(db)
    
    # Calcular skip
    skip = (pagination.page - 1) * pagination.page_size
    
    # Obtener permisos
    permissions, total = await service.get_all_permissions(
        skip=skip,
        limit=pagination.page_size,
        category=category,
        is_active=is_active
    )
    
    # Calcular total de páginas
    total_pages = math.ceil(total / pagination.page_size)
    
    return PermissionsPaginatedResponse(
        permissions=[PermissionListResponse.model_validate(p) for p in permissions],
        total=total,
        page=pagination.page,
        page_size=pagination.page_size,
        total_pages=total_pages
    )


@router.post(
    "/permissions",
    response_model=PermissionResponse,
    status_code=status.HTTP_201_CREATED
)
async def create_permission(
    permission_data: PermissionCreate,
    current_user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_async_db)
):
    """
    Crea un nuevo permiso
    
    **Campos requeridos:**
    - `name`: Nombre único del permiso (ej: "pqrs.create")
    - `display_name`: Nombre legible (ej: "Crear PQRS")
    - `category`: Categoría del permiso
    
    **Campos opcionales:**
    - `description`: Descripción del permiso
    
    **Categorías disponibles:**
    - system, pqrs, users, roles, comments, attachments, reports, dashboard, notifications
    
    **Errores:**
    - `400 Bad Request`: Si el permiso ya existe
    
    **Requiere:** Rol Administrador
    """
    service = get_role_permission_service(db)
    
    permission = await service.create_permission(permission_data)
    
    return PermissionResponse.model_validate(permission)


@router.get(
    "/permissions/{permission_id}",
    response_model=PermissionResponse,
    status_code=status.HTTP_200_OK
)
async def get_permission(
    permission_id: int,
    current_user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_async_db)
):
    """
    Obtiene un permiso por ID
    
    **Respuesta:**
    - Información completa del permiso
    
    **Errores:**
    - `404 Not Found`: Si el permiso no existe
    
    **Requiere:** Rol Administrador
    """
    service = get_role_permission_service(db)
    
    permission = await service.get_permission_by_id(permission_id)
    
    return PermissionResponse.model_validate(permission)


@router.put(
    "/permissions/{permission_id}",
    response_model=PermissionResponse,
    status_code=status.HTTP_200_OK
)
async def update_permission(
    permission_id: int,
    permission_data: PermissionUpdate,
    current_user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_async_db)
):
    """
    Actualiza un permiso
    
    **Campos actualizables:**
    - `display_name`: Nombre legible
    - `description`: Descripción
    - `category`: Categoría
    - `is_active`: Estado activo/inactivo
    
    **Nota:** El campo `name` no puede ser modificado
    
    **Errores:**
    - `404 Not Found`: Si el permiso no existe
    
    **Requiere:** Rol Administrador
    """
    service = get_role_permission_service(db)
    
    permission = await service.update_permission(permission_id, permission_data)
    
    return PermissionResponse.model_validate(permission)


@router.delete(
    "/permissions/{permission_id}",
    status_code=status.HTTP_200_OK
)
async def delete_permission(
    permission_id: int,
    current_user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_async_db)
):
    """
    Elimina un permiso
    
    **ADVERTENCIA:**
    - Esta acción eliminará el permiso de todos los roles
    - No se puede deshacer
    
    **Errores:**
    - `404 Not Found`: Si el permiso no existe
    
    **Requiere:** Rol Administrador
    """
    service = get_role_permission_service(db)
    
    await service.delete_permission(permission_id)
    
    return {
        "message": "Permiso eliminado exitosamente",
        "permission_id": permission_id,
        "success": True
    }


@router.get(
    "/permissions/by-category/grouped",
    response_model=list[PermissionsByCategoryResponse],
    status_code=status.HTTP_200_OK
)
async def get_permissions_by_category(
    current_user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_async_db)
):
    """
    Obtiene permisos agrupados por categoría
    
    **Respuesta:**
    - Lista de categorías con sus permisos
    - Solo incluye permisos activos
    
    **Útil para:**
    - Mostrar permisos organizados en formularios
    - Interfaces de asignación de permisos
    
    **Requiere:** Rol Administrador
    """
    service = get_role_permission_service(db)
    
    by_category = await service.get_permissions_by_category()
    
    result = []
    for category, permissions in by_category.items():
        result.append(
            PermissionsByCategoryResponse(
                category=category,
                permissions=[PermissionListResponse.model_validate(p) for p in permissions],
                count=len(permissions)
            )
        )
    
    return result


@router.get(
    "/permissions/stats",
    response_model=PermissionStatsResponse,
    status_code=status.HTTP_200_OK
)
async def get_permissions_stats(
    current_user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_async_db)
):
    """
    Obtiene estadísticas de permisos
    
    **Respuesta:**
    - Total de permisos
    - Permisos activos e inactivos
    - Distribución por categoría
    
    **Requiere:** Rol Administrador
    """
    service = get_role_permission_service(db)
    
    stats = await service.get_permission_usage_stats()
    
    return PermissionStatsResponse(**stats)


# =============================================================================
# ENDPOINTS DE ROLES
# =============================================================================

@router.get(
    "/roles",
    response_model=RolesPaginatedResponse,
    status_code=status.HTTP_200_OK
)
async def get_roles(
    pagination: PaginationParams = Depends(get_pagination_params),
    is_active: Optional[bool] = Query(default=None, description="Filtrar por estado"),
    is_system: Optional[bool] = Query(default=None, description="Filtrar por roles de sistema"),
    current_user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_async_db)
):
    """
    Obtiene lista paginada de roles
    
    **Filtros opcionales:**
    - `is_active`: Filtrar por estado activo (true/false)
    - `is_system`: Filtrar por roles de sistema (true/false)
    
    **Paginación:**
    - `page`: Número de página (default: 1)
    - `page_size`: Tamaño de página (default: 10, max: 100)
    
    **Respuesta:**
    - Lista de roles con información básica
    - Contador de permisos por rol
    - Total de registros
    - Información de paginación
    
    **Requiere:** Rol Administrador
    """
    service = get_role_permission_service(db)
    
    # Calcular skip
    skip = (pagination.page - 1) * pagination.page_size
    
    # Obtener roles
    roles, total = await service.get_all_roles(
        skip=skip,
        limit=pagination.page_size,
        is_active=is_active,
        is_system=is_system
    )
    
    # Calcular total de páginas
    total_pages = math.ceil(total / pagination.page_size)
    
    # Convertir a response
    roles_response = []
    for role in roles:
        role_dict = {
            "id": role.id,
            "name": role.name,
            "description": role.description,
            "is_system": role.is_system,
            "is_active": role.is_active,
            "permissions_count": len(role.permissions) if role.permissions else 0
        }
        roles_response.append(RoleListResponse(**role_dict))
    
    return RolesPaginatedResponse(
        roles=roles_response,
        total=total,
        page=pagination.page,
        page_size=pagination.page_size,
        total_pages=total_pages
    )


@router.post(
    "/roles",
    response_model=RoleWithPermissionsResponse,
    status_code=status.HTTP_201_CREATED
)
async def create_role(
    role_data: RoleCreate,
    current_user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_async_db)
):
    """
    Crea un nuevo rol personalizado
    
    **Campos requeridos:**
    - `name`: Nombre único del rol
    
    **Campos opcionales:**
    - `description`: Descripción del rol
    - `permission_ids`: Lista de IDs de permisos a asignar
    
    **Notas:**
    - Los roles creados NO son roles de sistema
    - Se pueden asignar permisos al momento de crear
    - Los permisos se pueden modificar después
    
    **Errores:**
    - `400 Bad Request`: Si el rol ya existe
    - `404 Not Found`: Si algún ID de permiso no existe
    
    **Requiere:** Rol Administrador
    """
    service = get_role_permission_service(db)
    
    role = await service.create_role(role_data)
    
    return RoleWithPermissionsResponse.model_validate(role)


@router.get(
    "/roles/{role_id}",
    response_model=RoleWithPermissionsResponse,
    status_code=status.HTTP_200_OK
)
async def get_role(
    role_id: int,
    current_user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_async_db)
):
    """
    Obtiene un rol por ID con sus permisos
    
    **Respuesta:**
    - Información completa del rol
    - Lista de permisos asignados
    
    **Errores:**
    - `404 Not Found`: Si el rol no existe
    
    **Requiere:** Rol Administrador
    """
    service = get_role_permission_service(db)
    
    role = await service.get_role_by_id(role_id, load_permissions=True)
    
    return RoleWithPermissionsResponse.model_validate(role)


@router.put(
    "/roles/{role_id}",
    response_model=RoleResponse,
    status_code=status.HTTP_200_OK
)
async def update_role(
    role_id: int,
    role_data: RoleUpdate,
    current_user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_async_db)
):
    """
    Actualiza un rol personalizado
    
    **Campos actualizables:**
    - `name`: Nombre del rol
    - `description`: Descripción
    - `is_active`: Estado activo/inactivo
    
    **RESTRICCIONES:**
    - No se pueden modificar roles de sistema
    - Los permisos se gestionan en endpoints separados
    
    **Requiere:** Rol Administrador
    """
    service = get_role_permission_service(db)
    
    role = await service.update_role(role_id, role_data)
    
    return RoleResponse.model_validate(role)


@router.delete(
    "/roles/{role_id}",
    status_code=status.HTTP_200_OK
)
async def delete_role(
    role_id: int,
    current_user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_async_db)
):
    """
    Elimina un rol personalizado
    
    **RESTRICCIONES:**
    - No se pueden eliminar roles del sistema (admin, gestor, ciudadano)
    - Los usuarios con este rol quedarán sin rol
    
    **ADVERTENCIA:**
    - Esta acción no se puede deshacer
    
    **Requiere:** Rol Administrador
    """
    service = get_role_permission_service(db)
    
    await service.delete_role(role_id)
    
    return {
        "message": "Rol eliminado exitosamente",
        "role_id": role_id,
        "success": True
    }


@router.get(
    "/roles/stats",
    response_model=RoleStatsResponse,
    status_code=status.HTTP_200_OK
)
async def get_roles_stats(
    current_user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_async_db)
):
    """
    Obtiene estadísticas de roles
    
    **Respuesta:**
    - Total de roles
    - Roles de sistema vs personalizados
    - Roles activos e inactivos
    - Distribución de usuarios por rol
    
    **Requiere:** Rol Administrador
    """
    service = get_role_permission_service(db)
    
    stats = await service.get_role_stats()
    
    return RoleStatsResponse(**stats)


# =============================================================================
# ENDPOINTS DE ASIGNACIÓN DE PERMISOS
# =============================================================================

@router.get(
    "/roles/{role_id}/permissions",
    response_model=RolePermissionsResponse,
    status_code=status.HTTP_200_OK
)
async def get_role_permissions(
    role_id: int,
    current_user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_async_db)
):
    """
    Obtiene todos los permisos asignados a un rol
    
    **Incluye:**
    - Nombre del rol
    - Lista completa de permisos
    - Total de permisos asignados
    
    **Requiere:** Rol Administrador
    """
    service = get_role_permission_service(db)
    
    role = await service.get_role_by_id(role_id, load_permissions=True)
    permissions = role.permissions
    
    return RolePermissionsResponse(
        role_id=role.id,
        role_name=role.name,
        permissions=[PermissionListResponse.model_validate(p) for p in permissions],
        total_permissions=len(permissions)
    )


@router.post(
    "/roles/{role_id}/permissions",
    response_model=RolePermissionsResponse,
    status_code=status.HTTP_200_OK
)
async def assign_permissions_to_role(
    role_id: int,
    request: AssignPermissionsRequest,
    current_user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_async_db)
):
    """
    Asigna permisos a un rol
    
    **IMPORTANTE:**
    - Agrega permisos sin remover los existentes
    - Si un permiso ya está asignado, no se duplica
    - Puede asignar múltiples permisos a la vez
    
    **Errores:**
    - `404 Not Found`: Si el rol o algún permiso no existe
    
    **Requiere:** Rol Administrador
    """
    service = get_role_permission_service(db)
    
    role = await service.assign_permissions_to_role(
        role_id,
        request.permission_ids
    )
    
    return RolePermissionsResponse(
        role_id=role.id,
        role_name=role.name,
        permissions=[PermissionListResponse.model_validate(p) for p in role.permissions],
        total_permissions=len(role.permissions)
    )


@router.delete(
    "/roles/{role_id}/permissions",
    response_model=RolePermissionsResponse,
    status_code=status.HTTP_200_OK
)
async def remove_permissions_from_role(
    role_id: int,
    request: RemovePermissionsRequest,
    current_user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_async_db)
):
    """
    Remueve permisos de un rol
    
    **IMPORTANTE:**
    - Solo remueve los permisos especificados
    - Los demás permisos se mantienen
    - Si un permiso no existe en el rol, se ignora
    
    **Errores:**
    - `404 Not Found`: Si el rol no existe
    
    **Requiere:** Rol Administrador
    """
    service = get_role_permission_service(db)
    
    role = await service.remove_permissions_from_role(
        role_id,
        request.permission_ids
    )
    
    return RolePermissionsResponse(
        role_id=role.id,
        role_name=role.name,
        permissions=[PermissionListResponse.model_validate(p) for p in role.permissions],
        total_permissions=len(role.permissions)
    )