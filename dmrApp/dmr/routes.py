from flask import Blueprint
from flask import render_template, url_for, redirect, flash, request, abort, session,\
    Response
from dmrApp import db, bcrypt, mail
from dmrApp.models import Dmrs, Employees, Employeeroles, Post, Restaurants, Shifts, User
from dmrApp.dmr.forms import DashboardForm, DmrForm, ShiftForm
from flask_login import login_user, current_user, logout_user, login_required
import secrets
import os
from PIL import Image
from datetime import datetime, date, time
from sqlalchemy import func
import pandas as pd
import io
from wsgiref.util import FileWrapper
import xlsxwriter
from flask_mail import Message
from dmrApp.dmr.utils import resExist, resIdInShipgarten, newDmrUtil, \
    getDateTime, floatify, flagDmrEntry, processDmrsShifts, existingShiftFlag, \
    restrictedResList, empIdNameRoleListUtil
from dmrApp.main.utils import buildUserPermDict

dmr = Blueprint('dmr', __name__)


@dmr.route('/dashboard', methods=["GET","POST"])
@login_required
def dashboard():
    form=DashboardForm()
    darkMode=User.query.get(current_user.id).theme
    
    if request.method == "POST":
        formDict = request.form.to_dict()
        session['dmrRestaurant'] = form.restaurant.data.name        
        parseDateString=[int(x) for x in request.form['dmrDate'].split('-')]
        dmrDateObj=date(parseDateString[0],parseDateString[1],parseDateString[2])
        resId=form.restaurant.data.id
        
    #Make new DMR
        if formDict.get('newDmr') and resId not in [1,2]:
            #Checking if the restaurant-date combination exists
            if resExist(dmrDateObj,form.restaurant.data.id):
                flash(f'DMR for that date at {form.restaurant.name} already exists', 'warning')
                return render_template('dashboard.html', title='Dashboard', form=form)

            #Add necessary DMRs
            newDmrUtil(dmrDateObj, resId)

            return redirect(url_for('dmr.dmrPage', resId=resId,dmrRestaurant=session['dmrRestaurant'],
                                    dmrDateObj=dmrDateObj))

    #View existing DMR
        else:
        # Check if DMR exits
            if not resExist(dmrDateObj,resId):
                if resId in [1,2]:#<--1 'CBC Restaurants', 2'Shipgarten'
                    flash(f'No DMRs for any restaurants on the selected date', 'warning')
                else:
                    flash(f"No DMR for {session['dmrRestaurant']} on the selected date", 'warning')
                return render_template('dashboard.html', title='Dashboard', form=form)

            session['resGroup']=True if form.restaurant.data.id in [1,2] else False
            return redirect(url_for('dmr.dmrPage', resId=form.restaurant.data.id, 
                dmrRestaurant=session['dmrRestaurant'], dmrDateObj=str(dmrDateObj)))

    return render_template('dashboard.html', legend='Dashboard', form=form,
        darkMode=darkMode)



@dmr.route('/dmr/<dmrRestaurant>/<dmrDateObj>', methods = ["GET", "POST"])
@login_required
def dmrPage(dmrRestaurant, dmrDateObj):
    form=DmrForm()
    shiftForm=ShiftForm()
    # dmrFormFlag=True
    resId=request.args['resId']
    employeeRoleData=Employeeroles.query
    
    if int(resId) in [3,4,5,6]:
        restaurantGroupId=2
        dmrIdSg = Dmrs.query.filter(Dmrs.restaurantId==2,Dmrs.dmrDate==dmrDateObj).with_entities(
        Dmrs.id).order_by(Dmrs.id.desc()).first()[0]
        dmrDataSg = Dmrs.query.get_or_404(dmrIdSg)
        
        employeeRoleData=employeeRoleData.filter((Employeeroles.restaurantId>=3) & (Employeeroles.restaurantId<=6))
    else:
        employeeRoleData=employeeRoleData.filter(Employeeroles.restaurantId==resId)
        restaurantGroupId=None

    dmrUtilLists=empIdNameRoleListUtil(employeeRoleData)
    #dmrUtilLists returns (filtered empID list, unique role list of filtered, name list filtered) *filter is required restaurants and no inactive employees
    
