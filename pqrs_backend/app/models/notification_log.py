"""
Modelo de Log de Notificaciones
Sistema PQRS - Equipo Desertados

Representa el historial de emails enviados por el sistema.
"""

from datetime import datetime
from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean, ForeignKey
from sqlalchemy.orm import relationship

from app.core.database import Base


class NotificationLog(Base):
    """
    Modelo de log de notificaciones
    
    Almacena el historial de todos los emails enviados por el sistema
    para auditoría y seguimiento.
    """
    
    __tablename__ = "notification_logs"
    
    # Identificación
    id = Column(Integer, primary_key=True, index=True)
    
    # Información del email
    to_email = Column(
        String(255),
        nullable=False,
        index=True,
        comment="Email del destinatario"
    )
    
    to_name = Column(
        String(255),
        nullable=True,
        comment="Nombre del destinatario"
    )
    
    subject = Column(
        String(500),
        nullable=False,
        comment="Asunto del email"
    )
    
    email_type = Column(
        String(50),
        nullable=False,
        index=True,
        comment="Tipo de email (pqrs_created, status_changed, etc.)"
    )
    
    # Relación con PQRS (opcional, puede ser null para emails generales)
    pqrs_id = Column(
        Integer,
        ForeignKey("pqrs.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
        comment="ID de la PQRS relacionada (si aplica)"
    )
    
    # Estado del envío
    sent_successfully = Column(
        Boolean,
        default=False,
        nullable=False,
        index=True,
        comment="Si el email se envió exitosamente"
    )
    
    error_message = Column(
        Text,
        nullable=True,
        comment="Mensaje de error si falló el envío"
    )
    
    # Intentos de envío
    retry_count = Column(
        Integer,
        default=0,
        nullable=False,
        comment="Número de intentos de envío"
    )
    
    # Timestamps
    sent_at = Column(
        DateTime,
        nullable=True,
        comment="Fecha y hora en que se envió el email"
    )
    
    created_at = Column(
        DateTime,
        default=datetime.utcnow,
        nullable=False,
        comment="Fecha y hora de creación del registro"
    )
    
    # Relaciones ORM
    pqrs = relationship("PQRS", foreign_keys=[pqrs_id])
    
    def __repr__(self):
        return f"<NotificationLog(id={self.id}, to='{self.to_email}', type='{self.email_type}', success={self.sent_successfully})>"
    
    def __str__(self):
        status = "✅ Enviado" if self.sent_successfully else "❌ Fallido"
        return f"{status} - {self.email_type} a {self.to_email}"
    
    @property
    def status_text(self) -> str:
        """Retorna el estado del envío en texto"""
        if self.sent_successfully:
            return "Enviado"
        elif self.retry_count > 0:
            return f"Fallido ({self.retry_count} intentos)"
        else:
            return "Fallido"
    
    @property
    def sent_at_formatted(self) -> str:
        """Retorna la fecha de envío formateada"""
        if self.sent_at:
            return self.sent_at.strftime("%Y-%m-%d %H:%M:%S")
        return "No enviado"