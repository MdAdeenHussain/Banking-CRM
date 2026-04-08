"""
app/notifications/services.py
Notification service: create, read, list.
"""

from app.extensions import db
from app.notifications.models import Notification
from app.auth.models import User
from app.common.audit import AuditLogService
from app.errors import NotFoundError, ValidationError
from app.constants import AuditAction
from uuid import uuid4
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class NotificationService:
    """Notification service."""
    
    @staticmethod
    def create_notification(
        user_id,
        message: str,
        notification_type: str = "SYSTEM",
        description: str = None,
        priority: str = "NORMAL",
        related_entity_type: str = None,
        related_entity_id: str = None,
        action_url: str = None,
        created_by_id: str = None
    ):
        """Create notification for user."""
        try:
            # Get user to find their tenant
            user = User.query.get(user_id)
            if not user:
                raise NotFoundError(f"User {user_id} not found")
            
            notification = Notification(
                id=str(uuid4()),
                tenant_id=user.tenant_id,
                user_id=user_id,
                message=message,
                description=description,
                notification_type=notification_type,
                priority=priority,
                related_entity_type=related_entity_type,
                related_entity_id=related_entity_id,
                action_url=action_url,
                is_read=False
            )
            
            db.session.add(notification)
            db.session.commit()
            
            logger.info(f"Notification created for user {user_id}: {message}")
            
            return notification.to_dict()
        
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error creating notification: {str(e)}")
            raise ValidationError(f"Notification creation failed: {str(e)}")
    
    @staticmethod
    def mark_as_read(notification_id: str):
        """Mark notification as read."""
        from uuid import UUID
        notification = Notification.query.get(notification_id)
        
        if not notification:
            raise NotFoundError(f"Notification {notification_id} not found")
        
        try:
            notification.is_read = True
            notification.read_at = datetime.utcnow()
            db.session.commit()
            
            logger.info(f"Notification marked as read: {notification_id}")
            
            return notification.to_dict()
        
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error marking notification as read: {str(e)}")
            raise ValidationError(f"Mark as read failed: {str(e)}")
    
    @staticmethod
    def mark_all_as_read(user_id):
        """Mark all user notifications as read."""
        try:
            from uuid import UUID
            notifications = Notification.query.filter_by(
                user_id=UUID(user_id),
                is_read=False
            ).all()
            
            count = 0
            for notif in notifications:
                notif.is_read = True
                notif.read_at = datetime.utcnow()
                count += 1
            
            db.session.commit()
            
            logger.info(f"Marked {count} notifications as read for user {user_id}")
            
            return {"marked_count": count}
        
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error marking all as read: {str(e)}")
            raise ValidationError(f"Operation failed: {str(e)}")
    
    @staticmethod
    def get_notifications(user_id, is_read: bool = None, skip: int = 0, limit: int = 20):
        """Get user notifications."""
        from uuid import UUID
        query = Notification.query.filter_by(user_id=user_id)
        
        if is_read is not None:
            query = query.filter_by(is_read=is_read)
        
        total = query.count()
        notifications = query.order_by(
            Notification.created_at.desc()
        ).offset(skip).limit(limit).all()
        
        return {
            "total": total,
            "items": [n.to_dict() for n in notifications],
            "page": skip // limit + 1,
            "page_size": limit
        }
    
    @staticmethod
    def delete_notification(notification_id: str):
        """Delete notification."""
        from uuid import UUID
        notification = Notification.query.get(notification_id)
        
        if not notification:
            raise NotFoundError(f"Notification {notification_id} not found")
        
        try:
            db.session.delete(notification)
            db.session.commit()
            
            logger.info(f"Notification deleted: {notification_id}")
            
            return {"status": "deleted"}
        
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error deleting notification: {str(e)}")
            raise ValidationError(f"Deletion failed: {str(e)}")
