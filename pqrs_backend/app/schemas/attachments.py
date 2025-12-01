"""
Schemas de Archivos Adjuntos
Sistema PQRS - Equipo Desertados

Schemas para validación y serialización de archivos adjuntos.
"""

from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional, List


# =============================================================================
# SCHEMAS BASE
# =============================================================================

class AttachmentBase(BaseModel):
    """Schema base para archivos adjuntos"""
    description: Optional[str] = Field(
        default=None,
        max_length=500,
        description="Descripción opcional del archivo"
    )


# =============================================================================
# SCHEMAS DE CREACIÓN Y ACTUALIZACIÓN
# =============================================================================

class AttachmentUpload(AttachmentBase):
    """Schema para subir archivo (form data)"""
    # El archivo se sube como multipart/form-data
    # Este schema solo maneja la descripción opcional
    pass


class AttachmentUpdateDescription(BaseModel):
    """Schema para actualizar descripción"""
    description: str = Field(
        ...,
        max_length=500,
        description="Nueva descripción del archivo"
    )
    
    class Config:
        json_schema_extra = {
            "example": {
                "description": "Cédula de ciudadanía - Frente y reverso"
            }
        }


# =============================================================================
# SCHEMAS DE RESPUESTA
# =============================================================================

class UserBasicResponse(BaseModel):
    """Schema básico de usuario"""
    id: int
    username: str
    full_name: str
    
    class Config:
        from_attributes = True


class AttachmentResponse(BaseModel):
    """Schema de respuesta de archivo adjunto"""
    id: int
    pqrs_id: int
    uploaded_by: int
    uploader: UserBasicResponse
    original_filename: str
    stored_filename: str
    file_size: int
    file_size_human: str
    mime_type: str
    file_extension: str
    description: Optional[str]
    is_image: bool
    is_pdf: bool
    is_document: bool
    uploaded_at: datetime
    
    class Config:
        from_attributes = True
        json_schema_extra = {
            "example": {
                "id": 1,
                "pqrs_id": 5,
                "uploaded_by": 2,
                "uploader": {
                    "id": 2,
                    "username": "ciudadano1",
                    "full_name": "Juan Pérez"
                },
                "original_filename": "cedula_frente.jpg",
                "stored_filename": "a1b2c3d4_cedula_frente.jpg",
                "file_size": 524288,
                "file_size_human": "512.0 KB",
                "mime_type": "image/jpeg",
                "file_extension": "jpg",
                "description": "Cédula de ciudadanía - Frente",
                "is_image": True,
                "is_pdf": False,
                "is_document": False,
                "uploaded_at": "2024-11-24T14:30:00"
            }
        }


class AttachmentListResponse(BaseModel):
    """Schema simplificado para listados"""
    id: int
    original_filename: str
    file_size_human: str
    mime_type: str
    description: Optional[str]
    uploaded_at: datetime
    
    class Config:
        from_attributes = True


# =============================================================================
# SCHEMAS DE PAGINACIÓN
# =============================================================================

class AttachmentPaginatedResponse(BaseModel):
    """Response paginada de archivos"""
    items: List[AttachmentResponse]
    total: int
    page: int
    page_size: int
    total_pages: int
    
    class Config:
        json_schema_extra = {
            "example": {
                "items": [],
                "total": 5,
                "page": 1,
                "page_size": 10,
                "total_pages": 1
            }
        }


# =============================================================================
# SCHEMAS DE ESTADÍSTICAS
# =============================================================================

class AttachmentStats(BaseModel):
    """Estadísticas de archivos de una PQRS"""
    total_files: int = Field(description="Total de archivos")
    total_size_bytes: int = Field(description="Tamaño total en bytes")
    total_size_human: str = Field(description="Tamaño total legible")
    images: int = Field(description="Cantidad de imágenes")
    pdfs: int = Field(description="Cantidad de PDFs")
    documents: int = Field(description="Cantidad de documentos (Word, Excel, etc.)")
    
    class Config:
        json_schema_extra = {
            "example": {
                "total_files": 8,
                "total_size_bytes": 5242880,
                "total_size_human": "5.0 MB",
                "images": 4,
                "pdfs": 3,
                "documents": 1
            }
        }


# =============================================================================
# SCHEMAS DE INFORMACIÓN
# =============================================================================

class AllowedFileTypes(BaseModel):
    """Información sobre tipos de archivo permitidos"""
    images: List[str] = ["JPG", "PNG", "GIF", "WEBP"]
    documents: List[str] = ["PDF", "DOC", "DOCX", "XLS", "XLSX"]
    text: List[str] = ["TXT"]
    max_size_mb: float = 10.0
    
    class Config:
        json_schema_extra = {
            "example": {
                "images": ["JPG", "PNG", "GIF", "WEBP"],
                "documents": ["PDF", "DOC", "DOCX", "XLS", "XLSX"],
                "text": ["TXT"],
                "max_size_mb": 10.0
            }
        }