"""Task Management Routes"""
from flask import Blueprint, render_template, request, redirect, url_for, session, jsonify
from app.models.task import Task
from app.models.reminder import Reminder
from app.models.employee import Employee
from app.models.lead import Lead
from app.models.user import User
from app.utils.decorators import login_required, role_required, permission_required
from app.services.audit_service import AuditService
from app.services.notification_service import NotificationService
from app.extensions import db
from datetime import datetime, timedelta
from sqlalchemy import or_, func
import uuid

tasks_bp = Blueprint('tasks', __name__, url_prefix='/tasks')


@tasks_bp.route('/')
@login_required
@permission_required('tasks', 'view')
def list_tasks():
    """List tasks with filters"""
    page = request.args.get('page', 1, type=int)
    status_filter = request.args.get('status', '')
    priority_filter = request.args.get('priority', '')
    assigned_to_filter = request.args.get('assigned_to', '')
    search = request.args.get('search', '')
    
    current_user_id = session.get('user_id')
    view_type = request.args.get('view', 'assigned_to_me')
    
    query = Task.query
    
    # Filter by view type
    if view_type == 'assigned_to_me':
        query = query.filter_by(assigned_to_id=current_user_id)
    elif view_type == 'created_by_me':
        query = query.filter_by(created_by_id=current_user_id)
    elif view_type == 'all' and not request.args.get('assigned_to'):
        pass  # Show all tasks
    
    if status_filter:
        query = query.filter_by(status=status_filter)
    
    if priority_filter:
        query = query.filter_by(priority=priority_filter)
    
    if assigned_to_filter:
        query = query.filter_by(assigned_to_id=assigned_to_filter)
    
    if search:
        query = query.filter(
            or_(
                Task.title.ilike(f'%{search}%'),
                Task.description.ilike(f'%{search}%')
            )
        )
    
    tasks = query.order_by(Task.due_date.asc()).paginate(page=page, per_page=20)
    employees = Employee.query.filter_by(status='active').all()
    
    # Statistics
    total_tasks = Task.query.count()
    overdue_tasks = Task.query.filter(
        Task.status != 'completed',
        Task.due_date < datetime.utcnow()
    ).count()
    
    my_tasks = Task.query.filter_by(assigned_to_id=current_user_id).count()
    
    return render_template(
        'tasks/list.html',
        tasks=tasks.items,
        pagination=tasks,
        employees=employees,
        status_filter=status_filter,
        priority_filter=priority_filter,
        assigned_to_filter=assigned_to_filter,
        search=search,
        view_type=view_type,
        total_tasks=total_tasks,
        overdue_tasks=overdue_tasks,
        my_tasks=my_tasks
    )


@tasks_bp.route('/create', methods=['GET', 'POST'])
@login_required
@permission_required('tasks', 'create')
def create_task():
    """Create new task"""
    if request.method == 'GET':
        leads = Lead.query.filter_by(status='active').all()
        employees = Employee.query.filter_by(status='active').all()
        return render_template('tasks/create.html', leads=leads, employees=employees)
    
    try:
        user_id = session.get('user_id')
        
        # Parse dates
        due_date_str = request.form.get('due_date')
        due_date = datetime.strptime(due_date_str, '%Y-%m-%d') if due_date_str else None
        
        task = Task(
            id=uuid.uuid4(),
            title=request.form.get('title'),
            description=request.form.get('description'),
            task_type=request.form.get('task_type', 'general'),
            status='open',
            priority=request.form.get('priority', 'medium'),
            assigned_to_id=request.form.get('assigned_to_id'),
            lead_id=request.form.get('lead_id') if request.form.get('lead_id') else None,
            due_date=due_date,
            created_by_id=user_id,
            created_at=datetime.utcnow()
        )
        
        db.session.add(task)
        db.session.flush()  # To get the task ID
        
        # Create reminder if requested
        if request.form.get('set_reminder') == 'on':
            reminder_days = int(request.form.get('reminder_days', 1))
            reminder_date = due_date - timedelta(days=reminder_days) if due_date else None
            
            if reminder_date:
                reminder = Reminder(
                    id=uuid.uuid4(),
                    task_id=task.id,
                    remind_at=reminder_date,
                    reminded=False
                )
                db.session.add(reminder)
        
        db.session.commit()
        
        # Audit log
        AuditService.log_action(
            user_id=user_id,
            action='CREATE',
            resource='Task',
            resource_id=str(task.id),
            details=f"Created task: {task.title}"
        )
        
        # Send notification to assigned user
        if task.assigned_to_id:
            assigned_user = User.query.get(task.assigned_to_id)
            if assigned_user:
                NotificationService.send_notification(
                    recipient_id=task.assigned_to_id,
                    title='New Task Assigned',
                    message=f"Task assigned: {task.title}",
                    notification_type='task_assignment'
                )
        
        return redirect(url_for('tasks.list_tasks'))
    
    except Exception as e:
        return jsonify({'error': str(e)}), 400


@tasks_bp.route('/<task_id>')
@login_required
@permission_required('tasks', 'view')
def task_detail(task_id):
    """View task details"""
    task = Task.query.get(task_id)
    if not task:
        return render_template('error.html', code=404), 404
    
    assigned_user = User.query.get(task.assigned_to_id) if task.assigned_to_id else None
    created_user = User.query.get(task.created_by_id) if task.created_by_id else None
    lead = Lead.query.get(task.lead_id) if task.lead_id else None
    reminders = Reminder.query.filter_by(task_id=task_id).all()
    
    return render_template(
        'tasks/detail.html',
        task=task,
        assigned_user=assigned_user,
        created_user=created_user,
        lead=lead,
        reminders=reminders
    )


