from flask import Blueprint, render_template, flash, redirect, url_for, request
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.security import check_password_hash, generate_password_hash
from app.forms import LoginForm, RegistrationForm, ForgotPasswordForm, ResetPasswordForm
from app.models.user import User
from app import db
from flask_mail import Mail, Message
from app.utils import generate_reset_token, verify_reset_token

from app import mail

bp = Blueprint('auth', __name__)

#Login Blueprint
@bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('portfolio.dashboard'))

    form = LoginForm()
    if form.validate_on_submit():
        user  = User.query.filter_by(email=form.email.data).first()
        if user and check_password_hash(user.password_hash, form.password.data):
            login_user(user)
            next_page = request.args.get('next')
            return redirect(next_page or url_for('portfolio.dashboard'))
        flash('Invalid email or password.')
    return render_template('auth/login.html', form=form)

#Registration blueprint
@bp.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('portfolio.dashboard'))

    form = RegistrationForm()
    if form.validate_on_submit():
        if User.query.filter_by(email=form.email.data).first():
            flash('Email already registered')
            return redirect(url_for('auth.register'))
        elif User.query.filter_by(username=form.username.data).first():
            flash('Username already registered')
            return redirect(url_for('auth.login'))
        elif form.validate_on_submit():
            if not form.disclaimer_accepted.data:
                flash('You must accept the disclaimer to register', 'danger')

        user = User(
            username=form.username.data,
            email=form.email.data,
            password_hash=generate_password_hash(form.password.data)
        )
        db.session.add(user)
        db.session.commit()
        flash('Registration successful!')
        return redirect(url_for('auth.login'))
    return render_template('auth/register.html', form=form)

@bp.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('auth.login'))


#Forgot password Link
@bp.route('/forgot', methods=['GET', 'POST'])
def forgot():
    if current_user.is_authenticated:
        return redirect(url_for('portfolio.dashboard'))
    form = ForgotPasswordForm()

    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()

        if user:
            token = generate_reset_token(user.email)
            reset_url = url_for('auth.reset_password', token=token, _external=True)

            #Sending Email
            msg = Message('Password Reset Request',
                          sender="noreply@example.com",
                          recipients=[user.email])
            msg.body = f"Click the link to reset your password: {reset_url}\nIf you did not request this, ignore this email."

            mail.send(msg)
            flash('A password reset link has been sent to your email.', 'info')
        else:
            flash('No account with that email exists.', 'warning')

        return redirect(url_for('auth.login'))
    return render_template('auth/forgot.html', form=form)


@bp.route('/reset/<token>', methods=['GET', 'POST'])
def reset_password(token):
    if current_user.is_authenticated:
        return redirect(url_for('portfolio.dashboard'))

    form = ResetPasswordForm() # Initailizing Form

    if form.validate_on_submit():
        email = verify_reset_token(token)
        if not email:
            flash('Invalid or expired token', 'warning')
            return redirect(url_for('auth.forgot'))

        user=User.query.filter_by(email=email).first()
        if not user:
            flash('No account with that email exists.', 'danger')
            return redirect(url_for('auth.forgot'))

        user.set_password(form.password.data) #Updating password
        db.session.commit()

        flash('Your password has been updated! You can now log in.', 'success')
        return redirect(url_for('auth.login'))

    return render_template('auth/reset_password.html', form=form, token=token)