# Add shift form ---only allow empNames associated with restaurant, if shipgarten, then all shipgarten restaurants
    empNames = dmrUtilLists[2]
    roles=dmrUtilLists[1]



    if int(resId) in [1,2]:
        dmrHtmlFlag=None
    else:
        dmrHtmlFlag=True
    
    
    dmrDateObj = date(int(dmrDateObj[0:4]), int(dmrDateObj[5:7]), int(dmrDateObj[8:10])) #dmrDateObj 2020-11-23 <class 'datetime.date'>
    
    dmrId = Dmrs.query.filter_by(restaurantId=resId, dmrDate=dmrDateObj).with_entities(
        Dmrs.id).order_by(Dmrs.id.desc()).first()[0]
    dmrData = Dmrs.query.get_or_404(dmrId)
    
    #  Filling in data in DMR top part populated by query
    form.startCash.data = 0 if dmrData.startCash == None else "{:.2f}".format(dmrData.startCash)
    form.payout.data = 0 if dmrData.payout == None else "{:.2f}".format(dmrData.payout)
    form.sales.data = 0 if dmrData.sales == None else "{:.2f}".format(dmrData.sales)
    form.compSales.data = 0 if dmrData.compSales == None else "{:.2f}".format(dmrData.compSales)
    form.voidSales.data = 0 if dmrData.voidSales == None else "{:.2f}".format(dmrData.voidSales)
    form.cashDrop.data = 0 if dmrData.cashDrop == None else "{:.2f}".format(dmrData.cashDrop)
    form.expectedCash.data = 0 if dmrData.expectedCash == None else "{:.2f}".format(dmrData.expectedCash)
    form.numHoursWorked.data = 0 if dmrData.numHoursWorked == None else "{:.2f}".format(dmrData.numHoursWorked)
    
    if restaurantGroupId:
        form.bartenderTipsPerHour.data = None if dmrDataSg.bartenderTipsPerHour == None else "{:.3f}".format(
            dmrDataSg.bartenderTipsPerHour)
        form.appTipsPerHour.data = None if dmrDataSg.appTipsPerHour == None else "{:.3f}".format(
            dmrDataSg.appTipsPerHour)
    else:
        form.bartenderTipsPerHour.data = None if dmrData.bartenderTipsPerHour == None else "{:.3f}".format(
        dmrData.bartenderTipsPerHour)
        form.appTipsPerHour.data = None if dmrData.appTipsPerHour == None else "{:.3f}".format(
        dmrData.appTipsPerHour)
    
    form.creditCardTip.data = 0 if dmrData.creditCardTip == None else "{:.2f}".format(dmrData.creditCardTip)
    form.cashTip.data = 0 if dmrData.cashTip == None else "{:.2f}".format(dmrData.cashTip)
    form.tip.data = 0 if dmrData.tip == None else "{:.2f}".format(dmrData.tip)
    tip = dmrData.tip
    form.wages.data = 0 if dmrData.wages == None else "{:.2f}".format(dmrData.wages)
    
