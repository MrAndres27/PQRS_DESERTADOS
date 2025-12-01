"""
Router de Archivos Adjuntos
Sistema PQRS - Equipo Desertados

Endpoints para archivos adjuntos en PQRS:
- POST /pqrs/{id}/attachments - Subir archivo
- GET /pqrs/{id}/attachments - Listar archivos
- GET /attachments/{id} - Ver info del archivo
- GET /attachments/{id}/download - Descargar archivo
- PUT /attachments/{id}/description - Actualizar descripción
- DELETE /attachments/{id} - Eliminar archivo
- GET /pqrs/{id}/attachments/stats - Estadísticas de archivos
- GET /attachments/allowed-types - Tipos permitidos
"""

from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    status,
    UploadFile,
    File,
    Form
)
from fastapi.responses import FileResponse
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional
import math

from app.core.database import get_async_db
from app.core.dependencies import (
    get_current_user,
    get_pagination_params,
    PaginationParams
)
from app.services.attachment_service import AttachmentService, get_attachment_service
from app.models.user import User
from app.schemas.attachments import (
    AttachmentResponse,
    AttachmentPaginatedResponse,
    AttachmentStats,
    AttachmentUpdateDescription,
    AllowedFileTypes
)


# =============================================================================
# ROUTER
# =============================================================================

router = APIRouter(tags=["Archivos Adjuntos"])


# =============================================================================
# ENDPOINTS DE INFORMACIÓN
# =============================================================================

@router.get(
    "/attachments/allowed-types",
    response_model=AllowedFileTypes,
    status_code=status.HTTP_200_OK
)
async def get_allowed_file_types():
    """
    Obtiene información sobre los tipos de archivo permitidos
    
    **Información:**
    - Tipos de imágenes permitidas
    - Tipos de documentos permitidos
    - Tamaño máximo de archivo
    
    **No requiere autenticación**
    """
    return AllowedFileTypes()


# =============================================================================
# ENDPOINTS DE CONSULTA
# =============================================================================

@router.get(
    "/pqrs/{pqrs_id}/attachments",
    response_model=AttachmentPaginatedResponse,
    status_code=status.HTTP_200_OK
)
async def list_attachments_by_pqrs(
    pqrs_id: int,
    pagination: PaginationParams = Depends(get_pagination_params),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_db)
):
    """
    Lista todos los archivos adjuntos de una PQRS
    
    **Paginación:**
    - `skip`: Registros a saltar (default: 0)
    - `limit`: Límite de resultados (default: 50, max: 100)
    
    **Ordenamiento:** Del más reciente al más antiguo
    
    **Requiere:** Usuario autenticado
    """
    attachment_service = get_attachment_service(db)
    
    attachments, total = await attachment_service.list_attachments_by_pqrs(
        pqrs_id=pqrs_id,
        skip=pagination.skip,
        limit=pagination.limit
    )
    
    # Calcular paginación
    page = (pagination.skip // pagination.limit) + 1
    total_pages = math.ceil(total / pagination.limit) if total > 0 else 1
    
    return AttachmentPaginatedResponse(
        items=attachments,
        total=total,
        page=page,
        page_size=pagination.limit,
        total_pages=total_pages
    )


@router.get(
    "/pqrs/{pqrs_id}/attachments/stats",
    response_model=AttachmentStats,
    status_code=status.HTTP_200_OK
)
async def get_attachment_stats(
    pqrs_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_db)
):
    """
    Obtiene estadísticas de archivos de una PQRS
    
    Incluye:
    - Total de archivos
    - Tamaño total ocupado
    - Cantidad de imágenes
    - Cantidad de PDFs
    - Cantidad de documentos
    
    **Requiere:** Usuario autenticado
    """
    attachment_service = get_attachment_service(db)
    
    stats = await attachment_service.get_attachment_stats(pqrs_id=pqrs_id)
    
    return AttachmentStats(**stats)


@router.get(
    "/attachments/{attachment_id}",
    response_model=AttachmentResponse,
    status_code=status.HTTP_200_OK
)
async def get_attachment_by_id(
    attachment_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_db)
):
    """
    Obtiene información detallada de un archivo
    
    **No descarga el archivo**, solo retorna su metadata.
    
    **Requiere:** Usuario autenticado
    """
    attachment_service = get_attachment_service(db)
    
    attachment = await attachment_service.get_attachment_by_id(attachment_id)
    
    return attachment


