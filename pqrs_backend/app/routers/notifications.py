"""
Router de Notificaciones
Sistema PQRS - Equipo Desertados

Endpoints para gestión de notificaciones por email:
- POST /notifications/test - Enviar email de prueba
- GET /notifications/config - Ver configuración
- GET /notifications/history - Ver historial de emails
- GET /notifications/statistics - Ver estadísticas
- GET /notifications/types - Ver tipos de email disponibles
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
import math

from app.core.database import get_async_db
from app.core.dependencies import (
    get_current_user,
    require_admin,
    get_pagination_params,
    PaginationParams
)
from app.models.user import User
from app.models.notification_log import NotificationLog
from app.repositories.notification_repository import NotificationLogRepository
from app.services.email_service import get_email_service
from app.config.email_config import get_email_settings, is_email_enabled, validate_email_config
from app.schemas.notifications import (
    TestEmailRequest,
    EmailSentResponse,
    NotificationLogResponse,
    NotificationLogPaginatedResponse,
    NotificationStatistics,
    EmailConfigResponse,
    EmailTypes
)


# =============================================================================
# ROUTER
# =============================================================================

router = APIRouter(tags=["Notificaciones"])


# =============================================================================
# ENDPOINTS DE INFORMACIÓN
# =============================================================================

@router.get(
    "/notifications/config",
    response_model=EmailConfigResponse,
    status_code=status.HTTP_200_OK
)
async def get_email_config(
    current_user: User = Depends(require_admin)
):
    """
    Obtiene la configuración actual de email
    
    **Información:**
    - Servidor SMTP configurado
    - Estado del servicio
    - Email remitente
    - Modo de prueba
    
    **Requiere:** Rol Administrador
    """
    settings = get_email_settings()
    config_validation = validate_email_config()
    
    return EmailConfigResponse(
        configured=config_validation['valid'],
        enabled=settings.EMAIL_ENABLED and is_email_enabled(),
        host=settings.SMTP_HOST,
        port=settings.SMTP_PORT,
        from_email=settings.SMTP_FROM_EMAIL,
        from_name=settings.SMTP_FROM_NAME,
        test_mode=settings.EMAIL_TEST_MODE
    )


@router.get(
    "/notifications/types",
    response_model=EmailTypes,
    status_code=status.HTTP_200_OK
)
async def get_email_types(
    current_user: User = Depends(get_current_user)
):
    """
    Obtiene los tipos de email disponibles
    
    Lista todos los tipos de notificaciones que el sistema puede enviar.
    
    **Requiere:** Usuario autenticado
    """
    return EmailTypes()


# =============================================================================
# ENDPOINTS DE ENVÍO
# =============================================================================

@router.post(
    "/notifications/test",
    response_model=EmailSentResponse,
    status_code=status.HTTP_200_OK
)
async def send_test_email(
    request: TestEmailRequest,
    current_user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_async_db)
):
    """
    Envía un email de prueba
    
    **Útil para:**
    - Verificar configuración SMTP
    - Probar conectividad con servidor de email
    - Validar que las plantillas se ven correctamente
    
    **Requiere:** Rol Administrador
    """
    # Verificar que email esté habilitado
    if not is_email_enabled():
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="El servicio de email no está configurado o está deshabilitado"
        )
    
    # Enviar email de prueba
    email_service = get_email_service()
    result = await email_service.send_test_email(
        to_email=request.to_email,
        to_name=request.to_name,
        test_message=request.test_message
    )
    
    # Crear log
    notification_log = NotificationLog(
        to_email=request.to_email,
        to_name=request.to_name or "Usuario de Prueba",
        subject="🧪 Email de Prueba - Sistema PQRS",
        email_type="test_email",
        sent_successfully=result['success'],
        error_message=result.get('error'),
        retry_count=0,
        sent_at=None if not result['success'] else None  # Se asignará automáticamente
    )
    
    notification_repo = NotificationLogRepository(db)
    created_log = await notification_repo.create(notification_log)
    await db.commit()
    
    return EmailSentResponse(
        success=result['success'],
        message=result['message'],
        error=result.get('error'),
        log_id=created_log.id
    )


# =============================================================================
# ENDPOINTS DE HISTORIAL
# =============================================================================

@router.get(
    "/notifications/history",
    response_model=NotificationLogPaginatedResponse,
    status_code=status.HTTP_200_OK
)
async def get_notification_history(
    pagination: PaginationParams = Depends(get_pagination_params),
    email_type: str = None,
    success_only: bool = None,
    failed_only: bool = None,
    current_user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_async_db)
):
    """
    Obtiene el historial de notificaciones enviadas
    
    **Filtros opcionales:**
    - `email_type`: Filtrar por tipo de email
    - `success_only`: Solo emails exitosos
    - `failed_only`: Solo emails fallidos
    
    **Paginación:**
    - `skip`: Registros a saltar
    - `limit`: Límite de resultados (max 100)
    
    **Ordenamiento:** Del más reciente al más antiguo
    
    **Requiere:** Rol Administrador
    """
    notification_repo = NotificationLogRepository(db)
    
    # Obtener logs
    logs = await notification_repo.get_all(
        skip=pagination.skip,
        limit=pagination.limit,
        email_type=email_type,
        success_only=success_only,
        failed_only=failed_only
    )
    
    # Contar total
    total = await notification_repo.count_all(
        email_type=email_type,
        success_only=success_only,
        failed_only=failed_only
    )
    
    # Calcular paginación
    page = (pagination.skip // pagination.limit) + 1
    total_pages = math.ceil(total / pagination.limit) if total > 0 else 1
    
    return NotificationLogPaginatedResponse(
        items=logs,
        total=total,
        page=page,
        page_size=pagination.limit,
        total_pages=total_pages
    )


@router.get(
    "/notifications/history/{log_id}",
    response_model=NotificationLogResponse,
    status_code=status.HTTP_200_OK
)
async def get_notification_log(
    log_id: int,
    current_user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_async_db)
):
    """
    Obtiene los detalles de un log específico
    
    **Requiere:** Rol Administrador
    """
    notification_repo = NotificationLogRepository(db)
    
    log = await notification_repo.get_by_id(log_id)
    
    if log is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Log de notificación con ID {log_id} no encontrado"
        )
    
    return log


@router.get(
    "/pqrs/{pqrs_id}/notifications",
    response_model=list[NotificationLogResponse],
    status_code=status.HTTP_200_OK
)
async def get_pqrs_notifications(
    pqrs_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_db)
):
    """
    Obtiene las notificaciones enviadas para una PQRS específica
    
    **Requiere:** Usuario autenticado
    """
    notification_repo = NotificationLogRepository(db)
    
    logs = await notification_repo.get_by_pqrs(pqrs_id)
    
    return logs


# =============================================================================
# ENDPOINTS DE ESTADÍSTICAS
# =============================================================================

@router.get(
    "/notifications/statistics",
    response_model=NotificationStatistics,
    status_code=status.HTTP_200_OK
)
async def get_notification_statistics(
    days: int = 7,
    current_user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_async_db)
):
    """
    Obtiene estadísticas de notificaciones
    
    **Query Params:**
    - `days`: Últimos X días (default: 7)
    
    **Incluye:**
    - Total de emails enviados
    - Tasa de éxito
    - Cantidad por tipo de email
    - Emails fallidos
    
    **Requiere:** Rol Administrador
    """
    if days < 1 or days > 365:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="El parámetro 'days' debe estar entre 1 y 365"
        )
    
    notification_repo = NotificationLogRepository(db)
    
    stats = await notification_repo.get_statistics(days=days)
    
    return NotificationStatistics(**stats)


# =============================================================================
# DOCUMENTACIÓN DE EVENTOS AUTOMÁTICOS
# =============================================================================

"""
NOTIFICACIONES AUTOMÁTICAS:

