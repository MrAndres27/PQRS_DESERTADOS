"""
Router de Dashboard
Sistema PQRS - Equipo Desertados

Endpoints para métricas, reportes y análisis del sistema.
"""

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import date
from typing import Optional

from app.core.database import get_async_db
from app.core.dependencies import get_current_user, require_admin
from app.models.user import User
from app.services.dashboard_service import get_dashboard_service, DashboardService
from app.schemas.dashboard import (
    DashboardOverview,
    OverviewKPIs,
    TypeStatisticsResponse,
    StatusStatisticsResponse,
    ManagerPerformanceResponse,
    TrendsResponse,
    TimeAnalysis
)


# =============================================================================
# ROUTER
# =============================================================================

router = APIRouter(prefix="/dashboard", tags=["Dashboard"])


# =============================================================================
# ENDPOINTS - VISTA GENERAL
# =============================================================================

@router.get(
    "/overview",
    response_model=DashboardOverview,
    status_code=status.HTTP_200_OK
)
async def get_dashboard_overview(
    start_date: Optional[date] = Query(
        default=None,
        description="Fecha de inicio del período (YYYY-MM-DD)"
    ),
    end_date: Optional[date] = Query(
        default=None,
        description="Fecha de fin del período (YYYY-MM-DD)"
    ),
    department_id: Optional[int] = Query(
        default=None,
        description="Filtrar por departamento"
    ),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_db)
):
    """
    Obtiene vista general completa del dashboard
    
    **Incluye:**
    - KPIs principales (totales, promedios, tasas)
    - Top 5 gestores por performance
    - Estadísticas por tipo de PQRS
    - Estadísticas por estado
    - Tendencias de últimos 6 meses
    
    **Filtros opcionales:**
    - `start_date`: Fecha inicio (formato: YYYY-MM-DD)
    - `end_date`: Fecha fin (formato: YYYY-MM-DD)
    - `department_id`: ID del departamento
    
    **Requiere:** Usuario autenticado
    """
    dashboard_service = get_dashboard_service(db)
    
    overview = await dashboard_service.get_overview(
        start_date=start_date,
        end_date=end_date,
        department_id=department_id
    )
    
    return overview


@router.get(
    "/kpis",
    response_model=OverviewKPIs,
    status_code=status.HTTP_200_OK
)
async def get_kpis(
    start_date: Optional[date] = Query(
        default=None,
        description="Fecha de inicio del período"
    ),
    end_date: Optional[date] = Query(
        default=None,
        description="Fecha de fin del período"
    ),
    department_id: Optional[int] = Query(
        default=None,
        description="Filtrar por departamento"
    ),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_db)
):
    """
    Obtiene KPIs principales del sistema
    
    **Métricas incluidas:**
    - Total de PQRS por estado
    - Tiempo promedio de respuesta (horas)
    - Tiempo promedio de resolución (días)
    - Tasa de resolución (%)
    - Gestores activos
    
    **Filtros opcionales:**
    - Rango de fechas
    - Departamento específico
    
    **Requiere:** Usuario autenticado
    """
    dashboard_service = get_dashboard_service(db)
    
    kpis = await dashboard_service.get_kpis(
        start_date=start_date,
        end_date=end_date,
        department_id=department_id
    )
    
    return kpis


# =============================================================================
# ENDPOINTS - ANÁLISIS POR TIPO Y ESTADO
# =============================================================================

@router.get(
    "/by-type",
    response_model=TypeStatisticsResponse,
    status_code=status.HTTP_200_OK
)
async def get_statistics_by_type(
    start_date: Optional[date] = Query(
        default=None,
        description="Fecha de inicio"
    ),
    end_date: Optional[date] = Query(
        default=None,
        description="Fecha de fin"
    ),
    department_id: Optional[int] = Query(
        default=None,
        description="Filtrar por departamento"
    ),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_db)
):
    """
    Obtiene estadísticas agrupadas por tipo de PQRS
    
    **Por cada tipo muestra:**
    - Cantidad total
    - Porcentaje del total
    - Cantidad resuelta
    - Tiempo promedio de resolución
    
    **Tipos:**
    - Petición
    - Queja
    - Reclamo
    - Sugerencia
    
    **Requiere:** Usuario autenticado
    """
    dashboard_service = get_dashboard_service(db)
    
    statistics = await dashboard_service.get_statistics_by_type(
        start_date=start_date,
        end_date=end_date,
        department_id=department_id
    )
    
    return statistics


