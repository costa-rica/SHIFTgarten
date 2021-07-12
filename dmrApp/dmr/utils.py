from datetime import datetime, date, time
from dmrApp import db
from dmrApp.models import Dmrs, Shifts, Employees, Restaurants, Employeeroles
from sqlalchemy import func
from flask import request
from flask_login import current_user


def restrictedResList(userPermDict):
    restaurantList=[]
    # print('userPermDict:::',list(userPermDict.values())[0])
    for i in list(userPermDict.values())[0]:
        restaurantList.append(Restaurants.query.filter_by(
            id=i).with_entities(Restaurants.name).first()[0])
            
    return restaurantList

def resExist(dmrDateObj, resId):
    dmrDatesCheckList=[i[0] for i in Dmrs.query.filter_by(
        restaurantId=resId).with_entities(Dmrs.dmrDate).all()]
    
    if dmrDateObj in dmrDatesCheckList:
        return True
    else:
        return False


def resIdInShipgarten(resId):
    if int(resId) in [3,4,5,6]:
        return True


def newDmrUtil(dmrDateObj, resId):
    if resIdInShipgarten(resId):
        restaurantGroupId=2
    else:
        restaurantGroupId=None
    #makes DMR for restaurant - always fires
    dmrNew=Dmrs(dmrDate=dmrDateObj, startCash=0, payout=0,sales=0,
        compSales=0,voidSales=0, cashDrop=0,expectedCash=0,restaurantId=resId,
        restaurantGroupId=restaurantGroupId, numHoursWorked=0,bartenderTipsPerHour=0,
        appTipsPerHour=0,creditCardTip=0,tip=0,
        cashTip=0, wages=0,user_id=current_user.id)
    db.session.add(dmrNew)
    db.session.commit()
    dmrId=db.session.query(Dmrs.id).filter_by(dmrDate=dmrDateObj,restaurantId=resId).first()[0]
    #make DMR for CBC if needed. this should fire almost every time
    if not db.session.query(Dmrs).filter_by(dmrDate=dmrDateObj,restaurantId=1).first():
        newCbcDmr=Dmrs(dmrDate=dmrDateObj, startCash=0, payout=0,sales=0,
            compSales=0,voidSales=0, cashDrop=0,expectedCash=0,restaurantId=1,
            restaurantGroupId=None, numHoursWorked=0,bartenderTipsPerHour=0,
            appTipsPerHour=0,creditCardTip=0,tip=0, wages=0,
            cashTip=0,infoFrom=str(dmrId),infoFromCount=1,user_id=current_user.id)
        db.session.add(newCbcDmr)
        db.session.commit()
    #make DMR for Shipgarten if needed
    if not db.session.query(Dmrs).filter_by(dmrDate=dmrDateObj,restaurantId=2).first():
        newShipgartenDmr=Dmrs(dmrDate=dmrDateObj, startCash=0, payout=0,sales=0,
            compSales=0,voidSales=0, cashDrop=0,expectedCash=0,restaurantId=2,
            restaurantGroupId=None, numHoursWorked=0,bartenderTipsPerHour=0,
            appTipsPerHour=0,creditCardTip=0,tip=0, wages=0,
            cashTip=0,infoFrom=str(dmrId),infoFromCount=1,user_id=current_user.id)
        db.session.add(newShipgartenDmr)
        db.session.commit()


def getDateTime(dmrDateStr, time1):
    if time1.hour <7:
        datetimevar1 = datetime(int(dmrDateStr[0:4]), int(dmrDateStr[5:7]), int(dmrDateStr[8:10])+1, time1.hour, time1.minute, 0, 0)
    else:
        datetimevar1 = datetime(int(dmrDateStr[0:4]), int(dmrDateStr[5:7]), int(dmrDateStr[8:10]), time1.hour, time1.minute, 0, 0)
    return datetimevar1
    

def floatify(stringList):
    floatList=[]
    if isinstance(stringList,dict):
        for h,i in stringList.items():
            floatList.append(float(i))
    elif isinstance(stringList,list):
        for h in stringList:
            floatList.append(float(i))
    return floatList


def flagDmrEntry(dmrDictList1):
    for h,i in dmrDictList1.items():
        if i==None or i=='':
            return h



