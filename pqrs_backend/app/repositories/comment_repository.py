"""
Repositorio de Comentarios
Sistema PQRS - Equipo Desertados

Maneja todas las operaciones de acceso a datos para comentarios.
"""

from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from sqlalchemy.orm import selectinload

from app.models.pqrs_comment import PQRSComment


class CommentRepository:
    """Repositorio para operaciones de comentarios"""
    
    def __init__(self, db: AsyncSession):
        """
        Inicializa el repositorio
        
        Args:
            db: Sesión asíncrona de SQLAlchemy
        """
        self.db = db
    
    # =========================================================================
    # OPERACIONES DE LECTURA
    # =========================================================================
    
    async def get_by_id(self, comment_id: int) -> Optional[PQRSComment]:
        """
        Obtiene un comentario por ID
        
        Args:
            comment_id: ID del comentario
            
        Returns:
            Comentario si existe, None si no
        """
        result = await self.db.execute(
            select(PQRSComment)
            .options(
                selectinload(PQRSComment.author),
                selectinload(PQRSComment.pqrs)
            )
            .where(PQRSComment.id == comment_id)
        )
        return result.scalar_one_or_none()
    
    async def get_by_pqrs(
        self,
        pqrs_id: int,
        include_internal: bool = True,
        skip: int = 0,
        limit: int = 50
    ) -> List[PQRSComment]:
        """
        Obtiene comentarios de una PQRS específica
        
        Args:
            pqrs_id: ID de la PQRS
            include_internal: Si incluir comentarios internos
            skip: Registros a saltar
            limit: Límite de resultados
            
        Returns:
            Lista de comentarios
        """
        query = select(PQRSComment).options(
            selectinload(PQRSComment.author)
        ).where(PQRSComment.pqrs_id == pqrs_id)
        
        # Filtrar comentarios internos si no se requieren
        if not include_internal:
            query = query.where(PQRSComment.is_internal == False)
        
        # Ordenar por fecha (más recientes primero)
        query = query.order_by(PQRSComment.created_at.desc())
        
        # Paginación
        query = query.offset(skip).limit(limit)
        
        result = await self.db.execute(query)
        return list(result.scalars().all())
    
    async def count_by_pqrs(
        self,
        pqrs_id: int,
        include_internal: bool = True
    ) -> int:
        """
        Cuenta comentarios de una PQRS
        
        Args:
            pqrs_id: ID de la PQRS
            include_internal: Si incluir comentarios internos
            
        Returns:
            Cantidad de comentarios
        """
        query = select(func.count(PQRSComment.id)).where(
            PQRSComment.pqrs_id == pqrs_id
        )
        
        if not include_internal:
            query = query.where(PQRSComment.is_internal == False)
        
        result = await self.db.execute(query)
        return result.scalar() or 0
    
    async def get_by_user(
        self,
        user_id: int,
        skip: int = 0,
        limit: int = 50
    ) -> List[PQRSComment]:
        """
        Obtiene comentarios de un usuario
        
        Args:
            user_id: ID del usuario
            skip: Registros a saltar
            limit: Límite de resultados
            
        Returns:
            Lista de comentarios
        """
        result = await self.db.execute(
            select(PQRSComment)
            .options(
                selectinload(PQRSComment.pqrs)
            )
            .where(PQRSComment.user_id == user_id)
            .order_by(PQRSComment.created_at.desc())
            .offset(skip)
            .limit(limit)
        )
        return list(result.scalars().all())
    
    # =========================================================================
    # OPERACIONES DE ESCRITURA
    # =========================================================================
    
    async def create(self, comment: PQRSComment) -> PQRSComment:
        """
        Crea un nuevo comentario
        
        Args:
            comment: Objeto PQRSComment a crear
            
        Returns:
            Comentario creado con ID asignado
        """
        self.db.add(comment)
        await self.db.flush()
        await self.db.refresh(comment)
        
        # Cargar relaciones
        result = await self.db.execute(
            select(PQRSComment)
            .options(
                selectinload(PQRSComment.author),
                selectinload(PQRSComment.pqrs)
            )
            .where(PQRSComment.id == comment.id)
        )
        return result.scalar_one()
    
    async def update(self, comment: PQRSComment) -> PQRSComment:
        """
        Actualiza un comentario existente
        
        Args:
            comment: Comentario con datos actualizados
            
        Returns:
            Comentario actualizado
        """
        await self.db.flush()
        await self.db.refresh(comment)
        
        # Cargar relaciones
        result = await self.db.execute(
            select(PQRSComment)
            .options(
                selectinload(PQRSComment.author),
                selectinload(PQRSComment.pqrs)
            )
            .where(PQRSComment.id == comment.id)
        )
        return result.scalar_one()
    
    async def delete(self, comment_id: int) -> bool:
        """
        Elimina un comentario
        
        Args:
            comment_id: ID del comentario a eliminar
            
        Returns:
            True si se eliminó, False si no existía
        """
        comment = await self.get_by_id(comment_id)
        
        if comment is None:
            return False
        
        await self.db.delete(comment)
        await self.db.flush()
        
        return True
    
    # =========================================================================
    # OPERACIONES DE VALIDACIÓN
    # =========================================================================
    
    async def exists(self, comment_id: int) -> bool:
        """
        Verifica si un comentario existe
        
        Args:
            comment_id: ID del comentario
            
        Returns:
            True si existe, False si no
        """
        result = await self.db.execute(
            select(func.count(PQRSComment.id)).where(
                PQRSComment.id == comment_id
            )
        )
        count = result.scalar()
        return count > 0
    
    async def is_author(self, comment_id: int, user_id: int) -> bool:
        """
        Verifica si un usuario es el autor de un comentario
        
        Args:
            comment_id: ID del comentario
            user_id: ID del usuario
            
        Returns:
            True si es el autor, False si no
        """
        result = await self.db.execute(
            select(func.count(PQRSComment.id)).where(
                PQRSComment.id == comment_id,
                PQRSComment.user_id == user_id
            )
        )
        count = result.scalar()
        return count > 0