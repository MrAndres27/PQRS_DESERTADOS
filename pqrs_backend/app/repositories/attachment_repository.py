"""
Repositorio de Archivos Adjuntos
Sistema PQRS - Equipo Desertados

Maneja todas las operaciones de acceso a datos para archivos adjuntos.
"""

from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from sqlalchemy.orm import selectinload

from app.models.file_attachment import FileAttachment


class AttachmentRepository:
    """Repositorio para operaciones de archivos adjuntos"""
    
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
    
    async def get_by_id(self, attachment_id: int) -> Optional[FileAttachment]:
        """
        Obtiene un archivo por ID
        
        Args:
            attachment_id: ID del archivo
            
        Returns:
            FileAttachment si existe, None si no
        """
        result = await self.db.execute(
            select(FileAttachment)
            .options(
                selectinload(FileAttachment.uploader),
                selectinload(FileAttachment.pqrs)
            )
            .where(FileAttachment.id == attachment_id)
        )
        return result.scalar_one_or_none()
    
    async def get_by_pqrs(
        self,
        pqrs_id: int,
        skip: int = 0,
        limit: int = 50
    ) -> List[FileAttachment]:
        """
        Obtiene archivos de una PQRS específica
        
        Args:
            pqrs_id: ID de la PQRS
            skip: Registros a saltar
            limit: Límite de resultados
            
        Returns:
            Lista de archivos
        """
        result = await self.db.execute(
            select(FileAttachment)
            .options(selectinload(FileAttachment.uploader))
            .where(FileAttachment.pqrs_id == pqrs_id)
            .order_by(FileAttachment.uploaded_at.desc())
            .offset(skip)
            .limit(limit)
        )
        return list(result.scalars().all())
    
    async def count_by_pqrs(self, pqrs_id: int) -> int:
        """
        Cuenta archivos de una PQRS
        
        Args:
            pqrs_id: ID de la PQRS
            
        Returns:
            Cantidad de archivos
        """
        result = await self.db.execute(
            select(func.count(FileAttachment.id)).where(
                FileAttachment.pqrs_id == pqrs_id
            )
        )
        return result.scalar() or 0
    
    async def get_by_user(
        self,
        user_id: int,
        skip: int = 0,
        limit: int = 50
    ) -> List[FileAttachment]:
        """
        Obtiene archivos subidos por un usuario
        
        Args:
            user_id: ID del usuario
            skip: Registros a saltar
            limit: Límite de resultados
            
        Returns:
            Lista de archivos
        """
        result = await self.db.execute(
            select(FileAttachment)
            .options(selectinload(FileAttachment.pqrs))
            .where(FileAttachment.uploaded_by == user_id)
            .order_by(FileAttachment.uploaded_at.desc())
            .offset(skip)
            .limit(limit)
        )
        return list(result.scalars().all())
    
    async def get_by_type(
        self,
        pqrs_id: int,
        mime_type_prefix: str
    ) -> List[FileAttachment]:
        """
        Obtiene archivos de un tipo específico de una PQRS
        
        Args:
            pqrs_id: ID de la PQRS
            mime_type_prefix: Prefijo del MIME type (ej: 'image/', 'application/pdf')
            
        Returns:
            Lista de archivos
        """
        result = await self.db.execute(
            select(FileAttachment)
            .where(
                FileAttachment.pqrs_id == pqrs_id,
                FileAttachment.mime_type.like(f"{mime_type_prefix}%")
            )
            .order_by(FileAttachment.uploaded_at.desc())
        )
        return list(result.scalars().all())
    
    async def get_total_size_by_pqrs(self, pqrs_id: int) -> int:
        """
        Calcula el tamaño total de archivos de una PQRS
        
        Args:
            pqrs_id: ID de la PQRS
            
        Returns:
            Tamaño total en bytes
        """
        result = await self.db.execute(
            select(func.sum(FileAttachment.file_size)).where(
                FileAttachment.pqrs_id == pqrs_id
            )
        )
        return result.scalar() or 0
    
    # =========================================================================
    # OPERACIONES DE ESCRITURA
    # =========================================================================
    
    async def create(self, attachment: FileAttachment) -> FileAttachment:
        """
        Crea un nuevo archivo adjunto
        
        Args:
            attachment: Objeto FileAttachment a crear
            
        Returns:
            Archivo creado con ID asignado
        """
        self.db.add(attachment)
        await self.db.flush()
        await self.db.refresh(attachment)
        
        # Cargar relaciones
        result = await self.db.execute(
            select(FileAttachment)
            .options(
                selectinload(FileAttachment.uploader),
                selectinload(FileAttachment.pqrs)
            )
            .where(FileAttachment.id == attachment.id)
        )
        return result.scalar_one()
    
    async def update(self, attachment: FileAttachment) -> FileAttachment:
        """
        Actualiza un archivo existente
        
        Args:
            attachment: Archivo con datos actualizados
            
        Returns:
            Archivo actualizado
        """
        await self.db.flush()
        await self.db.refresh(attachment)
        
        # Cargar relaciones
        result = await self.db.execute(
            select(FileAttachment)
            .options(
                selectinload(FileAttachment.uploader),
                selectinload(FileAttachment.pqrs)
            )
            .where(FileAttachment.id == attachment.id)
        )
        return result.scalar_one()
    
    async def delete(self, attachment_id: int) -> bool:
        """
        Elimina un archivo
        
        Args:
            attachment_id: ID del archivo a eliminar
            
        Returns:
            True si se eliminó, False si no existía
        """
        attachment = await self.get_by_id(attachment_id)
        
        if attachment is None:
            return False
        
        await self.db.delete(attachment)
        await self.db.flush()
        
        return True
    
    # =========================================================================
    # OPERACIONES DE VALIDACIÓN
    # =========================================================================
    
    async def exists(self, attachment_id: int) -> bool:
        """
        Verifica si un archivo existe
        
        Args:
            attachment_id: ID del archivo
            
        Returns:
            True si existe, False si no
        """
        result = await self.db.execute(
            select(func.count(FileAttachment.id)).where(
                FileAttachment.id == attachment_id
            )
        )
        count = result.scalar()
        return count > 0
    
    async def is_uploader(self, attachment_id: int, user_id: int) -> bool:
        """
        Verifica si un usuario es quien subió el archivo
        
        Args:
            attachment_id: ID del archivo
            user_id: ID del usuario
            
        Returns:
            True si es el uploader, False si no
        """
        result = await self.db.execute(
            select(func.count(FileAttachment.id)).where(
                FileAttachment.id == attachment_id,
                FileAttachment.uploaded_by == user_id
            )
        )
        count = result.scalar()
        return count > 0
    
    async def belongs_to_pqrs(self, attachment_id: int, pqrs_id: int) -> bool:
        """
        Verifica si un archivo pertenece a una PQRS
        
        Args:
            attachment_id: ID del archivo
            pqrs_id: ID de la PQRS
            
        Returns:
            True si pertenece, False si no
        """
        result = await self.db.execute(
            select(func.count(FileAttachment.id)).where(
                FileAttachment.id == attachment_id,
                FileAttachment.pqrs_id == pqrs_id
            )
        )
        count = result.scalar()
        return count > 0