def calcHours(resId, dmrDateObj):
    shiftData = Shifts.query.filter_by(restaurantId=resId, shiftDate=dmrDateObj)
    tipOutFullShiftIdList=[i.id for i in shiftData if i.employeerole.tipPercentage==1.0]
    tipOutHalfShiftIdList=[i.id for i in shiftData if i.employeerole.tipPercentage==0.5]
    # print('calcHours tip lsits:::',tipOutFullShiftIdList,tipOutHalfShiftIdList)
    fullTipOutHours=sum([Shifts.query.get(i).hoursWorked for i in tipOutFullShiftIdList])
    halfTipOutHours=sum([Shifts.query.get(i).hoursWorked for i in tipOutHalfShiftIdList])
    fullTipOutHours=0 if fullTipOutHours==None or fullTipOutHours=='' else fullTipOutHours
    halfTipOutHours=0 if halfTipOutHours==None or halfTipOutHours=='' else halfTipOutHours
    
    shiftDataCbc = Shifts.query.filter_by(shiftDate=dmrDateObj)
    tipOutFullShiftIdListCbc=[i.id for i in shiftDataCbc if i.employeerole.tipPercentage==1.0]
    tipOutHalfShiftIdListCbc=[i.id for i in shiftDataCbc if i.employeerole.tipPercentage==0.5]
    # print('calcHours tip lsits:::',tipOutFullShiftIdListCbc,tipOutHalfShiftIdListCbc)
    fullTipOutHoursCbc=sum([Shifts.query.get(i).hoursWorked for i in tipOutFullShiftIdListCbc])
    halfTipOutHoursCbc=sum([Shifts.query.get(i).hoursWorked for i in tipOutHalfShiftIdListCbc])
    fullTipOutHoursCbc=0 if fullTipOutHoursCbc==None or fullTipOutHoursCbc=='' else fullTipOutHoursCbc
    halfTipOutHoursCbc=0 if halfTipOutHoursCbc==None or halfTipOutHoursCbc=='' else halfTipOutHoursCbc
    
    if int(resId) in [3,4,5,6]:
        shiftDataG = Shifts.query.filter_by(restaurantGroupId=2, shiftDate=dmrDateObj)
        tipOutFullShiftIdListG=[i.id for i in shiftDataG if i.employeerole.tipPercentage==1.0]
        tipOutHalfShiftIdListG=[i.id for i in shiftDataG if i.employeerole.tipPercentage==0.5]
        fullTipOutHoursG=sum([Shifts.query.get(i).hoursWorked for i in tipOutFullShiftIdListG])
        halfTipOutHoursG=sum([Shifts.query.get(i).hoursWorked for i in tipOutHalfShiftIdListG])
        fullTipOutHoursG=0 if fullTipOutHoursG==None or fullTipOutHoursG=='' else fullTipOutHoursG
        halfTipOutHoursG=0 if halfTipOutHoursG==None or halfTipOutHoursG=='' else halfTipOutHoursG
        return (fullTipOutHours,halfTipOutHours,fullTipOutHoursCbc,halfTipOutHoursCbc,fullTipOutHoursG,halfTipOutHoursG)
    return (fullTipOutHours,halfTipOutHours,fullTipOutHoursCbc,halfTipOutHoursCbc)


def resAvgTips(resId, dmrDateObj, resHoursTuple):
    tip=db.session.query(Dmrs.tip,func.max(Dmrs.id)).filter_by(restaurantId=resId,dmrDate=dmrDateObj).first()[0]
    # print('resHoursTuple[0]::', resHoursTuple[0], 'resHoursTuple[1]::', resHoursTuple[1])
    if sum(list(resHoursTuple[0:2])) ==0:
        bartenderTipsPerHour=0
        appTipsPerHour=0
    elif resHoursTuple[0]>0 and resHoursTuple[1]==0:
        # print('resAvgTips, elif resHoursTuple[0]>0')
        bartenderTipsPerHour = tip / resHoursTuple[0]
        appTipsPerHour=0
    elif resHoursTuple[0]==0 and resHoursTuple[1]>0:
        # print('resAvgTips, elif resHoursTuple[0]==0')
        appTipsPerHour = tip / resHoursTuple[1]
        bartenderTipsPerHour=0
    else:
        # print('resAvgTips, else:')
        bartenderTipsPerHour = tip / (resHoursTuple[0] + resHoursTuple[1] * .5)
        appTipsPerHour = tip / (resHoursTuple[0] * 2 + resHoursTuple[1])
    # print('bartips:::',bartenderTipsPerHour,'apptips:::',appTipsPerHour)
    return(bartenderTipsPerHour,appTipsPerHour)
    

