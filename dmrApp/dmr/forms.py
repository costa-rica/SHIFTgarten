from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileAllowed #used for image uploading
from wtforms import StringField, PasswordField, SubmitField, BooleanField\
    , TextAreaField, DateTimeField, FloatField, DateField, TimeField
from wtforms.validators import DataRequired, Length, Email, EqualTo, ValidationError
from wtforms_sqlalchemy.fields import QuerySelectField
from dmrApp.models import User, Restaurants, Employeeroles
from flask_login import current_user
from datetime import datetime
from dmrApp import db
from dmrApp.main.utils import buildUserPermDict

def choice_query_restaurant():
    userObjList=[User.query.get(current_user.id)]
    userPermDict=buildUserPermDict(userObjList)
    resIds=list(userPermDict.values())[0]
    return db.session.query(Restaurants).filter(Restaurants.id.in_(resIds))

class DashboardForm(FlaskForm):
    restaurant = QuerySelectField(query_factory=choice_query_restaurant, allow_blank=True,
                                  validators=[DataRequired()], get_label='name')
    dmrDate = DateField('date', validators=[DataRequired()], format='%Y-%m-%d')
    viewDmr = SubmitField('View DMR')
    newDmr = SubmitField('Make New DMR')


class DmrForm(FlaskForm):
    # dmrDate = DateField('date', validators=[DataRequired()], format='%Y-%m-%d')
    startCash = FloatField('startCash', validators=[DataRequired(False)])
    payout = FloatField('payout', validators=[DataRequired(False)])
    sales = FloatField('sales', validators=[DataRequired(False)])
    compSales = FloatField('comp sales', validators=[DataRequired(False)])
    voidSales = FloatField('void sales', validators=[DataRequired(False)])
    cashDrop = FloatField('cash drop', validators=[DataRequired(False)])
    expectedCash = FloatField('expected cash', validators=[DataRequired(False)])
    numHoursWorked = FloatField('number of hours worked', validators=[DataRequired(False)])
    bartenderTipsPerHour = FloatField('Bartender Tips/Hour', validators=[DataRequired(False)])
    appTipsPerHour = FloatField('Apprentice Tips/Hour', validators=[DataRequired(False)])
    creditCardTip = FloatField('credit card tips', validators=[DataRequired(False)])
    cashTip=FloatField('cash tips', validators=[DataRequired(False)])
    tip = FloatField('sum of tips', validators=[DataRequired(False)])
    wages = FloatField('sum of wages', validators=[DataRequired(False)])
    dmrSubmit = SubmitField('Update DMR')
#     add time of update


class ShiftForm(FlaskForm):
    # role = QuerySelectField(query_factory=choice_query_role, allow_blank=True,
    #                               validators=[DataRequired()], get_label='role')
    name = StringField('Employee Name')
    schedTime = StringField('scheduled time')
    timeStart = TimeField('start time')
    timeOff = TimeField('off time')
    # hoursWorked = FloatField('hours worked')
    # shiftTips = FloatField('shift tips')
    shiftSubmit = SubmitField('Add shift')
