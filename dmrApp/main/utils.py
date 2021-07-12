from dmrApp import db
from dmrApp.models import Dmrs, Employees, Employeeroles, Post, \
    Restaurants, Shifts, User, Standardwages
from datetime import datetime, date, time
from datetime import timedelta
import datetime
from sqlalchemy import func
import pandas as pd
import xlsxwriter
import numpy as np
from flask_login import current_user
from dmrApp.dmr.utils import restrictedResList
from flask import render_template, url_for, redirect, flash
import numbers


def shiftDataLists(shiftData):
    shiftNamesList = [i.employee.name for i in shiftData]
    shiftRestaurantList = [i.restaurant.name for i in shiftData.all()]
    
    shiftRolesList = [Employeeroles.query.filter_by(
        id=i.employeeRolesId).with_entities(Employeeroles.role).first()[0] for i in shiftData]

    shiftSchedTimeList=[i.schedTime for i in shiftData]
    shiftTimeStartList = [i.timeStart.strftime("%I:%M %p") for i in shiftData]
    shiftTimeOffList = [i.timeOff.strftime("%I:%M %p") for i in shiftData]
    shiftHoursWorkedList = [i.hoursWorked for i in shiftData]
    shiftDateList=[i.shiftDate for i in shiftData]
    
    shiftTipList = []
    for i in shiftData:
        shiftTip=i.shiftTipsShipgarten if i.restaurant.id in [3,4,5,6] else i.shiftTips
        shiftTipList.append(shiftTip)
    shiftWagesList = [i.wages for i in shiftData]
    shiftTipWageList=[]
    for h,i in zip(shiftTipList,shiftWagesList):
        sum=float(h)+float(i)
        shiftTipWageList.append(sum)
    
    #Get hourly rate from DMR based on bartender or apprentice
    shiftTipsPerHourList=[]
    for i in shiftData:
        if i.employeerole.role == 'Bartender':
            shiftTipsPerHour=db.session.query(func.max(Dmrs.id),Dmrs.bartenderTipsPerHour,Dmrs.appTipsPerHour
                              ).filter_by(restaurantId=i.restaurant.id,dmrDate=i.shiftDate).first()[1]
        elif i.employeerole.role == 'Apprentice':
            shiftTipsPerHour=db.session.query(func.max(Dmrs.id),Dmrs.bartenderTipsPerHour,Dmrs.appTipsPerHour
                              ).filter_by(restaurantId=i.restaurant.id,dmrDate=i.shiftDate).first()[2]
        shiftTipsPerHourList.append(shiftTipsPerHour)
    
    #combine employee name and role
    empNameRoleList=[i+"-"+j for i,j in zip(shiftNamesList,shiftRolesList)]
        
    return (shiftDateList, empNameRoleList,shiftRestaurantList,
        shiftSchedTimeList,shiftTimeStartList,shiftTimeOffList,shiftHoursWorkedList,
        shiftTipList, shiftWagesList,shiftTipWageList,shiftTipsPerHourList)


def shiftDataLists2(shiftData):
    shiftNamesList = [i.employee.name for i in shiftData]
    shiftRestaurantList = [i.restaurant.name for i in shiftData.all()]
    
    shiftRolesList = [Employeeroles.query.filter_by(
        id=i.employeeRolesId).with_entities(Employeeroles.role).first()[0] for i in shiftData]

    shiftSchedTimeList=[i.schedTime for i in shiftData]
    shiftTimeStartList = [i.timeStart.strftime("%I:%M %p") for i in shiftData]
    shiftTimeOffList = [i.timeOff.strftime("%I:%M %p") for i in shiftData]
    shiftHoursWorkedList = [i.hoursWorked for i in shiftData]
    shiftDateList=[i.shiftDate for i in shiftData]
    
    shiftTipList = []
    for i in shiftData:
        shiftTip=i.shiftTipsShipgarten if i.restaurant.id in [3,4,5,6] else i.shiftTips
        shiftTipList.append(shiftTip)
    shiftWagesList = [i.wages for i in shiftData]
    shiftTipWageList=[]
    for h,i in zip(shiftTipList,shiftWagesList):
        sum=float(h)+float(i)
        shiftTipWageList.append(sum)
    
    #Get hourly rate from DMR based on bartender or apprentice
    shiftTipsPerHourList=[]
    for i in shiftData:
        if i.employeerole.role == 'Bartender':
            shiftTipsPerHour=db.session.query(func.max(Dmrs.id),Dmrs.bartenderTipsPerHour,Dmrs.appTipsPerHour
                              ).filter_by(restaurantId=i.restaurant.id,dmrDate=i.shiftDate).first()[1]
        elif i.employeerole.role == 'Apprentice':
            shiftTipsPerHour=db.session.query(func.max(Dmrs.id),Dmrs.bartenderTipsPerHour,Dmrs.appTipsPerHour
                              ).filter_by(restaurantId=i.restaurant.id,dmrDate=i.shiftDate).first()[2]
        shiftTipsPerHourList.append(shiftTipsPerHour)
    
    #combine employee name and role
    # empNameRoleList=[i+"-"+j for i,j in zip(shiftNamesList,shiftRolesList)]
        
    return (shiftDateList,shiftNamesList, shiftRestaurantList,shiftRolesList,
        shiftSchedTimeList,shiftTimeStartList,shiftTimeOffList,shiftHoursWorkedList,
        shiftTipList, shiftWagesList,shiftTipWageList,shiftTipsPerHourList)