def groupAvgTips(dmrDateObj, hoursTuple):
    tipG=db.session.query(Dmrs.tip,func.max(Dmrs.id)).filter_by(
        dmrDate=dmrDateObj,restaurantId=2).first()[0]
    if tipG==0 or sum(hoursTuple[4:])==0:
        bartenderTipsPerHour=0
        appTipsPerHour=0
    elif hoursTuple[4]>0 and hoursTuple[5]==0:
        bartenderTipsPerHour = tipG / hoursTuple[4]
        appTipsPerHour=0
    elif hoursTuple[4]==0 and hoursTuple[5]>0:
        bartenderTipsPerHour=0
        appTipsPerHour = tipG / hoursTuple[5]
    else:
        bartenderTipsPerHour = tipG / (hoursTuple[4] + hoursTuple[5] * .5)
        appTipsPerHour = tipG / (hoursTuple[4] * 2 + hoursTuple[5])
    return(bartenderTipsPerHour,appTipsPerHour)



def cbcAvgTips(dmrDateObj, hoursTuple):
    tipCbc=db.session.query(Dmrs.tip,func.max(Dmrs.id)).filter_by(
        dmrDate=dmrDateObj,restaurantId=1).first()[0]
    if tipCbc==0 or sum(hoursTuple[2:4])==0:
        bartenderTipsPerHour=0
        appTipsPerHour=0
    elif hoursTuple[2]>0 and hoursTuple[3]==0:
        bartenderTipsPerHour = tipCbc / hoursTuple[2]
        appTipsPerHour=0
    elif hoursTuple[2]==0 and hoursTuple[3]>0:
        bartenderTipsPerHour=0
        appTipsPerHour = tipCbc / hoursTuple[3]
    else:
        bartenderTipsPerHour = tipCbc / (hoursTuple[2] + hoursTuple[3] * .5)
        appTipsPerHour = tipCbc / (hoursTuple[2] * 2 + hoursTuple[3])
    return(bartenderTipsPerHour,appTipsPerHour)


def updateGroupDmr(dmrDateObj, groupDmr, resIds):


    groupDmr.startCash=sum(db.session.query(
        Dmrs.startCash).filter(Dmrs.id==i).first()[0] for i in resIds)
    groupDmr.payout =sum(db.session.query(
        Dmrs.payout).filter(Dmrs.id==i).first()[0] for i in resIds)
        
    groupDmr.sales =sum(db.session.query(
        Dmrs.sales).filter(Dmrs.id==i).first()[0] for i in resIds)
    groupDmr.compSales =sum(db.session.query(
        Dmrs.compSales).filter(Dmrs.id==i).first()[0] for i in resIds)
    groupDmr.voidSales =sum(db.session.query(
        Dmrs.voidSales).filter(Dmrs.id==i).first()[0] for i in resIds)
    groupDmr.cashDrop =sum(db.session.query(
        Dmrs.cashDrop).filter(Dmrs.id==i).first()[0] for i in resIds)
    groupDmr.expectedCash =sum(db.session.query(
        Dmrs.expectedCash).filter(Dmrs.id==i).first()[0] for i in resIds)
    groupDmr.numHoursWorked =sum(db.session.query(
        Dmrs.numHoursWorked).filter(Dmrs.id==i).first()[0] for i in resIds)
    # bartenderTipsPerHour
    # appTipsPerHour
    groupDmr.creditCardTip=sum(db.session.query(
        Dmrs.creditCardTip).filter(Dmrs.id==i).first()[0] for i in resIds)
    
    print('query:::',[db.session.query(Dmrs.cashTip).filter(Dmrs.id==i).first()[0] for i in resIds])
    
    groupDmr.cashTip=sum(db.session.query(
        Dmrs.cashTip).filter(Dmrs.id==i).first()[0] for i in resIds)
    
    groupDmr.tip=groupDmr.creditCardTip+groupDmr.cashTip
    
    groupDmr.wages=sum(db.session.query(
        Dmrs.wages).filter(Dmrs.id==i).first()[0] for i in resIds)
    
    groupDmr.infoFrom=str(resIds)
    groupDmr.infoFromCount=len(resIds)
    groupDmr.user_id=current_user.id
    groupDmr.dmrTimeStamp=datetime.now() 
    db.session.commit()


