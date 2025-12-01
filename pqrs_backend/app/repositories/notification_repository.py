"""
Repositorio de Logs de Notificaciones
Sistema PQRS - Equipo Desertados

Maneja todas las operaciones de acceso a datos para logs de notificaciones.
"""

from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, desc
from datetime import datetime, timedelta

from app.models.notification_log import NotificationLog


class NotificationLogRepository:
    """Repositorio para operaciones de logs de notificaciones"""
    
    def __init__(self, db: AsyncSession):
        """
        Inicializa el repositorio
        
        Args:
            db: Sesión asíncrona de SQLAlchemy
        """
        self.db = db
    
    # =========================================================================
    # OPERACIONES DE LECTURA
    # =========================================================================
    
    async def get_by_id(self, log_id: int) -> Optional[NotificationLog]:
        """
        Obtiene un log por ID
        
        Args:
            log_id: ID del log
            
        Returns:
            NotificationLog si existe, None si no
        """
        result = await self.db.execute(
            select(NotificationLog).where(NotificationLog.id == log_id)
        )
        return result.scalar_one_or_none()
    
    async def get_all(
        self,
        skip: int = 0,
        limit: int = 50,
        email_type: Optional[str] = None,
        success_only: Optional[bool] = None,
        failed_only: Optional[bool] = None
    ) -> List[NotificationLog]:
        """
        Obtiene logs con filtros opcionales
        
        Args:
            skip: Registros a saltar
            limit: Límite de resultados
            email_type: Filtrar por tipo de email (opcional)
            success_only: Solo exitosos (opcional)
            failed_only: Solo fallidos (opcional)
            
        Returns:
            Lista de logs
        """
        query = select(NotificationLog)
        
        # Filtros opcionales
        if email_type:
            query = query.where(NotificationLog.email_type == email_type)
        
        if success_only:
            query = query.where(NotificationLog.sent_successfully == True)
        
        if failed_only:
            query = query.where(NotificationLog.sent_successfully == False)
        
        # Ordenar por más recientes
        query = query.order_by(desc(NotificationLog.created_at))
        
        # Paginación
        query = query.offset(skip).limit(limit)
        
        result = await self.db.execute(query)
        return list(result.scalars().all())
    
    async def count_all(
        self,
        email_type: Optional[str] = None,
        success_only: Optional[bool] = None,
        failed_only: Optional[bool] = None
    ) -> int:
        """
        Cuenta logs con filtros opcionales
        
        Args:
            email_type: Filtrar por tipo (opcional)
            success_only: Solo exitosos (opcional)
            failed_only: Solo fallidos (opcional)
            
        Returns:
            Cantidad de logs
        """
        query = select(func.count(NotificationLog.id))
        
        if email_type:
            query = query.where(NotificationLog.email_type == email_type)
        
        if success_only:
            query = query.where(NotificationLog.sent_successfully == True)
        
        if failed_only:
            query = query.where(NotificationLog.sent_successfully == False)
        
        result = await self.db.execute(query)
        return result.scalar() or 0
    
    async def get_by_pqrs(
        self,
        pqrs_id: int,
        skip: int = 0,
        limit: int = 50
    ) -> List[NotificationLog]:
        """
        Obtiene logs de una PQRS específica
        
        Args:
            pqrs_id: ID de la PQRS
            skip: Registros a saltar
            limit: Límite de resultados
            
        Returns:
            Lista de logs
        """
        result = await self.db.execute(
            select(NotificationLog)
            .where(NotificationLog.pqrs_id == pqrs_id)
            .order_by(desc(NotificationLog.created_at))
            .offset(skip)
            .limit(limit)
        )
        return list(result.scalars().all())
    
    async def get_by_email(
        self,
        email: str,
        skip: int = 0,
        limit: int = 50
    ) -> List[NotificationLog]:
        """
        Obtiene logs enviados a un email específico
        
        Args:
            email: Email del destinatario
            skip: Registros a saltar
            limit: Límite de resultados
            
        Returns:
            Lista de logs
        """
        result = await self.db.execute(
            select(NotificationLog)
            .where(NotificationLog.to_email == email)
            .order_by(desc(NotificationLog.created_at))
            .offset(skip)
            .limit(limit)
        )
        return list(result.scalars().all())
    
    async def get_recent(
        self,
        hours: int = 24,
        limit: int = 100
    ) -> List[NotificationLog]:
        """
        Obtiene logs recientes
        
        Args:
            hours: Últimas X horas
            limit: Límite de resultados
            
        Returns:
            Lista de logs
        """
        since = datetime.utcnow() - timedelta(hours=hours)
        
        result = await self.db.execute(
            select(NotificationLog)
            .where(NotificationLog.created_at >= since)
            .order_by(desc(NotificationLog.created_at))
            .limit(limit)
        )
        return list(result.scalars().all())
    
    # =========================================================================
    # OPERACIONES DE ESCRITURA
    # =========================================================================
    
    async def create(self, log: NotificationLog) -> NotificationLog:
        """
        Crea un nuevo log de notificación
        
        Args:
            log: Objeto NotificationLog a crear
            
        Returns:
            Log creado con ID asignado
        """
        self.db.add(log)
        await self.db.flush()
        await self.db.refresh(log)
        
        return log
    
    async def update(self, log: NotificationLog) -> NotificationLog:
        """
        Actualiza un log existente
        
        Args:
            log: Log con datos actualizados
            
        Returns:
            Log actualizado
        """
        await self.db.flush()
        await self.db.refresh(log)
        
        return log
    
    # =========================================================================
    # ESTADÍSTICAS
    # =========================================================================
    
    async def get_statistics(
        self,
        days: int = 7
    ) -> dict:
        """
        Obtiene estadísticas de envío de emails
        
        Args:
            days: Últimos X días
            
        Returns:
            Dict con estadísticas
        """
        since = datetime.utcnow() - timedelta(days=days)
        
        # Total de emails
        total_result = await self.db.execute(
            select(func.count(NotificationLog.id)).where(
                NotificationLog.created_at >= since
            )
        )
        total = total_result.scalar() or 0
        
        # Emails exitosos
        success_result = await self.db.execute(
            select(func.count(NotificationLog.id)).where(
                NotificationLog.created_at >= since,
                NotificationLog.sent_successfully == True
            )
        )
        successful = success_result.scalar() or 0
        
        # Emails fallidos
        failed = total - successful
        
        # Por tipo
        by_type_result = await self.db.execute(
            select(
                NotificationLog.email_type,
                func.count(NotificationLog.id)
            )
            .where(NotificationLog.created_at >= since)
            .group_by(NotificationLog.email_type)
        )
        by_type = {row[0]: row[1] for row in by_type_result.fetchall()}
        
        # Tasa de éxito
        success_rate = (successful / total * 100) if total > 0 else 0
        
        return {
            "period_days": days,
            "total_sent": total,
            "successful": successful,
            "failed": failed,
            "success_rate": round(success_rate, 2),
            "by_type": by_type
        }