# =============================================================================
# ENDPOINTS DE DESCARGA
# =============================================================================

@router.get(
    "/attachments/{attachment_id}/download",
    status_code=status.HTTP_200_OK
)
async def download_attachment(
    attachment_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_db)
):
    """
    Descarga un archivo adjunto
    
    Retorna el archivo con el nombre original y el tipo MIME correcto.
    
    **Headers de respuesta:**
    - `Content-Type`: Tipo MIME del archivo
    - `Content-Disposition`: attachment; filename="nombre_original.ext"
    
    **Requiere:** Usuario autenticado
    """
    attachment_service = get_attachment_service(db)
    
    # Obtener archivo
    attachment = await attachment_service.get_attachment_by_id(attachment_id)
    
    # Obtener ruta del archivo
    file_path = attachment_service.get_file_path(attachment)
    
    # Retornar archivo para descarga
    return FileResponse(
        path=file_path,
        media_type=attachment.mime_type,
        filename=attachment.original_filename
    )


# =============================================================================
# ENDPOINTS DE MODIFICACIÓN
# =============================================================================

@router.post(
    "/pqrs/{pqrs_id}/attachments",
    response_model=AttachmentResponse,
    status_code=status.HTTP_201_CREATED
)
async def upload_attachment(
    pqrs_id: int,
    file: UploadFile = File(..., description="Archivo a subir"),
    description: Optional[str] = Form(None, max_length=500, description="Descripción opcional"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_db)
):
    """
    Sube un archivo adjunto a una PQRS
    
    **Tipos permitidos:**
    - Imágenes: JPG, PNG, GIF, WEBP
    - Documentos: PDF, DOC, DOCX, XLS, XLSX
    - Texto: TXT
    
    **Tamaño máximo:** 10 MB
    
    **Validaciones:**
    - Tipo de archivo debe estar permitido
    - Tamaño no debe exceder el límite
    - PQRS debe existir
    - Archivo no debe estar vacío
    
    **Formato:** multipart/form-data
    
    **Requiere:** Usuario autenticado
    """
    attachment_service = get_attachment_service(db)
    
    new_attachment = await attachment_service.upload_attachment(
        pqrs_id=pqrs_id,
        file=file,
        description=description,
        uploaded_by=current_user.id,
        current_user=current_user
    )
    
    return new_attachment


@router.put(
    "/attachments/{attachment_id}/description",
    response_model=AttachmentResponse,
    status_code=status.HTTP_200_OK
)
async def update_attachment_description(
    attachment_id: int,
    data: AttachmentUpdateDescription,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_db)
):
    """
    Actualiza la descripción de un archivo
    
    **Restricciones:**
    - Solo quien subió el archivo puede actualizar la descripción
    - O un administrador
    
    **No se puede cambiar el archivo en sí**, solo su descripción.
    
    **Requiere:** Usuario autenticado y ser el uploader
    """
    attachment_service = get_attachment_service(db)
    
    updated_attachment = await attachment_service.update_description(
        attachment_id=attachment_id,
        description=data.description,
        current_user=current_user
    )
    
    return updated_attachment


@router.delete(
    "/attachments/{attachment_id}",
    status_code=status.HTTP_200_OK
)
async def delete_attachment(
    attachment_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_db)
):
    """
    Elimina un archivo adjunto
    
    **Restricciones:**
    - Solo quien subió el archivo puede eliminarlo
    - O un administrador
    
    **IMPORTANTE:** 
    - Esta acción no se puede deshacer
    - Se elimina tanto de la base de datos como del disco
    
    **Requiere:** Usuario autenticado y ser el uploader o admin
    """
    attachment_service = get_attachment_service(db)
    
    success = await attachment_service.delete_attachment(
        attachment_id=attachment_id,
        current_user=current_user
    )
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error al eliminar el archivo"
        )
    
    return {
        "message": "Archivo eliminado exitosamente",
        "attachment_id": attachment_id,
        "success": True
    }