def shiftDataReport(dateFrom,dateTo, resId, colNamesShifts):
    shiftData = Shifts.query
    if dateFrom:
        shiftData = shiftData.filter(Shifts.shiftDate>=dateFrom)
    if dateTo:
        shiftData = shiftData.filter(Shifts.shiftDate<=dateTo)
    if resId:
        shiftData = shiftData.filter(Shifts.restaurantId==resId)

    shiftReportColumns = list(shiftDataLists(shiftData))

    dfShifts = pd.DataFrame(list(zip(shiftReportColumns[0],shiftReportColumns[1],
        shiftReportColumns[2],shiftReportColumns[3],shiftReportColumns[4],shiftReportColumns[5],
        shiftReportColumns[6],shiftReportColumns[7],shiftReportColumns[8],shiftReportColumns[9],
        shiftReportColumns[10])), columns=colNamesShifts)
    return dfShifts


def shiftDataPayStubReport(dateFrom,dateTo, resId, colNamesShifts):
    shiftData = Shifts.query
    if dateFrom:
        shiftData = shiftData.filter(Shifts.shiftDate>=dateFrom)
    if dateTo:
        shiftData = shiftData.filter(Shifts.shiftDate<=dateTo)
    if resId:
        shiftData = shiftData.filter(Shifts.restaurantId==resId)

    uniqueEmpIdList = shiftData.with_entities(Shifts.empId).distinct().all()
    dfList=[]
    employeeCharMax=10
    for i in uniqueEmpIdList:
        shiftReportColumns = list(shiftDataLists(shiftData.filter(Shifts.empId==i[0])))
        if len(max(shiftReportColumns[1], key = len))>employeeCharMax:
            employeeCharMax =len(max(shiftReportColumns[1], key = len))
        dfShifts = pd.DataFrame(list(zip(shiftReportColumns[0],shiftReportColumns[1],
            shiftReportColumns[2],shiftReportColumns[3],shiftReportColumns[4],shiftReportColumns[5],
            shiftReportColumns[6],shiftReportColumns[7],shiftReportColumns[8],shiftReportColumns[9],
            shiftReportColumns[10])), columns=colNamesShifts)
        dfList.append(dfShifts)
    return (dfList, employeeCharMax)


