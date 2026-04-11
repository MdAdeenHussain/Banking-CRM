"""Notification Management Routes"""
from flask import Blueprint, render_template, request, redirect, url_for, session, jsonify
from app.models.notification import Notification
from app.models.user import User
from app.utils.decorators import login_required
from app.extensions import db
from datetime import datetime
import uuid

notifications_bp = Blueprint('notifications', __name__, url_prefix='/notifications')


@notifications_bp.route('/')
@login_required
def list_notifications():
    """List user notifications"""
    user_id = session.get('user_id')
    page = request.args.get('page', 1, type=int)
    unread_only = request.args.get('unread_only', False, type=bool)
    
    query = Notification.query.filter_by(recipient_id=user_id)
    
    if unread_only:
        query = query.filter_by(read=False)
    
    notifications = query.order_by(Notification.created_at.desc()).paginate(page=page, per_page=20)
    
    return render_template(
        'notifications/list.html',
        notifications=notifications.items,
        pagination=notifications,
        unread_only=unread_only
    )


@notifications_bp.route('/mark-as-read/<notification_id>', methods=['POST'])
@login_required
def mark_as_read(notification_id):
    """Mark notification as read"""
    user_id = session.get('user_id')
    notification = Notification.query.filter_by(
        id=notification_id,
        recipient_id=user_id
    ).first()
    
    if not notification:
        return jsonify({'error': 'Notification not found'}), 404
    
    try:
        notification.read = True
        notification.read_at = datetime.utcnow()
        db.session.commit()
        
        return jsonify({'success': True, 'message': 'Notification marked as read'})
    
    except Exception as e:
        return jsonify({'error': str(e)}), 400


@notifications_bp.route('/mark-all-as-read', methods=['POST'])
@login_required
def mark_all_as_read():
    """Mark all notifications as read"""
    user_id = session.get('user_id')
    
    try:
        notifications = Notification.query.filter_by(
            recipient_id=user_id,
            read=False
        ).all()
        
        for notification in notifications:
            notification.read = True
            notification.read_at = datetime.utcnow()
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': f'{len(notifications)} notifications marked as read'
        })
    
    except Exception as e:
        return jsonify({'error': str(e)}), 400


@notifications_bp.route('/delete/<notification_id>', methods=['POST'])
@login_required
def delete_notification(notification_id):
    """Delete notification"""
    user_id = session.get('user_id')
    notification = Notification.query.filter_by(
        id=notification_id,
        recipient_id=user_id
    ).first()
    
    if not notification:
        return jsonify({'error': 'Notification not found'}), 404
    
    try:
        db.session.delete(notification)
        db.session.commit()
        
        return jsonify({'success': True, 'message': 'Notification deleted'})
    
    except Exception as e:
        return jsonify({'error': str(e)}), 400


@notifications_bp.route('/delete-all', methods=['POST'])
@login_required
def delete_all_notifications():
    """Delete all notifications for user"""
    user_id = session.get('user_id')
    
    try:
        notifications = Notification.query.filter_by(recipient_id=user_id).all()
        
        for notification in notifications:
            db.session.delete(notification)
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': f'{len(notifications)} notifications deleted'
        })
    
    except Exception as e:
        return jsonify({'error': str(e)}), 400


@notifications_bp.route('/api/unread-count')
@login_required
def api_unread_count():
    """Get count of unread notifications"""
    user_id = session.get('user_id')
    
    unread_count = Notification.query.filter_by(
        recipient_id=user_id,
        read=False
    ).count()
    
    return jsonify({'unread_count': unread_count})


@notifications_bp.route('/api/list')
@login_required
def api_notification_list():
    """Get notifications as JSON"""
    user_id = session.get('user_id')
    limit = request.args.get('limit', 10, type=int)
    unread_only = request.args.get('unread_only', False, type=bool)
    
    query = Notification.query.filter_by(recipient_id=user_id)
    
    if unread_only:
        query = query.filter_by(read=False)
    
    notifications = query.order_by(
        Notification.created_at.desc()
    ).limit(limit).all()
    
    return jsonify([{
        'id': str(n.id),
        'title': n.title,
        'message': n.message,
        'notification_type': n.notification_type,
        'read': n.read,
        'created_at': n.created_at.isoformat(),
        'action_url': n.action_url
    } for n in notifications])


@notifications_bp.route('/api/preferences', methods=['GET', 'POST'])
@login_required
def api_notification_preferences():
    """Get/update notification preferences"""
    user_id = session.get('user_id')
    user = User.query.get(user_id)
    
    if not user:
        return jsonify({'error': 'User not found'}), 404
    
    if request.method == 'GET':
        return jsonify({
            'email_notifications': user.email_notifications if hasattr(user, 'email_notifications') else True,
            'task_notifications': user.task_notifications if hasattr(user, 'task_notifications') else True,
            'commission_notifications': user.commission_notifications if hasattr(user, 'commission_notifications') else True,
            'document_notifications': user.document_notifications if hasattr(user, 'document_notifications') else True
        })
    
    try:
        user.email_notifications = request.json.get('email_notifications', True)
        user.task_notifications = request.json.get('task_notifications', True)
        user.commission_notifications = request.json.get('commission_notifications', True)
        user.document_notifications = request.json.get('document_notifications', True)
        
        db.session.commit()
        
        return jsonify({'success': True, 'message': 'Preferences updated'})
    
    except Exception as e:
        return jsonify({'error': str(e)}), 400
