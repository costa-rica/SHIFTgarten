import os
import json

with open('/etc/config.json') as config_file:
	config = json.load(config_file)

class Config:
    SECRET_KEY = config.get('SECRET_KEY_DMR')
    SQLALCHEMY_DATABASE_URI = config.get('SQLALCHEMY_DATABASE_URI_DMR')
    MAIL_SERVER = 'smtp.googlemail.com'
    MAIL_PORT = 587
    MAIL_USE_TLS = True
    MAIL_PASSWORD = config.get('MAIL_PASSWORD_CBC')
    MAIL_USERNAME = config.get('MAIL_USERNAME_CBC')