"""
Health Check Endpoint
Sistema PQRS - Equipo Desertados
"""

from fastapi import APIRouter, status
from datetime import datetime

router = APIRouter(tags=["Health"])


@router.get(
    "/health",
    status_code=status.HTTP_200_OK,
    summary="Health Check"
)
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "service": "PQRS Backend",
        "version": "1.0.0"
    }