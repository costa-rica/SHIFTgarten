import os

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY_DMR')
    SQLALCHEMY_DATABASE_URI = os.environ.get('SQLALCHEMY_DATABASE_URI_DMR')
    # SQLALCHEMY_DATABASE_URI = 'sqlite:///'
    MAIL_SERVER = 'smtp.googlemail.com'
    MAIL_PORT = 587
    MAIL_USE_TLS = True
    MAIL_PASSWORD = os.environ.get('MAIL_PASSWORD_CBC')
    MAIL_USERNAME = os.environ.get('MAIL_USERNAME_CBC')