@router.get(
    "/by-status",
    response_model=StatusStatisticsResponse,
    status_code=status.HTTP_200_OK
)
async def get_statistics_by_status(
    start_date: Optional[date] = Query(
        default=None,
        description="Fecha de inicio"
    ),
    end_date: Optional[date] = Query(
        default=None,
        description="Fecha de fin"
    ),
    department_id: Optional[int] = Query(
        default=None,
        description="Filtrar por departamento"
    ),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_db)
):
    """
    Obtiene estadísticas agrupadas por estado
    
    **Por cada estado muestra:**
    - Cantidad total
    - Porcentaje del total
    - Días promedio en ese estado
    
    **Estados:**
    - Nueva
    - En Revisión
    - En Proceso
    - Pendiente Información
    - Resuelta
    - Cerrada
    - Rechazada
    
    **Requiere:** Usuario autenticado
    """
    dashboard_service = get_dashboard_service(db)
    
    statistics = await dashboard_service.get_statistics_by_status(
        start_date=start_date,
        end_date=end_date,
        department_id=department_id
    )
    
    return statistics


# =============================================================================
# ENDPOINTS - PERFORMANCE
# =============================================================================

@router.get(
    "/managers",
    response_model=ManagerPerformanceResponse,
    status_code=status.HTTP_200_OK
)
async def get_manager_performance(
    start_date: Optional[date] = Query(
        default=None,
        description="Fecha de inicio"
    ),
    end_date: Optional[date] = Query(
        default=None,
        description="Fecha de fin"
    ),
    limit: int = Query(
        default=10,
        ge=1,
        le=50,
        description="Cantidad de gestores a mostrar (máx 50)"
    ),
    current_user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_async_db)
):
    """
    Obtiene performance de gestores (top N)
    
    **Por cada gestor muestra:**
    - Nombre completo
    - Total de PQRS asignadas
    - Cantidad resuelta
    - Cantidad en proceso
    - Tiempo promedio de resolución
    - Tasa de resolución (%)
    
    **Ordenamiento:** Por total de PQRS asignadas (DESC)
    
    **Requiere:** Rol Administrador o Gestor
    """
    dashboard_service = get_dashboard_service(db)
    
    performance = await dashboard_service.get_manager_performance(
        start_date=start_date,
        end_date=end_date,
        limit=limit
    )
    
    return performance


# =============================================================================
# ENDPOINTS - TENDENCIAS
# =============================================================================

@router.get(
    "/trends/monthly",
    response_model=TrendsResponse,
    status_code=status.HTTP_200_OK
)
async def get_trends_monthly(
    start_date: Optional[date] = Query(
        default=None,
        description="Fecha de inicio"
    ),
    end_date: Optional[date] = Query(
        default=None,
        description="Fecha de fin"
    ),
    months: int = Query(
        default=12,
        ge=1,
        le=24,
        description="Cantidad de meses (máx 24)"
    ),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_db)
):
    """
    Obtiene tendencias mensuales de PQRS
    
    **Por cada mes muestra:**
    - Período (YYYY-MM)
    - Total de PQRS creadas
    - Total de PQRS resueltas
    - Tiempo promedio de resolución
    
    **Query params:**
    - `months`: Últimos N meses (default: 12, máx: 24)
    - `start_date` y `end_date`: Rango específico
    
    **Útil para:**
    - Gráficas de líneas
    - Análisis de tendencias
    - Comparación mes a mes
    
    **Requiere:** Usuario autenticado
    """
    dashboard_service = get_dashboard_service(db)
    
    trends = await dashboard_service.get_trends_monthly(
        start_date=start_date,
        end_date=end_date,
        months=months
    )
    
    return trends


