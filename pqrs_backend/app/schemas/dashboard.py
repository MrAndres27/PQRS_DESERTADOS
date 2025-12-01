"""
Schemas de Dashboard
Sistema PQRS - Equipo Desertados

Schemas para métricas, reportes y análisis del sistema.
"""

from pydantic import BaseModel, Field
from datetime import date, datetime
from typing import Optional, List, Dict, Any


# =============================================================================
# FILTROS
# =============================================================================

class DashboardFilters(BaseModel):
    """Filtros para consultas de dashboard"""
    start_date: Optional[date] = Field(
        default=None,
        description="Fecha de inicio del período"
    )
    end_date: Optional[date] = Field(
        default=None,
        description="Fecha de fin del período"
    )
    department_id: Optional[int] = Field(
        default=None,
        description="Filtrar por departamento"
    )
    assignee_id: Optional[int] = Field(
        default=None,
        description="Filtrar por gestor asignado"
    )
    pqrs_type: Optional[str] = Field(
        default=None,
        description="Filtrar por tipo (peticion, queja, reclamo, sugerencia)"
    )


# =============================================================================
# KPIs GENERALES
# =============================================================================

class OverviewKPIs(BaseModel):
    """KPIs principales del sistema"""
    total_pqrs: int = Field(description="Total de PQRS en el sistema")
    new_pqrs: int = Field(description="PQRS nuevas (sin asignar)")
    in_progress: int = Field(description="PQRS en proceso")
    resolved: int = Field(description="PQRS resueltas")
    closed: int = Field(description="PQRS cerradas")
    
    avg_response_time_hours: Optional[float] = Field(
        description="Tiempo promedio de primera respuesta (horas)"
    )
    avg_resolution_time_days: Optional[float] = Field(
        description="Tiempo promedio de resolución (días)"
    )
    
    resolution_rate: float = Field(
        description="Tasa de resolución (%)"
    )
    satisfaction_rate: Optional[float] = Field(
        default=None,
        description="Tasa de satisfacción promedio (%)"
    )
    
    active_managers: int = Field(
        description="Gestores activos con PQRS asignadas"
    )
    
    class Config:
        json_schema_extra = {
            "example": {
                "total_pqrs": 1250,
                "new_pqrs": 45,
                "in_progress": 230,
                "resolved": 850,
                "closed": 125,
                "avg_response_time_hours": 4.5,
                "avg_resolution_time_days": 5.2,
                "resolution_rate": 68.0,
                "satisfaction_rate": 85.5,
                "active_managers": 12
            }
        }


# =============================================================================
# ESTADÍSTICAS POR TIPO
# =============================================================================

class TypeStatistics(BaseModel):
    """Estadísticas por tipo de PQRS"""
    type: str = Field(description="Tipo de PQRS")
    count: int = Field(description="Cantidad de PQRS de este tipo")
    percentage: float = Field(description="Porcentaje del total")
    resolved: int = Field(description="Cantidad resuelta")
    avg_resolution_days: Optional[float] = Field(
        description="Días promedio de resolución"
    )
    
    class Config:
        json_schema_extra = {
            "example": {
                "type": "queja",
                "count": 450,
                "percentage": 36.0,
                "resolved": 320,
                "avg_resolution_days": 4.8
            }
        }


class TypeStatisticsResponse(BaseModel):
    """Response con estadísticas por tipo"""
    statistics: List[TypeStatistics]
    total: int = Field(description="Total de PQRS")
    
    class Config:
        json_schema_extra = {
            "example": {
                "statistics": [
                    {
                        "type": "peticion",
                        "count": 350,
                        "percentage": 28.0,
                        "resolved": 280,
                        "avg_resolution_days": 6.2
                    },
                    {
                        "type": "queja",
                        "count": 450,
                        "percentage": 36.0,
                        "resolved": 320,
                        "avg_resolution_days": 4.8
                    },
                    {
                        "type": "reclamo",
                        "count": 300,
                        "percentage": 24.0,
                        "resolved": 210,
                        "avg_resolution_days": 3.5
                    },
                    {
                        "type": "sugerencia",
                        "count": 150,
                        "percentage": 12.0,
                        "resolved": 40,
                        "avg_resolution_days": 8.5
                    }
                ],
                "total": 1250
            }
        }


# =============================================================================
# ESTADÍSTICAS POR ESTADO
# =============================================================================

class StatusStatistics(BaseModel):
    """Estadísticas por estado de PQRS"""
    status: str = Field(description="Estado de la PQRS")
    count: int = Field(description="Cantidad en este estado")
    percentage: float = Field(description="Porcentaje del total")
    avg_days_in_status: Optional[float] = Field(
        description="Días promedio en este estado"
    )
    
    class Config:
        json_schema_extra = {
            "example": {
                "status": "en_proceso",
                "count": 230,
                "percentage": 18.4,
                "avg_days_in_status": 3.5
            }
        }


class StatusStatisticsResponse(BaseModel):
    """Response con estadísticas por estado"""
    statistics: List[StatusStatistics]
    total: int = Field(description="Total de PQRS")
    
    class Config:
        json_schema_extra = {
            "example": {
                "statistics": [
                    {
                        "status": "nueva",
                        "count": 45,
                        "percentage": 3.6,
                        "avg_days_in_status": 0.5
                    },
                    {
                        "status": "en_revision",
                        "count": 120,
                        "percentage": 9.6,
                        "avg_days_in_status": 1.2
                    }
                ],
                "total": 1250
            }
        }


# =============================================================================
# PERFORMANCE DE GESTORES
# =============================================================================

