# -*- coding: utf-8 -*-
"""
    WhatAClass.blueprints.user_mng_blue
    ~~~~~~~~~~~~~~~~~~~~~~
    Blueprint that adds a user management system to the app.


    :author: Javier Martínez
"""

from flask import (Blueprint, flash, render_template, url_for, abort,
                   redirect, session, request)
from flask_login import login_user, logout_user, current_user
from itsdangerous import BadSignature
from flask_babel import gettext as _
from sqlalchemy.exc import IntegrityError

from .redirect import is_safe_url
from .forms import LoginForm, SignUpForm, EmailForm, PasswordForm
from .models import User
from ..user_server import email_server
from ..user_server import db, ts, login_manager


user_mng = Blueprint('user_mng', __name__, template_folder='templates')


@login_manager.user_loader
def load_user(id):
    return User.query.get(int(id))


@user_mng.route('/login', methods=['GET', 'POST'])
def login():
    """Try to log in the user with the information provided."""
    view = 'login.html'

    next_ = request.args.get('next')

    if current_user.is_authenticated:
        flash(_('There is a logged in user already.'))
        return redirect(url_for('index'))

    form = LoginForm()

    if form.validate_on_submit():

        user = User.query.filter_by(email=form.email.data).first()

        if not check_and_login(form.password.data, user):
            return render_template(view, form=form)

        flash(_('Logged in successfully.'))

        if not is_safe_url(request, next_):
            return redirect(url_for('index'))

        return redirect(next_ or url_for('index'))

    return render_template(view, form=form)


def check_and_login(password, user):
    """Launch exception (that should be used [flask, werkzeug...]) if
    something does not match with what is expected."""
    if user is None or not user.is_correct_password(password):
        flash(_('Email or password were not correct.'))
        return False
    if not user.email_confirmed:
        flash(_('Email was not confirmed yet.'))
        return False
    if not login_user(user):
        flash(_('Something failed, contact your administrator.'))
        return False
    return True


@user_mng.route('/logout')
def logout():
    """Logs the user out, has no effect if there was no one logged in."""
    logout_user()
    session.clear()
    return redirect(url_for('index'))


@user_mng.route('/signup', methods=['GET', 'POST'])
def sign_up():
    """Creates a user from the email and password given and sends an email with
    a time sensitive serialized url to authenticate the user (ts)."""
    view = 'signup.html'

    if current_user.is_authenticated:
        flash(_('There is a logged in user already.'))
        return redirect(url_for('index'))

    form = SignUpForm()

    if form.validate_on_submit():

        user = User(
            email=form.email.data,
            password=form.password.data
        )

        db.session.add(user)
        try:
            db.session.commit()
        except IntegrityError:
            flash(_('Only one account for each email. (You can use the + tricks.)'))
            return render_template(view, form=form)

        token = ts.dumps(user.email, salt=b'email-whataclass-salt-key')  # TODO Technical debt: refactor to conf

        confirm_url = url_for(
            'user_mng.confirm_email',
            token=token,
            _external=True)

        email_body = render_template(
            'email/activate.html',
            confirm_url=confirm_url)

        if not email_server.send_email(user.email,
                                       _('WhatAClass: Confirm your email'),
                                       email_body):
            user.email_confirmed = True
            db.session.add(user)
            db.session.commit()

        flash(_('Signed up successfully.'))

        return redirect(url_for('user_mng.login'))

    return render_template(view, form=form)


@user_mng.route('/confirm/<token>')
def confirm_email(token):
    """Try to see if the token is actually de-cypher-able and try to change
    the user to confirm the email."""
    try:
        email = ts.loads(token, salt=b'email-whataclass-salt-key', max_age=86400)  # TODO Tech debt: refactor to conf
    except BadSignature:
        return abort(404)

    user = User.query.filter_by(email=email).first_or_404()

    user.email_confirmed = True

    db.session.add(user)
    db.session.commit()

    flash(_('Email successfully confirmed.'))

    return redirect(url_for('user_mng.login'))


@user_mng.route('/reset', methods=['GET', 'POST'])
def reset():
    """Reset the password given through an email with a time sensitive link."""
    form = EmailForm()

    view = 'reset.html'

    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first_or_404()

        if not user.email_confirmed:
            flash(_('The email was not confirmed yet.'))
            return render_template(view, form=form)

        token = ts.dumps(user.email, salt=b'recover-whataclass-key')  # TODO Technical debt: refactor to conf

        reset_url = url_for(
            'user_mng.recover',
            token=token,
            _external=True)

        body = render_template(
            'email/recover.html',
            reset_url=reset_url)

        if not email_server.send_email(user.email,
                                       _('Password reset requested'),
                                       body):
            flash(_('Feature not available until the '
                    'administrator of the service sets an email.'))

        return redirect(url_for('index'))
    return render_template(view, form=form)


@user_mng.route('/recover/<token>', methods=['GET', 'POST'])
def recover(token):
    """Try to get the email from the token and give the chance to change
    password."""
    try:
        email = ts.loads(token, salt=b'recover-whataclass-key', max_age=86400)  # TODO Technical debt: refactor to conf
    except BadSignature:
        return abort(404)

    form = PasswordForm()

    if form.validate_on_submit():
        user = User.query.filter_by(email=email).first_or_404()

        user.password = form.password.data

        db.session.add(user)
        db.session.commit()

        flash(_('Password successfully changed.'))

        return redirect(url_for('user_mng.login'))

    return render_template('recover.html', form=form, token=token)


@user_mng.route('/other/login', methods=['GET', 'POST'])
def other_logins():
    """For logins that are not the usual in the app."""
    return render_template('other_logins.html')
