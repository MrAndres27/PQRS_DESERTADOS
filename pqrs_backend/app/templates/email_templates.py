"""
Plantillas de Email
Sistema PQRS - Equipo Desertados

Plantillas HTML profesionales para diferentes tipos de notificaciones.
"""

from datetime import datetime
from typing import Dict, Any


# =============================================================================
# PLANTILLA BASE
# =============================================================================

BASE_TEMPLATE = """
<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{title}</title>
    <style>
        body {{
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            line-height: 1.6;
            color: #333333;
            background-color: #f4f4f4;
            margin: 0;
            padding: 0;
        }}
        .container {{
            max-width: 600px;
            margin: 20px auto;
            background-color: #ffffff;
            border-radius: 8px;
            overflow: hidden;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }}
        .header {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: #ffffff;
            padding: 30px 20px;
            text-align: center;
        }}
        .header h1 {{
            margin: 0;
            font-size: 28px;
            font-weight: 600;
        }}
        .content {{
            padding: 30px 20px;
        }}
        .alert-box {{
            background-color: {alert_color};
            border-left: 4px solid {alert_border};
            padding: 15px;
            margin: 20px 0;
            border-radius: 4px;
        }}
        .info-table {{
            width: 100%;
            border-collapse: collapse;
            margin: 20px 0;
        }}
        .info-table td {{
            padding: 10px;
            border-bottom: 1px solid #eeeeee;
        }}
        .info-table td:first-child {{
            font-weight: 600;
            width: 40%;
            color: #666666;
        }}
        .button {{
            display: inline-block;
            padding: 12px 30px;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: #ffffff !important;
            text-decoration: none;
            border-radius: 5px;
            margin: 20px 0;
            font-weight: 600;
        }}
        .footer {{
            background-color: #f8f9fa;
            padding: 20px;
            text-align: center;
            font-size: 12px;
            color: #666666;
            border-top: 1px solid #eeeeee;
        }}
        .footer a {{
            color: #667eea;
            text-decoration: none;
        }}
        .badge {{
            display: inline-block;
            padding: 5px 10px;
            border-radius: 3px;
            font-size: 12px;
            font-weight: 600;
            background-color: {badge_color};
            color: #ffffff;
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>📋 Sistema PQRS</h1>
            <p style="margin: 5px 0 0 0; opacity: 0.9;">{subtitle}</p>
        </div>
        <div class="content">
            {content}
        </div>
        <div class="footer">
            <p>Este es un correo automático del Sistema PQRS.</p>
            <p>Si tienes alguna pregunta, por favor contacta a soporte.</p>
            <p style="margin-top: 15px;">
                <a href="{frontend_url}">Ir al Sistema PQRS</a>
            </p>
            <p style="margin-top: 10px; color: #999999;">
                © {year} Sistema PQRS - Todos los derechos reservados
            </p>
        </div>
    </div>
</body>
</html>
"""


# =============================================================================
# PLANTILLA: PQRS CREADA
# =============================================================================

def get_pqrs_created_template(data: Dict[str, Any]) -> str:
    """
    Plantilla para cuando se crea una nueva PQRS
    
    Args:
        data: Dict con: radicado_number, type, subject, user_name, created_at
    """
    content = f"""
        <h2 style="color: #667eea; margin-top: 0;">¡Tu PQRS ha sido registrada exitosamente!</h2>
        
        <p>Hola <strong>{data.get('user_name', 'Usuario')}</strong>,</p>
        
        <p>Hemos recibido tu solicitud y ha sido registrada en nuestro sistema. A continuación encontrarás los detalles:</p>
        
        <div class="alert-box">
            <strong>📝 Número de Radicado:</strong><br>
            <span style="font-size: 24px; color: #667eea; font-weight: 700;">{data.get('radicado_number')}</span>
        </div>
        
        <table class="info-table">
            <tr>
                <td>Tipo:</td>
                <td><span class="badge">{data.get('type', 'N/A').upper()}</span></td>
            </tr>
            <tr>
                <td>Asunto:</td>
                <td>{data.get('subject', 'N/A')}</td>
            </tr>
            <tr>
                <td>Fecha de registro:</td>
                <td>{data.get('created_at', 'N/A')}</td>
            </tr>
            <tr>
                <td>Estado:</td>
                <td><span class="badge">NUEVA</span></td>
            </tr>
        </table>
        
        <p><strong>¿Qué sigue?</strong></p>
        <ul>
            <li>Tu solicitud será revisada por nuestro equipo</li>
            <li>Recibirás notificaciones sobre cualquier cambio de estado</li>
            <li>Puedes consultar el estado en cualquier momento usando tu número de radicado</li>
        </ul>
        
        <center>
            <a href="{data.get('frontend_url')}/pqrs/{data.get('radicado_number')}" class="button">
                Ver mi PQRS
            </a>
        </center>
        
        <p style="color: #666666; font-size: 14px; margin-top: 30px;">
            <strong>Consejo:</strong> Guarda este número de radicado para futuras consultas.
        </p>
    """
    
    return BASE_TEMPLATE.format(
        title="PQRS Creada Exitosamente",
        subtitle="Nueva Solicitud Registrada",
        content=content,
        alert_color="#e8f5e9",
        alert_border="#4caf50",
        badge_color="#667eea",
        frontend_url=data.get('frontend_url', '#'),
        year=datetime.now().year
    )


