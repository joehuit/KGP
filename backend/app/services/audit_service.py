"""Audit trail service for recording and retrieving critical administrative events."""

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple
from sqlalchemy import desc, func, select
from sqlalchemy.orm import Session
from app.models.audit_log import AuditActorType, AuditLog


class AuditService:
    """Service for managing immutable audit trail records."""

    @staticmethod
    def log_event(
        db: Session,
        actor_type: AuditActorType,
        actor_id: Optional[str],
        action: str,
        entity_type: str,
        entity_id: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
        ip_address: Optional[str] = None,
    ) -> AuditLog:
        """Create and persist a new audit trail entry."""
        log = AuditLog(
            actor_type=actor_type.value if isinstance(actor_type, AuditActorType) else str(actor_type),
            actor_id=str(actor_id) if actor_id is not None else None,
            action=action,
            entity_type=entity_type,
            entity_id=str(entity_id) if entity_id is not None else None,
            details=details,
            ip_address=ip_address,
        )
        db.add(log)
        db.commit()
        db.refresh(log)
        return log

    @staticmethod
    def list_logs(
        db: Session,
        page: int = 1,
        page_size: int = 20,
        entity_type: Optional[str] = None,
        action: Optional[str] = None,
        actor_type: Optional[str] = None,
    ) -> Tuple[List[AuditLog], int]:
        """Query audit log entries with optional filters and pagination."""
        query = select(AuditLog)

        if entity_type:
            query = query.where(AuditLog.entity_type == entity_type)
        if action:
            query = query.where(AuditLog.action == action)
        if actor_type:
            query = query.where(AuditLog.actor_type == actor_type)

        count_query = select(func.count()).select_from(query.subquery())
        total = db.scalar(count_query) or 0

        offset = (page - 1) * page_size
        items = list(
            db.scalars(
                query.order_by(desc(AuditLog.created_at), desc(AuditLog.id))
                .offset(offset)
                .limit(page_size)
            ).all()
        )
        return items, total
