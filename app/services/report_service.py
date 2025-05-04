from app import db
from app.models.report import Report
from app.models.user import User
from app.models.portfolio import Portfolio, Holding
from app.services.market_service import MarketService
from app.services.notification_service import NotificationService
from datetime import datetime
import pandas as pd
import os
import matplotlib.pyplot as plt
from flask import current_app
import seaborn as sns
import numpy as np

from app.models.report import Report

from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter


class ReportService:
    def __init__(self):
        self.market_service = MarketService()
        self.notification_service = NotificationService()

    def create_report(self, user_id, title, description, report_type, format='pdf'):
        """Create a new report record"""
        report = Report(
            user_id=user_id,
            title=title,
            description=description,
            report_type=report_type,
            format=format,
            generated_at=datetime.utcnow()
        )
        db.session.add(report)
        db.session.commit()
        return report

    def get_user_reports(self, user_id, report_type=None, limit=20):
        """Get reports for a user"""
        query = Report.query.filter_by(user_id=user_id)

        if report_type:
            query = query.filter_by(report_type=report_type)

        return query.order_by(Report.generated_at.desc()).limit(limit).all()

    def get_report(self, report_id, user_id):
        """Get a specific report"""
        return Report.query.filter_by(id=report_id, user_id=user_id).first()

    def archive_report(self, report_id, user_id):
        """Archive a report"""
        report = Report.query.filter_by(id=report_id, user_id=user_id).first()
        if report:
            report.is_archived = True
            db.session.commit()
            return True
        return False

    def delete_report(self, report_id, user_id):
        """Delete a report"""
        report = Report.query.filter_by(id=report_id, user_id=user_id).first()
        if report:
            # Delete the file if it exists
            if report.file_path and os.path.exists(report.file_path):
                os.remove(report.file_path)

            db.session.delete(report)
            db.session.commit()
            return True
        return False

    def generate_portfolio_performance_report(self, user_id, portfolio_id=None):
        """Generate a portfolio performance report"""
        from app.models.portfolio import PortfolioHistory

        # Define the report directory
        report_dir = os.path.join(current_app.instance_path, 'reports')
        os.makedirs(report_dir, exist_ok=True)

        # Get the portfolio
        if portfolio_id:
            portfolio = Portfolio.query.filter_by(id=portfolio_id, user_id=user_id).first()
            if not portfolio:
                return None
            portfolios = [portfolio]
        else:
            portfolios = Portfolio.query.filter_by(user_id=user_id).all()
            if not portfolios:
                return None

        # Create the report record
        report_title = f"Performance Report - {portfolios[0].name if portfolio_id else 'All Portfolios'}"
        report = self.create_report(
            user_id=user_id,
            title=report_title,
            description="Analysis of portfolio performance over time",
            report_type="performance",
            format="pdf"
        )

        # Prepare data for each portfolio
        all_portfolio_data = []
        for portfolio in portfolios:
            # Get historical data
            history = PortfolioHistory.query.filter_by(portfolio_id=portfolio.id).order_by(PortfolioHistory.date).all()

            if not history:
                continue

            # Create dataframe from history
            history_data = {
                'date': [h.date for h in history],
                'value': [h.total_value for h in history]
            }
            df = pd.DataFrame(history_data)

            # Calculate performance metrics
            if len(df) > 1:
                start_value = df['value'].iloc[0]
                end_value = df['value'].iloc[-1]
                total_return = (end_value - start_value) / start_value * 100

                # Calculate daily returns
                df['daily_return'] = df['value'].pct_change()

                # Calculate metrics
                volatility = df['daily_return'].std() * (252 ** 0.5) * 100  # Annualized volatility
                sharpe = np.mean(df['daily_return']) / df['daily_return'].std() * (252 ** 0.5)  # Sharpe ratio

                portfolio_data = {
                    'portfolio_name': portfolio.name,
                    'start_date': df['date'].iloc[0],
                    'end_date': df['date'].iloc[-1],
                    'start_value': start_value,
                    'end_value': end_value,
                    'total_return': total_return,
                    'volatility': volatility,
                    'sharpe_ratio': sharpe,
                    'history_df': df
                }
                all_portfolio_data.append(portfolio_data)

        if not all_portfolio_data:
            # No historical data found
            self.delete_report(report.id, user_id)
            return None

        # Create the report visualizations and save to file
        report_file = os.path.join(report_dir, f"performance_report_{report.id}.pdf")

        # Use matplotlib to create visualizations
        plt.figure(figsize=(10, 8))

        # Plot performance over time for each portfolio
        plt.subplot(2, 1, 1)
        for data in all_portfolio_data:
            plt.plot(data['history_df']['date'], data['history_df']['value'], label=data['portfolio_name'])

        plt.title('Portfolio Value Over Time')
        plt.xlabel('Date')
        plt.ylabel('Value ($)')
        plt.legend()
        plt.grid(True)

        # Create a bar chart of total returns
        plt.subplot(2, 1, 2)
        portfolio_names = [data['portfolio_name'] for data in all_portfolio_data]
        returns = [data['total_return'] for data in all_portfolio_data]

        plt.bar(portfolio_names, returns)
        plt.title('Total Return by Portfolio')
        plt.xlabel('Portfolio')
        plt.ylabel('Total Return (%)')
        plt.xticks(rotation=45)
        plt.grid(True, axis='y')

        plt.tight_layout()
        plt.savefig(report_file)
        plt.close()

        # Update the report record with the file path
        report.file_path = report_file
        db.session.commit()

        # Create a notification
        self.notification_service.create_notification(
            user_id=user_id,
            title="Performance Report Generated",
            message=f"Your portfolio performance report is now available.",
            notification_type="info",
            source="report"
        )

        return report

    def generate_allocation_report(self, user_id, portfolio_id=None):
        """Generate an allocation report for holdings by sector and asset type"""
        # Define the report directory
        report_dir = os.path.join(current_app.instance_path, 'reports')
        os.makedirs(report_dir, exist_ok=True)

        # Get the portfolio
        if portfolio_id:
            portfolio = Portfolio.query.filter_by(id=portfolio_id, user_id=user_id).first()
            if not portfolio:
                return None
            portfolios = [portfolio]
        else:
            portfolios = Portfolio.query.filter_by(user_id=user_id).all()
            if not portfolios:
                return None

        # Create the report record
        report_title = f"Allocation Report - {portfolios[0].name if portfolio_id else 'All Portfolios'}"
        report = self.create_report(
            user_id=user_id,
            title=report_title,
            description="Analysis of portfolio allocation by sector and asset type",
            report_type="allocation",
            format="pdf"
        )

        # Collect all holdings data
        all_holdings = []
        for portfolio in portfolios:
            for holding in portfolio.holdings:
                stock_data = self.market_service.get_stock_data(holding.symbol)
                if not stock_data:
                    continue

                current_price = stock_data.get('current_price', 0)
                current_value = current_price * holding.quantity

                holding_data = {
                    'portfolio_name': portfolio.name,
                    'symbol': holding.symbol,
                    'quantity': holding.quantity,
                    'current_price': current_price,
                    'current_value': current_value,
                    'sector': stock_data.get('sector', 'Unknown'),
                    'asset_type': stock_data.get('asset_type', 'Stock')
                }
                all_holdings.append(holding_data)

        if not all_holdings:
            # No holdings found
            self.delete_report(report.id, user_id)
            return None

        # Create a DataFrame for analysis
        holdings_df = pd.DataFrame(all_holdings)

        # Analyze sector allocation
        sector_allocation = holdings_df.groupby('sector')['current_value'].sum().reset_index()
        sector_allocation['percentage'] = sector_allocation['current_value'] / sector_allocation[
            'current_value'].sum() * 100

        # Analyze asset type allocation
        asset_allocation = holdings_df.groupby('asset_type')['current_value'].sum().reset_index()
        asset_allocation['percentage'] = asset_allocation['current_value'] / asset_allocation[
            'current_value'].sum() * 100

        # Create the report visualizations and save to file
        report_file = os.path.join(report_dir, f"allocation_report_{report.id}.pdf")

        # Use matplotlib to create visualizations
        plt.figure(figsize=(12, 10))

        # Sector allocation pie chart
        plt.subplot(2, 1, 1)
        plt.pie(sector_allocation['percentage'], labels=sector_allocation['sector'], autopct='%1.1f%%')
        plt.title('Portfolio Allocation by Sector')
        plt.axis('equal')

        # Asset type allocation pie chart
        plt.subplot(2, 1, 2)
        plt.pie(asset_allocation['percentage'], labels=asset_allocation['asset_type'], autopct='%1.1f%%')
        plt.title('Portfolio Allocation by Asset Type')
        plt.axis('equal')

        plt.tight_layout()
        plt.savefig(report_file)
        plt.close()

        # Update the report record with the file path
        report.file_path = report_file
        db.session.commit()

        # Create a notification
        self.notification_service.create_notification(
            user_id=user_id,
            title="Allocation Report Generated",
            message=f"Your portfolio allocation report is now available.",
            notification_type="info",
            source="report"
        )

        return report

    def generate_portfolio_summary_report(self, user_id, portfolio_id=None):
        """Generating portfolio summary report"""
        from app.models.portfolio import Portfolio, Holding
        from app.services.market_service import MarketService

        market_service = MarketService()

        # Get user's portfolios
        if portfolio_id:
            portfolios = Portfolio.query.filter_by(id=portfolio_id, user_id=user_id).all()
        else:
            portfolios = Portfolio.query.filter_by(user_id=user_id).all()

        if not portfolios:
            return None

        # Preparing report data
        report_data = []
        total_value = 0
        total_cost = 0

        for portfolio in portfolios:
            portfolio_data = {
                'portfolio_name': portfolio.name,
                'holdings': []
            }

            portfolio_value = 0
            portfolio_cost = 0

            for holding in portfolio.holdings:
                stock_data = market_service.get_stock_data(holding.symbol)
                current_price = stock_data.get('current_price', 0)
                current_value = current_price * holding.quantity
                purchase_value = holding.purchase_price * holding.quantity
                gain_loss = current_value - purchase_value
                gain_loss_percent = (gain_loss / purchase_value * 100) if purchase_value > 0 else 0

                holding_data = {
                    'symbol': holding.symbol,
                    'quantity': holding.quantity,
                    'purchase_price': holding.purchase_price,
                    'current_price': current_price,
                    'current_value': current_value,
                    'gain_loss': gain_loss,
                    'gain_loss_percent': gain_loss_percent
                }

                portfolio_data['holdings'].append(holding_data)
                portfolio_value += current_value
                portfolio_cost += purchase_value

            portfolio_data['total_value'] = portfolio_value
            portfolio_data['total_cost'] = portfolio_cost
            portfolio_data['total_gain_loss'] = portfolio_value - portfolio_cost
            portfolio_data['total_gain_loss_percent'] = (
                    (portfolio_value - portfolio_cost) / portfolio_cost * 100) if portfolio_cost > 0 else 0

            report_data.append(portfolio_data)
            total_value += portfolio_value
            total_cost += portfolio_cost

        # Creating report record
        report = Report(
            user_id=user_id,
            title="Portfolio Summary CSV Report",
            description="Exportable CSV data of your portfolio holdings",
            report_type='portfolio_summary',
            format='csv',
            generated_at=datetime.utcnow()
        )
        db.session.add(report)
        db.session.commit()

        # Saving report data
        report_path = os.path.join(current_app.config['REPORT_DIR'], f'report_{report.id}.csv')

        # Creating a flat structure for CSV export
        csv_data = []
        for portfolio in report_data:
            for holding in portfolio['holdings']:
                row = {
                    'portfolio_name': portfolio['portfolio_name'],
                    **holding
                }
                csv_data.append(row)

        # Adding total value row for the entire report
        total_value_row = {
            'portfolio_name': 'Total Portfolio Value',
            'quantity': '',
            'purchase_price': '',
            'current_price': '',
            'current_value': total_value,  # Total portfolio value
            'gain_loss': total_value - total_cost,  # Total gain/loss
            'gain_loss_percent': (total_value - total_cost) / total_cost * 100 if total_cost > 0 else 0
        }

        # Append the total value row to the csv_data
        csv_data.append(total_value_row)

        df = pd.DataFrame(csv_data)
        df.to_csv(report_path, index=False)

        # Updating report record with path
        report.file_path = report_path
        db.session.commit()

        # Creating notification
        self.notification_service.create_notification(
            user_id=user_id,
            title="Portfolio Summary Report",
            message=f"Your portfolio summary report is now available. Total value: ${total_value:.2f}",
            notification_type='info',
            source='report'
        )

        return report

    def generate_portfolio_summary_pdf_report(self, user_id, portfolio_id=None):
        """Generating beautiful portfolio summary report as PDF"""
        from app.models.portfolio import Portfolio
        from app.services.market_service import MarketService

        market_service = MarketService()

        if portfolio_id:
            portfolios = Portfolio.query.filter_by(id=portfolio_id, user_id=user_id).all()
        else:
            portfolios = Portfolio.query.filter_by(user_id=user_id).all()

        if not portfolios:
            return None

        # Create report record
        report = Report(
            user_id=user_id,
            title="Portfolio Summary PDF Report",
            description="Comprehensive overview of your portfolio holdings and performance",
            report_type='portfolio_summary_pdf',
            format='pdf',
            generated_at=datetime.utcnow()
        )
        db.session.add(report)
        db.session.commit()

        # Setup PDF
        pdf_path = os.path.join(current_app.config['REPORT_DIR'], f'report_{report.id}.pdf')
        doc = SimpleDocTemplate(pdf_path, pagesize=letter)
        elements = []
        styles = getSampleStyleSheet()

        title = Paragraph("Portfolio Summary Report", styles['Title'])
        elements.append(title)
        elements.append(Spacer(1, 24))

        total_value = 0
        total_cost = 0

        for portfolio in portfolios:
            portfolio_title = Paragraph(f"<b>Portfolio: {portfolio.name}</b>", styles['Heading2'])
            elements.append(portfolio_title)
            elements.append(Spacer(1, 12))

            # Table headers
            data = [['Symbol', 'Quantity', 'Purchase Price', 'Current Price', 'Current Value', 'Gain/Loss %']]

            for holding in portfolio.holdings:
                stock_data = market_service.get_stock_data(holding.symbol)
                current_price = stock_data.get('current_price', 0)
                current_value = current_price * holding.quantity
                purchase_value = holding.purchase_price * holding.quantity
                gain_loss = current_value - purchase_value
                gain_loss_percent = (gain_loss / purchase_value * 100) if purchase_value > 0 else 0

                data.append([
                    holding.symbol,
                    f"{holding.quantity:.2f}",
                    f"${holding.purchase_price:,.2f}",
                    f"${current_price:,.2f}",
                    f"${current_value:,.2f}",
                    f"{gain_loss_percent:.2f}%",
                ])

                total_value += current_value
                total_cost += purchase_value

            # Create the holdings table
            table = Table(data, hAlign='LEFT', colWidths=[70, 70, 90, 90, 90, 70])

            # Style for holdings table
            style = TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.lightblue),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
                ('ALIGN', (0, 0), (-1, 0), 'CENTER'),  # header
                ('ALIGN', (1, 1), (-1, -1), 'RIGHT'),  # numbers right
                ('ALIGN', (0, 1), (0, -1), 'LEFT'),  # symbol left
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, -1), 9),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('BACKGROUND', (0, 1), (-1, -1), colors.whitesmoke),
                ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
            ])

            # Add color for Gain/Loss %
            for i in range(1, len(data)):
                gain_loss_value = float(data[i][5].replace('%', ''))
                if gain_loss_value > 0:
                    style.add('TEXTCOLOR', (5, i), (5, i), colors.green)
                elif gain_loss_value < 0:
                    style.add('TEXTCOLOR', (5, i), (5, i), colors.red)
                else:
                    style.add('TEXTCOLOR', (5, i), (5, i), colors.black)

            table.setStyle(style)

            elements.append(table)
            elements.append(Spacer(1, 24))

        # After all portfolios, add total portfolio summary
        if total_cost > 0:
            total_gain_loss = total_value - total_cost
            total_gain_loss_percent = (total_gain_loss / total_cost) * 100
        else:
            total_gain_loss = 0
            total_gain_loss_percent = 0

        total_data = [[
            'Total Portfolio Value', '', '', '',
            f"${total_value:,.2f}",
            f"{total_gain_loss_percent:.2f}%"
        ]]

        total_table = Table(total_data, hAlign='LEFT', colWidths=[70, 70, 90, 90, 90, 70])

        total_table_style = TableStyle([
            ('SPAN', (0, 0), (3, 0)),
            ('BACKGROUND', (0, 0), (-1, 0), colors.lightgrey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.black),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
        ])

        total_table.setStyle(total_table_style)
        elements.append(total_table)

        doc.build(elements)

        report.file_path = pdf_path
        db.session.commit()

        self.notification_service.create_notification(
            user_id=user_id,
            title="Portfolio PDF Report",
            message="Your beautiful portfolio PDF report is now available!",
            notification_type='info',
            source='report'
        )

        return report


    def generate_tax_report(self, user_id, tax_year=None, portfolio_id=None):
        """Generate a tax report showing realized gains/losses and dividend income"""
        from app.models.portfolio import Portfolio
        from app.services.market_service import MarketService

        market_service = MarketService()

        # If no tax year is specified, use the current year
        if not tax_year:
            tax_year = datetime.utcnow().year

        # Define the report directory
        report_dir = os.path.join(current_app.instance_path, 'reports')
        os.makedirs(report_dir, exist_ok=True)

        # Get the portfolio(s)
        if portfolio_id:
            portfolios = Portfolio.query.filter_by(id=portfolio_id, user_id=user_id).all()
        else:
            portfolios = Portfolio.query.filter_by(user_id=user_id).all()

        if not portfolios:
            return None

        # Create the report record
        report_title = f"Tax Report {tax_year} - {portfolios[0].name if portfolio_id else 'All Portfolios'}"
        report = self.create_report(
            user_id=user_id,
            title=report_title,
            description=f"Tax information for {tax_year} including realized gains/losses and dividend income",
            report_type="tax",
            format="pdf"
        )

        # Prepare data for tax report
        tax_data = []
        total_realized_gains = 0
        total_dividend_income = 0

        for portfolio in portfolios:
            # Get realized transactions
            # In a real implementation, you'd query a transactions table
            # For this example, we'll create simulated data

            # Simulate realized gains/losses
            realized_gains = []
            for i in range(3):
                realized_gains.append({
                    'symbol': f"STOCK{i + 1}",
                    'purchase_date': datetime(tax_year - 1, i + 1, 15),
                    'sale_date': datetime(tax_year, i + 6, 20),
                    'quantity': 10 * (i + 1),
                    'purchase_price': 100.0 + (i * 10),
                    'sale_price': 120.0 + (i * 15),
                    'gain_loss': (120.0 + (i * 15) - (100.0 + (i * 10))) * 10 * (i + 1)
                })
                total_realized_gains += realized_gains[-1]['gain_loss']

            # Simulate dividend income
            dividend_income = []
            for i in range(2):
                dividend_income.append({
                    'symbol': f"DIV{i + 1}",
                    'payment_date': datetime(tax_year, i + 3, 10),
                    'amount': 50.0 * (i + 1.5),
                    'qualified': i % 2 == 0
                })
                total_dividend_income += dividend_income[-1]['amount']

            portfolio_tax_data = {
                'portfolio_name': portfolio.name,
                'realized_gains': realized_gains,
                'dividend_income': dividend_income
            }
            tax_data.append(portfolio_tax_data)

        # Create the report visualizations and save to file
        report_file = os.path.join(report_dir, f"tax_report_{report.id}.pdf")

        # Use matplotlib to create visualizations
        plt.figure(figsize=(10, 8))

        # Plot realized gains/losses
        plt.subplot(2, 1, 1)
        labels = ['Realized Gains/Losses', 'Dividend Income']
        values = [total_realized_gains, total_dividend_income]

        plt.bar(labels, values)
        plt.title(f'Tax Summary for {tax_year}')
        plt.ylabel('Amount ($)')
        plt.grid(True, axis='y')

        # Create a pie chart of qualified vs non-qualified dividends
        plt.subplot(2, 1, 2)
        qualified = sum([div['amount'] for port in tax_data for div in port['dividend_income'] if div['qualified']])
        non_qualified = sum([div['amount'] for port in tax_data for div in port['dividend_income'] if not div['qualified']])

        plt.pie([qualified, non_qualified], labels=['Qualified Dividends', 'Non-Qualified Dividends'], autopct='%1.1f%%')
        plt.title('Dividend Breakdown')

        plt.tight_layout()
        plt.savefig(report_file)
        plt.close()

        # Update the report record with the file path
        report.file_path = report_file
        db.session.commit()

        # Create a notification
        self.notification_service.create_notification(
            user_id=user_id,
            title=f"Tax Report for {tax_year} Generated",
            message=f"Your tax report for {tax_year} is now available.",
            notification_type="info",
            source="report"
        )

        return report


    def generate_risk_analysis_report(self, user_id, portfolio_id=None):
        """Generate a risk analysis report with volatility metrics and correlation analysis"""
        from app.models.portfolio import Portfolio, PortfolioHistory

        # Define the report directory
        report_dir = os.path.join(current_app.instance_path, 'reports')
        os.makedirs(report_dir, exist_ok=True)

        # Get the portfolio(s)
        if portfolio_id:
            portfolios = Portfolio.query.filter_by(id=portfolio_id, user_id=user_id).all()
        else:
            portfolios = Portfolio.query.filter_by(user_id=user_id).all()

        if not portfolios:
            return None

        # Create the report record
        report_title = f"Risk Analysis - {portfolios[0].name if portfolio_id else 'All Portfolios'}"
        report = self.create_report(
            user_id=user_id,
            title=report_title,
            description="Detailed risk analysis including volatility metrics and stress test scenarios",
            report_type="risk",
            format="pdf"
        )

        # Collect data for risk analysis
        all_portfolio_data = []

        for portfolio in portfolios:
            # Get historical data
            history = PortfolioHistory.query.filter_by(portfolio_id=portfolio.id).order_by(PortfolioHistory.date).all()

            if not history:
                continue

            # Create dataframe from history
            history_data = {
                'date': [h.date for h in history],
                'value': [h.total_value for h in history]
            }
            df = pd.DataFrame(history_data)

            # Calculate daily returns
            df['daily_return'] = df['value'].pct_change().fillna(0)

            # Calculate various risk metrics
            volatility = df['daily_return'].std() * (252 ** 0.5) * 100  # Annualized volatility
            max_drawdown = (df['value'] / df['value'].cummax() - 1).min() * 100  # Maximum drawdown

            # Calculate Value at Risk (VaR)
            var_95 = np.percentile(df['daily_return'], 5) * 100
            var_99 = np.percentile(df['daily_return'], 1) * 100

            # Create simulated stress tests
            stress_tests = [
                {
                    'scenario': 'Market Crash (2008)',
                    'impact': -45.0  # Simulated loss percentage
                },
                {
                    'scenario': 'Tech Bubble Burst',
                    'impact': -30.0
                },
                {
                    'scenario': 'Pandemic Shock',
                    'impact': -25.0
                },
                {
                    'scenario': 'Interest Rate Hike',
                    'impact': -10.0
                }
            ]

            portfolio_value = df['value'].iloc[-1] if not df.empty else 0

            # Calculate dollar impacts for each stress test
            for test in stress_tests:
                test['dollar_impact'] = portfolio_value * (test['impact'] / 100)

            portfolio_data = {
                'portfolio_name': portfolio.name,
                'current_value': portfolio_value,
                'volatility': volatility,
                'max_drawdown': max_drawdown,
                'var_95': var_95,
                'var_99': var_99,
                'stress_tests': stress_tests,
                'returns_df': df
            }

            all_portfolio_data.append(portfolio_data)

        if not all_portfolio_data:
            # No historical data found
            self.delete_report(report.id, user_id)
            return None

        # Create the report visualizations and save to file
        report_file = os.path.join(report_dir, f"risk_report_{report.id}.pdf")

        # Use matplotlib to create visualizations
        plt.figure(figsize=(12, 10))

        # Plot volatility comparison
        plt.subplot(2, 2, 1)
        portfolio_names = [data['portfolio_name'] for data in all_portfolio_data]
        volatilities = [data['volatility'] for data in all_portfolio_data]

        plt.bar(portfolio_names, volatilities)
        plt.title('Portfolio Volatility (Annualized)')
        plt.ylabel('Volatility (%)')
        plt.xticks(rotation=45)
        plt.grid(True, axis='y')

        # Plot max drawdown comparison
        plt.subplot(2, 2, 2)
        max_drawdowns = [data['max_drawdown'] for data in all_portfolio_data]

        plt.bar(portfolio_names, max_drawdowns)
        plt.title('Maximum Drawdown')
        plt.ylabel('Drawdown (%)')
        plt.xticks(rotation=45)
        plt.grid(True, axis='y')

        # Plot Value at Risk (VaR) for first portfolio
        plt.subplot(2, 2, 3)
        var_data = [[data['var_95'], data['var_99']] for data in all_portfolio_data]
        var_labels = ['95% VaR', '99% VaR']

        if var_data:
            plt.bar(var_labels, var_data[0])
            plt.title(f'Daily Value at Risk ({all_portfolio_data[0]["portfolio_name"]})')
            plt.ylabel('Loss (%)')
            plt.grid(True, axis='y')

        # Plot stress test scenarios for first portfolio
        plt.subplot(2, 2, 4)
        if all_portfolio_data:
            first_portfolio = all_portfolio_data[0]
            scenario_names = [test['scenario'] for test in first_portfolio['stress_tests']]
            impacts = [test['impact'] for test in first_portfolio['stress_tests']]

            plt.barh(scenario_names, impacts)
            plt.title(f'Stress Test Scenarios ({first_portfolio["portfolio_name"]})')
            plt.xlabel('Potential Loss (%)')
            plt.grid(True, axis='x')

        plt.tight_layout()
        plt.savefig(report_file)
        plt.close()

        # Update the report record with the file path
        report.file_path = report_file
        db.session.commit()

        # Create a notification
        self.notification_service.create_notification(
            user_id=user_id,
            title="Risk Analysis Report Generated",
            message="Your risk analysis report is now available.",
            notification_type="info",
            source="report"
        )

        return report