# =============================================================================
# PLANTILLA: PQRS ASIGNADA A GESTOR
# =============================================================================

def get_pqrs_assigned_template(data: Dict[str, Any]) -> str:
    """
    Plantilla para cuando una PQRS es asignada a un gestor
    
    Args:
        data: Dict con: radicado_number, type, subject, assignee_name, priority
    """
    priority_colors = {
        'baja': '#4caf50',
        'media': '#ff9800',
        'alta': '#f44336',
        'critica': '#9c27b0'
    }
    
    priority = data.get('priority', 'media').lower()
    priority_color = priority_colors.get(priority, '#ff9800')
    
    content = f"""
        <h2 style="color: #667eea; margin-top: 0;">Te han asignado una nueva PQRS</h2>
        
        <p>Hola <strong>{data.get('assignee_name', 'Gestor')}</strong>,</p>
        
        <p>Se te ha asignado una nueva solicitud que requiere tu atención:</p>
        
        <div class="alert-box">
            <strong>📝 Número de Radicado:</strong><br>
            <span style="font-size: 24px; color: #667eea; font-weight: 700;">{data.get('radicado_number')}</span>
        </div>
        
        <table class="info-table">
            <tr>
                <td>Tipo:</td>
                <td><span class="badge">{data.get('type', 'N/A').upper()}</span></td>
            </tr>
            <tr>
                <td>Asunto:</td>
                <td>{data.get('subject', 'N/A')}</td>
            </tr>
            <tr>
                <td>Prioridad:</td>
                <td><span class="badge" style="background-color: {priority_color};">{priority.upper()}</span></td>
            </tr>
            <tr>
                <td>Ciudadano:</td>
                <td>{data.get('citizen_name', 'N/A')}</td>
            </tr>
            <tr>
                <td>Fecha límite:</td>
                <td>{data.get('due_date', 'N/A')}</td>
            </tr>
        </table>
        
        <center>
            <a href="{data.get('frontend_url')}/pqrs/{data.get('radicado_number')}" class="button">
                Ver detalles de la PQRS
            </a>
        </center>
        
        <p style="color: #666666; font-size: 14px; margin-top: 30px;">
            Por favor, atiende esta solicitud lo antes posible.
        </p>
    """
    
    return BASE_TEMPLATE.format(
        title="Nueva PQRS Asignada",
        subtitle="Solicitud pendiente de atención",
        content=content,
        alert_color="#fff3e0",
        alert_border="#ff9800",
        badge_color="#667eea",
        frontend_url=data.get('frontend_url', '#'),
        year=datetime.now().year
    )


# =============================================================================
# PLANTILLA: CAMBIO DE ESTADO
# =============================================================================

