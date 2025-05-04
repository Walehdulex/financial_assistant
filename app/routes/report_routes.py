from datetime import datetime

from flask import Blueprint, render_template, request, jsonify, send_file, redirect, url_for, abort, flash, current_app
from flask_login import login_required, current_user
from app.services.report_service import ReportService
from app.models.report import Report
import os

bp = Blueprint('reports', __name__, url_prefix='/reports')
report_service = ReportService()


@bp.route('/')
@login_required
def index():
    """Show list of reports"""
    report_type = request.args.get('type')
    reports = report_service.get_user_reports(current_user.id, report_type=report_type)
    return render_template('reports/index.html', reports=reports, active_type=report_type)


@bp.route('/view/<int:report_id>')
@login_required
def view_report(report_id):
    """View a specific report"""
    report = report_service.get_report(report_id, current_user.id)
    if not report:
        abort(404)

    # For PDF reports, serve the file
    if report.format == 'pdf' and report.file_path and os.path.exists(report.file_path):
        return send_file(report.file_path, as_attachment=False)

    # For other report types, render a template
    return render_template('reports/view.html', report=report)


@bp.route('/download/<int:report_id>')
@login_required
def download_report(report_id):
    """Download a report file"""
    report = report_service.get_report(report_id, current_user.id)
    if not report or not report.file_path or not os.path.exists(report.file_path):
        abort(404)

    return send_file(report.file_path, as_attachment=True,
                     download_name=f"{report.report_type}_report_{report.id}.{report.format}")


@bp.route('/generate', methods=['GET', 'POST'])
@login_required
def generate_report():
    """Generate a new report"""
    if request.method == 'POST':
        report_type = request.form.get('report_type')
        portfolio_id = request.form.get('portfolio_id')

        if portfolio_id and portfolio_id.lower() == 'all':
            portfolio_id = None
        elif portfolio_id:
            portfolio_id = int(portfolio_id)

        if report_type == 'performance':
            report = report_service.generate_portfolio_performance_report(
                user_id=current_user.id,
                portfolio_id=portfolio_id
            )
        elif report_type == 'allocation':
            report = report_service.generate_allocation_report(
                user_id=current_user.id,
                portfolio_id=portfolio_id
            )
        else:
            # Invalid report type
            return redirect(url_for('reports.index'))

        if report:
            return redirect(url_for('reports.view_report', report_id=report.id))
        else:
            # Failed to generate report
            return render_template('reports/generate.html', error="Failed to generate report. No data available.")

    # GET request - show form to generate report
    from app.models.portfolio import Portfolio
    portfolios = Portfolio.query.filter_by(user_id=current_user.id).all()
    return render_template('reports/generate.html', portfolios=portfolios)


@bp.route('/archive/<int:report_id>', methods=['POST'])
@login_required
def archive_report(report_id):
    """Archive a report"""
    result = report_service.archive_report(report_id, current_user.id)

    if request.headers.get('Accept', '').find('application/json') != -1:
        return jsonify({'success': result})

    return redirect(url_for('reports.index'))


@bp.route('/delete/<int:report_id>', methods=['POST'])
@login_required
def delete_report(report_id):
    """Delete a report"""
    result = report_service.delete_report(report_id, current_user.id)

    if request.headers.get('Accept', '').find('application/json') != -1:
        return jsonify({'success': result})

    return redirect(url_for('reports.index'))


@bp.route('/generate/tax', methods=['GET', 'POST'])
@login_required
def generate_tax_report():
    """Generate a tax report"""
    try:
        if request.method == 'POST':
            portfolio_id = request.form.get('portfolio_id')
            tax_year = request.form.get('tax_year', datetime.utcnow().year)

            if portfolio_id and portfolio_id.lower() == 'all':
                portfolio_id = None
            elif portfolio_id:
                portfolio_id = int(portfolio_id)

            report = report_service.generate_tax_report(
                user_id=current_user.id,
                tax_year=int(tax_year),
                portfolio_id=portfolio_id
            )

            if report:
                flash('Tax report generated successfully!', 'success')
                return redirect(url_for('reports.view_report', report_id=report.id))
            else:
                flash('Failed to generate tax report. No data available.', 'warning')
                return redirect(url_for('reports.index'))

        # GET request - show form
        from app.models.portfolio import Portfolio
        portfolios = Portfolio.query.filter_by(user_id=current_user.id).all()

        # Generate a list of possible tax years (last 5 years)
        current_year = datetime.utcnow().year
        years = list(range(current_year - 4, current_year + 1))

        return render_template(
            'reports/generate_tax.html',
            portfolios=portfolios,
            years=years,
            current_year=current_year
        )
    except Exception as e:
        from flask import current_app
        current_app.logger.error(f"Tax report error: {str(e)}")
        import traceback
        current_app.logger.error(traceback.format_exc())
        flash(f"Error generating tax report: {str(e)}", "danger")
        return redirect(url_for('reports.index'))


@bp.route('/generate/risk', methods=['GET', 'POST'])
@login_required
def generate_risk_report():
    """Generate a risk analysis report"""
    try:
        if request.method == 'POST':
            portfolio_id = request.form.get('portfolio_id')

            if portfolio_id and portfolio_id.lower() == 'all':
                portfolio_id = None
            elif portfolio_id:
                portfolio_id = int(portfolio_id)

            report = report_service.generate_risk_analysis_report(
                user_id=current_user.id,
                portfolio_id=portfolio_id
            )

            if report:
                flash('Risk report generated successfully!', 'success')
                return redirect(url_for('reports.view_report', report_id=report.id))
            else:
                flash('Failed to generate risk report. No historical data available.', 'warning')
                return redirect(url_for('reports.index'))

        # GET request - show form
        from app.models.portfolio import Portfolio
        portfolios = Portfolio.query.filter_by(user_id=current_user.id).all()

        return render_template(
            'reports/generate_risk.html',
            portfolios=portfolios
        )
    except Exception as e:
        from flask import current_app
        current_app.logger.error(f"Risk report error: {str(e)}")
        import traceback
        current_app.logger.error(traceback.format_exc())
        flash(f"Error generating risk report: {str(e)}", "danger")
        return redirect(url_for('reports.index'))