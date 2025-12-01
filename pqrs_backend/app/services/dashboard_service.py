"""
Servicio de Dashboard
Sistema PQRS - Equipo Desertados

Lógica de negocio para métricas y reportes del sistema.
"""

from typing import Optional, Dict, Any
from datetime import datetime, date
from sqlalchemy.ext.asyncio import AsyncSession

from app.repositories.dashboard_repository import DashboardRepository
from app.schemas.dashboard import (
    OverviewKPIs,
    TypeStatistics,
    TypeStatisticsResponse,
    StatusStatistics,
    StatusStatisticsResponse,
    ManagerPerformance,
    ManagerPerformanceResponse,
    TrendDataPoint,
    TrendsResponse,
    TimeAnalysis,
    DashboardOverview
)


class DashboardService:
    """Servicio para dashboard y reportes"""
    
    def __init__(self, db: AsyncSession):
        """
        Inicializa el servicio
        
        Args:
            db: Sesión asíncrona de SQLAlchemy
        """
        self.db = db
        self.repository = DashboardRepository(db)
    
    # =========================================================================
    # OVERVIEW COMPLETO
    # =========================================================================
    
    async def get_overview(
        self,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
        department_id: Optional[int] = None
    ) -> DashboardOverview:
        """
        Obtiene vista general completa del dashboard
        
        Args:
            start_date: Fecha de inicio (opcional)
            end_date: Fecha de fin (opcional)
            department_id: ID de departamento (opcional)
            
        Returns:
            DashboardOverview con todas las métricas
        """
        # Obtener KPIs
        kpis = await self.get_kpis(start_date, end_date, department_id)
        
        # Obtener estadísticas por tipo
        by_type_data = await self.repository.get_statistics_by_type(
            start_date, end_date, department_id
        )
        by_type = [TypeStatistics(**item) for item in by_type_data]
        
        # Obtener estadísticas por estado
        by_status_data = await self.repository.get_statistics_by_status(
            start_date, end_date, department_id
        )
        by_status = [StatusStatistics(**item) for item in by_status_data]
        
        # Top 5 gestores
        top_managers_data = await self.repository.get_manager_performance(
            start_date, end_date, limit=5
        )
        top_managers = [ManagerPerformance(**item) for item in top_managers_data]
        
        # Últimas 6 tendencias mensuales
        recent_trends_data = await self.repository.get_trends_by_month(
            start_date, end_date, months=6
        )
        recent_trends = [TrendDataPoint(**item) for item in recent_trends_data]
        
        return DashboardOverview(
            kpis=kpis,
            by_type=by_type,
            by_status=by_status,
            top_managers=top_managers,
            recent_trends=recent_trends,
            generated_at=datetime.now(),
            period_start=start_date,
            period_end=end_date
        )
    
    # =========================================================================
    # KPIs
    # =========================================================================
    
    async def get_kpis(
        self,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
        department_id: Optional[int] = None
    ) -> OverviewKPIs:
        """
        Obtiene KPIs principales
        
        Args:
            start_date: Fecha de inicio (opcional)
            end_date: Fecha de fin (opcional)
            department_id: ID de departamento (opcional)
            
        Returns:
            OverviewKPIs con métricas principales
        """
        # Total de PQRS
        total_pqrs = await self.repository.get_total_pqrs(
            start_date, end_date, department_id
        )
        
        # Por estado
        new_pqrs = await self.repository.get_pqrs_by_status(
            'nueva', start_date, end_date, department_id
        )
        in_progress = await self.repository.get_pqrs_by_status(
            'en_proceso', start_date, end_date, department_id
        )
        resolved = await self.repository.get_pqrs_by_status(
            'resuelta', start_date, end_date, department_id
        )
        closed = await self.repository.get_pqrs_by_status(
            'cerrada', start_date, end_date, department_id
        )
        
        # Tiempos promedio
        avg_response_time_hours = await self.repository.get_avg_response_time_hours(
            start_date, end_date
        )
        avg_resolution_time_days = await self.repository.get_avg_resolution_time_days(
            start_date, end_date
        )
        
        # Tasa de resolución
        resolution_rate = await self.repository.get_resolution_rate(
            start_date, end_date
        )
        
        # Gestores activos
        active_managers = await self.repository.get_active_managers_count()
        
        return OverviewKPIs(
            total_pqrs=total_pqrs,
            new_pqrs=new_pqrs,
            in_progress=in_progress,
            resolved=resolved,
            closed=closed,
            avg_response_time_hours=avg_response_time_hours,
            avg_resolution_time_days=avg_resolution_time_days,
            resolution_rate=resolution_rate,
            satisfaction_rate=None,  # Implementar si hay sistema de calificación
            active_managers=active_managers
        )
    
    # =========================================================================
    # ESTADÍSTICAS POR TIPO
    # =========================================================================
    
    async def get_statistics_by_type(
        self,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
        department_id: Optional[int] = None
    ) -> TypeStatisticsResponse:
        """
        Obtiene estadísticas por tipo de PQRS
        
        Args:
            start_date: Fecha de inicio (opcional)
            end_date: Fecha de fin (opcional)
            department_id: ID de departamento (opcional)
            
        Returns:
            TypeStatisticsResponse con estadísticas
        """
        data = await self.repository.get_statistics_by_type(
            start_date, end_date, department_id
        )
        
        statistics = [TypeStatistics(**item) for item in data]
        total = sum(stat.count for stat in statistics)
        
        return TypeStatisticsResponse(
            statistics=statistics,
            total=total
        )
    
    # =========================================================================
    # ESTADÍSTICAS POR ESTADO
    # =========================================================================
    
    async def get_statistics_by_status(
        self,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
        department_id: Optional[int] = None
    ) -> StatusStatisticsResponse:
        """
        Obtiene estadísticas por estado
        
        Args:
            start_date: Fecha de inicio (opcional)
            end_date: Fecha de fin (opcional)
            department_id: ID de departamento (opcional)
            
        Returns:
            StatusStatisticsResponse con estadísticas
        """
        data = await self.repository.get_statistics_by_status(
            start_date, end_date, department_id
        )
        
        statistics = [StatusStatistics(**item) for item in data]
        total = sum(stat.count for stat in statistics)
        
        return StatusStatisticsResponse(
            statistics=statistics,
            total=total
        )
    
    # =========================================================================
    # PERFORMANCE DE GESTORES
    # =========================================================================
    
    async def get_manager_performance(
        self,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
        limit: int = 10
    ) -> ManagerPerformanceResponse:
        """
        Obtiene performance de gestores
        
        Args:
            start_date: Fecha de inicio (opcional)
            end_date: Fecha de fin (opcional)
            limit: Cantidad máxima de gestores a retornar
            
        Returns:
            ManagerPerformanceResponse con performance
        """
        data = await self.repository.get_manager_performance(
            start_date, end_date, limit
        )
        
        managers = [ManagerPerformance(**item) for item in data]
        
        return ManagerPerformanceResponse(
            managers=managers,
            total_managers=len(managers)
        )
    
    # =========================================================================
    # TENDENCIAS
    # =========================================================================
    
    async def get_trends_monthly(
        self,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
        months: int = 12
    ) -> TrendsResponse:
        """
        Obtiene tendencias mensuales
        
        Args:
            start_date: Fecha de inicio (opcional)
            end_date: Fecha de fin (opcional)
            months: Cantidad de meses a retornar
            
        Returns:
            TrendsResponse con tendencias
        """
        data = await self.repository.get_trends_by_month(
            start_date, end_date, months
        )
        
        trends = [TrendDataPoint(**item) for item in data]
        
        return TrendsResponse(
            trends=trends,
            period_type='monthly',
            total_periods=len(trends)
        )
    
    async def get_trends_weekly(
        self,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
        weeks: int = 12
    ) -> TrendsResponse:
        """
        Obtiene tendencias semanales
        
        Args:
            start_date: Fecha de inicio (opcional)
            end_date: Fecha de fin (opcional)
            weeks: Cantidad de semanas a retornar
            
        Returns:
            TrendsResponse con tendencias
        """
        data = await self.repository.get_trends_by_week(
            start_date, end_date, weeks
        )
        
        trends = [TrendDataPoint(**item) for item in data]
        
        return TrendsResponse(
            trends=trends,
            period_type='weekly',
            total_periods=len(trends)
        )
    
    # =========================================================================
    # ANÁLISIS DE TIEMPOS
    # =========================================================================
    
    async def get_time_analysis(
        self,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None
    ) -> TimeAnalysis:
        """
        Obtiene análisis detallado de tiempos
        
        Args:
            start_date: Fecha de inicio (opcional)
            end_date: Fecha de fin (opcional)
            
        Returns:
            TimeAnalysis con análisis de tiempos
        """
        data = await self.repository.get_time_analysis(start_date, end_date)
        
        # Tiempo promedio de primera respuesta
        avg_response_hours = await self.repository.get_avg_response_time_hours(
            start_date, end_date
        )
        
        return TimeAnalysis(
            avg_first_response_hours=avg_response_hours,
            avg_resolution_days=data['avg_resolution_days'],
            median_resolution_days=data['median_resolution_days'],
            resolved_within_24h=data['resolved_within_24h'],
            resolved_within_3d=data['resolved_within_3d'],
            resolved_within_7d=data['resolved_within_7d'],
            resolved_within_15d=data['resolved_within_15d'],
            resolved_over_15d=data['resolved_over_15d']
        )


# =============================================================================
# FUNCIÓN HELPER
# =============================================================================

def get_dashboard_service(db: AsyncSession) -> DashboardService:
    """
    Factory function para obtener una instancia del DashboardService
    
    Args:
        db: Sesión asíncrona de SQLAlchemy
        
    Returns:
        Instancia de DashboardService
    """
    return DashboardService(db)