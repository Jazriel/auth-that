# -*- coding: utf-8 -*-
"""
    WhatAClass.blueprints.oauth.google
    ~~~~~~~~~~~~~~~~~~~~~~



    :author: Javier Martínez
"""
from flask import Blueprint, request, session, redirect, url_for, flash
from flask_babel import gettext as _
from flask_login import login_user
from sqlalchemy.exc import IntegrityError, OperationalError

from ...user_server import google_, db
from ..models import User


oauth_google = Blueprint('oauth_google', __name__, url_prefix='/google')

@oauth_google.route('/login')
def login():
    return google_.authorize(callback=url_for('oauth_google.authorized', _external=True))


@oauth_google.route('/logout')
def logout():
    session.pop('google_token', None)
    return redirect(url_for('index'))


@oauth_google.route('/login/authorized')
def authorized():
    resp = google_.authorized_response()
    if resp is None:
        return 'Access denied: reason={} error={}'.format(
            request.args['error_reason'],
            request.args['error_description']
        )

    session['google_token'] = (resp['access_token'], '')

    try:
        user = User.query.filter_by(oauth_token=str(google_.get('userinfo').data.get('id'))).first()
    except OperationalError:
        user = None  # we'll register the user instead

    if not check_and_login_or_register(user, google_.get('userinfo')):
        return redirect(url_for('index.base'))

    return redirect(url_for('index.base'))


def check_and_login_or_register(user, google_user):
    """Login or register, if there are problems return flashes."""
    if user is None:

        user = User(
            email=google_user.data.get('email'),
            password=None,
            oauth_token=str(google_user.data.get('id'))
        )
        user.email_confirmed = True

        db.session.add(user)
        try:
            db.session.commit()
        except IntegrityError:
            flash(_('Only one account for each email. (You can use the + email tricks.)'))
            return False

    if not login_user(user):
        flash(_('Something failed, contact your administrator.'))
        return False
    return True



