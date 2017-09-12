from . import app

app.config.from_object('config.default')


from flask_babel import Babel
babel = Babel(app)

from flask_sqlalchemy import SQLAlchemy
db = SQLAlchemy(app)

from itsdangerous import URLSafeTimedSerializer
ts = URLSafeTimedSerializer(app.config.get('TS_PASS', 'NotSecretKey'))  # TODO: have in config or will be using this one

from flask_bcrypt import Bcrypt
bcrypt = Bcrypt(app)

from .user_control.email import EmailServer
email_server = EmailServer(config=app.config.get('EMAIL_CONFIG', {'FROM': None,
                                                                  'PASS': None,
                                                                  'HOST': None,
                                                                  'PORT': None}))  # TODO: have in config or change here


from flask_login import LoginManager
login_manager = LoginManager(app)


from .user_control.models import User

@login_manager.user_loader
def load_user(user_id):
    """Method required by flask_login to identify how user are going to be logged in."""
    return User.query.filter(User.id == user_id.decode()).first()

csk = app.config.get('GOOGLE_CLIENT_ID', None)  # TODO: have in config or here
css = app.config.get('GOOGLE_SECRET', None)  # TODO: have in config or here

if csk is not None and css is not None:
    from flask_oauthlib.client import OAuth
    oauth = OAuth(app)
    google_ = oauth.remote_app(
        'google',
        consumer_key=csk,  # TODO: have in config or here
        consumer_secret=css,  # TODO: have in config or here
        request_token_params={
            'scope': 'email'
        },
        base_url='https://www.googleapis.com/oauth2/v1/',
        request_token_url=None,
        access_token_method='POST',
        access_token_url='https://accounts.google.com/o/oauth2/token',
        authorize_url='https://accounts.google.com/o/oauth2/auth',
    )

    from flask import session

    @google_.tokengetter
    def get_google_oauth_token():
        return session.get('google_token')

    from .user_control.oauth.google import oauth_google

    app.register_blueprint(oauth_google)


def _create_all_tables(app):
    """Creates all the tables with retries to give some time to the db to initialize,
    does not recreate existing tables."""
    print('Trying to create tables')
    max_attemps = 5
    with app.app_context():
        for n in range(max_attemps):
            try:
                db.init_app(app)
                db.create_all()
            except Exception as e:
                print('Attempt failed ({}/{}): {}'.format(n+1, max_attemps, e))
                from time import sleep
                sleep(5)
                # Could not create db: failing
                if n+1 == max_attemps:
                    print('Could not create db')
                    raise
            else:
                print('Finished creating tables')
                return


from .user_control.controllers import user_mng
app.register_blueprint(user_mng, )  # TODO: maybe add a PREFIX

login_manager.login_view = 'user_mng.login'


def run():
    _create_all_tables(app)
    app.run(host='0.0.0.0')


def debug(database_route):
    app.config['SQLALCHEMY_DATABASE_URI'] = database_route

    _create_all_tables(app)

    app.run(debug=True)


if __name__ == '__main__':
    run()