def dmrDataReport(dateFrom,dateTo,resId, colNamesDmrs):
    dmrDataReport= db.session.query(Dmrs, func.max(Dmrs.id)).group_by(
        Dmrs.restaurantId, Dmrs.dmrDate)
    if dateFrom:
        dmrDataReport=dmrDataReport.filter(Dmrs.dmrDate>=dateFrom)
    if dateTo:
        dmrDataReport=dmrDataReport.filter(Dmrs.dmrDate<=dateTo)
    if resId:
        dmrDataReport=dmrDataReport.filter(Dmrs.restaurantId==resId)
            
    dmrDateList = [i[0].dmrDate for i in dmrDataReport]
    restaurantList = [i[0].restaurant.name for i in dmrDataReport]
    startCashList = ["{:.2f}".format(i[0].startCash) for i in dmrDataReport]
    payoutList = ["{:.2f}".format(i[0].payout) for i in dmrDataReport]
    salesList = ["{:.2f}".format(i[0].sales) for i in dmrDataReport]
    compSalesList = ["{:.2f}".format(i[0].compSales) for i in dmrDataReport]
    voidSalesList = ["{:.2f}".format(i[0].voidSales) for i in dmrDataReport]
    cashDropList = ["{:.2f}".format(i[0].cashDrop) for i in dmrDataReport]
    expectedCashList = ["{:.2f}".format(i[0].expectedCash) for i in dmrDataReport]
    numHoursWorkedList = ["{:.2f}".format(i[0].numHoursWorked) for i in dmrDataReport]
    bartenderTipsPerHourList = ["{:.2f}".format(i[0].bartenderTipsPerHour) for i in dmrDataReport]
    appTipsPerHourList = ["{:.2f}".format(i[0].appTipsPerHour) for i in dmrDataReport]
    creditCardTipList = ["{:.2f}".format(i[0].creditCardTip) for i in dmrDataReport]
    cashTipList = ["{:.2f}".format(i[0].cashTip) for i in dmrDataReport]
    tip = ["{:.2f}".format(i[0].tip) for i in dmrDataReport]
    wage = ["{:.2f}".format(i[0].wages) for i in dmrDataReport]

    dfDmrs = pd.DataFrame(list(zip(dmrDateList, restaurantList, 
        startCashList, payoutList, salesList, compSalesList, 
        voidSalesList, cashDropList, expectedCashList, 
        numHoursWorkedList, bartenderTipsPerHourList, 
        appTipsPerHourList, creditCardTipList, cashTipList, tip, wage)), 
        columns=colNamesDmrs)

    return dfDmrs

def checkEmpIdHasRoles(empId):
    empRolesList=db.session.query(Employees).filter(Employees.id==empId).first().empRoles
    if empRolesList==[]:
        return False
    else:
        return True


def empTableListUtil(employeeData):
    # if empName:
        # employees = Employees.query.with_entities(Employees.id, Employees.name).filter(
            # (Employees.name=empName[0]) & (Employees.deactivatedBy==None)).all()
    # else:
        # employees = Employees.query.with_entities(Employees.id, Employees.name).all()
    roleList=[]
    resIdList=[]
    
    for i in employeeData:
        #check for employee role, if none, returns employeeID
        if checkEmpIdHasRoles(i[0])==False:
            return i[0]
        else:
            empRolesList=db.session.query(Employeeroles).filter(Employeeroles.empId==i[0]).with_entities(Employeeroles.role).all()
            empRolesList = [j[0] for j in empRolesList]
            empResIdList =list(np.unique(db.session.query(Employeeroles).filter(
                Employeeroles.empId==i[0]).with_entities(Employeeroles.restaurantId).all()))
            empRolesListString=''
            for i in empRolesList:
                if empRolesListString=='':
                    empRolesListString=i
                else:
                    empRolesListString=empRolesListString+', '+i

            roleList.append(empRolesListString)
            resIdList.append(empResIdList)

    resList=[]
    for k in resIdList:
        empResList=[db.session.query(Restaurants).filter(Restaurants.id==int(l)).with_entities(
            Restaurants.name).first()[0] for l in k]
        resList.append(empResList)
    
    empTableList=[]
    for a,b,c in zip(employeeData, resList, roleList):
        empTableList.append([a[0],a[1],b[0],c])
    
    return empTableList


def addEmpRolesUtil(userId, empId, resName, roleList, formDict):
    roleDict={key:'' for key in roleList if key in formDict}
    if 'Bartender' in roleDict and 'Apprentice' in roleDict:
        del roleDict['Apprentice']
    
    roleAppendList=[]
    print('roleDict:::',roleDict, 'range(len(range(len(roleDict))::::',range(len(roleDict)))
    for role, i in zip(roleDict,range(len(roleDict))):
        wage=Standardwages.query.filter(
            Standardwages.role==role).with_entities(Standardwages.wage).first()[0]
        
        tipPercentage=Standardwages.query.filter(
            Standardwages.role==role).with_entities(
            Standardwages.tipPercentage).first()[0]

        restaurantId=Restaurants.query.filter_by(
            name=resName).with_entities(
            Restaurants.id).first()[0]
        
        standardWageId=Standardwages.query.filter_by(
            role=role).with_entities(Standardwages.id).first()[0]
        
        #I should probably make a class for this
        vars()['role' + str(i)]=Employeeroles(role=role,
            wage=wage,tipPercentage=tipPercentage,restaurantId=restaurantId,
            createdBy=userId, standardWageId=standardWageId,
            empId=empId)
        print(i)
        roleAppendList.append(vars()['role' + str(i)])
    return roleAppendList