def updateShifts(dmrDateObj,shifts,resAvgTipsTuple,groupAvgTipsTuple):
    # print('updateShift def - resAvgTipsTuple:::',resAvgTipsTuple,' groupAvgTipsTuple:::',groupAvgTipsTuple)
    for i in shifts:
        resFullTipRate=db.session.query(Dmrs.bartenderTipsPerHour,func.max(Dmrs.id)).filter_by(
            restaurantId=i.restaurant.id, dmrDate=dmrDateObj).first()[0]
        resHalfTipRate=db.session.query(Dmrs.appTipsPerHour,func.max(Dmrs.id)).filter_by(
            restaurantId=i.restaurant.id, dmrDate=dmrDateObj).first()[0]
        
        if i.employeerole.tipPercentage ==1.0:
            i.shiftTips=i.hoursWorked * resFullTipRate
            i.shiftTipsShipgarten=i.hoursWorked * groupAvgTipsTuple[0]
        elif i.employeerole.tipPercentage ==0.5:
            i.shiftTips= i.hoursWorked * resHalfTipRate
            i.shiftTipsShipgarten= i.hoursWorked * groupAvgTipsTuple[1]
        # i.wages=i.hoursWorked * i.employeerole.wage
        #commented out above with addition of wageCalcuated in dmr/routes/line254 -- if this works delete comments
        db.session.commit()


#standard process for any change to DMR or shift
def processDmrsShifts(resId, dmrDateObj):
    print('processDmrsShifts -START')
#calculate Hours
    hoursTuple=calcHours(resId, dmrDateObj)
    print('hoursTuple (fullTipRes,halfTipRes,fullTipCbc,halfCbc[,fullG,halfG]) :::',hoursTuple)
    
#Get resId DMR updated except for hours and tips
    dmrData=db.session.query(Dmrs,func.max(Dmrs.id)).filter_by(dmrDate=dmrDateObj, restaurantId=resId).first()[0]

#update CBC DMR
    resIds=db.session.query(func.max(Dmrs.id)).filter(
        Dmrs.dmrDate==dmrDateObj,Dmrs.restaurantId!=1,Dmrs.restaurantId!=2).group_by(
        Dmrs.restaurantId).all()
    resIds=[i[0] for i in resIds]
    
    cbcDmr=db.session.query(Dmrs,func.max(Dmrs.id)).filter_by(
        dmrDate=dmrDateObj,restaurantId=1).first()[0]
    print('dmrDateObj, cbcDmr, resIds::::',dmrDateObj, cbcDmr, resIds)
    updateGroupDmr(dmrDateObj, cbcDmr, resIds)
#**end CBC DMR update
    dmrDataCbc=db.session.query(Dmrs,func.max(Dmrs.id)).filter_by(dmrDate=dmrDateObj, restaurantId=1).first()[0]

#calculate resAvgTips
    resAvgTipsTuple=resAvgTips(resId, dmrDateObj, hoursTuple)
    print('resAvgTipsTuple (bartenderTipsPerHour, appTipsPerHour):::',resAvgTipsTuple)
    print('resAvgTipsTuple goes straight to dmr')
#update DMR hours and avg tips
    dmrData.numHoursWorked=sum(list(hoursTuple[0:2]))
    dmrData.bartenderTipsPerHour=resAvgTipsTuple[0]
    dmrData.appTipsPerHour=resAvgTipsTuple[1]
    dmrData.user_id=current_user.id
    dmrData.dmrTimeStamp=datetime.now()
    # print('resAvgTipsTuple[1]:::',resAvgTipsTuple[1])
    db.session.commit()
    #apptips still 0 here
    
# calculate cbcAvgTips
    cbcAvgTipsTuple=cbcAvgTips(dmrDateObj, hoursTuple)
    print('cbcAvgTips (bartenderTipsPerHour, appTipsPerHour):::', cbcAvgTipsTuple)
# update cbcDMR hours and avg tips
    dmrDataCbc.numHoursWorked=sum(list(hoursTuple[2:4]))
    dmrDataCbc.bartenderTipsPerHour=cbcAvgTipsTuple[0]
    dmrDataCbc.appTipsPerHour=cbcAvgTipsTuple[1]
    db.session.commit()
    
# calculate groupAvgTips
    groupAvgTipsTuple=[0,0]
    if resIdInShipgarten(resId):
