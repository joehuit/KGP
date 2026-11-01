"""Audit log inspection API endpoints for administrators."""

from math import ceil
from typing import Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from app.api.deps import PaginationParams, get_db_session, require_roles
from app.core.security import AdminRole
from app.models.admin_user import AdminUser
from app.schemas.audit_log import AuditLogResponse
from app.schemas.common import PaginatedResponse, PaginationMeta, ResponseEnvelope
from app.services.audit_service import AuditService

router = APIRouter(prefix="/audit-logs", tags=["Audit Logs"])


@router.get("", response_model=ResponseEnvelope[PaginatedResponse[AuditLogResponse]])
def list_audit_logs(
    entity_type: Optional[str] = Query(None, description="Filter by target entity type (e.g. PRODUCT, CATEGORY)"),
    action: Optional[str] = Query(None, description="Filter by action name (e.g. DELETE, STATUS_UPDATE)"),
    actor_type: Optional[str] = Query(None, description="Filter by actor type (ADMIN, CUSTOMER, SYSTEM)"),
    pagination: PaginationParams = Depends(),
    _superadmin: AdminUser = Depends(require_roles([AdminRole.SUPERADMIN])),
    db: Session = Depends(get_db_session),
) -> ResponseEnvelope[PaginatedResponse[AuditLogResponse]]:
    """Retrieve system audit logs for administrative oversight (Superadmin only)."""
    items, total = AuditService.list_logs(
        db=db,
        page=pagination.page,
        page_size=pagination.page_size,
        entity_type=entity_type,
        action=action,
        actor_type=actor_type,
    )
    total_pages = ceil(total / pagination.page_size) if total > 0 else 0

    paginated_data = PaginatedResponse[AuditLogResponse](
        items=[AuditLogResponse.model_validate(it) for it in items],
        meta=PaginationMeta(
            page=pagination.page,
            page_size=pagination.page_size,
            total_items=total,
            total_pages=total_pages,
        ),
    )
    return ResponseEnvelope(data=paginated_data)
