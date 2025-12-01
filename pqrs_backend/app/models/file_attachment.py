"""
Modelo de Archivos Adjuntos
Sistema PQRS - Equipo Desertados

Representa archivos adjuntos a PQRS.
Soporta documentos, imágenes y evidencias.
"""

from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, BigInteger
from sqlalchemy.orm import relationship

from app.core.database import Base


class FileAttachment(Base):
    """
    Modelo de archivos adjuntos a PQRS
    
    Almacena información de archivos subidos por usuarios
    como evidencias, documentos o imágenes relacionadas con PQRS.
    """
    
    __tablename__ = "file_attachments"
    
    # Identificación
    id = Column(Integer, primary_key=True, index=True)
    
    # Relaciones
    pqrs_id = Column(
        Integer,
        ForeignKey("pqrs.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="ID de la PQRS a la que pertenece el archivo"
    )
    
    uploaded_by = Column(
        Integer,
        ForeignKey("users.id"),
        nullable=False,
        index=True,
        comment="ID del usuario que subió el archivo"
    )
    
    # Información del archivo
    original_filename = Column(
        String(255),
        nullable=False,
        comment="Nombre original del archivo"
    )
    
    stored_filename = Column(
        String(255),
        nullable=False,
        unique=True,
        comment="Nombre con el que se guardó en disco (único)"
    )
    
    file_path = Column(
        String(500),
        nullable=False,
        comment="Ruta completa donde se almacenó el archivo"
    )
    
    file_size = Column(
        BigInteger,
        nullable=False,
        comment="Tamaño del archivo en bytes"
    )
    
    mime_type = Column(
        String(100),
        nullable=False,
        comment="Tipo MIME del archivo (ej: application/pdf, image/jpeg)"
    )
    
    file_extension = Column(
        String(10),
        nullable=False,
        comment="Extensión del archivo (ej: pdf, jpg, docx)"
    )
    
    # Descripción opcional
    description = Column(
        String(500),
        nullable=True,
        comment="Descripción opcional del archivo"
    )
    
    # Timestamps
    uploaded_at = Column(
        DateTime,
        default=datetime.utcnow,
        nullable=False,
        comment="Fecha y hora de subida"
    )
    
    # Relaciones ORM
    pqrs = relationship("PQRS", back_populates="files")
    uploader = relationship("User", foreign_keys=[uploaded_by])
    
    def __repr__(self):
        return f"<FileAttachment(id={self.id}, filename='{self.original_filename}', pqrs_id={self.pqrs_id})>"
    
    def __str__(self):
        return f"{self.original_filename} ({self.file_size_human})"
    
    @property
    def file_size_human(self) -> str:
        """Retorna el tamaño del archivo en formato legible"""
        size = self.file_size
        for unit in ['B', 'KB', 'MB', 'GB']:
            if size < 1024.0:
                return f"{size:.1f} {unit}"
            size /= 1024.0
        return f"{size:.1f} TB"
    
    @property
    def is_image(self) -> bool:
        """Verifica si el archivo es una imagen"""
        return self.mime_type.startswith('image/')
    
    @property
    def is_pdf(self) -> bool:
        """Verifica si el archivo es un PDF"""
        return self.mime_type == 'application/pdf'
    
    @property
    def is_document(self) -> bool:
        """Verifica si el archivo es un documento (Word, Excel, etc.)"""
        doc_types = [
            'application/msword',
            'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
            'application/vnd.ms-excel',
            'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        ]
        return self.mime_type in doc_types