def addEmployeeUtility(empName,userId, resName, roleList, formDict,customEmpId, onlyActive):
            if customEmpId:
                print('employee ID flag::::',Employees.query.filter_by(id=customEmpId).first())
                if Employees.query.filter_by(id=customEmpId).first():
                    flash('Your Employee ID is already in use', 'warning')
                    return redirect(url_for('main.addEmployeeDup',empName=empName, onlyActive=onlyActive))
                addEmp=Employees(id=customEmpId,name=empName, createdBy=userId)
            else:
                newEmpId=1
                flag=True
                while flag:
                    if Employees.query.filter_by(id=newEmpId).first():
                        newEmpId+=1
                    else:
                        flag=False
                addEmp=Employees(id=newEmpId,name=empName, createdBy=userId)
            
            db.session.add(addEmp)
            db.session.commit()
            
            if customEmpId:
                empId=customEmpId
            else:
                empId=newEmpId
            
            addEmpRoles = addEmpRolesUtil(userId,empId, resName, roleList, formDict)
           
            db.session.add_all(addEmpRoles)
            db.session.commit()
            flash('Your employee has been added!', 'success')



def payrollReportUtil(dateFrom,dateTo,resId):
    shiftDf=pd.read_sql_table('shifts',db.engine)
    employeerolesDf=pd.read_sql_table('employeeroles',db.engine)
    restaurantsDf=pd.read_sql_table('restaurants',db.engine)

    #added new 27 January 2021
    if dateFrom=='':
        dateFrom = date.today()- timedelta(days=14)
        dateFrom=dateFrom.strftime("%Y-%m-%d")
    #Build dictionary of weeks with Start and end dates
    #get date ranges for tables
    weekStartDt= datetime.datetime.strptime(dateFrom,'%Y-%m-%d').date()
    weekEndDt=datetime.datetime.strptime(dateFrom,'%Y-%m-%d').date() + timedelta(days=6)
    weeksDict={}

    for i in range(1,2):
        weeksDict[f'week{i}']=[weekStartDt,weekEndDt]
        weekStartDt=weekEndDt + timedelta(days=1)
        weekEndDt = weekEndDt + timedelta(days=7)
        i+=1
    weeksDict[f'week{i}']=[weeksDict[f'week{i-1}'][0] + timedelta(days=7),weeksDict[f'week{i-1}'][1] + timedelta(days=7)]
    
    #build dataframe for one week's payroll if it exists
    dfList=[]
    # i=1
    for x,y in weeksDict.items():
        df=shiftDf[(shiftDf['shiftDate']>=str(y[0])) & (shiftDf['shiftDate']<=str(y[1]))]
        if resId==None:
            pass
        elif resId>=3:
            df=df[df['restaurantId']==resId]
        elif resId==2:
            df=df[(df['restaurantId']>=3)& (df['restaurantId']<=6)]
            
        if len(df)>0:
            df=df.groupby(['name','empId','employeeRolesId','restaurantId']).sum()
            df=df[['hoursWorked','shiftTips','shiftTipsShipgarten','wages']].copy()
            df.reset_index(inplace=True)
            df['Tips']=np.where((df['restaurantId'] >=3) & (df['restaurantId']<=6),df['shiftTipsShipgarten'],df['shiftTips'])
            df.set_index(['name','empId','employeeRolesId','restaurantId'], inplace=True)
            df1=df[['hoursWorked','Tips','wages']].copy()
            df1.columns=['Hours', 'Tips','Wages']
            df1['Tips+Wages']=df1['Tips']+df1['Wages']
            dfList.append(df1)
        else:
            noShiftsColumn=f'No shifts {str(y[0])} thru {str(y[1])}'
    
    if len(dfList)==0:
        return print('***no Shifts***')
    elif len(dfList)==1:
        df2=dfList[0]
    else:
        df2=pd.merge(dfList[0],dfList[1],how='outer', on=['name','empId','employeeRolesId','restaurantId'], 
             suffixes=(' Week1',' Week2')).fillna(0)
        df2['Total Hours']=df2['Hours Week1']+df2['Hours Week2']
        df2['Total Tips']=df2['Tips Week1']+df2['Tips Week2']
        df2['Total Wages']=df2['Wages Week1']+df2['Wages Week2']
        df2['Total Tips+Wages']=df2['Tips+Wages Week1']+df2['Tips+Wages Week2']
    
    #get hourly rate from employee roles
    rolesDf=employeerolesDf[['id','role','wage']].copy()
    rolesDf.columns=['roleId','Role','Wage']
    df2.reset_index(inplace=True)
    df2.set_index('employeeRolesId')
    df3=pd.merge(df2,rolesDf,how='left',left_on='employeeRolesId',right_on='roleId')
    
    restaurantsDf.columns=['restaurantId','Restaurant Name']
    df4=pd.merge(df3,restaurantsDf,how='left',left_on='restaurantId',right_on='restaurantId')
    #merge name and role
    df4['Employee']=df4['name'] + '-' +df4['Role']
    print(len(df4.columns), df4.columns)
    if len(df4.columns)==13:
        # colNames=['Name','Restaurant Name','Role','Hours','Wages','Tips', 'Tips+Wages', 'Shift Status']
        colNames=['Employee','Restaurant Name','Hours','Wages','Tips', 'Tips+Wages']
        payrollReportDf=df4[['Employee','Restaurant Name','Hours','Wages','Tips','Tips+Wages']].copy()
        # payrollReportDf['Week Start']=weeksDict['week1'][0]
        # payrollReportDf['Shift Status']=noShiftsColumn
        #rounding and cutting off decimal in file
        # for i in payrollReportDf.iloc[:,3:-2]:
            # payrollReportDf[i]=payrollReportDf[i].apply(lambda x: round(x, 2))
    else:
        colNames=['Employee','Restaurant Name','Hours Week1','Hours Week2','Total Hours','Wages Week1',
                           'Wages Week2','Total Wages','Tips Week1','Tips Week2','Total Tips', 'Tips+Wages Week1', 'Tips+Wages Week2',
                           'Total Tips+Wages']
        payrollReportDf=df4[['Employee','Restaurant Name','Hours Week1','Hours Week2','Total Hours','Wages Week1',
                           'Wages Week2','Total Wages','Tips Week1','Tips Week2','Total Tips', 'Tips+Wages Week1', 'Tips+Wages Week2',
                           'Total Tips+Wages']].copy()
        # payrollReportDf['Week1 Start']=weeksDict['week1'][0]
        # payrollReportDf['Week2 Start']=weeksDict['week2'][0]
        # for i in payrollReportDf.iloc[:,3:-2]:
            # payrollReportDf[i]=payrollReportDf[i].apply(lambda x: round(x, 2))
    # payrollReportDf.rename(columns={'name':'Name'},inplace=True)
    
    
    # convert weeksDict to df
    dfWeeks=pd.DataFrame(weeksDict)
    print('payrollReport Completed Successfully')
    return (payrollReportDf,colNames,dfWeeks)
    
