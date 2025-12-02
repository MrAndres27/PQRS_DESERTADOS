"""
Routers del Sistema PQRS
Sistema PQRS - Equipo Desertados

Registro de todos los routers de la aplicación.
"""

from fastapi import APIRouter

# Crear router principal
api_router = APIRouter()

# =============================================================================
# REGISTRAR TODOS LOS ROUTERS
# =============================================================================

# 1. Autenticación
try:
    from app.routers.auth import router as auth_router
    api_router.include_router(
        auth_router,
        prefix="/auth",
        tags=["Autenticación"]
    )
    print("✅ Auth router cargado")
except ImportError as e:
    print(f"⚠️ No se pudo cargar auth router: {e}")

# 2. PQRS
try:
    from app.routers.pqrs import router as pqrs_router
    api_router.include_router(
        pqrs_router,
        prefix="/pqrs",
        tags=["PQRS"]
    )
    print("✅ PQRS router cargado")
except ImportError as e:
    print(f"⚠️ No se pudo cargar pqrs router: {e}")

# 3. Usuarios (Admin)
try:
    from app.routers.users import router as users_router
    api_router.include_router(
        users_router,
        prefix="/users",
        tags=["Usuarios (Admin)"]
    )
    print("✅ Users router cargado")
except ImportError as e:
    print(f"⚠️ No se pudo cargar users router: {e}")

# 4. Comentarios
try:
    from app.routers.comments import router as comments_router
    api_router.include_router(
        comments_router,
        prefix="/comments",
        tags=["Comentarios"]
    )
    print("✅ Comments router cargado")
except ImportError as e:
    print(f"⚠️ No se pudo cargar comments router: {e}")

# 5. Archivos Adjuntos
try:
    from app.routers.attachments import router as attachments_router
    api_router.include_router(
        attachments_router,
        prefix="/attachments",
        tags=["Archivos Adjuntos"]
    )
    print("✅ Attachments router cargado")
except ImportError as e:
    print(f"⚠️ No se pudo cargar attachments router: {e}")

# 6. Dashboard y Métricas
try:
    from app.routers.dashboard import router as dashboard_router
    api_router.include_router(
        dashboard_router,
        prefix="/dashboard",
        tags=["Dashboard y Métricas"]
    )
    print("✅ Dashboard router cargado")
except ImportError as e:
    print(f"⚠️ No se pudo cargar dashboard router: {e}")

# 7. Notificaciones
try:
    from app.routers.notifications import router as notifications_router
    api_router.include_router(
        notifications_router,
        prefix="/notifications",
        tags=["Notificaciones"]
    )
    print("✅ Notifications router cargado")
except ImportError as e:
    print(f"⚠️ No se pudo cargar notifications router: {e}")

# 8. Roles y Permisos (Admin)
try:
    from app.routers.roles_permissions import router as roles_permissions_router
    api_router.include_router(
        roles_permissions_router,
        # Ya tiene prefix="/admin" en el router
        tags=["Roles y Permisos (Admin)"]
    )
    print("✅ Roles/Permissions router cargado")
except ImportError as e:
    print(f"⚠️ No se pudo cargar roles_permissions router: {e}")



# Health check
try:
    from app.routers.health import router as health_router
    api_router.include_router(health_router, prefix="")
    print("✅ Health router cargado")
except ImportError as e:
    print(f"⚠️ No se pudo cargar health router: {e}")

# Lista de routers disponibles
__all__ = ["api_router"]