# Populate existing shift data
    if resId=='1':
        shiftData = Shifts.query.filter_by(shiftDate=dmrDateObj)
    elif resId=='2':
        shiftData = Shifts.query.filter_by(shiftDate=dmrDateObj, restaurantGroupId=2)
    else:
        shiftData = Shifts.query.filter_by(shiftDate=dmrDateObj, restaurantId=resId)
    
    shiftNamesList=[i.employee.name for i in shiftData]
    shiftRolesList = [Employeeroles.query.filter_by(id=i.employeeRolesId).with_entities(
        Employeeroles.role).first() for i in shiftData.all()]
    shiftResList = [i.restaurant.name for i in shiftData]
    shiftSchedTime= shiftData.with_entities(Shifts.schedTime).all()
    shiftSchedTimeList=[i[0] for i in shiftSchedTime]
    shiftTimeStart=shiftData.with_entities(Shifts.timeStart).all()
    shiftTimeStartList = [i[0].strftime("%I:%M %p") for i in shiftTimeStart]
    shiftTimeOff=shiftData.with_entities(Shifts.timeOff).all()
    shiftTimeOffList = [i[0].strftime("%I:%M %p") for i in shiftTimeOff]
    shiftHoursWorked=shiftData.with_entities(Shifts.hoursWorked).all()
    shiftHoursWorkedList = ["{:.2f}".format(i[0]) for i in shiftHoursWorked]
    
    shiftTipList=[]
    for i in shiftData:
        if i.restaurantId in [2,3,4,5,6,]:
            shiftTipList.append("{:.2f}".format(i.shiftTipsShipgarten))
            # shiftTipList.append(i.shiftTipsShipgarten)
        else:
            shiftTipList.append("{:.2f}".format(i.shiftTips))
            # shiftTipList.append(i.shiftTips)

    print('error none for shiftWagesList***')
    # print(


    shiftWagesList=["{:.2f}".format(i.wages) for i in shiftData]    
    # shiftWagesList=[i.wages for i in shiftData]    
    shiftCount = len(shiftData.all())
    shiftWagePlusTipList=["{:.2f}".format(float(h)+float(i)) for h,i in zip(shiftTipList,shiftWagesList)]
    # shiftWagePlusTipList=[float(h)+float(i) for h,i in zip(shiftTipList,shiftWagesList)]

# This list is used for the delete buttons
    shiftIdList=[i.id for i in shiftData.all()]




    if request.method == "POST":
        formDict = request.form.to_dict()                   
    #DMR Form validation
        startCash =request.form.get('startCash')
        payout =request.form.get('payout')
        sales =request.form.get('sales')
        compSales = request.form.get('compSales')
        voidSales = request.form.get('voidSales')
        cashDrop = request.form.get('cashDrop')
        expectedCash = request.form.get('expectedCash')
        
        numHoursWorked = request.form.get('numHoursWorked')
        bartenderTipsPerHour = request.form.get('bartenderTipsPerHour')
        appTipsPerHour = request.form.get('appTipsPerHour')
        
        creditCardTip=request.form.get('creditCardTip')
        cashTip=request.form.get('cashTip')
        tip=float(creditCardTip)+float(cashTip)
        
        dmrDictList1={'startCash':startCash,'payout':payout,'sales':sales,
            'compSales':compSales,'voidSales':voidSales,'cashDrop':cashDrop,
            'expectedCash':expectedCash,'numHoursWorked':numHoursWorked,
            'bartenderTipsPerHour':bartenderTipsPerHour,'appTipsPerHour':appTipsPerHour,
            'creditCardTip':creditCardTip,'cashTip':cashTip}

        if flagDmrEntry(dmrDictList1):
            flash(f'{flagDmrEntry(dmrDictList1)} cannot be empty (zero or positive number)', 'warning')
            return redirect(url_for('dmr.dmrPage', resId=resId, dmrDateObj=dmrDateObj,
                            dmrRestaurant=dmrRestaurant))

    #***End DMR form Validation
        
    #Update DMR
        if formDict.get('dmrSubmit'):
            dmrItems=floatify(dmrDictList1)
            
        #Add DMR - no hours no tips
            addDmr = Dmrs(dmrDate=dmrDateObj,startCash=dmrItems[0],payout=dmrItems[1],
                sales=dmrItems[2], compSales=dmrItems[3],voidSales=dmrItems[4], cashDrop=dmrItems[5],
                expectedCash=dmrItems[6],numHoursWorked=dmrItems[7],
                bartenderTipsPerHour=dmrItems[8],appTipsPerHour=dmrItems[9],
                creditCardTip=dmrItems[10],cashTip=dmrItems[11],tip=tip,wages=0,restaurantId=resId,
                user_id=current_user.id,infoFrom=str(db.session.query(func.max(Dmrs.id)).filter_by(
                restaurantId=resId).first()[0]),
                infoFromCount=1, restaurantGroupId=restaurantGroupId)
            db.session.add(addDmr)
            db.session.commit()
                        