#return excel files formatted
def formatExcelHeader(workbook,worksheet, df, startRow):
    header_format = workbook.add_format({
        'bold': True,
        'text_wrap': True,
        'valign': 'top',
        'align':'center',
        'border': 0})
    for col_num, value in enumerate(df.columns.values):
        worksheet.write(startRow, col_num, value,header_format)
        width=len(value)+1 if len(value)>8 else 8
        worksheet.set_column(col_num,col_num,width)

#List of users that can be modified
def restrictedUserListObj():
    userObjList=db.session.query(User).filter(User.username!='CostaRica').all()
    return userObjList

#user permissions dictionary username : string of resId's comma seperated
def buildUserPermDict(userObjList):
    userPermDict={}
    for i in userObjList:
        if i.permission==None:
            userPermDict[i.username]=None
        else:
            subList=[]
            for h in i.permission.split(','):
                subList.append(int(h))
            userPermDict[i.username]=subList
    return userPermDict


def empRolesDfUtil(empId):
    empRolesObj = Employeeroles.query.filter_by(empId=int(empId)).all()
    empRoleIdList=[]
    columns=['Role ID','Role','Wage Rate','Tip Percentage','Restaurant', 'Notes']
    df = pd.DataFrame(columns=columns)
    i=0
    for role in empRolesObj:
        roleId= role.id
        roleRole = role.role
        roleWage = role.wage
        roleTipPercentage = str(int(role.tipPercentage) * 100) + '%'
        roleRes = Restaurants.query.filter_by(id=role.restaurantId).first().name
        roleNotes = role.notes
        subList=[roleId, roleRole, roleWage, roleTipPercentage, roleRes, roleNotes]
        df.loc[i]=subList
        i+=1
        empRoleIdList.append(roleId)
    df.set_index('Role ID', inplace=True)
    return (df, columns, empRoleIdList)
    
