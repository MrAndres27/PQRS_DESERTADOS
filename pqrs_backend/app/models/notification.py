"""Modelo de notificaciones"""
from datetime import datetime
from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime, ForeignKey, Enum as SQLEnum
from sqlalchemy.orm import relationship
import enum
from app.core.database import Base

class NotificationType(str, enum.Enum):
    EMAIL = "email"
    IN_APP = "in_app"

class Notification(Base):
    """Notificaciones del sistema"""
    __tablename__ = "notifications"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    pqrs_id = Column(Integer, ForeignKey("pqrs.id", ondelete="SET NULL"), nullable=True)
    type = Column(SQLEnum(NotificationType), nullable=False, default=NotificationType.IN_APP)
    title = Column(String(255), nullable=False, comment="Título de la notificación")
    message = Column(Text, nullable=False, comment="Mensaje de la notificación")
    is_read = Column(Boolean, default=False, nullable=False, comment="Si fue leída")
    sent_at = Column(DateTime, nullable=True, comment="Cuándo se envió el email")
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    user = relationship("User", back_populates="notifications")
    pqrs = relationship("PQRS", back_populates="notifications")
    
    def __repr__(self):
        return f"<Notification(id={self.id}, user_id={self.user_id}, title='{self.title}')>"