#***START: Standard process for change in shift or DMR after changes made
            processDmrsShifts(resId, dmrDateObj)
#***END: Standard process for change in shift or DMR after changes made
            return redirect(url_for('dmr.dmrPage', resId=resId, dmrDateObj=dmrDateObj,
                dmrRestaurant=dmrRestaurant))


# ***Add Shift***
        elif formDict.get('shiftSubmit'):
            newRole=request.form.get('role')
        #Validation role and name filled out for new shift
            if newRole == '' or shiftForm.name.data =='' or shiftForm.name.data ==None or\
                    shiftForm.timeOff.data == None or shiftForm.timeStart.data==None:
                flash(f'Shift form missing data', 'warning')
                return redirect(url_for('dmr.dmrPage', resId=resId, dmrDateObj=dmrDateObj,
                                    dmrRestaurant=dmrRestaurant))
            
            empId = Employees.query.filter_by(name=shiftForm.name.data).with_entities(Employees.id).first()[0]

        #check employee has role
            addShiftEmpRolesList=[i[0] for i in db.session.query(Employeeroles).filter_by(
                empId=empId).with_entities(Employeeroles.role).all()]
            
            if newRole not in addShiftEmpRolesList:
                flash(f'Role not associated with employee. Select another role.', 'warning')
                return redirect(url_for('dmr.dmrPage', resId=resId, dmrDateObj=dmrDateObj,
                                    dmrRestaurant=dmrRestaurant))            
            
            print('getDateTime Pars:::',str(dmrDateObj), shiftForm.timeStart.data)
            
            
            empRoleId=db.session.query(Employeeroles.id).filter(
                Employeeroles.empId==empId,Employeeroles.role==newRole).first()[0]
            timeStartVar = getDateTime(str(dmrDateObj), shiftForm.timeStart.data)  # returns datetime.datetime obj
            timeOffVar = getDateTime(str(dmrDateObj), shiftForm.timeOff.data)
            hoursWorked = (timeOffVar - timeStartVar).total_seconds() / 3600  # float obj
            wageCalculated = Employeeroles.query.filter_by(empId=empId,role=newRole).with_entities(
                Employeeroles.wage).first()[0] * hoursWorked
            
#check if employee is already working another shift on that day and time
            if existingShiftFlag(empId,dmrDateObj,timeStartVar, timeOffVar):
                flash(f"""{shiftForm.name.data} (Employee ID: {empId}) already assigned to shift overlapping these times.
                Check employee name and/or time.""", 'warning')
                return redirect(url_for('dmr.dmrPage', resId=resId, dmrDateObj=dmrDateObj,
                                    dmrRestaurant=dmrRestaurant))                  
            # print('timeStartVar:::',timeStartVar,type(timeStartVar))
            # print('timeOffVar:::',timeOffVar,type(timeOffVar))
            

            addShift=Shifts(name=shiftForm.name.data, shiftDate=dmrDateObj,schedTime=shiftForm.schedTime.data,
                            timeStart=timeStartVar, timeOff=timeOffVar,hoursWorked=hoursWorked,
                            shiftTips=0, shiftTipsShipgarten=0, wages=wageCalculated, empId=empId,
                            restaurantId=resId,restaurantGroupId=restaurantGroupId,
                            userId=current_user.id, employeeRolesId=empRoleId)
            
            db.session.add(addShift)
            db.session.commit()
            
        #Add DMR - no hours no tips
            addDmr = Dmrs(dmrDate=dmrDateObj,startCash=startCash,payout=payout,
                sales=sales, compSales=compSales,voidSales=voidSales, cashDrop=cashDrop,
                expectedCash=expectedCash,numHoursWorked=numHoursWorked,
                bartenderTipsPerHour=bartenderTipsPerHour,appTipsPerHour=appTipsPerHour,
                creditCardTip=creditCardTip,cashTip=cashTip,tip=tip,wages=0,restaurantId=resId,
                user_id=current_user.id,infoFrom=db.session.query(func.max(Dmrs.id)).filter_by(
                restaurantId=resId).first()[0],
                infoFromCount=1, restaurantGroupId=restaurantGroupId)
            db.session.add(addDmr)
            db.session.commit()
            