def addEmpRoleUtil(empId, userId, formDict):
    role = formDict.get('role')
    wage = formDict.get('wage')
    tipPercent = float(formDict.get('tipPercent').strip('%'))/100
    restaurantId = Restaurants.query.filter_by(name=formDict.get('restaurant')).with_entities(Restaurants.id).first()[0]
    notes = formDict.get('notes')
    
    newRole=Employeeroles(role=role,
            wage=wage,tipPercentage=tipPercent,restaurantId=restaurantId,
            createdBy=userId,empId=int(empId), notes=notes)
    db.session.add(newRole)
    db.session.commit()
    
def addEmpValidationFlag(formDict, userPermDict):
    if formDict.get('restaurant') not in restrictedResList(userPermDict):
        return 'Enter a valid restaurant'
    if formDict.get('tipPercent') not in ['100%','50%','0%']:
        print('fired not in')
        return 'Tip percent can only be 100%, 50% or 0%'
    try:
        float(formDict.get('wage'))
        # float(formDict.get('tipPercent'))
        # print('fired try')
    except:
        # print('fired except')
        return 'Wage must be a numeric value'

    return None

def checkShifts(roleId):
    shiftDate=db.session.query(Shifts.shiftDate,func.max(Shifts.id)).filter_by(employeeRolesId=roleId).first()
    if shiftDate==(None, None):
        return None
    else:
        return shiftDate[0].strftime("%m-%d-%Y")

def deactivateEmpUtil(empId):
    #get highest availible employee id working back form 99999
    # newDeactiveId=999999
    # flag=True
    # print('do we get here1?????')
    # while flag:
        # if Employees.query.filter_by(id=newDeactiveId).first():
            # newDeactiveId = newDeactiveId-1
            # print(newDeactiveId)
        # else:
            # flag=False
    emp1=Employees.query.filter_by(id=empId).first()
    # emp1.id=newDeactiveId
    emp1.deactivatedBy=current_user.id
    db.session.commit()
    # emp1Roles=Employeeroles.query.filter_by(empId=empId).all()
    # for i in emp1Roles:
        # i.empId=newDeactiveId

    # emp1Shifts=Shifts.query.filter_by(empId=empId).all()
    # for i in emp1Shifts:
        # i.empId=newDeactiveId
    # db.session.commit()

def deleteEmpUtil(empId):
    Employees.query.filter_by(id=empId).delete()
    emp1Roles=Employeeroles.query.filter_by(empId=empId).all()
    for i in emp1Roles:
        i.delete()
    db.session.commit()
    
def addRoleFillStdWageUtil(stdWage):
    if stdWage==None or stdWage=='':
        role=''
        wage=''
        tipPercentage=''
    elif stdWage!=None:
        stdWageData=Standardwages.query.filter_by(role=stdWage).first()
        role=stdWageData.role
        wage=stdWageData.wage
        tipPercentage=str(float(stdWageData.tipPercentage)*100)[:-2]+'%'
    return (role,wage,tipPercentage)


def convertDictNumbersTwoDecimals(df_to_dict_records):
    #This formats dictionary values that are numbers to two decimals
    for i in df_to_dict_records:
        for j,k in i.items():
            if isinstance(k, numbers.Number):
                i[j]="{0:,.2f}".format(k)
    return df_to_dict_records