class ManagerPerformance(BaseModel):
    """Performance de un gestor"""
    manager_id: int
    manager_name: str
    total_assigned: int = Field(description="Total asignadas")
    resolved: int = Field(description="Total resueltas")
    in_progress: int = Field(description="En proceso")
    avg_resolution_days: Optional[float] = Field(
        description="Días promedio de resolución"
    )
    resolution_rate: float = Field(description="Tasa de resolución (%)")
    
    class Config:
        json_schema_extra = {
            "example": {
                "manager_id": 5,
                "manager_name": "Juan Pérez",
                "total_assigned": 85,
                "resolved": 62,
                "in_progress": 18,
                "avg_resolution_days": 4.2,
                "resolution_rate": 72.9
            }
        }


class ManagerPerformanceResponse(BaseModel):
    """Response con performance de gestores"""
    managers: List[ManagerPerformance]
    total_managers: int
    
    class Config:
        json_schema_extra = {
            "example": {
                "managers": [],
                "total_managers": 12
            }
        }


# =============================================================================
# TENDENCIAS TEMPORALES
# =============================================================================

class TrendDataPoint(BaseModel):
    """Punto de dato en una tendencia temporal"""
    period: str = Field(description="Período (fecha o mes)")
    count: int = Field(description="Cantidad de PQRS")
    resolved: int = Field(description="Cantidad resuelta")
    avg_resolution_days: Optional[float] = Field(
        description="Días promedio de resolución"
    )
    
    class Config:
        json_schema_extra = {
            "example": {
                "period": "2024-11",
                "count": 125,
                "resolved": 98,
                "avg_resolution_days": 5.1
            }
        }


class TrendsResponse(BaseModel):
    """Response con tendencias temporales"""
    trends: List[TrendDataPoint]
    period_type: str = Field(description="Tipo de período (daily, weekly, monthly)")
    total_periods: int
    
    class Config:
        json_schema_extra = {
            "example": {
                "trends": [
                    {
                        "period": "2024-11",
                        "count": 125,
                        "resolved": 98,
                        "avg_resolution_days": 5.1
                    },
                    {
                        "period": "2024-12",
                        "count": 142,
                        "resolved": 110,
                        "avg_resolution_days": 4.8
                    }
                ],
                "period_type": "monthly",
                "total_periods": 2
            }
        }


# =============================================================================
# ANÁLISIS DE TIEMPOS
# =============================================================================

class TimeAnalysis(BaseModel):
    """Análisis de tiempos de respuesta y resolución"""
    avg_first_response_hours: Optional[float] = Field(
        description="Tiempo promedio hasta primera respuesta (horas)"
    )
    avg_resolution_days: Optional[float] = Field(
        description="Tiempo promedio de resolución (días)"
    )
    median_resolution_days: Optional[float] = Field(
        description="Mediana de días de resolución"
    )
    
    # Distribución por rangos
    resolved_within_24h: int = Field(description="Resueltas en menos de 24h")
    resolved_within_3d: int = Field(description="Resueltas en menos de 3 días")
    resolved_within_7d: int = Field(description="Resueltas en menos de 7 días")
    resolved_within_15d: int = Field(description="Resueltas en menos de 15 días")
    resolved_over_15d: int = Field(description="Resueltas en más de 15 días")
    
    class Config:
        json_schema_extra = {
            "example": {
                "avg_first_response_hours": 4.5,
                "avg_resolution_days": 5.2,
                "median_resolution_days": 4.0,
                "resolved_within_24h": 45,
                "resolved_within_3d": 320,
                "resolved_within_7d": 550,
                "resolved_within_15d": 680,
                "resolved_over_15d": 55
            }
        }


# =============================================================================
# ANÁLISIS POR PERÍODO
# =============================================================================

class PeriodComparison(BaseModel):
    """Comparación entre períodos"""
    current_period: Dict[str, Any] = Field(description="Datos del período actual")
    previous_period: Dict[str, Any] = Field(description="Datos del período anterior")
    changes: Dict[str, float] = Field(description="Cambios porcentuales")
    
    class Config:
        json_schema_extra = {
            "example": {
                "current_period": {
                    "total": 142,
                    "resolved": 110,
                    "avg_resolution_days": 4.8
                },
                "previous_period": {
                    "total": 125,
                    "resolved": 98,
                    "avg_resolution_days": 5.1
                },
                "changes": {
                    "total": 13.6,
                    "resolved": 12.2,
                    "avg_resolution_days": -5.9
                }
            }
        }


# =============================================================================
# DASHBOARD OVERVIEW COMPLETO
# =============================================================================

class DashboardOverview(BaseModel):
    """Vista general completa del dashboard"""
    kpis: OverviewKPIs
    by_type: List[TypeStatistics]
    by_status: List[StatusStatistics]
    top_managers: List[ManagerPerformance]
    recent_trends: List[TrendDataPoint]
    
    # Metadata
    generated_at: datetime = Field(description="Fecha y hora de generación")
    period_start: Optional[date] = Field(description="Inicio del período analizado")
    period_end: Optional[date] = Field(description="Fin del período analizado")
    
    class Config:
        json_schema_extra = {
            "example": {
                "kpis": {
                    "total_pqrs": 1250,
                    "new_pqrs": 45,
                    "in_progress": 230,
                    "resolved": 850,
                    "closed": 125,
                    "avg_response_time_hours": 4.5,
                    "avg_resolution_time_days": 5.2,
                    "resolution_rate": 68.0,
                    "satisfaction_rate": 85.5,
                    "active_managers": 12
                },
                "by_type": [],
                "by_status": [],
                "top_managers": [],
                "recent_trends": [],
                "generated_at": "2024-11-24T15:30:00",
                "period_start": "2024-01-01",
                "period_end": "2024-11-24"
            }
        }