"""
Configuración de Email
Sistema PQRS - Equipo Desertados

Configuración SMTP para envío de emails automáticos.
Soporta Gmail, Outlook y servidores SMTP personalizados.
"""

from pydantic_settings import BaseSettings
from typing import Optional


class EmailSettings(BaseSettings):
    """
    Configuración de email para notificaciones
    
    Variables de entorno necesarias:
    - SMTP_HOST: Servidor SMTP (ej: smtp.gmail.com)
    - SMTP_PORT: Puerto SMTP (ej: 587 para TLS, 465 para SSL)
    - SMTP_USER: Usuario/email para autenticación
    - SMTP_PASSWORD: Contraseña o App Password
    - SMTP_FROM_EMAIL: Email remitente
    - SMTP_FROM_NAME: Nombre del remitente
    """
    
    # Configuración SMTP
    SMTP_HOST: str = "smtp.gmail.com"
    SMTP_PORT: int = 587
    SMTP_USER: str = ""
    SMTP_PASSWORD: str = ""
    SMTP_USE_TLS: bool = True
    SMTP_USE_SSL: bool = False
    
    # Información del remitente
    SMTP_FROM_EMAIL: str = ""
    SMTP_FROM_NAME: str = "Sistema PQRS"
    
    # URLs del sistema (para links en emails)
    FRONTEND_URL: str = "http://localhost:4200"
    BACKEND_URL: str = "http://localhost:8000"
    
    # Configuración de reintentos
    EMAIL_MAX_RETRIES: int = 3
    EMAIL_RETRY_DELAY: int = 60  # segundos
    
    # Habilitar/deshabilitar envío de emails
    EMAIL_ENABLED: bool = True
    
    # Email para pruebas (enviar todos los emails aquí en modo dev)
    EMAIL_TEST_MODE: bool = False
    EMAIL_TEST_ADDRESS: Optional[str] = None
    
    class Config:
        env_file = ".env"
        case_sensitive = True
        extra = "ignore"  # Ignorar variables extra del .env


# =============================================================================
# PRESETS PARA PROVEEDORES COMUNES
# =============================================================================

GMAIL_SETTINGS = {
    "SMTP_HOST": "smtp.gmail.com",
    "SMTP_PORT": 587,
    "SMTP_USE_TLS": True,
    "SMTP_USE_SSL": False,
}

OUTLOOK_SETTINGS = {
    "SMTP_HOST": "smtp-mail.outlook.com",
    "SMTP_PORT": 587,
    "SMTP_USE_TLS": True,
    "SMTP_USE_SSL": False,
}

OFFICE365_SETTINGS = {
    "SMTP_HOST": "smtp.office365.com",
    "SMTP_PORT": 587,
    "SMTP_USE_TLS": True,
    "SMTP_USE_SSL": False,
}


# =============================================================================
# INSTANCIA GLOBAL
# =============================================================================

email_settings = EmailSettings()


# =============================================================================
# FUNCIONES HELPER
# =============================================================================

def get_email_settings() -> EmailSettings:
    """
    Obtiene la configuración de email
    
    Returns:
        Instancia de EmailSettings
    """
    return email_settings


def is_email_enabled() -> bool:
    """
    Verifica si el envío de emails está habilitado
    
    Returns:
        True si está habilitado
    """
    return email_settings.EMAIL_ENABLED and bool(
        email_settings.SMTP_HOST and
        email_settings.SMTP_USER and
        email_settings.SMTP_PASSWORD and
        email_settings.SMTP_FROM_EMAIL
    )


def validate_email_config() -> dict:
    """
    Valida la configuración de email
    
    Returns:
        Dict con resultado de validación
    """
    errors = []
    
    if not email_settings.SMTP_HOST:
        errors.append("SMTP_HOST no configurado")
    
    if not email_settings.SMTP_USER:
        errors.append("SMTP_USER no configurado")
    
    if not email_settings.SMTP_PASSWORD:
        errors.append("SMTP_PASSWORD no configurado")
    
    if not email_settings.SMTP_FROM_EMAIL:
        errors.append("SMTP_FROM_EMAIL no configurado")
    
    if email_settings.SMTP_USE_TLS and email_settings.SMTP_USE_SSL:
        errors.append("No se puede usar TLS y SSL simultáneamente")
    
    return {
        "valid": len(errors) == 0,
        "errors": errors,
        "config": {
            "host": email_settings.SMTP_HOST,
            "port": email_settings.SMTP_PORT,
            "user": email_settings.SMTP_USER,
            "from_email": email_settings.SMTP_FROM_EMAIL,
            "from_name": email_settings.SMTP_FROM_NAME,
            "tls": email_settings.SMTP_USE_TLS,
            "ssl": email_settings.SMTP_USE_SSL,
            "enabled": email_settings.EMAIL_ENABLED,
            "test_mode": email_settings.EMAIL_TEST_MODE,
        }
    }


# =============================================================================
# DOCUMENTACIÓN DE CONFIGURACIÓN
# =============================================================================

"""
CONFIGURACIÓN EN .env:

# === GMAIL ===
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=tu-email@gmail.com
SMTP_PASSWORD=tu-app-password  # No tu contraseña normal, usa App Password
SMTP_FROM_EMAIL=tu-email@gmail.com
SMTP_FROM_NAME=Sistema PQRS
SMTP_USE_TLS=True
EMAIL_ENABLED=True

NOTA GMAIL: 
1. Ve a: https://myaccount.google.com/apppasswords
2. Genera una "App Password" (no uses tu contraseña normal)
3. Usa esa App Password en SMTP_PASSWORD

# === OUTLOOK ===
SMTP_HOST=smtp-mail.outlook.com
SMTP_PORT=587
SMTP_USER=tu-email@outlook.com
SMTP_PASSWORD=tu-contraseña
SMTP_FROM_EMAIL=tu-email@outlook.com
SMTP_FROM_NAME=Sistema PQRS
SMTP_USE_TLS=True
EMAIL_ENABLED=True

# === OFFICE 365 ===
SMTP_HOST=smtp.office365.com
SMTP_PORT=587
SMTP_USER=tu-email@tuempresa.com
SMTP_PASSWORD=tu-contraseña
SMTP_FROM_EMAIL=tu-email@tuempresa.com
SMTP_FROM_NAME=Sistema PQRS
SMTP_USE_TLS=True
EMAIL_ENABLED=True

# === SERVIDOR SMTP PERSONALIZADO ===
SMTP_HOST=mail.tudominio.com
SMTP_PORT=587  # o 465 para SSL
SMTP_USER=notificaciones@tudominio.com
SMTP_PASSWORD=tu-contraseña-segura
SMTP_FROM_EMAIL=notificaciones@tudominio.com
SMTP_FROM_NAME=Sistema PQRS - Tu Empresa
SMTP_USE_TLS=True  # o False si usas SSL
SMTP_USE_SSL=False  # True si usas puerto 465
EMAIL_ENABLED=True

# === URLs DEL SISTEMA ===
FRONTEND_URL=http://localhost:4200
BACKEND_URL=http://localhost:8000

# === MODO DE PRUEBAS (OPCIONAL) ===
EMAIL_TEST_MODE=False  # True para enviar todos los emails a EMAIL_TEST_ADDRESS
EMAIL_TEST_ADDRESS=pruebas@tuempresa.com  # Solo si EMAIL_TEST_MODE=True

# === DESHABILITAR EMAILS (DESARROLLO) ===
EMAIL_ENABLED=False  # Poner en False para desactivar completamente
"""