#***START: Standard process for change in shift or DMR after changes made
            processDmrsShifts(resId, dmrDateObj)
#***END: Standard process for change in shift or DMR after changes made
            return redirect(url_for('dmr.dmrPage', resId=resId, dmrDateObj=dmrDateObj,
                            dmrRestaurant=dmrRestaurant))

# ***Delete shift *** this is basically firing as if its an else: because request.form is always true
        elif formDict.get('delete shift'):            
            Shifts.query.filter_by(id=request.form["delete shift"]).delete()
            db.session.commit()
        #Add DMR - no hours no tips
            addDmr = Dmrs(dmrDate=dmrDateObj,startCash=startCash,payout=payout,
                sales=sales, compSales=compSales,voidSales=voidSales, cashDrop=cashDrop,
                expectedCash=expectedCash,numHoursWorked=numHoursWorked,
                bartenderTipsPerHour=bartenderTipsPerHour,appTipsPerHour=appTipsPerHour,
                creditCardTip=creditCardTip,cashTip=cashTip,tip=tip,wages=0, restaurantId=resId,
                user_id=current_user.id,infoFrom=db.session.query(func.max(Dmrs.id)).filter_by(
                restaurantId=resId).first()[0]+1,
                infoFromCount=1, restaurantGroupId=restaurantGroupId)
            db.session.add(addDmr)
            db.session.commit()

#***START: Standard process for change in shift or DMR after changes made
            processDmrsShifts(resId, dmrDateObj)
#***END: Standard process for change in shift or DMR after changes made

            return redirect(url_for('dmr.dmrPage', resId=resId, dmrDateObj=dmrDateObj,
                                    dmrRestaurant=dmrRestaurant, form=form, legend='daily manager report',
                                               dateObjForDmr=str(dmrDateObj), shiftRolesList=shiftRolesList,
                                               shiftCount=shiftCount, shiftForm=shiftForm, empNames=empNames,
                                               shiftSchedTimeList=shiftSchedTimeList, roles=roles,
                                               shiftTimeStartList=shiftTimeStartList, shiftTimeOffList=shiftTimeOffList,
                                               shiftNamesList=shiftNamesList, shiftIdList=shiftIdList,
                                               shiftHoursWorkedList=shiftHoursWorkedList, shiftTipList=shiftTipList,
                                               shiftWagesList=shiftWagesList, shiftWagePlusTipList=shiftWagePlusTipList,
                                               shiftResList=shiftResList))


    return render_template('dmr.html', dmrRestaurant=dmrRestaurant,form=form, legend='Daily Manager Report',
                           dmrHtmlFlag=dmrHtmlFlag, restaurantGroupId=restaurantGroupId,
                           dateObjForDmr=str(dmrDateObj),shiftRolesList=shiftRolesList,
                           shiftCount=shiftCount, shiftForm=shiftForm, empNames=empNames,
                           shiftSchedTimeList=shiftSchedTimeList, roles=roles,
                           shiftTimeStartList=shiftTimeStartList,shiftTimeOffList=shiftTimeOffList,
                           shiftNamesList=shiftNamesList, shiftIdList=shiftIdList,
                           shiftHoursWorkedList=shiftHoursWorkedList, shiftTipList=shiftTipList,
                           shiftWagesList=shiftWagesList, shiftWagePlusTipList=shiftWagePlusTipList,
                                               shiftResList=shiftResList)