def get_status_changed_template(data: Dict[str, Any]) -> str:
    """
    Plantilla para cuando cambia el estado de una PQRS
    
    Args:
        data: Dict con: radicado_number, old_status, new_status, user_name
    """
    status_colors = {
        'nueva': '#2196f3',
        'en revision': '#ff9800',
        'en proceso': '#9c27b0',
        'pendiente informacion': '#f44336',
        'resuelta': '#4caf50',
        'cerrada': '#607d8b',
        'rechazada': '#f44336'
    }
    
    new_status = data.get('new_status', '').lower()
    status_color = status_colors.get(new_status, '#667eea')
    
    content = f"""
        <h2 style="color: #667eea; margin-top: 0;">Actualización de tu PQRS</h2>
        
        <p>Hola <strong>{data.get('user_name', 'Usuario')}</strong>,</p>
        
        <p>El estado de tu solicitud ha cambiado:</p>
        
        <div class="alert-box">
            <strong>📝 Número de Radicado:</strong><br>
            <span style="font-size: 24px; color: #667eea; font-weight: 700;">{data.get('radicado_number')}</span>
        </div>
        
        <table class="info-table">
            <tr>
                <td>Estado anterior:</td>
                <td><span class="badge" style="background-color: #999999;">{data.get('old_status', 'N/A').upper()}</span></td>
            </tr>
            <tr>
                <td>Estado actual:</td>
                <td><span class="badge" style="background-color: {status_color};">{data.get('new_status', 'N/A').upper()}</span></td>
            </tr>
            <tr>
                <td>Fecha de cambio:</td>
                <td>{data.get('changed_at', datetime.now().strftime('%Y-%m-%d %H:%M'))}</td>
            </tr>
        </table>
        
        {f'<div class="alert-box"><strong>Comentario del gestor:</strong><br>{data.get("comment", "")}</div>' if data.get('comment') else ''}
        
        <center>
            <a href="{data.get('frontend_url')}/pqrs/{data.get('radicado_number')}" class="button">
                Ver detalles completos
            </a>
        </center>
        
        <p style="color: #666666; font-size: 14px; margin-top: 30px;">
            Mantente informado sobre el progreso de tu solicitud.
        </p>
    """
    
    return BASE_TEMPLATE.format(
        title="Cambio de Estado - PQRS",
        subtitle="Tu solicitud ha sido actualizada",
        content=content,
        alert_color="#e3f2fd",
        alert_border="#2196f3",
        badge_color="#667eea",
        frontend_url=data.get('frontend_url', '#'),
        year=datetime.now().year
    )


# =============================================================================
# PLANTILLA: PQRS RESUELTA
# =============================================================================

def get_pqrs_resolved_template(data: Dict[str, Any]) -> str:
    """
    Plantilla para cuando una PQRS es resuelta
    
    Args:
        data: Dict con: radicado_number, user_name, resolution, resolved_at
    """
    content = f"""
        <h2 style="color: #4caf50; margin-top: 0;">✅ ¡Tu PQRS ha sido resuelta!</h2>
        
        <p>Hola <strong>{data.get('user_name', 'Usuario')}</strong>,</p>
        
        <p>Nos complace informarte que tu solicitud ha sido atendida y resuelta exitosamente.</p>
        
        <div class="alert-box" style="background-color: #e8f5e9; border-left-color: #4caf50;">
            <strong>📝 Número de Radicado:</strong><br>
            <span style="font-size: 24px; color: #4caf50; font-weight: 700;">{data.get('radicado_number')}</span>
        </div>
        
        <table class="info-table">
            <tr>
                <td>Estado final:</td>
                <td><span class="badge" style="background-color: #4caf50;">RESUELTA</span></td>
            </tr>
            <tr>
                <td>Fecha de resolución:</td>
                <td>{data.get('resolved_at', 'N/A')}</td>
            </tr>
            <tr>
                <td>Tiempo de atención:</td>
                <td>{data.get('resolution_time', 'N/A')}</td>
            </tr>
        </table>
        
        {f'<div class="alert-box"><strong>Detalles de la resolución:</strong><br>{data.get("resolution", "")}</div>' if data.get('resolution') else ''}
        
        <center>
            <a href="{data.get('frontend_url')}/pqrs/{data.get('radicado_number')}" class="button">
                Ver resolución completa
            </a>
        </center>
        
        <p style="margin-top: 30px;"><strong>¿Cómo calificarías nuestro servicio?</strong></p>
        <p style="color: #666666; font-size: 14px;">
            Tu opinión es muy importante para nosotros. Por favor, tómate un momento para calificar la atención recibida.
        </p>
        
        <center style="margin: 20px 0;">
            <a href="{data.get('frontend_url')}/pqrs/{data.get('radicado_number')}/feedback" 
               style="display: inline-block; padding: 10px 20px; margin: 5px; background-color: #4caf50; color: white; text-decoration: none; border-radius: 5px;">
                ⭐ Calificar servicio
            </a>
        </center>
    """
    
    return BASE_TEMPLATE.format(
        title="PQRS Resuelta",
        subtitle="Tu solicitud ha sido atendida",
        content=content,
        alert_color="#e8f5e9",
        alert_border="#4caf50",
        badge_color="#4caf50",
        frontend_url=data.get('frontend_url', '#'),
        year=datetime.now().year
    )


