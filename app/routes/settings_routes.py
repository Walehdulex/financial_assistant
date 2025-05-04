from flask import Blueprint, render_template, request, jsonify, redirect, url_for
from flask_login import login_required, current_user
from app.models.user import UserSettings
from app import db
from sqlalchemy import true

bp = Blueprint('settings', __name__)


@bp.route('/preferences', methods=['GET', 'POST'])
@login_required
def preferences():
    if request.method == 'POST':
        data = request.get_json()

        # Getting or Creating User Settings
        settings = UserSettings.query.filter_by(user_id=current_user.id).first()
        if not settings:
            settings = UserSettings(user_id=current_user.id)
            db.session.add(settings)

        # Updating User settings
        settings.risk_tolerance = data.get('risk_tolerance', 'Moderate')
        settings.default_chart_period = data.get('default_chart_period', '1y')
        settings.enable_notifications = data.get('enable_notifications', False)
        settings.investment_goal = data.get('investment_goal', 'Growth')
        settings.time_horizon = data.get('time_horizon', 'Long-term')
        settings.preferred_sectors = data.get('preferred_sectors', '')
        settings.preferred_assets = data.get('preferred_assets', '')
        settings.tax_consideration = data.get('tax_consideration', False)

        db.session.commit()
        return jsonify({'success': True, 'message': 'Settings updated successfully'})

    # GET request for Current Settings
    settings = UserSettings.query.filter_by(user_id=current_user.id).first()
    if not settings:
        settings = UserSettings(user_id=current_user.id)
        db.session.add(settings)
        db.session.commit()

    return jsonify({
        'risk_tolerance': settings.risk_tolerance,
        'default_chart_period': settings.default_chart_period,
        'enable_notifications': settings.enable_notifications,
        'investment_goal': settings.investment_goal if hasattr(settings, 'investment_goal') else 'Growth',
        'time_horizon': settings.time_horizon if hasattr(settings, 'time_horizon') else 'Long-term',
        'preferred_sectors': settings.preferred_sectors if hasattr(settings, 'preferred_sectors') else '',
        'preferred_assets': settings.preferred_assets if hasattr(settings, 'preferred_assets') else '',
        'tax_consideration': settings.tax_consideration if hasattr(settings, 'tax_consideration') else False
    })