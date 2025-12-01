"""
Schemas de Notificaciones
Sistema PQRS - Equipo Desertados

Schemas para validación y serialización de notificaciones por email.
"""

from pydantic import BaseModel, EmailStr, Field
from datetime import datetime
from typing import Optional, List, Dict, Any


# =============================================================================
# SCHEMAS DE ENVÍO
# =============================================================================

class TestEmailRequest(BaseModel):
    """Schema para enviar email de prueba"""
    to_email: EmailStr = Field(
        ...,
        description="Email del destinatario de prueba"
    )
    to_name: Optional[str] = Field(
        default=None,
        description="Nombre del destinatario (opcional)"
    )
    test_message: Optional[str] = Field(
        default=None,
        max_length=500,
        description="Mensaje personalizado de prueba (opcional)"
    )
    
    class Config:
        json_schema_extra = {
            "example": {
                "to_email": "admin@ejemplo.com",
                "to_name": "Administrador",
                "test_message": "Esta es una prueba del sistema de notificaciones"
            }
        }


class SendEmailRequest(BaseModel):
    """Schema para enviar email manual"""
    to_email: EmailStr = Field(..., description="Email del destinatario")
    to_name: Optional[str] = Field(default=None, description="Nombre del destinatario")
    subject: str = Field(..., min_length=3, max_length=500, description="Asunto del email")
    message: str = Field(..., min_length=10, description="Mensaje del email")
    pqrs_id: Optional[int] = Field(default=None, description="ID de PQRS relacionada (opcional)")
    
    class Config:
        json_schema_extra = {
            "example": {
                "to_email": "ciudadano@ejemplo.com",
                "to_name": "Juan Pérez",
                "subject": "Información adicional sobre tu solicitud",
                "message": "Hola Juan, necesitamos que nos proporciones...",
                "pqrs_id": 5
            }
        }


# =============================================================================
# SCHEMAS DE RESPUESTA
# =============================================================================

class EmailSentResponse(BaseModel):
    """Response de email enviado"""
    success: bool = Field(description="Si el email se envió exitosamente")
    message: str = Field(description="Mensaje descriptivo del resultado")
    error: Optional[str] = Field(default=None, description="Mensaje de error (si aplica)")
    log_id: Optional[int] = Field(default=None, description="ID del log de notificación")
    
    class Config:
        json_schema_extra = {
            "example": {
                "success": True,
                "message": "Email sent successfully",
                "error": None,
                "log_id": 42
            }
        }


class NotificationLogResponse(BaseModel):
    """Response de log de notificación"""
    id: int
    to_email: str
    to_name: Optional[str]
    subject: str
    email_type: str
    pqrs_id: Optional[int]
    sent_successfully: bool
    error_message: Optional[str]
    retry_count: int
    sent_at: Optional[datetime]
    created_at: datetime
    status_text: str
    
    class Config:
        from_attributes = True
        json_schema_extra = {
            "example": {
                "id": 1,
                "to_email": "ciudadano@ejemplo.com",
                "to_name": "Juan Pérez",
                "subject": "PQRS Registrada - Radicado PQRS-2024-001",
                "email_type": "pqrs_created",
                "pqrs_id": 5,
                "sent_successfully": True,
                "error_message": None,
                "retry_count": 0,
                "sent_at": "2024-11-24T10:30:00",
                "created_at": "2024-11-24T10:30:00",
                "status_text": "Enviado"
            }
        }


class NotificationLogPaginatedResponse(BaseModel):
    """Response paginada de logs"""
    items: List[NotificationLogResponse]
    total: int
    page: int
    page_size: int
    total_pages: int
    
    class Config:
        json_schema_extra = {
            "example": {
                "items": [],
                "total": 150,
                "page": 1,
                "page_size": 50,
                "total_pages": 3
            }
        }


class NotificationStatistics(BaseModel):
    """Estadísticas de notificaciones"""
    period_days: int = Field(description="Período en días")
    total_sent: int = Field(description="Total de emails enviados")
    successful: int = Field(description="Emails enviados exitosamente")
    failed: int = Field(description="Emails fallidos")
    success_rate: float = Field(description="Tasa de éxito en porcentaje")
    by_type: Dict[str, int] = Field(description="Cantidad por tipo de email")
    
    class Config:
        json_schema_extra = {
            "example": {
                "period_days": 7,
                "total_sent": 245,
                "successful": 238,
                "failed": 7,
                "success_rate": 97.14,
                "by_type": {
                    "pqrs_created": 45,
                    "pqrs_assigned": 38,
                    "status_changed": 89,
                    "pqrs_resolved": 42,
                    "new_comment": 31
                }
            }
        }


class EmailConfigResponse(BaseModel):
    """Response de configuración de email"""
    configured: bool = Field(description="Si el email está configurado")
    enabled: bool = Field(description="Si el envío está habilitado")
    host: str = Field(description="Servidor SMTP")
    port: int = Field(description="Puerto SMTP")
    from_email: str = Field(description="Email remitente")
    from_name: str = Field(description="Nombre del remitente")
    test_mode: bool = Field(description="Si está en modo de prueba")
    
    class Config:
        json_schema_extra = {
            "example": {
                "configured": True,
                "enabled": True,
                "host": "smtp.gmail.com",
                "port": 587,
                "from_email": "notificaciones@sistema-pqrs.com",
                "from_name": "Sistema PQRS",
                "test_mode": False
            }
        }


# =============================================================================
# SCHEMAS DE TIPOS DE EMAIL
# =============================================================================

class EmailTypes(BaseModel):
    """Tipos de email disponibles"""
    types: List[str] = [
        "pqrs_created",
        "pqrs_assigned",
        "status_changed",
        "pqrs_resolved",
        "new_comment",
        "test_email"
    ]
    descriptions: Dict[str, str] = {
        "pqrs_created": "Email enviado cuando se crea una PQRS",
        "pqrs_assigned": "Email enviado cuando se asigna una PQRS a un gestor",
        "status_changed": "Email enviado cuando cambia el estado de una PQRS",
        "pqrs_resolved": "Email enviado cuando se resuelve una PQRS",
        "new_comment": "Email enviado cuando hay un nuevo comentario",
        "test_email": "Email de prueba"
    }
    
    class Config:
        json_schema_extra = {
            "example": {
                "types": [
                    "pqrs_created",
                    "pqrs_assigned",
                    "status_changed",
                    "pqrs_resolved",
                    "new_comment",
                    "test_email"
                ],
                "descriptions": {
                    "pqrs_created": "Email enviado cuando se crea una PQRS"
                }
            }
        }