import os

# SQLALCHEMY
SQLALCHEMY_TRACK_MODIFICATIONS = True
SQLALCHEMY_ECHO = False
SQLALCHEMY_DATABASE_URI = os.getenv('DATABASE_URL', 'sqlite:////usr/src/app/user.db')

# BCRYPT
BCRYPT_LOG_ROUNDS = 12

# CSRF
SECRET_KEY = os.getenv('SECRET_KEY', 'This_key_is_not_a_secret')
