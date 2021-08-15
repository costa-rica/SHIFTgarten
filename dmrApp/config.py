import os
import json

if os.environ.get('COMPUTERNAME')=='CAPTAIN2020':
    with open(r'D:\OneDrive\Documents\professional\config_files\config_dmrAppConda.json') as config_file:
        config = json.load(config_file)
elif os.environ.get('USER')=='sanjose':
    with open('/home/sanjose/Documents/environments/config.json') as config_file:
        config = json.load(config_file)
else:
    with open('/home/ubuntu/environments/config.json') as config_file:
        config = json.load(config_file)



class Config:
    SECRET_KEY = config.get('SECRET_KEY_DMR')
    SQLALCHEMY_DATABASE_URI = config.get('SQLALCHEMY_DATABASE_URI_DMR')
    MAIL_SERVER = 'smtp.googlemail.com'
    MAIL_PORT = 587
    MAIL_USE_TLS = True
    MAIL_PASSWORD = config.get('MAIL_PASSWORD_CBC')
    MAIL_USERNAME = config.get('MAIL_USERNAME_CBC')
    DEBUG = True