# =============================================================================
# PLANTILLA: NUEVO COMENTARIO
# =============================================================================

def get_new_comment_template(data: Dict[str, Any]) -> str:
    """
    Plantilla para cuando hay un nuevo comentario en una PQRS
    
    Args:
        data: Dict con: radicado_number, user_name, author_name, comment
    """
    content = f"""
        <h2 style="color: #667eea; margin-top: 0;">💬 Nuevo comentario en tu PQRS</h2>
        
        <p>Hola <strong>{data.get('user_name', 'Usuario')}</strong>,</p>
        
        <p>Se ha agregado un nuevo comentario a tu solicitud:</p>
        
        <div class="alert-box">
            <strong>📝 Número de Radicado:</strong><br>
            <span style="font-size: 24px; color: #667eea; font-weight: 700;">{data.get('radicado_number')}</span>
        </div>
        
        <div class="alert-box" style="background-color: #f5f5f5; border-left-color: #667eea;">
            <strong>Comentario de {data.get('author_name', 'Sistema')}:</strong><br>
            <p style="margin: 10px 0 0 0; color: #333333;">
                {data.get('comment', 'Sin comentario')}
            </p>
            <p style="margin: 10px 0 0 0; font-size: 12px; color: #999999;">
                {data.get('commented_at', datetime.now().strftime('%Y-%m-%d %H:%M'))}
            </p>
        </div>
        
        <center>
            <a href="{data.get('frontend_url')}/pqrs/{data.get('radicado_number')}" class="button">
                Ver todos los comentarios
            </a>
        </center>
    """
    
    return BASE_TEMPLATE.format(
        title="Nuevo Comentario - PQRS",
        subtitle="Actualización en tu solicitud",
        content=content,
        alert_color="#e3f2fd",
        alert_border="#2196f3",
        badge_color="#667eea",
        frontend_url=data.get('frontend_url', '#'),
        year=datetime.now().year
    )


# =============================================================================
# PLANTILLA: EMAIL DE PRUEBA
# =============================================================================

def get_test_email_template(data: Dict[str, Any]) -> str:
    """
    Plantilla para email de prueba
    
    Args:
        data: Dict con: test_message, sent_at
    """
    content = f"""
        <h2 style="color: #667eea; margin-top: 0;">🧪 Email de Prueba</h2>
        
        <p>Este es un email de prueba del Sistema PQRS.</p>
        
        <div class="alert-box" style="background-color: #fff3e0; border-left-color: #ff9800;">
            <strong>⚡ Configuración de email funcionando correctamente</strong><br>
            <p style="margin: 10px 0 0 0;">
                Si estás recibiendo este mensaje, significa que el sistema de notificaciones por email está configurado y funcionando correctamente.
            </p>
        </div>
        
        <table class="info-table">
            <tr>
                <td>Tipo de prueba:</td>
                <td>Email de prueba</td>
            </tr>
            <tr>
                <td>Enviado el:</td>
                <td>{data.get('sent_at', datetime.now().strftime('%Y-%m-%d %H:%M:%S'))}</td>
            </tr>
            <tr>
                <td>Estado:</td>
                <td><span class="badge" style="background-color: #4caf50;">EXITOSO</span></td>
            </tr>
        </table>
        
        {f'<p style="margin-top: 20px; padding: 15px; background-color: #f5f5f5; border-radius: 5px;"><strong>Mensaje de prueba:</strong><br>{data.get("test_message", "Sin mensaje")}</p>' if data.get('test_message') else ''}
        
        <p style="color: #666666; font-size: 14px; margin-top: 30px;">
            <strong>Nota:</strong> Este es solo un email de prueba. No requiere ninguna acción de tu parte.
        </p>
    """
    
    return BASE_TEMPLATE.format(
        title="Email de Prueba - Sistema PQRS",
        subtitle="Verificación de configuración SMTP",
        content=content,
        alert_color="#e8f5e9",
        alert_border="#4caf50",
        badge_color="#667eea",
        frontend_url=data.get('frontend_url', '#'),
        year=datetime.now().year
    )