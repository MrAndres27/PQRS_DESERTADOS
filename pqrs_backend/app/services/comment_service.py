"""
Servicio de Comentarios
Sistema PQRS - Equipo Desertados

Maneja toda la lógica de negocio para:
- Crear comentarios en PQRS
- Listar comentarios (públicos e internos)
- Editar y eliminar comentarios
- Validaciones de permisos
"""

from typing import List, Optional, Dict, Any
from datetime import datetime
from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.pqrs_comment import PQRSComment
from app.models.pqrs import PQRS
from app.models.user import User
from app.repositories.comment_repository import CommentRepository


class CommentService:
    """Servicio para gestión de comentarios"""
    
    def __init__(self, db: AsyncSession):
        """
        Inicializa el servicio con la sesión de BD
        
        Args:
            db: Sesión asíncrona de SQLAlchemy
        """
        self.db = db
        self.comment_repo = CommentRepository(db)
    
    # =========================================================================
    # OPERACIONES DE CONSULTA
    # =========================================================================
    
    async def get_comment_by_id(
        self,
        comment_id: int,
        current_user: User
    ) -> PQRSComment:
        """
        Obtiene un comentario por ID
        
        Args:
            comment_id: ID del comentario
            current_user: Usuario actual (para validar acceso a internos)
            
        Returns:
            Comentario encontrado
            
        Raises:
            HTTPException 404: Si no existe
            HTTPException 403: Si es interno y no tiene permiso
        """
        comment = await self.comment_repo.get_by_id(comment_id)
        
        if comment is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Comentario con ID {comment_id} no encontrado"
            )
        
        # Verificar acceso a comentarios internos
        if comment.is_internal:
            # Solo gestores/admins pueden ver comentarios internos
            if not self._can_view_internal(current_user):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="No tienes permiso para ver comentarios internos"
                )
        
        return comment
    
    async def list_comments_by_pqrs(
        self,
        pqrs_id: int,
        current_user: User,
        skip: int = 0,
        limit: int = 50
    ) -> tuple[List[PQRSComment], int]:
        """
        Lista comentarios de una PQRS
        
        Args:
            pqrs_id: ID de la PQRS
            current_user: Usuario actual
            skip: Registros a saltar
            limit: Límite de resultados
            
        Returns:
            Tupla (lista_comentarios, total_count)
        """
        # Verificar que la PQRS existe
        await self._verify_pqrs_exists(pqrs_id)
        
        # Determinar si puede ver comentarios internos
        include_internal = self._can_view_internal(current_user)
        
        # Obtener comentarios
        comments = await self.comment_repo.get_by_pqrs(
            pqrs_id=pqrs_id,
            include_internal=include_internal,
            skip=skip,
            limit=limit
        )
        
        # Contar total
        total = await self.comment_repo.count_by_pqrs(
            pqrs_id=pqrs_id,
            include_internal=include_internal
        )
        
        return comments, total
    
    async def list_my_comments(
        self,
        user_id: int,
        skip: int = 0,
        limit: int = 50
    ) -> tuple[List[PQRSComment], int]:
        """
        Lista comentarios del usuario actual
        
        Args:
            user_id: ID del usuario
            skip: Registros a saltar
            limit: Límite de resultados
            
        Returns:
            Tupla (lista_comentarios, total_count)
        """
        comments = await self.comment_repo.get_by_user(
            user_id=user_id,
            skip=skip,
            limit=limit
        )
        
        # Para el total, hacemos una consulta adicional
        # (en producción, esto debería optimizarse)
        total = len(comments)
        
        return comments, total
    
    # =========================================================================
    # OPERACIONES DE MODIFICACIÓN
    # =========================================================================
    
    async def create_comment(
        self,
        pqrs_id: int,
        content: str,
        is_internal: bool,
        author_id: int,
        current_user: User
    ) -> PQRSComment:
        """
        Crea un nuevo comentario
        
        Args:
            pqrs_id: ID de la PQRS
            content: Contenido del comentario
            is_internal: Si es comentario interno
            author_id: ID del autor
            current_user: Usuario actual (para validación)
            
        Returns:
            Comentario creado
            
        Raises:
            HTTPException 404: Si la PQRS no existe
            HTTPException 403: Si intenta crear comentario interno sin permiso
        """
        # Verificar que la PQRS existe
        await self._verify_pqrs_exists(pqrs_id)
        
        # Validar que el usuario actual es el autor
        if author_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="No puedes crear comentarios en nombre de otro usuario"
            )
        
        # Validar que puede crear comentarios internos
        if is_internal and not self._can_create_internal(current_user):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="No tienes permiso para crear comentarios internos"
            )
        
        # Validar longitud del contenido
        if len(content.strip()) < 1:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="El comentario no puede estar vacío"
            )
        
        if len(content) > 5000:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="El comentario no puede exceder 5000 caracteres"
            )
        
        # Crear comentario
        new_comment = PQRSComment(
            pqrs_id=pqrs_id,
            user_id=author_id,
            content=content.strip(),
            is_internal=is_internal
        )
        
        created_comment = await self.comment_repo.create(new_comment)
        await self.db.commit()
        
        return created_comment
    
    async def update_comment(
        self,
        comment_id: int,
        content: str,
        current_user: User
    ) -> PQRSComment:
        """
        Actualiza un comentario existente
        
        Args:
            comment_id: ID del comentario
            content: Nuevo contenido
            current_user: Usuario actual
            
        Returns:
            Comentario actualizado
            
        Raises:
            HTTPException 404: Si no existe
            HTTPException 403: Si no es el autor
        """
        # Obtener comentario
        comment = await self.get_comment_by_id(comment_id, current_user)
        
        # Verificar que es el autor
        if not await self._is_author_or_admin(comment_id, current_user):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Solo el autor puede editar este comentario"
            )
        
        # Validar longitud del contenido
        if len(content.strip()) < 1:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="El comentario no puede estar vacío"
            )
        
        if len(content) > 5000:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="El comentario no puede exceder 5000 caracteres"
            )
        
        # Actualizar
        comment.content = content.strip()
        comment.updated_at = datetime.utcnow()
        
        updated_comment = await self.comment_repo.update(comment)
        await self.db.commit()
        
        return updated_comment
    
    async def delete_comment(
        self,
        comment_id: int,
        current_user: User
    ) -> bool:
        """
        Elimina un comentario
        
        Args:
            comment_id: ID del comentario
            current_user: Usuario actual
            
        Returns:
            True si se eliminó correctamente
            
        Raises:
            HTTPException 404: Si no existe
            HTTPException 403: Si no es el autor o admin
        """
        # Obtener comentario
        comment = await self.get_comment_by_id(comment_id, current_user)
        
        # Verificar que es el autor o admin
        if not await self._is_author_or_admin(comment_id, current_user):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Solo el autor o un administrador pueden eliminar este comentario"
            )
        
        # Eliminar
        success = await self.comment_repo.delete(comment_id)
        await self.db.commit()
        
        return success
    
    # =========================================================================
    # VALIDACIONES Y PERMISOS
    # =========================================================================
    
    def _can_view_internal(self, user: User) -> bool:
        """
        Verifica si un usuario puede ver comentarios internos
        
        Args:
            user: Usuario a verificar
            
        Returns:
            True si puede ver internos
        """
        # Verificar si el usuario tiene un rol de gestor o superior
        # Puedes ajustar esta lógica según tus roles
        if hasattr(user, 'role') and user.role:
            allowed_roles = ['Administrador', 'Gestor', 'Supervisor']
            return user.role.name in allowed_roles
        return False
    
    def _can_create_internal(self, user: User) -> bool:
        """
        Verifica si un usuario puede crear comentarios internos
        
        Args:
            user: Usuario a verificar
            
        Returns:
            True si puede crear internos
        """
        # Misma lógica que ver internos
        return self._can_view_internal(user)
    
    async def _is_author_or_admin(
        self,
        comment_id: int,
        user: User
    ) -> bool:
        """
        Verifica si un usuario es el autor o admin
        
        Args:
            comment_id: ID del comentario
            user: Usuario a verificar
            
        Returns:
            True si es autor o admin
        """
        # Verificar si es admin
        if hasattr(user, 'role') and user.role:
            if user.role.name == 'Administrador':
                return True
        
        # Verificar si es el autor
        return await self.comment_repo.is_author(comment_id, user.id)
    
    async def _verify_pqrs_exists(self, pqrs_id: int) -> None:
        """
        Verifica que una PQRS existe
        
        Args:
            pqrs_id: ID de la PQRS
            
        Raises:
            HTTPException 404: Si no existe
        """
        from sqlalchemy import select
        
        result = await self.db.execute(
            select(PQRS).where(PQRS.id == pqrs_id)
        )
        pqrs = result.scalar_one_or_none()
        
        if pqrs is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"PQRS con ID {pqrs_id} no encontrada"
            )
    
    # =========================================================================
    # ESTADÍSTICAS
    # =========================================================================
    
    async def get_comment_stats_by_pqrs(
        self,
        pqrs_id: int,
        current_user: User
    ) -> Dict[str, Any]:
        """
        Obtiene estadísticas de comentarios de una PQRS
        
        Args:
            pqrs_id: ID de la PQRS
            current_user: Usuario actual
            
        Returns:
            Dict con estadísticas
        """
        include_internal = self._can_view_internal(current_user)
        
        total = await self.comment_repo.count_by_pqrs(
            pqrs_id=pqrs_id,
            include_internal=include_internal
        )
        
        public_count = await self.comment_repo.count_by_pqrs(
            pqrs_id=pqrs_id,
            include_internal=False
        )
        
        internal_count = total - public_count if include_internal else 0
        
        return {
            "total": total,
            "public": public_count,
            "internal": internal_count if include_internal else None
        }


# =============================================================================
# FUNCIÓN HELPER
# =============================================================================

def get_comment_service(db: AsyncSession) -> CommentService:
    """
    Factory function para obtener una instancia del CommentService
    
    Args:
        db: Sesión de base de datos
        
    Returns:
        Instancia de CommentService
    """
    return CommentService(db)