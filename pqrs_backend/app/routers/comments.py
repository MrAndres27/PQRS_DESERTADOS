"""
Router de Comentarios
Sistema PQRS - Equipo Desertados

Endpoints para comentarios en PQRS:
- POST /pqrs/{id}/comments - Agregar comentario
- GET /pqrs/{id}/comments - Listar comentarios
- GET /comments/{id} - Ver comentario específico
- PUT /comments/{id} - Editar comentario
- DELETE /comments/{id} - Eliminar comentario
- GET /pqrs/{id}/comments/stats - Estadísticas de comentarios
"""

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List
import math

from app.core.database import get_async_db
from app.core.dependencies import (
    get_current_user,
    get_pagination_params,
    PaginationParams
)
from app.services.comment_service import CommentService, get_comment_service
from app.models.user import User
from app.schemas.comments import (
    CommentCreate,
    CommentUpdate,
    CommentResponse,
    CommentPaginatedResponse,
    CommentStats
)


# =============================================================================
# ROUTER
# =============================================================================

router = APIRouter(tags=["Comentarios"])


# =============================================================================
# ENDPOINTS DE CONSULTA
# =============================================================================

@router.get(
    "/pqrs/{pqrs_id}/comments",
    response_model=CommentPaginatedResponse,
    status_code=status.HTTP_200_OK
)
async def list_comments_by_pqrs(
    pqrs_id: int,
    pagination: PaginationParams = Depends(get_pagination_params),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_db)
):
    """
    Lista todos los comentarios de una PQRS
    
    **Visibilidad:**
    - Usuarios normales: Solo ven comentarios públicos
    - Gestores/Admins: Ven comentarios públicos e internos
    
    **Paginación:**
    - `skip`: Registros a saltar (default: 0)
    - `limit`: Límite de resultados (default: 50, max: 100)
    
    **Ordenamiento:** Del más reciente al más antiguo
    
    **Requiere:** Usuario autenticado
    """
    comment_service = get_comment_service(db)
    
    comments, total = await comment_service.list_comments_by_pqrs(
        pqrs_id=pqrs_id,
        current_user=current_user,
        skip=pagination.skip,
        limit=pagination.limit
    )
    
    # Calcular paginación
    page = (pagination.skip // pagination.limit) + 1
    total_pages = math.ceil(total / pagination.limit) if total > 0 else 1
    
    return CommentPaginatedResponse(
        items=comments,
        total=total,
        page=page,
        page_size=pagination.limit,
        total_pages=total_pages
    )


@router.get(
    "/pqrs/{pqrs_id}/comments/stats",
    response_model=CommentStats,
    status_code=status.HTTP_200_OK
)
async def get_comment_stats(
    pqrs_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_db)
):
    """
    Obtiene estadísticas de comentarios de una PQRS
    
    Incluye:
    - Total de comentarios visibles
    - Comentarios públicos
    - Comentarios internos (si tiene permiso)
    
    **Requiere:** Usuario autenticado
    """
    comment_service = get_comment_service(db)
    
    stats = await comment_service.get_comment_stats_by_pqrs(
        pqrs_id=pqrs_id,
        current_user=current_user
    )
    
    return CommentStats(**stats)


@router.get(
    "/comments/{comment_id}",
    response_model=CommentResponse,
    status_code=status.HTTP_200_OK
)
async def get_comment_by_id(
    comment_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_db)
):
    """
    Obtiene un comentario específico por ID
    
    **Notas:**
    - Si es comentario interno, solo gestores/admins pueden verlo
    - Si no existe, retorna 404
    
    **Requiere:** Usuario autenticado
    """
    comment_service = get_comment_service(db)
    
    comment = await comment_service.get_comment_by_id(
        comment_id=comment_id,
        current_user=current_user
    )
    
    return comment


# =============================================================================
# ENDPOINTS DE MODIFICACIÓN
# =============================================================================

@router.post(
    "/pqrs/{pqrs_id}/comments",
    response_model=CommentResponse,
    status_code=status.HTTP_201_CREATED
)
async def create_comment(
    pqrs_id: int,
    comment_data: CommentCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_db)
):
    """
    Crea un nuevo comentario en una PQRS
    
    **Tipos de comentario:**
    - `is_internal: false` - Visible para el ciudadano y gestores (por defecto)
    - `is_internal: true` - Solo visible para gestores/admins
    
    **Validaciones:**
    - Contenido mínimo: 1 carácter
    - Contenido máximo: 5000 caracteres
    - PQRS debe existir
    - Solo gestores/admins pueden crear comentarios internos
    
    **Requiere:** Usuario autenticado
    """
    comment_service = get_comment_service(db)
    
    new_comment = await comment_service.create_comment(
        pqrs_id=pqrs_id,
        content=comment_data.content,
        is_internal=comment_data.is_internal,
        author_id=current_user.id,
        current_user=current_user
    )
    
    return new_comment