#**update shipgarten DMR
        resIds=db.session.query(func.max(Dmrs.id)).filter(
        Dmrs.dmrDate==dmrDateObj,Dmrs.restaurantGroupId==2).group_by(
        Dmrs.restaurantId).all()
        resIds=[i[0] for i in resIds]
    
        cbcDmr=db.session.query(Dmrs,func.max(Dmrs.id)).filter_by(
            dmrDate=dmrDateObj,restaurantId=2).first()[0]

        updateGroupDmr(dmrDateObj, cbcDmr, resIds)
        
        
        
        groupAvgTipsTuple=groupAvgTips(dmrDateObj, hoursTuple)
        dmrGroupDataAdd=db.session.query(Dmrs,func.max(Dmrs.id)).filter_by(dmrDate=dmrDateObj, restaurantId=2).first()[0]

    # update Group DMR
        dmrGroupDataAdd.numHoursWorked=sum(list(hoursTuple[4:]))
        dmrGroupDataAdd.bartenderTipsPerHour=groupAvgTipsTuple[0]
        dmrGroupDataAdd.appTipsPerHour=groupAvgTipsTuple[1]

        db.session.commit()

    # update Shifts
        shiftDataAdd=Shifts.query.filter_by(shiftDate=dmrDateObj,restaurantGroupId=2)
        updateShifts(dmrDateObj,shiftDataAdd,resAvgTipsTuple,groupAvgTipsTuple)
        
    #After wages get calculated for each shift, collect the shift wages, add them into group DMR
        shiftDataAdd1=Shifts.query.filter_by(shiftDate=dmrDateObj,restaurantId=resId)
        shiftDataAdd2=Shifts.query.filter_by(shiftDate=dmrDateObj,restaurantGroupId=2)
        shiftDataAdd3=Shifts.query.filter_by(shiftDate=dmrDateObj)
        dmrData.wages = sum([i.wages for i in shiftDataAdd1])
        dmrGroupDataAdd.wages = sum([i.wages for i in shiftDataAdd2])
        dmrDataCbc.wages = sum([i.wages for i in shiftDataAdd3])
        
    else:
        shiftDataAdd=Shifts.query.filter_by(shiftDate=dmrDateObj,restaurantId=resId)
        print('shiftDataAdd:::',shiftDataAdd.with_entities(Shifts.shiftTips).all())
        
        updateShifts(dmrDateObj,shiftDataAdd,resAvgTipsTuple,groupAvgTipsTuple)
        
        #delete two lines below after checking
        shiftDataAdd=Shifts.query.filter_by(shiftDate=dmrDateObj,restaurantId=resId)
        print('shiftDataAdd - after update:::',shiftDataAdd.with_entities(Shifts.shiftTips).all())
        
    #After wages get calculated for each shift, collect the shift wages, add them into group DMR
        shiftDataAdd1=Shifts.query.filter_by(shiftDate=dmrDateObj,restaurantId=resId)
        shiftDataAdd3=Shifts.query.filter_by(shiftDate=dmrDateObj)
        dmrData.wages = sum([i.wages for i in shiftDataAdd1])
        dmrDataCbc.wages = sum([i.wages for i in shiftDataAdd3])
    db.session.commit()
    print('processDmrsShifts -END')
    # return print('DMR and shifts updated; resId::',resId,' dmrDateObj::',dmrDateObj,' hoursTuple(resBar,resAppren,cbcBar...)::',hoursTuple)


def existingShiftFlag(empId,shiftdate,newStartTime, newEndTime):
    empDayShifts=db.session.query(Shifts).filter_by(empId=empId, shiftDate=shiftdate)
    startShiftsFlagged=empDayShifts.filter(Shifts.timeOff>=newStartTime)
    endShiftsFlagged=[i.id for i in empDayShifts.filter(Shifts.timeStart<=newEndTime).with_entities(Shifts.id)]
    for i in startShiftsFlagged:
        if i.id in endShiftsFlagged:
            return True
        else:
            return False

def empIdNameRoleListUtil(employeeRoleData):
    employeeRoleEmpIdList=[i[0] for i in employeeRoleData.with_entities(Employeeroles.empId).distinct().all()]
    #employeeRoleEmpIdList unique list of all empID's
    
    employeeDataFiltered=Employees.query.filter(Employees.id.in_(employeeRoleEmpIdList) & Employees.deactivatedBy==None).all()
    empIdListFiltered=[i.id for i in employeeDataFiltered]
    #empId's filtered
    
# #     use employeeIdList to get roles
    employeeRoleList=Employeeroles.query.filter(Employeeroles.empId.in_(empIdListFiltered)).with_entities(
        Employeeroles.role).distinct().all()
    employeeRoleList=[i[0] for i in employeeRoleList]
    
# #     Get employee Names list
    empNameList=Employees.query.filter(Employees.id.in_(empIdListFiltered)).with_entities(Employees.name).all()
    empNameList=[i[0] for i in empNameList]
    # returns (filtered empID list, unique role list of filtered, name list filtered) *filter is required restaurants and no inactive employees
    return (empIdListFiltered,employeeRoleList,empNameList)