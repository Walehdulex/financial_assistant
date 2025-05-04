from flask import Blueprint, jsonify, request, render_template, current_app, redirect, url_for
from flask_login import login_required, current_user
from app.services.notification_service import NotificationService
from app.models.notification import Notification

bp = Blueprint('notifications', __name__)
notification_service = NotificationService()


# API endpoints for notifications
@bp.route('/', methods=['GET'])
@login_required
def get_notifications():
    """Getting user's notifications"""
    unread_only = request.args.get('unread_only', 'false').lower() == 'true'
    limit = int(request.args.get('limit', 20))

    notifications = notification_service.get_user_notifications(
        current_user.id,
        unread_only=unread_only,
        limit=limit
    )

    # If HTML is requested, render the template
    if request.headers.get('Accept', '').find('application/json') == -1 and request.args.get('format') != 'json':
        return render_template('notifications/index.html',
                               notifications=notifications,
                               unread_count=current_user.notifications.filter_by(is_read=False).count())

    # Otherwise return JSON
    return jsonify({
        'notifications': [n.to_dict() for n in notifications],
        'unread_count': current_user.notifications.filter_by(is_read=False).count()
    })


@bp.route('/api', methods=['GET'])
@login_required
def get_notifications_api():
    """API endpoint to get notifications (for AJAX calls)"""
    unread_only = request.args.get('unread', 'false').lower() == 'true'
    limit = int(request.args.get('limit', 10))

    query = Notification.query.filter_by(user_id=current_user.id)
    if unread_only:
        query = query.filter_by(is_read=False)

    notifications = query.order_by(Notification.created_at.desc()).limit(limit).all()

    return jsonify({
        'notifications': [n.to_dict() for n in notifications],
        'unread_count': Notification.query.filter_by(user_id=current_user.id, is_read=False).count()
    })


@bp.route('/mark_read/<int:notification_id>', methods=['POST'])
@login_required
def mark_as_read(notification_id):
    """Mark a notification as read"""
    result = notification_service.mark_as_read(notification_id, current_user.id)

    return jsonify({
        'success': result,
        'unread_count': current_user.notifications.filter_by(is_read=False).count()
    })


@bp.route('/mark_all_read', methods=['POST'])
@login_required
def mark_all_read():
    """Mark all notifications as read"""
    result = notification_service.mark_all_as_read(current_user.id)

    # Check if the request wants JSON (API call) or HTML (browser)
    if request.headers.get('Accept', '').find('application/json') != -1 or request.args.get('format') == 'json':
        return jsonify({
            'success': result,
            'unread_count': 0
        })

    # Otherwise redirect back to notifications
    return redirect(url_for('notifications.get_notifications'))


@bp.route('/delete/<int:notification_id>', methods=['DELETE', 'POST'])
@login_required
def delete_notification(notification_id):
    """Delete a notification"""
    result = notification_service.delete_notification(notification_id, current_user.id)

    # If it's an API request, return JSON
    if request.method == 'DELETE' or request.headers.get('Accept', '').find('application/json') != -1:
        return jsonify({
            'success': result
        })

    # Otherwise redirect back to notifications
    return redirect(url_for('notifications.get_notifications'))


@bp.route('/view/<int:notification_id>', methods=['GET'])
@login_required
def view_notification(notification_id):
    """View a single notification and mark it as read"""
    notification = Notification.query.filter_by(id=notification_id, user_id=current_user.id).first_or_404()
    notification_service.mark_as_read(notification_id, current_user.id)

    # Determine where to redirect based on the notification source
    if notification.source == 'portfolio':
        return render_template('notifications/view.html', notification=notification,
                               redirect_url='/portfolio/dashboard')
    elif notification.source == 'market':
        return render_template('notifications/view.html', notification=notification,
                               redirect_url='/market/overview')
    elif notification.source == 'report':
        return render_template('notifications/view.html', notification=notification,
                               redirect_url='/reports')
    else:
        return render_template('notifications/view.html', notification=notification)