@tasks_bp.route('/<task_id>/edit', methods=['GET', 'POST'])
@login_required
@permission_required('tasks', 'edit')
def edit_task(task_id):
    """Edit task"""
    task = Task.query.get(task_id)
    if not task:
        return render_template('error.html', code=404), 404
    
    if request.method == 'GET':
        leads = Lead.query.filter_by(status='active').all()
        employees = Employee.query.filter_by(status='active').all()
        return render_template('tasks/edit.html', task=task, leads=leads, employees=employees)
    
    try:
        old_status = task.status
        
        task.title = request.form.get('title')
        task.description = request.form.get('description')
        task.status = request.form.get('status')
        task.priority = request.form.get('priority')
        task.assigned_to_id = request.form.get('assigned_to_id')
        
        due_date_str = request.form.get('due_date')
        task.due_date = datetime.strptime(due_date_str, '%Y-%m-%d') if due_date_str else None
        
        if request.form.get('status') == 'completed' and old_status != 'completed':
            task.completed_at = datetime.utcnow()
        
        db.session.commit()
        
        # Audit log
        user_id = session.get('user_id')
        AuditService.log_action(
            user_id=user_id,
            action='UPDATE',
            resource='Task',
            resource_id=str(task.id),
            details=f"Updated task: {task.title}, Status: {task.status}"
        )
        
        return redirect(url_for('tasks.task_detail', task_id=task_id))
    
    except Exception as e:
        return jsonify({'error': str(e)}), 400


@tasks_bp.route('/<task_id>/complete', methods=['POST'])
@login_required
def complete_task(task_id):
    """Mark task as complete"""
    task = Task.query.get(task_id)
    if not task:
        return jsonify({'error': 'Task not found'}), 404
    
    try:
        task.status = 'completed'
        task.completed_at = datetime.utcnow()
        db.session.commit()
        
        # Audit log
        user_id = session.get('user_id')
        AuditService.log_action(
            user_id=user_id,
            action='COMPLETE',
            resource='Task',
            resource_id=str(task.id),
            details=f"Completed task: {task.title}"
        )
        
        return jsonify({'success': True, 'message': 'Task marked as complete'})
    
    except Exception as e:
        return jsonify({'error': str(e)}), 400


@tasks_bp.route('/<task_id>/delete', methods=['POST'])
@login_required
@role_required(['SUPER_ADMIN', 'ADMIN'])
def delete_task(task_id):
    """Delete task"""
    task = Task.query.get(task_id)
    if not task:
        return jsonify({'error': 'Task not found'}), 404
    
    try:
        task_title = task.title
        db.session.delete(task)
        db.session.commit()
        
        # Audit log
        user_id = session.get('user_id')
        AuditService.log_action(
            user_id=user_id,
            action='DELETE',
            resource='Task',
            resource_id=task_id,
            details=f"Deleted task: {task_title}"
        )
        
        return jsonify({'success': True, 'message': 'Task deleted successfully'})
    
    except Exception as e:
        return jsonify({'error': str(e)}), 400


@tasks_bp.route('/my-tasks')
@login_required
def my_tasks():
    """View my assigned tasks"""
    user_id = session.get('user_id')
    page = request.args.get('page', 1, type=int)
    status_filter = request.args.get('status', '')
    
    query = Task.query.filter_by(assigned_to_id=user_id)
    
    if status_filter:
        query = query.filter_by(status=status_filter)
    
    tasks = query.order_by(Task.due_date.asc()).paginate(page=page, per_page=20)
    
    # Statistics
    total = Task.query.filter_by(assigned_to_id=user_id).count()
    completed = Task.query.filter_by(assigned_to_id=user_id, status='completed').count()
    overdue = Task.query.filter(
        Task.assigned_to_id == user_id,
        Task.status != 'completed',
        Task.due_date < datetime.utcnow()
    ).count()
    
    return render_template(
        'tasks/my_tasks.html',
        tasks=tasks.items,
        pagination=tasks,
        status_filter=status_filter,
        total=total,
        completed=completed,
        overdue=overdue
    )


@tasks_bp.route('/overdue')
@login_required
def overdue_tasks():
    """View overdue tasks"""
    page = request.args.get('page', 1, type=int)
    user_filter = request.args.get('assigned_to', '')
    
    query = Task.query.filter(
        Task.status != 'completed',
        Task.due_date < datetime.utcnow()
    )
    
    if user_filter:
        query = query.filter_by(assigned_to_id=user_filter)
    
    tasks = query.order_by(Task.due_date.asc()).paginate(page=page, per_page=20)
    employees = Employee.query.filter_by(status='active').all()
    
    return render_template(
        'tasks/overdue.html',
        tasks=tasks.items,
        pagination=tasks,
        employees=employees,
        user_filter=user_filter
    )


@tasks_bp.route('/api/stats')
@login_required
def api_task_stats():
    """API endpoint for task statistics"""
    user_id = session.get('user_id')
    
    stats = {
        'my_total': Task.query.filter_by(assigned_to_id=user_id).count(),
        'my_completed': Task.query.filter_by(assigned_to_id=user_id, status='completed').count(),
        'my_overdue': Task.query.filter(
            Task.assigned_to_id == user_id,
            Task.status != 'completed',
            Task.due_date < datetime.utcnow()
        ).count(),
        'system_total': Task.query.count()
    }
    
    return jsonify(stats)
