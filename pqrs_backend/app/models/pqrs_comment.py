"""
Modelo de Comentarios de PQRS
Sistema PQRS - Equipo Desertados

Representa comentarios/conversaciones internas en una PQRS.
Permite colaboración entre gestores y seguimiento de discusiones.
"""

from datetime import datetime
from sqlalchemy import Column, Integer, Text, DateTime, ForeignKey, Boolean
from sqlalchemy.orm import relationship

from app.core.database import Base


class PQRSComment(Base):
    """
    Modelo de comentarios de PQRS
    
    Permite conversaciones internas entre gestores
    y comunicación con ciudadanos sobre una PQRS.
    """
    
    __tablename__ = "pqrs_comments"
    
    # Identificación
    id = Column(Integer, primary_key=True, index=True)
    
    # Relaciones
    pqrs_id = Column(
        Integer,
        ForeignKey("pqrs.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="ID de la PQRS a la que pertenece el comentario"
    )
    
    user_id = Column(
        Integer,
        ForeignKey("users.id"),
        nullable=False,
        index=True,
        comment="ID del usuario que escribió el comentario"
    )
    
    # Contenido
    content = Column(
        Text,
        nullable=False,
        comment="Contenido del comentario"
    )
    
    # Tipo de comentario
    is_internal = Column(
        Boolean,
        default=False,
        nullable=False,
        comment="Si es true, solo visible para gestores. Si es false, visible para ciudadano"
    )
    
    # Timestamps
    created_at = Column(
        DateTime,
        default=datetime.utcnow,
        nullable=False,
        comment="Fecha de creación del comentario"
    )
    
    updated_at = Column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False,
        comment="Fecha de última actualización"
    )
    
    # Relaciones ORM
    pqrs = relationship("PQRS", back_populates="comments")
    author = relationship("User", foreign_keys=[user_id])
    
    def __repr__(self):
        return f"<PQRSComment(id={self.id}, pqrs_id={self.pqrs_id}, author_id={self.user_id})>"
    
    def __str__(self):
        preview = self.content[:50] + "..." if len(self.content) > 50 else self.content
        return f"Comentario #{self.id}: {preview}"
    
    @property
    def is_edited(self) -> bool:
        """Verifica si el comentario fue editado"""
        # Si updated_at es más de 1 segundo después de created_at
        if self.updated_at and self.created_at:
            delta = (self.updated_at - self.created_at).total_seconds()
            return delta > 1
        return False