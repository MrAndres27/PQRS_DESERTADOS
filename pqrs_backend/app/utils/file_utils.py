"""
Utilidades para Manejo de Archivos
Sistema PQRS - Equipo Desertados

Funciones helper para guardar, validar y eliminar archivos.
"""

import os
import uuid
import mimetypes
from pathlib import Path
from typing import Tuple, Optional
from fastapi import UploadFile, HTTPException, status


# =============================================================================
# CONFIGURACIÓN
# =============================================================================

# Tipos de archivo permitidos
ALLOWED_MIME_TYPES = {
    # Imágenes
    'image/jpeg': '.jpg',
    'image/png': '.png',
    'image/gif': '.gif',
    'image/webp': '.webp',
    # PDFs
    'application/pdf': '.pdf',
    # Word
    'application/msword': '.doc',
    'application/vnd.openxmlformats-officedocument.wordprocessingml.document': '.docx',
    # Excel
    'application/vnd.ms-excel': '.xls',
    'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet': '.xlsx',
    # Texto
    'text/plain': '.txt',
}

# Tamaño máximo de archivo (10 MB por defecto)
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10 MB en bytes

# Directorio base para almacenar archivos
UPLOAD_DIR = Path("uploads/pqrs_attachments")


# =============================================================================
# INICIALIZACIÓN
# =============================================================================

def ensure_upload_directory():
    """Asegura que el directorio de uploads existe"""
    UPLOAD_DIR.mkdir(parents=True, exist_ok=True)


# =============================================================================
# VALIDACIONES
# =============================================================================

def validate_file_type(file: UploadFile) -> Tuple[str, str]:
    """
    Valida el tipo de archivo
    
    Args:
        file: Archivo subido
        
    Returns:
        Tupla (mime_type, extension)
        
    Raises:
        HTTPException 400: Si el tipo no es permitido
    """
    # Obtener MIME type del archivo
    mime_type = file.content_type
    
    # Validar que el MIME type está permitido
    if mime_type not in ALLOWED_MIME_TYPES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Tipo de archivo no permitido: {mime_type}. "
                   f"Tipos permitidos: PDF, imágenes (JPG, PNG, GIF, WEBP), "
                   f"Word (DOC, DOCX), Excel (XLS, XLSX), texto (TXT)"
        )
    
    # Obtener extensión esperada
    extension = ALLOWED_MIME_TYPES[mime_type]
    
    # Verificar que la extensión del nombre coincide (opcional, más seguro)
    filename_extension = Path(file.filename).suffix.lower()
    if filename_extension and filename_extension != extension:
        # Si la extensión no coincide, usar la del MIME type
        pass
    
    return mime_type, extension


def validate_file_size(file: UploadFile) -> int:
    """
    Valida el tamaño del archivo
    
    Args:
        file: Archivo subido
        
    Returns:
        Tamaño del archivo en bytes
        
    Raises:
        HTTPException 400: Si el archivo es muy grande
    """
    # Leer el archivo para obtener el tamaño
    file.file.seek(0, 2)  # Ir al final del archivo
    file_size = file.file.tell()  # Obtener posición (tamaño)
    file.file.seek(0)  # Volver al inicio
    
    # Validar tamaño máximo
    if file_size > MAX_FILE_SIZE:
        size_mb = file_size / (1024 * 1024)
        max_mb = MAX_FILE_SIZE / (1024 * 1024)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Archivo muy grande: {size_mb:.1f} MB. "
                   f"Tamaño máximo permitido: {max_mb:.1f} MB"
        )
    
    # Validar que no esté vacío
    if file_size == 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="El archivo está vacío"
        )
    
    return file_size


# =============================================================================
# OPERACIONES DE ARCHIVO
# =============================================================================

def generate_unique_filename(original_filename: str, extension: str) -> str:
    """
    Genera un nombre único para el archivo
    
    Args:
        original_filename: Nombre original del archivo
        extension: Extensión del archivo
        
    Returns:
        Nombre único para almacenar
    """
    # Generar UUID único
    unique_id = uuid.uuid4().hex
    
    # Limpiar nombre original (solo alfanuméricos)
    clean_name = "".join(c for c in Path(original_filename).stem if c.isalnum() or c in (' ', '-', '_'))
    clean_name = clean_name[:50]  # Limitar longitud
    
    # Formato: uuid_nombreoriginal.ext
    if clean_name:
        return f"{unique_id}_{clean_name}{extension}"
    else:
        return f"{unique_id}{extension}"


async def save_upload_file(file: UploadFile) -> Tuple[str, str, int]:
    """
    Guarda un archivo subido en disco
    
    Args:
        file: Archivo a guardar
        
    Returns:
        Tupla (stored_filename, file_path, file_size)
        
    Raises:
        HTTPException: Si hay error al guardar
    """
    # Asegurar que el directorio existe
    ensure_upload_directory()
    
    # Validar tipo y tamaño
    mime_type, extension = validate_file_type(file)
    file_size = validate_file_size(file)
    
    # Generar nombre único
    stored_filename = generate_unique_filename(file.filename, extension)
    file_path = UPLOAD_DIR / stored_filename
    
    # Guardar archivo
    try:
        with open(file_path, "wb") as f:
            # Leer en chunks para archivos grandes
            chunk_size = 1024 * 1024  # 1 MB
            while True:
                chunk = await file.read(chunk_size)
                if not chunk:
                    break
                f.write(chunk)
        
        return stored_filename, str(file_path), file_size
    
    except Exception as e:
        # Si falla, eliminar archivo parcial si existe
        if file_path.exists():
            file_path.unlink()
        
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al guardar el archivo: {str(e)}"
        )


def delete_file(file_path: str) -> bool:
    """
    Elimina un archivo del disco
    
    Args:
        file_path: Ruta del archivo a eliminar
        
    Returns:
        True si se eliminó, False si no existía
    """
    try:
        path = Path(file_path)
        if path.exists():
            path.unlink()
            return True
        return False
    except Exception as e:
        # Log error pero no fallar
        print(f"Error al eliminar archivo {file_path}: {e}")
        return False


def get_file_info(file_path: str) -> Optional[dict]:
    """
    Obtiene información de un archivo
    
    Args:
        file_path: Ruta del archivo
        
    Returns:
        Dict con info o None si no existe
    """
    try:
        path = Path(file_path)
        if not path.exists():
            return None
        
        stat = path.stat()
        
        return {
            "exists": True,
            "size": stat.st_size,
            "created": datetime.fromtimestamp(stat.st_ctime),
            "modified": datetime.fromtimestamp(stat.st_mtime),
        }
    except Exception:
        return None


# =============================================================================
# HELPERS
# =============================================================================

def format_file_size(size_bytes: int) -> str:
    """
    Formatea tamaño de archivo en formato legible
    
    Args:
        size_bytes: Tamaño en bytes
        
    Returns:
        String formateado (ej: "5.2 MB")
    """
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if size_bytes < 1024.0:
            return f"{size_bytes:.1f} {unit}"
        size_bytes /= 1024.0
    return f"{size_bytes:.1f} PB"


def get_mime_type_from_filename(filename: str) -> str:
    """
    Obtiene el MIME type de un archivo por su nombre
    
    Args:
        filename: Nombre del archivo
        
    Returns:
        MIME type o 'application/octet-stream' por defecto
    """
    mime_type, _ = mimetypes.guess_type(filename)
    return mime_type or 'application/octet-stream'


# Importar datetime al inicio si no está
from datetime import datetime