@router.get(
    "/trends/weekly",
    response_model=TrendsResponse,
    status_code=status.HTTP_200_OK
)
async def get_trends_weekly(
    start_date: Optional[date] = Query(
        default=None,
        description="Fecha de inicio"
    ),
    end_date: Optional[date] = Query(
        default=None,
        description="Fecha de fin"
    ),
    weeks: int = Query(
        default=12,
        ge=1,
        le=52,
        description="Cantidad de semanas (máx 52)"
    ),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_db)
):
    """
    Obtiene tendencias semanales de PQRS
    
    **Por cada semana muestra:**
    - Período (YYYY-WW)
    - Total de PQRS creadas
    - Total de PQRS resueltas
    - Tiempo promedio de resolución
    
    **Query params:**
    - `weeks`: Últimas N semanas (default: 12, máx: 52)
    - `start_date` y `end_date`: Rango específico
    
    **Útil para:**
    - Análisis de corto plazo
    - Detección de picos
    - Monitoreo semanal
    
    **Requiere:** Usuario autenticado
    """
    dashboard_service = get_dashboard_service(db)
    
    trends = await dashboard_service.get_trends_weekly(
        start_date=start_date,
        end_date=end_date,
        weeks=weeks
    )
    
    return trends


# =============================================================================
# ENDPOINTS - ANÁLISIS DE TIEMPOS
# =============================================================================

@router.get(
    "/time-analysis",
    response_model=TimeAnalysis,
    status_code=status.HTTP_200_OK
)
async def get_time_analysis(
    start_date: Optional[date] = Query(
        default=None,
        description="Fecha de inicio"
    ),
    end_date: Optional[date] = Query(
        default=None,
        description="Fecha de fin"
    ),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_db)
):
    """
    Obtiene análisis detallado de tiempos de respuesta y resolución
    
    **Métricas incluidas:**
    - Tiempo promedio de primera respuesta (horas)
    - Tiempo promedio de resolución (días)
    - Tiempo mediano de resolución
    
    **Distribución por rangos:**
    - Resueltas en menos de 24 horas
    - Resueltas en menos de 3 días
    - Resueltas en menos de 7 días
    - Resueltas en menos de 15 días
    - Resueltas en más de 15 días
    
    **Útil para:**
    - SLA monitoring
    - Identificar cuellos de botella
    - Optimización de procesos
    
    **Requiere:** Usuario autenticado
    """
    dashboard_service = get_dashboard_service(db)
    
    analysis = await dashboard_service.get_time_analysis(
        start_date=start_date,
        end_date=end_date
    )
    
    return analysis


# =============================================================================
# DOCUMENTACIÓN DE USO
# =============================================================================

"""
EJEMPLOS DE USO:

1. Dashboard completo sin filtros:
   GET /api/dashboard/overview
   
2. Dashboard del último mes:
   GET /api/dashboard/overview?start_date=2024-11-01&end_date=2024-11-30
   
3. KPIs de un departamento:
   GET /api/dashboard/kpis?department_id=5
   
4. Estadísticas por tipo:
   GET /api/dashboard/by-type
   
5. Top 10 gestores:
   GET /api/dashboard/managers?limit=10
   
6. Tendencias últimos 6 meses:
   GET /api/dashboard/trends/monthly?months=6
   
7. Análisis de tiempos del último trimestre:
   GET /api/dashboard/time-analysis?start_date=2024-09-01&end_date=2024-11-30

FILTROS DISPONIBLES:

- start_date: YYYY-MM-DD (ej: 2024-01-01)
- end_date: YYYY-MM-DD (ej: 2024-12-31)
- department_id: ID numérico del departamento
- limit: Cantidad de resultados (para /managers)
- months: Cantidad de meses (para /trends/monthly)
- weeks: Cantidad de semanas (para /trends/weekly)

PERMISOS:

- Todos los endpoints requieren autenticación
- /managers requiere rol Admin o Gestor
- Los demás endpoints permiten cualquier usuario autenticado

CASOS DE USO:

1. Panel de administración:
   - Llamar /overview para vista completa
   - Mostrar KPIs en cards grandes
   - Gráfica de tendencias mensuales
   - Tabla de top gestores

2. Panel de gestor:
   - Llamar /kpis para métricas personales
   - Llamar /by-status para ver distribución
   - Llamar /time-analysis para SLA

3. Reportes ejecutivos:
   - Filtrar por período (trimestre, año)
   - Exportar a Excel/PDF (implementar si es necesario)
   - Comparar con período anterior

4. Monitoreo en tiempo real:
   - Llamar /overview cada 5 minutos
   - Alertas si métricas caen
   - Dashboard actualizado automáticamente
"""