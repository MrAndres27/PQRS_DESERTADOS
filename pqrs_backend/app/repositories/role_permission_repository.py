"""
Repository de Roles y Permisos
Sistema PQRS - Equipo Desertados

Maneja todas las operaciones de base de datos para roles y permisos.
"""

from typing import Optional, List, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, delete, func, and_
from sqlalchemy.orm import selectinload

from app.models.role import Role
from app.models.permission import Permission
from app.models.user import User


class RolePermissionRepository:
    """Repository para operaciones de roles y permisos"""
    
    def __init__(self, db: AsyncSession):
        """
        Inicializa el repository
        
        Args:
            db: Sesión asíncrona de SQLAlchemy
        """
        self.db = db
    
    # =========================================================================
    # PERMISOS - CRUD
    # =========================================================================
    
    async def create_permission(self, permission: Permission) -> Permission:
        """
        Crea un nuevo permiso
        
        Args:
            permission: Objeto Permission a crear
            
        Returns:
            Permission creado con ID asignado
        """
        self.db.add(permission)
        await self.db.flush()
        await self.db.refresh(permission)
        return permission
    
    async def get_permission_by_id(self, permission_id: int) -> Optional[Permission]:
        """
        Obtiene un permiso por ID
        
        Args:
            permission_id: ID del permiso
            
        Returns:
            Permission o None si no existe
        """
        result = await self.db.execute(
            select(Permission).where(Permission.id == permission_id)
        )
        return result.scalar_one_or_none()
    
    async def get_permission_by_name(self, name: str) -> Optional[Permission]:
        """
        Obtiene un permiso por nombre
        
        Args:
            name: Nombre del permiso
            
        Returns:
            Permission o None si no existe
        """
        result = await self.db.execute(
            select(Permission).where(Permission.name == name)
        )
        return result.scalar_one_or_none()
    
    async def permission_exists(self, name: str) -> bool:
        """
        Verifica si existe un permiso con el nombre dado
        
        Args:
            name: Nombre del permiso
            
        Returns:
            True si existe, False si no
        """
        result = await self.db.execute(
            select(func.count(Permission.id)).where(Permission.name == name)
        )
        count = result.scalar()
        return count > 0
    
    async def get_all_permissions(
        self,
        skip: int = 0,
        limit: int = 100,
        category: Optional[str] = None,
        is_active: Optional[bool] = None
    ) -> List[Permission]:
        """
        Obtiene lista de permisos con filtros opcionales
        
        Args:
            skip: Número de registros a saltar
            limit: Número máximo de registros a retornar
            category: Filtrar por categoría
            is_active: Filtrar por estado activo
            
        Returns:
            Lista de Permission
        """
        query = select(Permission)
        
        # Aplicar filtros
        conditions = []
        if category:
            conditions.append(Permission.category == category)
        if is_active is not None:
            conditions.append(Permission.is_active == is_active)
        
        if conditions:
            query = query.where(and_(*conditions))
        
        # Ordenar y paginar
        query = query.order_by(Permission.category, Permission.name)
        query = query.offset(skip).limit(limit)
        
        result = await self.db.execute(query)
        return list(result.scalars().all())
    
    async def count_permissions(
        self,
        category: Optional[str] = None,
        is_active: Optional[bool] = None
    ) -> int:
        """
        Cuenta permisos con filtros opcionales
        
        Args:
            category: Filtrar por categoría
            is_active: Filtrar por estado
            
        Returns:
            Número total de permisos
        """
        query = select(func.count(Permission.id))
        
        conditions = []
        if category:
            conditions.append(Permission.category == category)
        if is_active is not None:
            conditions.append(Permission.is_active == is_active)
        
        if conditions:
            query = query.where(and_(*conditions))
        
        result = await self.db.execute(query)
        return result.scalar()
    
    async def get_permissions_by_category(self) -> Dict[str, List[Permission]]:
        """
        Obtiene permisos agrupados por categoría
        
        Returns:
            Diccionario {categoría: [permisos]}
        """
        result = await self.db.execute(
            select(Permission)
            .where(Permission.is_active == True)
            .order_by(Permission.category, Permission.name)
        )
        permissions = result.scalars().all()
        
        # Agrupar por categoría
        by_category = {}
        for permission in permissions:
            category = permission.category
            if category not in by_category:
                by_category[category] = []
            by_category[category].append(permission)
        
        return by_category
    
    async def update_permission(self, permission: Permission) -> Permission:
        """
        Actualiza un permiso
        
        Args:
            permission: Permission con datos actualizados
            
        Returns:
            Permission actualizado
        """
        await self.db.flush()
        await self.db.refresh(permission)
        return permission
    
    async def delete_permission(self, permission_id: int) -> bool:
        """
        Elimina un permiso
        
        Args:
            permission_id: ID del permiso
            
        Returns:
            True si se eliminó
        """
        result = await self.db.execute(
            delete(Permission).where(Permission.id == permission_id)
        )
        return result.rowcount > 0
    
    # =========================================================================
    # ROLES - CRUD
    # =========================================================================
    
    async def create_role(self, role: Role) -> Role:
        """
        Crea un nuevo rol
        
        Args:
            role: Objeto Role a crear
            
        Returns:
            Role creado con ID asignado
        """
        self.db.add(role)
        await self.db.flush()
        await self.db.refresh(role)
        return role
    
    async def get_role_by_id(
        self,
        role_id: int,
        load_permissions: bool = True
    ) -> Optional[Role]:
        """
        Obtiene un rol por ID
        
        Args:
            role_id: ID del rol
            load_permissions: Si True, carga los permisos relacionados
            
        Returns:
            Role o None si no existe
        """
        query = select(Role).where(Role.id == role_id)
        
        if load_permissions:
            query = query.options(selectinload(Role.permissions))
        
        result = await self.db.execute(query)
        return result.scalar_one_or_none()
    
    async def get_role_by_name(self, name: str) -> Optional[Role]:
        """
        Obtiene un rol por nombre
        
        Args:
            name: Nombre del rol
            
        Returns:
            Role o None si no existe
        """
        result = await self.db.execute(
            select(Role).where(Role.name == name)
        )
        return result.scalar_one_or_none()
    
    async def role_exists(self, name: str) -> bool:
        """
        Verifica si existe un rol con el nombre dado
        
        Args:
            name: Nombre del rol
            
        Returns:
            True si existe, False si no
        """
        result = await self.db.execute(
            select(func.count(Role.id)).where(Role.name == name)
        )
        count = result.scalar()
        return count > 0
    
    async def get_all_roles(
        self,
        skip: int = 0,
        limit: int = 100,
        is_active: Optional[bool] = None,
        is_system: Optional[bool] = None
    ) -> List[Role]:
        """
        Obtiene lista de roles con filtros opcionales
        
        Args:
            skip: Número de registros a saltar
            limit: Número máximo de registros a retornar
            is_active: Filtrar por estado activo
            is_system: Filtrar por roles de sistema
            
        Returns:
            Lista de Role
        """
        query = select(Role).options(selectinload(Role.permissions))
        
        # Aplicar filtros
        conditions = []
        if is_active is not None:
            conditions.append(Role.is_active == is_active)
        if is_system is not None:
            conditions.append(Role.is_system == is_system)
        
        if conditions:
            query = query.where(and_(*conditions))
        
        # Ordenar y paginar
        query = query.order_by(Role.name)
        query = query.offset(skip).limit(limit)
        
        result = await self.db.execute(query)
        return list(result.scalars().all())
    
    async def count_roles(
        self,
        is_active: Optional[bool] = None,
        is_system: Optional[bool] = None
    ) -> int:
        """
        Cuenta roles con filtros opcionales
        
        Args:
            is_active: Filtrar por estado
            is_system: Filtrar por tipo de rol
            
        Returns:
            Número total de roles
        """
        query = select(func.count(Role.id))
        
        conditions = []
        if is_active is not None:
            conditions.append(Role.is_active == is_active)
        if is_system is not None:
            conditions.append(Role.is_system == is_system)
        
        if conditions:
            query = query.where(and_(*conditions))
        
        result = await self.db.execute(query)
        return result.scalar()
    
    async def update_role(self, role: Role) -> Role:
        """
        Actualiza un rol
        
        Args:
            role: Role con datos actualizados
            
        Returns:
            Role actualizado
        """
        await self.db.flush()
        await self.db.refresh(role, ['permissions'])
        return role
    
    async def delete_role(self, role_id: int) -> bool:
        """
        Elimina un rol
        
        Args:
            role_id: ID del rol
            
        Returns:
            True si se eliminó
        """
        result = await self.db.execute(
            delete(Role).where(Role.id == role_id)
        )
        return result.rowcount > 0
    
    # =========================================================================
    # ASIGNACIÓN DE PERMISOS
    # =========================================================================
    
    async def assign_permissions_to_role(
        self,
        role: Role,
        permission_ids: List[int]
    ) -> Role:
        """
        Asigna permisos a un rol (agrega sin remover existentes)
        
        Args:
            role: Rol al que asignar permisos
            permission_ids: Lista de IDs de permisos
            
        Returns:
            Role actualizado con permisos
        """
        # Obtener permisos
        result = await self.db.execute(
            select(Permission).where(Permission.id.in_(permission_ids))
        )
        permissions = list(result.scalars().all())
        
        # Agregar permisos (no duplicar)
        existing_ids = {p.id for p in role.permissions}
        for permission in permissions:
            if permission.id not in existing_ids:
                role.permissions.append(permission)
        
        await self.db.flush()
        await self.db.refresh(role, ['permissions'])
        return role
    
    async def remove_permissions_from_role(
        self,
        role: Role,
        permission_ids: List[int]
    ) -> Role:
        """
        Remueve permisos de un rol
        
        Args:
            role: Rol del que remover permisos
            permission_ids: Lista de IDs de permisos a remover
            
        Returns:
            Role actualizado
        """
        # Filtrar permisos que no estén en la lista de IDs
        role.permissions = [
            p for p in role.permissions if p.id not in permission_ids
        ]
        
        await self.db.flush()
        await self.db.refresh(role, ['permissions'])
        return role
    
    async def replace_role_permissions(
        self,
        role: Role,
        permission_ids: List[int]
    ) -> Role:
        """
        Reemplaza todos los permisos de un rol
        
        Args:
            role: Rol a actualizar
            permission_ids: Lista de IDs de permisos nuevos
            
        Returns:
            Role actualizado
        """
        # Limpiar permisos actuales
        role.permissions.clear()
        
        # Asignar nuevos permisos
        result = await self.db.execute(
            select(Permission).where(Permission.id.in_(permission_ids))
        )
        permissions = list(result.scalars().all())
        role.permissions.extend(permissions)
        
        await self.db.flush()
        await self.db.refresh(role, ['permissions'])
        return role
    
    async def get_role_permissions(self, role_id: int) -> List[Permission]:
        """
        Obtiene todos los permisos de un rol
        
        Args:
            role_id: ID del rol
            
        Returns:
            Lista de Permission
        """
        result = await self.db.execute(
            select(Permission)
            .join(Permission.roles)
            .where(Role.id == role_id)
            .order_by(Permission.category, Permission.name)
        )
        return list(result.scalars().all())
    
    # =========================================================================
    # ESTADÍSTICAS
    # =========================================================================
    
    async def get_permission_usage_stats(self) -> Dict[str, Any]:
        """
        Obtiene estadísticas de uso de permisos
        
        Returns:
            Diccionario con estadísticas
        """
        # Total de permisos
        total = await self.db.execute(select(func.count(Permission.id)))
        total_permissions = total.scalar()
        
        # Permisos activos
        active = await self.db.execute(
            select(func.count(Permission.id)).where(Permission.is_active == True)
        )
        active_permissions = active.scalar()
        
        # Permisos por categoría
        by_category = await self.db.execute(
            select(
                Permission.category,
                func.count(Permission.id).label('count')
            )
            .group_by(Permission.category)
            .order_by(Permission.category)
        )
        permissions_by_category = {row.category: row.count for row in by_category}
        
        return {
            "total_permissions": total_permissions,
            "active_permissions": active_permissions,
            "inactive_permissions": total_permissions - active_permissions,
            "permissions_by_category": permissions_by_category
        }
    
    async def get_role_stats(self) -> Dict[str, Any]:
        """
        Obtiene estadísticas de roles
        
        Returns:
            Diccionario con estadísticas
        """
        # Total de roles
        total = await self.db.execute(select(func.count(Role.id)))
        total_roles = total.scalar()
        
        # Roles de sistema
        system = await self.db.execute(
            select(func.count(Role.id)).where(Role.is_system == True)
        )
        system_roles = system.scalar()
        
        # Roles activos
        active = await self.db.execute(
            select(func.count(Role.id)).where(Role.is_active == True)
        )
        active_roles = active.scalar()
        
        # Usuarios por rol
        users_by_role = await self.db.execute(
            select(
                Role.name,
                func.count(User.id).label('count')
            )
            .join(User, User.role_id == Role.id, isouter=True)
            .group_by(Role.id, Role.name)
            .order_by(Role.name)
        )
        users_per_role = {row.name: row.count for row in users_by_role}
        
        return {
            "total_roles": total_roles,
            "system_roles": system_roles,
            "custom_roles": total_roles - system_roles,
            "active_roles": active_roles,
            "inactive_roles": total_roles - active_roles,
            "users_by_role": users_per_role
        }