El sistema envía emails automáticamente en los siguientes eventos:

1. PQRS CREADA (pqrs_created):
   - Destinatario: Ciudadano que creó la PQRS
   - Contenido: Confirmación de registro con número de radicado
   - Momento: Inmediatamente después de crear la PQRS

2. PQRS ASIGNADA (pqrs_assigned):
   - Destinatario: Gestor asignado
   - Contenido: Notificación de nueva PQRS asignada
   - Momento: Cuando se asigna un gestor a la PQRS

3. CAMBIO DE ESTADO (status_changed):
   - Destinatario: Ciudadano propietario de la PQRS
   - Contenido: Información sobre el nuevo estado
   - Momento: Cuando cambia el estado de la PQRS

4. PQRS RESUELTA (pqrs_resolved):
   - Destinatario: Ciudadano propietario de la PQRS
   - Contenido: Notificación de resolución con detalles
   - Momento: Cuando la PQRS se marca como resuelta

5. NUEVO COMENTARIO (new_comment):
   - Destinatario: Ciudadano o gestores involucrados
   - Contenido: Notificación de nuevo comentario público
   - Momento: Cuando se agrega un comentario público

CONFIGURACIÓN:

Para habilitar notificaciones, configurar en .env:

SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=tu-email@gmail.com
SMTP_PASSWORD=tu-app-password
SMTP_FROM_EMAIL=tu-email@gmail.com
SMTP_FROM_NAME=Sistema PQRS
SMTP_USE_TLS=True
EMAIL_ENABLED=True

MODO DE PRUEBA:

Para probar sin enviar emails reales:

EMAIL_TEST_MODE=True
EMAIL_TEST_ADDRESS=pruebas@tuempresa.com

Todos los emails se redirigirán a EMAIL_TEST_ADDRESS

DESHABILITAR EMAILS:

EMAIL_ENABLED=False
"""