from flask import Blueprint, render_template, request,jsonify, redirect, url_for
from flask_login import login_required, current_user
from app.models.user import UserSettings
from app import db

bp = Blueprint('settings', __name__)

@bp.route('/preferences', methods=['GET', 'POST'])
@login_required
def preferences():
    if request.method == 'POST':
        data = request.get_json()

        #Getting or Creating User Settings
        settings = UserSettings.query.filter_by(user_id=current_user.id).first()
        if not settings:
            settings = UserSettings(user_id=current_user.id)
            db.session.add(settings)

        #Updating User settings
        settings.risk_tolerance = data.get('risk_tolerance', 'Moderate')
        settings.default_chart_period = data.get('default_chart_period', '1y')
        settings.enable_notifications = data.get('enable_notifications', True)

        db.session.commit()
        return jsonify({'success': True})

    #GET request for Current Settings
    settings = UserSettings.query.filter_by(user_id=current_user.id).first()
    if not settings:
        settings = UserSettings(user_id=current_user.id)
        db.session.add(settings)
        db.session.commit()

    return jsonify({
        'risk_tolerance': settings.risk_tolerance,
        'default_chart_period': settings.default_chart_period,
        'enable_notifications': settings.enable_notifications
    })