@router.put(
    "/comments/{comment_id}",
    response_model=CommentResponse,
    status_code=status.HTTP_200_OK
)
async def update_comment(
    comment_id: int,
    comment_data: CommentUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_db)
):
    """
    Actualiza el contenido de un comentario
    
    **Restricciones:**
    - Solo el autor puede editar su comentario
    - No se puede cambiar el tipo (interno/público)
    - No se puede cambiar la PQRS asociada
    
    **Validaciones:**
    - Contenido mínimo: 1 carácter
    - Contenido máximo: 5000 caracteres
    
    **Nota:** El campo `is_edited` se marcará como true automáticamente
    
    **Requiere:** Usuario autenticado y ser el autor
    """
    comment_service = get_comment_service(db)
    
    updated_comment = await comment_service.update_comment(
        comment_id=comment_id,
        content=comment_data.content,
        current_user=current_user
    )
    
    return updated_comment


@router.delete(
    "/comments/{comment_id}",
    status_code=status.HTTP_200_OK
)
async def delete_comment(
    comment_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_db)
):
    """
    Elimina un comentario
    
    **Restricciones:**
    - Solo el autor o un administrador pueden eliminar
    - La eliminación es permanente (no es soft delete)
    
    **IMPORTANTE:** Esta acción no se puede deshacer
    
    **Requiere:** Usuario autenticado y ser el autor o admin
    """
    comment_service = get_comment_service(db)
    
    success = await comment_service.delete_comment(
        comment_id=comment_id,
        current_user=current_user
    )
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error al eliminar el comentario"
        )
    
    return {
        "message": "Comentario eliminado exitosamente",
        "comment_id": comment_id,
        "success": True
    }


# =============================================================================
# NOTAS DE IMPLEMENTACIÓN
# =============================================================================

"""
CARACTERÍSTICAS IMPLEMENTADAS:

1. TIPOS DE COMENTARIOS:
   - Públicos: Visibles para ciudadanos y gestores
   - Internos: Solo visibles entre gestores/admins

2. PERMISOS:
   - Cualquier usuario autenticado puede crear comentarios públicos
   - Solo gestores/admins pueden crear comentarios internos
   - Solo gestores/admins pueden VER comentarios internos
   - Solo el autor puede EDITAR su comentario
   - Solo el autor o admin puede ELIMINAR comentarios

3. VALIDACIONES:
   - Longitud de contenido (1-5000 caracteres)
   - Verificación de existencia de PQRS
   - Verificación de autoría
   - Verificación de permisos según tipo

4. FUNCIONALIDADES:
   - Listado paginado con filtrado automático según permisos
   - Ordenamiento cronológico inverso (más recientes primero)
   - Marca de "editado" si el comentario fue modificado
   - Estadísticas de comentarios por PQRS
   - Carga eager de relaciones (autor)

5. CASOS DE USO:

   a) Ciudadano comenta su PQRS:
      - POST /pqrs/5/comments {"content": "...", "is_internal": false}
      - Visible para todos

   b) Gestor responde públicamente:
      - POST /pqrs/5/comments {"content": "...", "is_internal": false}
      - Visible para el ciudadano

   c) Gestores discuten internamente:
      - POST /pqrs/5/comments {"content": "...", "is_internal": true}
      - Solo visible entre gestores

   d) Ciudadano ve comentarios:
      - GET /pqrs/5/comments
      - Solo ve comentarios públicos

   e) Gestor ve todos los comentarios:
      - GET /pqrs/5/comments
      - Ve públicos e internos

   f) Usuario edita su comentario:
      - PUT /comments/10 {"content": "..."}
      - Solo si es el autor

   g) Admin elimina comentario inapropiado:
      - DELETE /comments/10
      - Admin puede eliminar cualquier comentario

6. FLUJO TÍPICO DE CONVERSACIÓN:

   Ciudadano crea PQRS → 
   Ciudadano comenta: "Necesito esto urgente" (público) →
   Gestor comenta: "Revisaremos su caso" (público) →
   Gestores discuten: "Este caso requiere aprobación del jefe" (interno) →
   Gestores discuten: "Aprobado, proceder" (interno) →
   Gestor responde: "Hemos aprobado su solicitud" (público) →
   Ciudadano responde: "Gracias!" (público)

7. SEGURIDAD:
   - Autenticación requerida en todos los endpoints
   - Validación de autoría para editar/eliminar
   - Filtrado automático de comentarios internos según permisos
   - No se puede crear comentarios en nombre de otros
   - Admin tiene permisos especiales para eliminar

8. OPTIMIZACIONES:
   - Carga eager de relaciones (author)
   - Paginación eficiente
   - Conteo optimizado con COUNT()
   - Índices en BD (pqrs_id, user_id)
"""