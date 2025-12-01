"""
Servicio de Roles y Permisos
Sistema PQRS - Equipo Desertados

Lógica de negocio para gestión de roles y permisos.
"""

from typing import List, Optional, Dict, Any
from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.repositories.role_permission_repository import RolePermissionRepository
from app.models.role import Role
from app.models.permission import Permission
from app.schemas.roles_permissions import (
    PermissionCreate,
    PermissionUpdate,
    RoleCreate,
    RoleUpdate
)


class RolePermissionService:
    """Servicio para gestión de roles y permisos"""
    
    def __init__(self, db: AsyncSession):
        """
        Inicializa el servicio
        
        Args:
            db: Sesión asíncrona de SQLAlchemy
        """
        self.db = db
        self.repository = RolePermissionRepository(db)
    
    # =========================================================================
    # PERMISOS - CRUD
    # =========================================================================
    
    async def create_permission(
        self,
        permission_data: PermissionCreate
    ) -> Permission:
        """
        Crea un nuevo permiso
        
        Args:
            permission_data: Datos del permiso
            
        Returns:
            Permiso creado
            
        Raises:
            HTTPException 400: Si el permiso ya existe
        """
        # Verificar que no exista
        if await self.repository.permission_exists(permission_data.name):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"El permiso '{permission_data.name}' ya existe"
            )
        
        # Crear permiso
        permission = Permission(**permission_data.model_dump())
        created = await self.repository.create_permission(permission)
        await self.db.commit()
        
        return created
    
    async def get_permission_by_id(
        self,
        permission_id: int
    ) -> Permission:
        """
        Obtiene un permiso por ID
        
        Args:
            permission_id: ID del permiso
            
        Returns:
            Permiso encontrado
            
        Raises:
            HTTPException 404: Si no existe
        """
        permission = await self.repository.get_permission_by_id(permission_id)
        
        if not permission:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Permiso con ID {permission_id} no encontrado"
            )
        
        return permission
    
    async def get_all_permissions(
        self,
        skip: int = 0,
        limit: int = 100,
        category: Optional[str] = None,
        is_active: Optional[bool] = None
    ) -> tuple[List[Permission], int]:
        """
        Obtiene lista paginada de permisos
        
        Args:
            skip: Registros a saltar
            limit: Registros máximos
            category: Filtrar por categoría
            is_active: Filtrar por estado
            
        Returns:
            Tupla (lista de permisos, total)
        """
        permissions = await self.repository.get_all_permissions(
            skip=skip,
            limit=limit,
            category=category,
            is_active=is_active
        )
        
        total = await self.repository.count_permissions(
            category=category,
            is_active=is_active
        )
        
        return permissions, total
    
    async def get_permissions_by_category(self) -> Dict[str, List[Permission]]:
        """
        Obtiene permisos agrupados por categoría
        
        Returns:
            Diccionario {categoría: [permisos]}
        """
        return await self.repository.get_permissions_by_category()
    
    async def update_permission(
        self,
        permission_id: int,
        permission_data: PermissionUpdate
    ) -> Permission:
        """
        Actualiza un permiso
        
        Args:
            permission_id: ID del permiso
            permission_data: Datos a actualizar
            
        Returns:
            Permiso actualizado
            
        Raises:
            HTTPException 404: Si no existe
        """
        permission = await self.get_permission_by_id(permission_id)
        
        # Actualizar campos
        update_data = permission_data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(permission, field, value)
        
        updated = await self.repository.update_permission(permission)
        await self.db.commit()
        
        return updated
    
    async def delete_permission(self, permission_id: int) -> bool:
        """
        Elimina un permiso
        
        Args:
            permission_id: ID del permiso
            
        Returns:
            True si se eliminó
            
        Raises:
            HTTPException 404: Si no existe
            HTTPException 400: Si está asignado a roles
        """
        permission = await self.get_permission_by_id(permission_id)
        
        # Verificar si está asignado a algún rol
        # (se puede eliminar de todas formas por CASCADE, pero advertir)
        
        deleted = await self.repository.delete_permission(permission_id)
        await self.db.commit()
        
        return deleted
    
    # =========================================================================
    # ROLES - CRUD
    # =========================================================================
    
    async def create_role(
        self,
        role_data: RoleCreate
    ) -> Role:
        """
        Crea un nuevo rol
        
        Args:
            role_data: Datos del rol
            
        Returns:
            Rol creado con permisos asignados
            
        Raises:
            HTTPException 400: Si el rol ya existe
        """
        # Verificar que no exista
        if await self.repository.role_exists(role_data.name):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"El rol '{role_data.name}' ya existe"
            )
        
        # Crear rol (sin permisos primero)
        role_dict = role_data.model_dump(exclude={'permission_ids'})
        role = Role(**role_dict)
        
        created = await self.repository.create_role(role)
        
        # Asignar permisos si se proporcionaron
        if role_data.permission_ids:
            created = await self.repository.assign_permissions_to_role(
                created,
                role_data.permission_ids
            )
        
        await self.db.commit()
        
        return created
    
    async def get_role_by_id(
        self,
        role_id: int,
        load_permissions: bool = True
    ) -> Role:
        """
        Obtiene un rol por ID
        
        Args:
            role_id: ID del rol
            load_permissions: Si True, carga permisos
            
        Returns:
            Rol encontrado
            
        Raises:
            HTTPException 404: Si no existe
        """
        role = await self.repository.get_role_by_id(role_id, load_permissions)
        
        if not role:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Rol con ID {role_id} no encontrado"
            )
        
        return role
    
    async def get_all_roles(
        self,
        skip: int = 0,
        limit: int = 100,
        is_active: Optional[bool] = None,
        is_system: Optional[bool] = None
    ) -> tuple[List[Role], int]:
        """
        Obtiene lista paginada de roles
        
        Args:
            skip: Registros a saltar
            limit: Registros máximos
            is_active: Filtrar por estado
            is_system: Filtrar por tipo
            
        Returns:
            Tupla (lista de roles, total)
        """
        roles = await self.repository.get_all_roles(
            skip=skip,
            limit=limit,
            is_active=is_active,
            is_system=is_system
        )
        
        total = await self.repository.count_roles(
            is_active=is_active,
            is_system=is_system
        )
        
        return roles, total
    
    async def update_role(
        self,
        role_id: int,
        role_data: RoleUpdate
    ) -> Role:
        """
        Actualiza un rol
        
        Args:
            role_id: ID del rol
            role_data: Datos a actualizar
            
        Returns:
            Rol actualizado
            
        Raises:
            HTTPException 404: Si no existe
            HTTPException 400: Si intenta modificar rol de sistema
        """
        role = await self.get_role_by_id(role_id, load_permissions=False)
        
        # No permitir modificar roles de sistema
        if role.is_system:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No se pueden modificar roles del sistema"
            )
        
        # Actualizar campos
        update_data = role_data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(role, field, value)
        
        updated = await self.repository.update_role(role)
        await self.db.commit()
        
        return updated
    
    async def delete_role(self, role_id: int) -> bool:
        """
        Elimina un rol
        
        Args:
            role_id: ID del rol
            
        Returns:
            True si se eliminó
            
        Raises:
            HTTPException 404: Si no existe
            HTTPException 400: Si es rol de sistema o tiene usuarios
        """
        role = await self.get_role_by_id(role_id, load_permissions=False)
        
        # No permitir eliminar roles de sistema
        if role.is_system:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No se pueden eliminar roles del sistema"
            )
        
        # Aquí podrías verificar si tiene usuarios asignados
        # y prevenir la eliminación o reasignarlos
        
        deleted = await self.repository.delete_role(role_id)
        await self.db.commit()
        
        return deleted
    
    # =========================================================================
    # ASIGNACIÓN DE PERMISOS
    # =========================================================================
    
    async def assign_permissions_to_role(
        self,
        role_id: int,
        permission_ids: List[int]
    ) -> Role:
        """
        Asigna permisos a un rol
        
        Args:
            role_id: ID del rol
            permission_ids: Lista de IDs de permisos
            
        Returns:
            Rol actualizado
            
        Raises:
            HTTPException 404: Si el rol o algún permiso no existe
        """
        role = await self.get_role_by_id(role_id, load_permissions=True)
        
        # Verificar que todos los permisos existan
        for perm_id in permission_ids:
            perm = await self.repository.get_permission_by_id(perm_id)
            if not perm:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Permiso con ID {perm_id} no existe"
                )
        
        # Asignar permisos
        updated_role = await self.repository.assign_permissions_to_role(
            role,
            permission_ids
        )
        await self.db.commit()
        
        return updated_role
    
    async def remove_permissions_from_role(
        self,
        role_id: int,
        permission_ids: List[int]
    ) -> Role:
        """
        Remueve permisos de un rol
        
        Args:
            role_id: ID del rol
            permission_ids: Lista de IDs de permisos a remover
            
        Returns:
            Rol actualizado
            
        Raises:
            HTTPException 404: Si el rol no existe
        """
        role = await self.get_role_by_id(role_id, load_permissions=True)
        
        # Remover permisos
        updated_role = await self.repository.remove_permissions_from_role(
            role,
            permission_ids
        )
        await self.db.commit()
        
        return updated_role
    
    async def replace_role_permissions(
        self,
        role_id: int,
        permission_ids: List[int]
    ) -> Role:
        """
        Reemplaza todos los permisos de un rol
        
        Args:
            role_id: ID del rol
            permission_ids: Nueva lista de IDs de permisos
            
        Returns:
            Rol actualizado
            
        Raises:
            HTTPException 404: Si el rol o algún permiso no existe
        """
        role = await self.get_role_by_id(role_id, load_permissions=True)
        
        # Verificar que todos los permisos existan
        for perm_id in permission_ids:
            perm = await self.repository.get_permission_by_id(perm_id)
            if not perm:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Permiso con ID {perm_id} no existe"
                )
        
        # Reemplazar permisos
        updated_role = await self.repository.replace_role_permissions(
            role,
            permission_ids
        )
        await self.db.commit()
        
        return updated_role
    
    async def get_role_permissions(self, role_id: int) -> List[Permission]:
        """
        Obtiene todos los permisos de un rol
        
        Args:
            role_id: ID del rol
            
        Returns:
            Lista de permisos
            
        Raises:
            HTTPException 404: Si el rol no existe
        """
        await self.get_role_by_id(role_id, load_permissions=False)  # Verificar que exista
        
        return await self.repository.get_role_permissions(role_id)
    
    # =========================================================================
    # ESTADÍSTICAS
    # =========================================================================
    
    async def get_permission_usage_stats(self) -> Dict[str, Any]:
        """
        Obtiene estadísticas de uso de permisos
        
        Returns:
            Diccionario con estadísticas
        """
        return await self.repository.get_permission_usage_stats()
    
    async def get_role_stats(self) -> Dict[str, Any]:
        """
        Obtiene estadísticas de roles
        
        Returns:
            Diccionario con estadísticas
        """
        return await self.repository.get_role_stats()


# =============================================================================
# FUNCIÓN HELPER
# =============================================================================

def get_role_permission_service(db: AsyncSession) -> RolePermissionService:
    """
    Factory function para obtener una instancia del servicio
    
    Args:
        db: Sesión asíncrona de SQLAlchemy
        
    Returns:
        Instancia de RolePermissionService
    """
    return RolePermissionService(db)