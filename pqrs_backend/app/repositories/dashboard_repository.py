"""
Repositorio de Dashboard
Sistema PQRS - Equipo Desertados

Consultas analíticas complejas para métricas y reportes.
"""

from typing import List, Optional, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, or_, case, extract
from datetime import datetime, date, timedelta

from app.models.pqrs import PQRS
from app.models.user import User
from app.models.pqrs_comment import PQRSComment as Comment 


class DashboardRepository:
    """Repository para consultas de dashboard y reportes"""
    
    def __init__(self, db: AsyncSession):
        """
        Inicializa el repositorio
        
        Args:
            db: Sesión asíncrona de SQLAlchemy
        """
        self.db = db
    
    # =========================================================================
    # KPIs GENERALES
    # =========================================================================
    
    async def get_total_pqrs(
        self,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
        department_id: Optional[int] = None
    ) -> int:
        """Obtiene total de PQRS con filtros"""
        query = select(func.count(PQRS.id))
        query = self._apply_filters(query, start_date, end_date, department_id)
        
        result = await self.db.execute(query)
        return result.scalar() or 0
    
    async def get_pqrs_by_status(
        self,
        status: str,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
        department_id: Optional[int] = None
    ) -> int:
        """Obtiene cantidad de PQRS por estado"""
        query = select(func.count(PQRS.id)).where(
            PQRS.status == status
        )
        query = self._apply_filters(query, start_date, end_date, department_id)
        
        result = await self.db.execute(query)
        return result.scalar() or 0
    
    async def get_avg_response_time_hours(
        self,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None
    ) -> Optional[float]:
        """
        Calcula tiempo promedio de primera respuesta en horas
        (Tiempo desde creación hasta primer comentario)
        """
        # Subconsulta para obtener el primer comentario de cada PQRS
        first_comment_subquery = (
            select(
                Comment.pqrs_id,
                func.min(Comment.created_at).label('first_comment_at')
            )
            .group_by(Comment.pqrs_id)
            .subquery()
        )
        
        # Query principal
        query = select(
            func.avg(
                func.extract('epoch', first_comment_subquery.c.first_comment_at - PQRS.created_at) / 3600
            )
        ).select_from(PQRS).join(
            first_comment_subquery,
            PQRS.id == first_comment_subquery.c.pqrs_id
        )
        
        if start_date:
            query = query.where(PQRS.created_at >= start_date)
        if end_date:
            query = query.where(PQRS.created_at <= end_date)
        
        result = await self.db.execute(query)
        avg = result.scalar()
        
        return round(avg, 2) if avg else None
    
    async def get_avg_resolution_time_days(
        self,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None
    ) -> Optional[float]:
        """
        Calcula tiempo promedio de resolución en días
        (Solo PQRS resueltas o cerradas)
        """
        query = select(
            func.avg(
                func.extract('epoch', PQRS.updated_at - PQRS.created_at) / 86400
            )
        ).where(
            or_(PQRS.status == 'resuelta', PQRS.status == 'cerrada')
        )
        
        if start_date:
            query = query.where(PQRS.created_at >= start_date)
        if end_date:
            query = query.where(PQRS.created_at <= end_date)
        
        result = await self.db.execute(query)
        avg = result.scalar()
        
        return round(avg, 2) if avg else None
    
    async def get_resolution_rate(
        self,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None
    ) -> float:
        """Calcula tasa de resolución (%)"""
        total = await self.get_total_pqrs(start_date, end_date)
        
        if total == 0:
            return 0.0
        
        resolved = await self.get_pqrs_by_status('resuelta', start_date, end_date)
        closed = await self.get_pqrs_by_status('cerrada', start_date, end_date)
        
        return round((resolved + closed) / total * 100, 2)
    
    async def get_active_managers_count(self) -> int:
        """Obtiene cantidad de gestores con PQRS asignadas actualmente"""
        query = select(func.count(func.distinct(PQRS.assigned_to))).where(
            and_(
                PQRS.assigned_to.isnot(None),
                PQRS.status.notin_(['resuelta', 'cerrada'])
            )
        )
        
        result = await self.db.execute(query)
        return result.scalar() or 0
    
    # =========================================================================
    # ESTADÍSTICAS POR TIPO
    # =========================================================================
    
    async def get_statistics_by_type(
        self,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
        department_id: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """Obtiene estadísticas agrupadas por tipo de PQRS"""
        # Total para calcular porcentajes
        total = await self.get_total_pqrs(start_date, end_date, department_id)
        
        # Subconsulta para días de resolución
        resolution_days = func.extract('epoch', PQRS.updated_at - PQRS.created_at) / 86400
        
        # Query principal
        query = select(
            PQRS.type,
            func.count(PQRS.id).label('count'),
            func.sum(
                case((or_(PQRS.status == 'resuelta', PQRS.status == 'cerrada'), 1), else_=0)
            ).label('resolved'),
            func.avg(
                case(
                    (or_(PQRS.status == 'resuelta', PQRS.status == 'cerrada'), resolution_days),
                    else_=None
                )
            ).label('avg_resolution_days')
        ).group_by(PQRS.type)
        
        query = self._apply_filters(query, start_date, end_date, department_id)
        
        result = await self.db.execute(query)
        rows = result.all()
        
        statistics = []
        for row in rows:
            statistics.append({
                'type': row.type,
                'count': row.count,
                'percentage': round(row.count / total * 100, 2) if total > 0 else 0.0,
                'resolved': row.resolved or 0,
                'avg_resolution_days': round(row.avg_resolution_days, 2) if row.avg_resolution_days else None
            })
        
        return statistics
    
    # =========================================================================
    # ESTADÍSTICAS POR ESTADO
    # =========================================================================
    
    async def get_statistics_by_status(
        self,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
        department_id: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """Obtiene estadísticas agrupadas por estado"""
        total = await self.get_total_pqrs(start_date, end_date, department_id)
        
        # Días en estado actual (desde updated_at hasta ahora)
        days_in_status = func.extract('epoch', func.now() - PQRS.updated_at) / 86400
        
        query = select(
            PQRS.status,
            func.count(PQRS.id).label('count'),
            func.avg(days_in_status).label('avg_days_in_status')
        ).group_by(PQRS.status)
        
        query = self._apply_filters(query, start_date, end_date, department_id)
        
        result = await self.db.execute(query)
        rows = result.all()
        
        statistics = []
        for row in rows:
            statistics.append({
                'status': row.status,
                'count': row.count,
                'percentage': round(row.count / total * 100, 2) if total > 0 else 0.0,
                'avg_days_in_status': round(row.avg_days_in_status, 2) if row.avg_days_in_status else None
            })
        
        return statistics
    
    # =========================================================================
    # PERFORMANCE DE GESTORES
    # =========================================================================
    
    async def get_manager_performance(
        self,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """Obtiene performance de gestores (top N)"""
        resolution_days = func.extract('epoch', PQRS.updated_at - PQRS.created_at) / 86400
        
        query = select(
            PQRS.assigned_to.label('manager_id'),
            User.full_name.label('manager_name'),
            func.count(PQRS.id).label('total_assigned'),
            func.sum(
                case((or_(PQRS.status == 'resuelta', PQRS.status == 'cerrada'), 1), else_=0)
            ).label('resolved'),
            func.sum(
                case((PQRS.status.in_(['en_proceso', 'en_revision', 'pendiente_informacion']), 1), else_=0)
            ).label('in_progress'),
            func.avg(
                case(
                    (or_(PQRS.status == 'resuelta', PQRS.status == 'cerrada'), resolution_days),
                    else_=None
                )
            ).label('avg_resolution_days')
        ).select_from(PQRS).join(
            User,
            PQRS.assigned_to == User.id
        ).where(
            PQRS.assigned_to.isnot(None)
        ).group_by(
            PQRS.assigned_to,
            User.full_name
        ).order_by(
            func.count(PQRS.id).desc()
        ).limit(limit)
        
        if start_date:
            query = query.where(PQRS.created_at >= start_date)
        if end_date:
            query = query.where(PQRS.created_at <= end_date)
        
        result = await self.db.execute(query)
        rows = result.all()
        
        performance = []
        for row in rows:
            total = row.total_assigned
            resolved = row.resolved or 0
            resolution_rate = round(resolved / total * 100, 2) if total > 0 else 0.0
            
            performance.append({
                'manager_id': row.manager_id,
                'manager_name': row.manager_name,
                'total_assigned': total,
                'resolved': resolved,
                'in_progress': row.in_progress or 0,
                'avg_resolution_days': round(row.avg_resolution_days, 2) if row.avg_resolution_days else None,
                'resolution_rate': resolution_rate
            })
        
        return performance
    
    # =========================================================================
    # TENDENCIAS TEMPORALES
    # =========================================================================
    
    async def get_trends_by_month(
        self,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
        months: int = 12
    ) -> List[Dict[str, Any]]:
        """Obtiene tendencias mensuales"""
        resolution_days = func.extract('epoch', PQRS.updated_at - PQRS.created_at) / 86400
        
        # Formato YYYY-MM para agrupar por mes
        month_period = func.to_char(PQRS.created_at, 'YYYY-MM')
        
        query = select(
            month_period.label('period'),
            func.count(PQRS.id).label('count'),
            func.sum(
                case((or_(PQRS.status == 'resuelta', PQRS.status == 'cerrada'), 1), else_=0)
            ).label('resolved'),
            func.avg(
                case(
                    (or_(PQRS.status == 'resuelta', PQRS.status == 'cerrada'), resolution_days),
                    else_=None
                )
            ).label('avg_resolution_days')
        ).group_by(
            month_period
        ).order_by(
            month_period.desc()
        ).limit(months)
        
        if start_date:
            query = query.where(PQRS.created_at >= start_date)
        if end_date:
            query = query.where(PQRS.created_at <= end_date)
        
        result = await self.db.execute(query)
        rows = result.all()
        
        trends = []
        for row in rows:
            trends.append({
                'period': row.period,
                'count': row.count,
                'resolved': row.resolved or 0,
                'avg_resolution_days': round(row.avg_resolution_days, 2) if row.avg_resolution_days else None
            })
        
        # Invertir para que el más antiguo esté primero
        return list(reversed(trends))
    
    async def get_trends_by_week(
        self,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
        weeks: int = 12
    ) -> List[Dict[str, Any]]:
        """Obtiene tendencias semanales"""
        resolution_days = func.extract('epoch', PQRS.updated_at - PQRS.created_at) / 86400
        
        # Formato YYYY-WW para agrupar por semana
        week_period = func.to_char(PQRS.created_at, 'IYYY-IW')
        
        query = select(
            week_period.label('period'),
            func.count(PQRS.id).label('count'),
            func.sum(
                case((or_(PQRS.status == 'resuelta', PQRS.status == 'cerrada'), 1), else_=0)
            ).label('resolved'),
            func.avg(
                case(
                    (or_(PQRS.status == 'resuelta', PQRS.status == 'cerrada'), resolution_days),
                    else_=None
                )
            ).label('avg_resolution_days')
        ).group_by(
            week_period
        ).order_by(
            week_period.desc()
        ).limit(weeks)
        
        if start_date:
            query = query.where(PQRS.created_at >= start_date)
        if end_date:
            query = query.where(PQRS.created_at <= end_date)
        
        result = await self.db.execute(query)
        rows = result.all()
        
        trends = []
        for row in rows:
            trends.append({
                'period': row.period,
                'count': row.count,
                'resolved': row.resolved or 0,
                'avg_resolution_days': round(row.avg_resolution_days, 2) if row.avg_resolution_days else None
            })
        
        return list(reversed(trends))
    
    # =========================================================================
    # ANÁLISIS DE TIEMPOS
    # =========================================================================
    
    async def get_time_analysis(
        self,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None
    ) -> Dict[str, Any]:
        """Obtiene análisis detallado de tiempos"""
        resolution_days = func.extract('epoch', PQRS.updated_at - PQRS.created_at) / 86400
        
        # Query para promedios
        avg_query = select(
            func.avg(resolution_days).label('avg_days')
        ).where(
            or_(PQRS.status == 'resuelta', PQRS.status == 'cerrada')
        )
        
        if start_date:
            avg_query = avg_query.where(PQRS.created_at >= start_date)
        if end_date:
            avg_query = avg_query.where(PQRS.created_at <= end_date)
        
        avg_result = await self.db.execute(avg_query)
        avg_days = avg_result.scalar()
        
        # Query para distribución por rangos
        base_query = select(PQRS).where(
            or_(PQRS.status == 'resuelta', PQRS.status == 'cerrada')
        )
        
        if start_date:
            base_query = base_query.where(PQRS.created_at >= start_date)
        if end_date:
            base_query = base_query.where(PQRS.created_at <= end_date)
        
        result = await self.db.execute(base_query)
        pqrs_list = result.scalars().all()
        
        # Contar por rangos
        within_24h = 0
        within_3d = 0
        within_7d = 0
        within_15d = 0
        over_15d = 0
        
        for pqrs in pqrs_list:
            delta = pqrs.updated_at - pqrs.created_at
            days = delta.total_seconds() / 86400
            
            if days < 1:
                within_24h += 1
            elif days < 3:
                within_3d += 1
            elif days < 7:
                within_7d += 1
            elif days < 15:
                within_15d += 1
            else:
                over_15d += 1
        
        return {
            'avg_resolution_days': round(avg_days, 2) if avg_days else None,
            'median_resolution_days': None,  # Requeriría cálculo más complejo
            'resolved_within_24h': within_24h,
            'resolved_within_3d': within_3d,
            'resolved_within_7d': within_7d,
            'resolved_within_15d': within_15d,
            'resolved_over_15d': over_15d
        }
    
    # =========================================================================
    # HELPERS
    # =========================================================================
    
    def _apply_filters(
        self,
        query,
        start_date: Optional[date],
        end_date: Optional[date],
        department_id: Optional[int]
    ):
        """Aplica filtros comunes a una query"""
        if start_date:
            query = query.where(PQRS.created_at >= start_date)
        if end_date:
            query = query.where(PQRS.created_at <= end_date)
        if department_id:
            query = query.where(PQRS.department_id == department_id)
        
        return query