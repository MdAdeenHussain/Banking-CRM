"""Notification Service"""
from app.models.notification import Notification
from app.extensions import db
from datetime import datetime
import uuid


class NotificationService:
    """Service for notification management"""
    
    @staticmethod
    def send_notification(recipient_id, title, message, notification_type='general', action_url=None):
        """Send notification to a user"""
        try:
            notification = Notification(
                id=uuid.uuid4(),
                recipient_id=recipient_id,
                title=title,
                message=message,
                notification_type=notification_type,
                action_url=action_url,
                read=False,
                created_at=datetime.utcnow()
            )
            
            db.session.add(notification)
            db.session.commit()
            
            return notification
        
        except Exception as e:
            print(f"Notification send failed: {str(e)}")
            return None
    
    @staticmethod
    def broadcast_notification(user_ids, title, message, notification_type='general'):
        """Send notification to multiple users"""
        try:
            notifications = []
            for user_id in user_ids:
                notification = Notification(
                    id=uuid.uuid4(),
                    recipient_id=user_id,
                    title=title,
                    message=message,
                    notification_type=notification_type,
                    read=False,
                    created_at=datetime.utcnow()
                )
                notifications.append(notification)
            
            db.session.add_all(notifications)
            db.session.commit()
            
            return len(notifications)
        
        except Exception as e:
            print(f"Broadcast notification failed: {str(e)}")
            return 0
    
    @staticmethod
    def get_unread_notifications(user_id, limit=10):
        """Get unread notifications for user"""
        return Notification.query.filter_by(
            recipient_id=user_id,
            read=False
        ).order_by(Notification.created_at.desc()).limit(limit).all()
    
    @staticmethod
    def mark_as_read(notification_id):
        """Mark notification as read"""
        try:
            notification = Notification.query.get(notification_id)
            if not notification:
                return False
            
            notification.read = True
            notification.read_at = datetime.utcnow()
            db.session.commit()
            
            return True
        
        except Exception as e:
            print(f"Mark as read failed: {str(e)}")
            return False
    
    @staticmethod
    def send_task_notification(assigned_to_id, task_title):
        """Send task assignment notification"""
        return NotificationService.send_notification(
            recipient_id=assigned_to_id,
            title='New Task Assigned',
            message=f'Task assigned: {task_title}',
            notification_type='task_assignment'
        )
    
    @staticmethod
    def send_commission_notification(employee_id, commission_amount):
        """Send commission notification"""
        return NotificationService.send_notification(
            recipient_id=employee_id,
            title='Commission Update',
            message=f'New commission earned: ₹{commission_amount}',
            notification_type='commission_alert'
        )
    
    @staticmethod
    def send_lead_status_notification(assigned_to_id, lead_name, new_status):
        """Send lead status change notification"""
        return NotificationService.send_notification(
            recipient_id=assigned_to_id,
            title='Lead Status Changed',
            message=f'Lead {lead_name} status changed to {new_status}',
            notification_type='lead_update'
        )
