"""
Servicio de Email
Sistema PQRS - Equipo Desertados

Maneja el envío de emails usando SMTP con soporte para:
- Envío asíncrono
- Reintentos automáticos
- Modo de prueba
- Logging de emails enviados
"""

import smtplib
import asyncio
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime
from typing import Optional, List
import logging

from app.config.email_config import get_email_settings, is_email_enabled
from app.templates import email_templates


# Configurar logging
logger = logging.getLogger(__name__)


class EmailService:
    """Servicio para envío de emails"""
    
    def __init__(self):
        """Inicializa el servicio de email"""
        self.settings = get_email_settings()
    
    # =========================================================================
    # ENVÍO DE EMAILS
    # =========================================================================
    
    async def send_email(
        self,
        to_email: str,
        subject: str,
        html_body: str,
        to_name: Optional[str] = None
    ) -> dict:
        """
        Envía un email
        
        Args:
            to_email: Email del destinatario
            subject: Asunto del email
            html_body: Cuerpo del email en HTML
            to_name: Nombre del destinatario (opcional)
            
        Returns:
            Dict con resultado del envío: {success, message, error}
        """
        # Verificar si el envío está habilitado
        if not is_email_enabled():
            logger.warning("Email sending is disabled")
            return {
                "success": False,
                "message": "Email sending is disabled",
                "error": "EMAIL_DISABLED"
            }
        
        # Modo de prueba: redirigir a email de prueba
        original_to_email = to_email
        if self.settings.EMAIL_TEST_MODE and self.settings.EMAIL_TEST_ADDRESS:
            to_email = self.settings.EMAIL_TEST_ADDRESS
            subject = f"[TEST - Original: {original_to_email}] {subject}"
            logger.info(f"Test mode: redirecting email to {to_email}")
        
        try:
            # Crear mensaje
            msg = MIMEMultipart('alternative')
            msg['From'] = f"{self.settings.SMTP_FROM_NAME} <{self.settings.SMTP_FROM_EMAIL}>"
            msg['To'] = f"{to_name} <{to_email}>" if to_name else to_email
            msg['Subject'] = subject
            
            # Agregar cuerpo HTML
            html_part = MIMEText(html_body, 'html', 'utf-8')
            msg.attach(html_part)
            
            # Enviar usando asyncio
            result = await self._send_smtp(msg, to_email)
            
            if result['success']:
                logger.info(f"Email sent successfully to {to_email}: {subject}")
            else:
                logger.error(f"Failed to send email to {to_email}: {result.get('error')}")
            
            return result
        
        except Exception as e:
            logger.error(f"Unexpected error sending email: {str(e)}")
            return {
                "success": False,
                "message": f"Error sending email: {str(e)}",
                "error": str(e)
            }
    
    async def _send_smtp(self, msg: MIMEMultipart, to_email: str) -> dict:
        """
        Envía email usando SMTP
        
        Args:
            msg: Mensaje MIME a enviar
            to_email: Email del destinatario
            
        Returns:
            Dict con resultado
        """
        def _send():
            try:
                # Conectar al servidor SMTP
                if self.settings.SMTP_USE_SSL:
                    # SSL (puerto 465)
                    server = smtplib.SMTP_SSL(
                        self.settings.SMTP_HOST,
                        self.settings.SMTP_PORT,
                        timeout=30
                    )
                else:
                    # TLS (puerto 587) o sin encriptación
                    server = smtplib.SMTP(
                        self.settings.SMTP_HOST,
                        self.settings.SMTP_PORT,
                        timeout=30
                    )
                    
                    if self.settings.SMTP_USE_TLS:
                        server.starttls()
                
                # Autenticar
                server.login(
                    self.settings.SMTP_USER,
                    self.settings.SMTP_PASSWORD
                )
                
                # Enviar mensaje
                server.send_message(msg)
                server.quit()
                
                return {
                    "success": True,
                    "message": "Email sent successfully"
                }
            
            except smtplib.SMTPAuthenticationError as e:
                return {
                    "success": False,
                    "message": "SMTP authentication failed",
                    "error": f"SMTP_AUTH_ERROR: {str(e)}"
                }
            
            except smtplib.SMTPException as e:
                return {
                    "success": False,
                    "message": "SMTP error occurred",
                    "error": f"SMTP_ERROR: {str(e)}"
                }
            
            except Exception as e:
                return {
                    "success": False,
                    "message": "Unexpected error",
                    "error": str(e)
                }
        
        # Ejecutar en thread pool (SMTP es bloqueante)
        loop = asyncio.get_event_loop()
        result = await loop.run_in_executor(None, _send)
        
        return result
    
    # =========================================================================
    # MÉTODOS ESPECÍFICOS PARA EVENTOS PQRS
    # =========================================================================
    
    async def send_pqrs_created(
        self,
        to_email: str,
        to_name: str,
        radicado_number: str,
        pqrs_type: str,
        subject: str,
        created_at: str
    ) -> dict:
        """
        Envía email cuando se crea una PQRS
        
        Args:
            to_email: Email del ciudadano
            to_name: Nombre del ciudadano
            radicado_number: Número de radicado
            pqrs_type: Tipo de PQRS
            subject: Asunto de la PQRS
            created_at: Fecha de creación
            
        Returns:
            Dict con resultado
        """
        data = {
            'user_name': to_name,
            'radicado_number': radicado_number,
            'type': pqrs_type,
            'subject': subject,
            'created_at': created_at,
            'frontend_url': self.settings.FRONTEND_URL
        }
        
        html_body = email_templates.get_pqrs_created_template(data)
        
        return await self.send_email(
            to_email=to_email,
            subject=f"PQRS Registrada - Radicado {radicado_number}",
            html_body=html_body,
            to_name=to_name
        )
    
    async def send_pqrs_assigned(
        self,
        to_email: str,
        to_name: str,
        radicado_number: str,
        pqrs_type: str,
        subject: str,
        priority: str,
        citizen_name: str,
        due_date: Optional[str] = None
    ) -> dict:
        """
        Envía email cuando se asigna una PQRS a un gestor
        
        Args:
            to_email: Email del gestor
            to_name: Nombre del gestor
            radicado_number: Número de radicado
            pqrs_type: Tipo de PQRS
            subject: Asunto de la PQRS
            priority: Prioridad
            citizen_name: Nombre del ciudadano
            due_date: Fecha límite (opcional)
            
        Returns:
            Dict con resultado
        """
        data = {
            'assignee_name': to_name,
            'radicado_number': radicado_number,
            'type': pqrs_type,
            'subject': subject,
            'priority': priority,
            'citizen_name': citizen_name,
            'due_date': due_date or 'No definida',
            'frontend_url': self.settings.FRONTEND_URL
        }
        
        html_body = email_templates.get_pqrs_assigned_template(data)
        
        return await self.send_email(
            to_email=to_email,
            subject=f"Nueva PQRS Asignada - Radicado {radicado_number}",
            html_body=html_body,
            to_name=to_name
        )
    
    async def send_status_changed(
        self,
        to_email: str,
        to_name: str,
        radicado_number: str,
        old_status: str,
        new_status: str,
        comment: Optional[str] = None
    ) -> dict:
        """
        Envía email cuando cambia el estado de una PQRS
        
        Args:
            to_email: Email del ciudadano
            to_name: Nombre del ciudadano
            radicado_number: Número de radicado
            old_status: Estado anterior
            new_status: Estado nuevo
            comment: Comentario del gestor (opcional)
            
        Returns:
            Dict con resultado
        """
        data = {
            'user_name': to_name,
            'radicado_number': radicado_number,
            'old_status': old_status,
            'new_status': new_status,
            'changed_at': datetime.now().strftime('%Y-%m-%d %H:%M'),
            'comment': comment,
            'frontend_url': self.settings.FRONTEND_URL
        }
        
        html_body = email_templates.get_status_changed_template(data)
        
        return await self.send_email(
            to_email=to_email,
            subject=f"Actualización de tu PQRS - Radicado {radicado_number}",
            html_body=html_body,
            to_name=to_name
        )
    
    async def send_pqrs_resolved(
        self,
        to_email: str,
        to_name: str,
        radicado_number: str,
        resolution: str,
        resolved_at: str,
        resolution_time: Optional[str] = None
    ) -> dict:
        """
        Envía email cuando se resuelve una PQRS
        
        Args:
            to_email: Email del ciudadano
            to_name: Nombre del ciudadano
            radicado_number: Número de radicado
            resolution: Descripción de la resolución
            resolved_at: Fecha de resolución
            resolution_time: Tiempo que tomó resolverla (opcional)
            
        Returns:
            Dict con resultado
        """
        data = {
            'user_name': to_name,
            'radicado_number': radicado_number,
            'resolution': resolution,
            'resolved_at': resolved_at,
            'resolution_time': resolution_time or 'N/A',
            'frontend_url': self.settings.FRONTEND_URL
        }
        
        html_body = email_templates.get_pqrs_resolved_template(data)
        
        return await self.send_email(
            to_email=to_email,
            subject=f"¡Tu PQRS ha sido resuelta! - Radicado {radicado_number}",
            html_body=html_body,
            to_name=to_name
        )
    
    async def send_new_comment(
        self,
        to_email: str,
        to_name: str,
        radicado_number: str,
        author_name: str,
        comment: str,
        commented_at: str
    ) -> dict:
        """
        Envía email cuando hay un nuevo comentario
        
        Args:
            to_email: Email del destinatario
            to_name: Nombre del destinatario
            radicado_number: Número de radicado
            author_name: Nombre del autor del comentario
            comment: Contenido del comentario
            commented_at: Fecha del comentario
            
        Returns:
            Dict con resultado
        """
        data = {
            'user_name': to_name,
            'radicado_number': radicado_number,
            'author_name': author_name,
            'comment': comment,
            'commented_at': commented_at,
            'frontend_url': self.settings.FRONTEND_URL
        }
        
        html_body = email_templates.get_new_comment_template(data)
        
        return await self.send_email(
            to_email=to_email,
            subject=f"Nuevo comentario en tu PQRS - Radicado {radicado_number}",
            html_body=html_body,
            to_name=to_name
        )
    
    async def send_test_email(
        self,
        to_email: str,
        to_name: Optional[str] = None,
        test_message: Optional[str] = None
    ) -> dict:
        """
        Envía email de prueba
        
        Args:
            to_email: Email de prueba
            to_name: Nombre (opcional)
            test_message: Mensaje de prueba (opcional)
            
        Returns:
            Dict con resultado
        """
        data = {
            'sent_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'test_message': test_message,
            'frontend_url': self.settings.FRONTEND_URL
        }
        
        html_body = email_templates.get_test_email_template(data)
        
        return await self.send_email(
            to_email=to_email,
            subject="🧪 Email de Prueba - Sistema PQRS",
            html_body=html_body,
            to_name=to_name or "Usuario de Prueba"
        )


# =============================================================================
# FUNCIÓN HELPER
# =============================================================================

def get_email_service() -> EmailService:
    """
    Factory function para obtener una instancia del EmailService
    
    Returns:
        Instancia de EmailService
    """
    return EmailService()