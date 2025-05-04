from app import db
from app.models.notification import Notification
from app.models.user import User
from flask import current_app
from datetime import datetime
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

class NotificationService:
    def create_notification(self, user_id, title, message, notification_type='info', source='system'):
        """Creating a new notification for a user"""
        notification = Notification(
            user_id=user_id,
            title=title,
            message=message,
            notification_type=notification_type,
            source=source,
            is_read=False
        )
        db.session.add(notification)
        db.session.commit()
        return notification

    def get_user_notifications(self, user_id, unread_only=False, limit=20):
        """Getting notifications for a user"""
        query = Notification.query.filter_by(user_id=user_id)

        if unread_only:
            query = query.filter_by(is_read=False)

        return query.order_by(Notification.created_at.desc()).limit(limit).all()

    def mark_as_read(self, notification_id, user_id):
        """Marking a notification as read"""
        notification = Notification.query.filter_by(id=notification_id, user_id=user_id).first()
        if notification:
            notification.is_read = True
            db.session.commit()
            return True
        return False

    def mark_all_as_read(self, user_id):
        """Marking all notifications as read for a user"""
        Notification.query.filter_by(user_id=user_id, is_read=False).update({'is_read': True})
        db.session.commit()
        return True

    def delete_notification(self, notification_id, user_id):
        """Deleting a notification"""
        notification = Notification.query.filter_by(id=notification_id, user_id=user_id).first()
        if notification:
            db.session.delete(notification)
            db.session.commit()
            return True
        return False

    def create_price_alert_notification(self, user_id, symbol, price, threshold, alert_type):
        """Creating a notification for a price alert"""
        title = f"Price Alert: {symbol}"
        if alert_type == 'above':
            message = f"{symbol} has risen above your threshold of ${threshold:.2f}. Current price: ${price:.2f}"
        else:
            message = f"{symbol} has fallen below your threshold of ${threshold:.2f}. Current price: ${price:.2f}"

        return self.create_notification(
            user_id=user_id,
            title=title,
            message=message,
            notification_type='alert',
            source='market'
        )

    def create_portfolio_change_notification(self, user_id, portfolio_name, change_percent):
        """Creating a notification for significant portfolio changes"""
        direction = "increased" if change_percent > 0 else "decreased"
        title = f"Portfolio Update: {portfolio_name}"
        message = f"Your portfolio '{portfolio_name}' has {direction} by {abs(change_percent):.2f}% today."

        notification_type = 'success' if change_percent > 0 else 'warning'

        return self.create_notification(
            user_id=user_id,
            title=title,
            message=message,
            notification_type=notification_type,
            source='portfolio'
        )

    def send_email_notification(self, user_id, subject, body):
        """Sending an email notification to a user"""
        user = User.query.get(user_id)
        if not user or not user.email:
            return False

        try:
            # Get email config from app config
            smtp_server = current_app.config.get('MAIL_SERVER')
            smtp_port = current_app.config.get('MAIL_PORT')
            smtp_user = current_app.config.get('MAIL_USERNAME')
            smtp_password = current_app.config.get('MAIL_PASSWORD')
            sender_email = current_app.config.get('MAIL_DEFAULT_SENDER')

            # Create message
            msg = MIMEMultipart()
            msg['From'] = sender_email
            msg['To'] = user.email
            msg['Subject'] = subject

            # Add body to email
            msg.attach(MIMEText(body, 'plain'))

            # Send email
            server = smtplib.SMTP(smtp_server, smtp_port)
            server.starttls()
            server.login(smtp_user, smtp_password)
            server.send_message(msg)
            server.quit()

            return True
        except Exception as e:
            current_app.logger.error(f"Failed to send email notification: {str(e)}")
            return False