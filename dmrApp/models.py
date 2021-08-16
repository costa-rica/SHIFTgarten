from dmrApp import db, login_manager
from datetime import datetime, date
from itsdangerous import TimedJSONWebSignatureSerializer as Serializer
from flask import current_app
from flask_login import UserMixin

from flask_script import Manager
from flask_migrate import Migrate, MigrateCommand

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


class Dmrs(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    dmrDate= db.Column(db.Date, default=datetime.today)
    startCash=db.Column(db.Float, nullable=True)
    payout=db.Column(db.Float)
    sales=db.Column(db.Float)
    compSales=db.Column(db.Float)
    voidSales=db.Column(db.Float)
    cashDrop=db.Column(db.Float)#dmrTop4-1
    expectedCash=db.Column(db.Float)#dmrTop5-1
    numHoursWorked=db.Column(db.Float)#dmrTop6-1
    bartenderTipsPerHour=db.Column(db.Float)#dmrTop7-1
    appTipsPerHour=db.Column(db.Float)
    creditCardTip=db.Column(db.Float)
    cashTip=db.Column(db.Float)
    tip=db.Column(db.Float)
    wages=db.Column(db.Float)
    dmrTimeStamp=db.Column(db.DateTime,default=datetime.now)
    infoFrom=db.Column(db.String(200))
    infoFromCount=db.Column(db.Integer)
    restaurantId = db.Column(db.Integer, db.ForeignKey('restaurants.id'))
    restaurantGroupId = db.Column(db.Integer)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))


    def __repr__(self):
        return f"Dmr('{self.id}','{self.dmrDate}','{self.restaurantId}'," \
               f"'{Restaurants.query.filter_by(id=self.restaurantId).with_entities(Restaurants.name).all()[0][0]}')"


class Shifts(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    shiftDate = db.Column(db.Date, default=datetime.today)
    name = db.Column(db.String(100))#name is in empid table
    schedTime= db.Column(db.String(100))
    timeStart= db.Column(db.DateTime)# ***, nullable=False
    timeOff= db.Column(db.DateTime)
    hoursWorked= db.Column(db.Float)
    shiftTips= db.Column(db.Float)
    shiftTipsShipgarten = db.Column(db.Float)
    wages=db.Column(db.Float)
    shiftsTimeStamp = db.Column(db.DateTime, default=datetime.now)
    empId= db.Column(db.Integer, db.ForeignKey('employees.id'))
    employeeRolesId=db.Column(db.Integer, db.ForeignKey('employeeroles.id'))
    userId = db.Column(db.Integer, db.ForeignKey('user.id'))
    restaurantId = db.Column(db.Integer, db.ForeignKey('restaurants.id'))
    restaurantGroupId = db.Column(db.Integer)


    def __repr__(self):
        return f"Shift('{self.id}','{self.schedTime}','empId: {self.empId}'," \
               f"'{Employees.query.filter_by(id=self.empId).with_entities(Employees.name).all()[0][0]}'," \
               f"'{Restaurants.query.filter_by(id=self.restaurantId).with_entities(Restaurants.name).all()[0][0]}')"


class Restaurants(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50))
    dmrId = db.relationship('Dmrs',backref='restaurant', lazy=True)
    shiftId = db.relationship('Shifts', backref='restaurant', lazy=True)
    empRolesId = db.relationship('Employeeroles',backref='restaurant', lazy=True)

    def __repr__(self):
        return f"Restaurants('{self.id}','{self.name}')"

class Employees(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50),nullable=False)
    timeStamp = db.Column(db.DateTime, default=datetime.now)
    createdBy = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    shifts = db.relationship('Shifts', backref='employee', lazy=True)
    empRoles = db.relationship('Employeeroles',backref='roles', lazy=True)
    deactivatedBy = db.Column(db.Integer)

    def __repr__(self):
        if self.deactivatedBy==None:
            return f"Employee('{self.id}','{self.name}','{self.empRoles[0].restaurant.name}')"
        else:
            deactivatedByUser=User.query.filter_by(id=self.deactivatedBy).with_entities(User.username).first()[0]
            return f"Employee('{self.id}','{self.name}','{self.empRoles[0].restaurant.name}', deactivatedBy:'{deactivatedByUser}')"


class Employeeroles(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    role= db.Column(db.String(50),nullable=False)
    wage= db.Column(db.Float)
    tipPercentage= db.Column(db.Float)
    notes=db.Column(db.Text)
    standardWageFlag=db.Column(db.Boolean, default=True, nullable=False)
    createdBy = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    restaurantId = db.Column(db.Integer,db.ForeignKey('restaurants.id'))
    shiftId = db.relationship('Shifts', backref='employeerole', lazy=True)
    standardWageId = db.Column(db.Integer,db.ForeignKey('standardwages.id'))
    empId = db.Column(db.Integer,db.ForeignKey('employees.id'))
    

    def __repr__(self):
        return f"Employeeroles('{self.id}','{self.role}','stdWageFlag: {self.standardWageFlag}'," \
        f"'{Restaurants.query.filter_by(id=self.restaurantId).with_entities(Restaurants.name).all()[0][0]}')"

class Standardwages(db.Model):
    id=db.Column(db.Integer, primary_key=True)
    role= db.Column(db.String(50),nullable=False)
    wage=db.Column(db.Float)
    tipPercentage= db.Column(db.Float)
    employeerolesId=db.relationship('Employeeroles',backref='standardwage', lazy=True)
    
    def __repr__(self):
        return f"Standardwages('{self.id}','{self.role}','wage: {self.wage}','tip pct: {self.tipPercentage}')"

class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username=db.Column(db.String(50), unique=True, nullable=False)
    email = db.Column(db.String(150), unique=True, nullable=False)
    image_file = db.Column(db.String(100),nullable=False, default='default.jpg')
    password = db.Column(db.String(100), nullable=False)
    timeStamp = db.Column(db.DateTime, default=datetime.now)
    permission = db.Column(db.Text, default="3")
    theme = db.Column(db.Text)
    posts = db.relationship('Post', backref='author', lazy=True)
    dmrsEntry = db.relationship('Dmrs', backref='dmrUser', lazy=True)
    shiftsEntry = db.relationship('Shifts', backref='dmrShiftUser', lazy=True)
    employeeId = db.relationship('Employees', backref='employeeUser', lazy=True)

    def get_reset_token(self, expires_sec=1800):
        s=Serializer(current_app.config['SECRET_KEY'], expires_sec)
        return s.dumps({'user_id': self.id}).decode('utf-8')

    @staticmethod
    def verify_reset_token(token):
        s=Serializer(current_app.config['SECRET_KEY'])
        try:
            user_id = s.loads(token)['user_id']
        except:
            return None
        return User.query.get(user_id)

    def __repr__(self):
        return f"User('{self.id}','{self.username}','{self.email}','{self.permission}')"

class Post(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title= db.Column(db.String(100), nullable=False)
    date_posted = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    content = db.Column(db.Text)
    screenshot = db.Column(db.String(100))
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

    def __repr__(self):
        return f"Post('{self.title}','{self.date_posted}')"