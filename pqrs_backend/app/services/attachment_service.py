"""
Servicio de Archivos Adjuntos
Sistema PQRS - Equipo Desertados

Maneja toda la lógica de negocio para:
- Subir archivos a PQRS
- Listar y descargar archivos
- Eliminar archivos
- Validaciones y permisos
"""

from typing import List, Optional, Dict, Any
from fastapi import HTTPException, status, UploadFile
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from pathlib import Path

from app.models.file_attachment import FileAttachment
from app.models.pqrs import PQRS
from app.models.user import User
from app.repositories.attachment_repository import AttachmentRepository
from app.utils.file_utils import (
    save_upload_file,
    delete_file,
    validate_file_type,
    validate_file_size,
    get_file_info
)


class AttachmentService:
    """Servicio para gestión de archivos adjuntos"""
    
    def __init__(self, db: AsyncSession):
        """
        Inicializa el servicio con la sesión de BD
        
        Args:
            db: Sesión asíncrona de SQLAlchemy
        """
        self.db = db
        self.attachment_repo = AttachmentRepository(db)
    
    # =========================================================================
    # OPERACIONES DE CONSULTA
    # =========================================================================
    
    async def get_attachment_by_id(
        self,
        attachment_id: int
    ) -> FileAttachment:
        """
        Obtiene un archivo por ID
        
        Args:
            attachment_id: ID del archivo
            
        Returns:
            Archivo encontrado
            
        Raises:
            HTTPException 404: Si no existe
        """
        attachment = await self.attachment_repo.get_by_id(attachment_id)
        
        if attachment is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Archivo con ID {attachment_id} no encontrado"
            )
        
        return attachment
    
    async def list_attachments_by_pqrs(
        self,
        pqrs_id: int,
        skip: int = 0,
        limit: int = 50
    ) -> tuple[List[FileAttachment], int]:
        """
        Lista archivos de una PQRS
        
        Args:
            pqrs_id: ID de la PQRS
            skip: Registros a saltar
            limit: Límite de resultados
            
        Returns:
            Tupla (lista_archivos, total_count)
        """
        # Verificar que la PQRS existe
        await self._verify_pqrs_exists(pqrs_id)
        
        # Obtener archivos
        attachments = await self.attachment_repo.get_by_pqrs(
            pqrs_id=pqrs_id,
            skip=skip,
            limit=limit
        )
        
        # Contar total
        total = await self.attachment_repo.count_by_pqrs(pqrs_id)
        
        return attachments, total
    
    async def get_attachment_stats(
        self,
        pqrs_id: int
    ) -> Dict[str, Any]:
        """
        Obtiene estadísticas de archivos de una PQRS
        
        Args:
            pqrs_id: ID de la PQRS
            
        Returns:
            Dict con estadísticas
        """
        # Contar total
        total = await self.attachment_repo.count_by_pqrs(pqrs_id)
        
        # Calcular tamaño total
        total_size = await self.attachment_repo.get_total_size_by_pqrs(pqrs_id)
        
        # Contar por tipo
        images = await self.attachment_repo.get_by_type(pqrs_id, "image/")
        pdfs = await self.attachment_repo.get_by_type(pqrs_id, "application/pdf")
        
        return {
            "total_files": total,
            "total_size_bytes": total_size,
            "total_size_human": self._format_size(total_size),
            "images": len(images),
            "pdfs": len(pdfs),
            "documents": total - len(images) - len(pdfs)
        }
    
    # =========================================================================
    # OPERACIONES DE MODIFICACIÓN
    # =========================================================================
    
    async def upload_attachment(
        self,
        pqrs_id: int,
        file: UploadFile,
        description: Optional[str],
        uploaded_by: int,
        current_user: User
    ) -> FileAttachment:
        """
        Sube un archivo adjunto a una PQRS
        
        Args:
            pqrs_id: ID de la PQRS
            file: Archivo a subir
            description: Descripción opcional
            uploaded_by: ID del usuario que sube
            current_user: Usuario actual
            
        Returns:
            Archivo creado
            
        Raises:
            HTTPException 404: Si la PQRS no existe
            HTTPException 400: Si el archivo no es válido
        """
        # Verificar que la PQRS existe
        await self._verify_pqrs_exists(pqrs_id)
        
        # Validar que el usuario actual es quien sube
        if uploaded_by != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="No puedes subir archivos en nombre de otro usuario"
            )
        
        # Guardar archivo en disco
        stored_filename, file_path, file_size = await save_upload_file(file)
        
        # Obtener MIME type y extensión
        mime_type, extension = validate_file_type(file)
        
        # Crear registro en BD
        try:
            new_attachment = FileAttachment(
                pqrs_id=pqrs_id,
                uploaded_by=uploaded_by,
                original_filename=file.filename,
                stored_filename=stored_filename,
                file_path=file_path,
                file_size=file_size,
                mime_type=mime_type,
                file_extension=extension.lstrip('.'),
                description=description
            )
            
            created_attachment = await self.attachment_repo.create(new_attachment)
            await self.db.commit()
            
            return created_attachment
        
        except Exception as e:
            # Si falla la BD, eliminar archivo del disco
            delete_file(file_path)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error al registrar el archivo: {str(e)}"
            )
    
    async def update_description(
        self,
        attachment_id: int,
        description: str,
        current_user: User
    ) -> FileAttachment:
        """
        Actualiza la descripción de un archivo
        
        Args:
            attachment_id: ID del archivo
            description: Nueva descripción
            current_user: Usuario actual
            
        Returns:
            Archivo actualizado
        """
        # Obtener archivo
        attachment = await self.get_attachment_by_id(attachment_id)
        
        # Verificar que es el uploader o admin
        if not await self._is_uploader_or_admin(attachment_id, current_user):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Solo quien subió el archivo puede modificar su descripción"
            )
        
        # Actualizar
        attachment.description = description
        
        updated_attachment = await self.attachment_repo.update(attachment)
        await self.db.commit()
        
        return updated_attachment
    
    async def delete_attachment(
        self,
        attachment_id: int,
        current_user: User
    ) -> bool:
        """
        Elimina un archivo (de BD y disco)
        
        Args:
            attachment_id: ID del archivo
            current_user: Usuario actual
            
        Returns:
            True si se eliminó correctamente
        """
        # Obtener archivo
        attachment = await self.get_attachment_by_id(attachment_id)
        
        # Verificar que es el uploader o admin
        if not await self._is_uploader_or_admin(attachment_id, current_user):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Solo quien subió el archivo o un administrador pueden eliminarlo"
            )
        
        # Guardar ruta antes de eliminar de BD
        file_path = attachment.file_path
        
        # Eliminar de BD
        success = await self.attachment_repo.delete(attachment_id)
        await self.db.commit()
        
        # Eliminar archivo del disco
        if success:
            delete_file(file_path)
        
        return success
    
    # =========================================================================
    # OPERACIONES DE DESCARGA
    # =========================================================================
    
    def get_file_path(self, attachment: FileAttachment) -> Path:
        """
        Obtiene la ruta del archivo en disco
        
        Args:
            attachment: Archivo adjunto
            
        Returns:
            Path del archivo
            
        Raises:
            HTTPException 404: Si el archivo no existe en disco
        """
        file_path = Path(attachment.file_path)
        
        if not file_path.exists():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="El archivo no existe en el disco. Puede haber sido eliminado."
            )
        
        return file_path
    
    # =========================================================================
    # VALIDACIONES Y PERMISOS
    # =========================================================================
    
    async def _verify_pqrs_exists(self, pqrs_id: int) -> None:
        """
        Verifica que una PQRS existe
        
        Args:
            pqrs_id: ID de la PQRS
            
        Raises:
            HTTPException 404: Si no existe
        """
        result = await self.db.execute(
            select(PQRS).where(PQRS.id == pqrs_id)
        )
        pqrs = result.scalar_one_or_none()
        
        if pqrs is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"PQRS con ID {pqrs_id} no encontrada"
            )
    
    async def _is_uploader_or_admin(
        self,
        attachment_id: int,
        user: User
    ) -> bool:
        """
        Verifica si un usuario es quien subió el archivo o es admin
        
        Args:
            attachment_id: ID del archivo
            user: Usuario a verificar
            
        Returns:
            True si es uploader o admin
        """
        # Verificar si es admin
        if hasattr(user, 'role') and user.role:
            if user.role.name == 'Administrador':
                return True
        
        # Verificar si es el uploader
        return await self.attachment_repo.is_uploader(attachment_id, user.id)
    
    # =========================================================================
    # HELPERS
    # =========================================================================
    
    def _format_size(self, size_bytes: int) -> str:
        """Formatea tamaño en formato legible"""
        for unit in ['B', 'KB', 'MB', 'GB']:
            if size_bytes < 1024.0:
                return f"{size_bytes:.1f} {unit}"
            size_bytes /= 1024.0
        return f"{size_bytes:.1f} TB"


# =============================================================================
# FUNCIÓN HELPER
# =============================================================================

def get_attachment_service(db: AsyncSession) -> AttachmentService:
    """
    Factory function para obtener una instancia del AttachmentService
    
    Args:
        db: Sesión de base de datos
        
    Returns:
        Instancia de AttachmentService
    """
    return AttachmentService(db)