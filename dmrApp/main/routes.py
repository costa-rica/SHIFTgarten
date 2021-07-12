from flask import Blueprint
from flask import render_template, url_for, redirect, flash, request, abort, session,\
    Response, current_app, send_from_directory
from dmrApp import db, bcrypt, mail
from dmrApp.models import Dmrs, Employees, Employeeroles, Post, Restaurants, Shifts, \
    User, Standardwages
from dmrApp.main.forms import EmployeeForm, AddRestaurantForm, DatabaseForm, AddRoleForm
from flask_login import login_user, current_user, logout_user, login_required
import secrets
import os
from PIL import Image
from datetime import datetime, date, time
import datetime
from sqlalchemy import func, desc
import pandas as pd
import io
from wsgiref.util import FileWrapper
import xlsxwriter
from flask_mail import Message
from dmrApp.main.utils import shiftDataReport, dmrDataReport, \
    addEmpRolesUtil, empTableListUtil, payrollReportUtil, formatExcelHeader, \
    buildUserPermDict, restrictedUserListObj, addEmployeeUtility, \
    empRolesDfUtil, addEmpRoleUtil, addEmpValidationFlag, checkShifts, \
    deactivateEmpUtil, addRoleFillStdWageUtil, convertDictNumbersTwoDecimals, \
    shiftDataPayStubReport
from dmrApp.dmr.utils import restrictedResList
import openpyxl
from werkzeug.utils import secure_filename
import json
import glob

main = Blueprint('main', __name__)


@main.route("/")
@main.route("/home")
def home():
    posts = Post.query.order_by(desc(Post.id)).all()
    print(current_user.is_authenticated)    
    return render_template('index.html', posts=posts)


@main.route('/addEmployee', methods=["GET","POST"])
@login_required
def addEmployee():
    form=EmployeeForm()
    #Restrict users from accessing restaurants not granted permissions for
    userObjList=[User.query.get(current_user.id)]
    userPermDict=buildUserPermDict(userObjList)
    resPermList = restrictedResList(userPermDict)
    if 'CBC Restaurants' in resPermList:
        resPermList.remove('CBC Restaurants')
    if 'Shipgarten' in resPermList:
        resPermList.remove('Shipgarten')
    
    #get employees viewable by user through employeeroles table
    viewableEmpIds=Employeeroles.query.filter(Employeeroles.restaurantId.in_(
        list(userPermDict.values())[0])).with_entities(Employeeroles.empId).distinct().all()
    viewableEmpIds=[i[0] for i in viewableEmpIds]

    onlyActive=request.args['onlyActive']

    if onlyActive=='True':
        employeeData = Employees.query.filter(
            (Employees.deactivatedBy==None) & (Employees.id.in_(viewableEmpIds))).with_entities(
            Employees.id, Employees.name).all()
    else:
        employeeData = Employees.query.filter(Employees.id.in_(viewableEmpIds)).with_entities(
            Employees.id, Employees.name).all()
    empTableList = empTableListUtil(employeeData)

    if isinstance(empTableList,int):
        #this means empId Returned and that empID is missing a role.
        #go to database upload and add a role

        flash(f"""Employee ID {empTableList} is missing at least one role. There is NO current quick fix. Call Nick.
        This only occurs if the employee role table in database
        has been deleted so there is a chance other roles are missing as well. Deleting employee ID {empTableList} and
        re-adding them could solve the problem. Probably need to call Nick.""", 'danger')
        return render_template('employee.html', legend=f"""Remove EmployeeID {empTableList} or call Nick.""",
            form=form)
        
    if request.method == 'POST':
        formDict = request.form.to_dict()
        if formDict.get('addEmployee') == 'True':
            customEmpId=formDict.get('customEmpId')
            empName=formDict.get('newEmployeeName')
            resName=formDict.get('resName')
            userId=current_user.id
            roleList=['Bartender', 'Apprentice','Security','Driver','Kitchen']
            
            # if employee name alraedy used
            if db.session.query(Employees).filter(
                (Employees.name==empName)).all():
                flash('Employee name has already used. Use a different name.', 'warning')
                return redirect(url_for('main.addEmployee', onlyActive=onlyActive))

            addEmployeeUtility(empName,userId, resName, roleList, formDict,customEmpId, onlyActive='True')
            
            return redirect(url_for('main.addEmployee',  legend='Add Employee',
                                    onlyActive=onlyActive))            

        if formDict.get('editEmployee'):
            _, empId=formDict.get('editEmployee').split('|')
            return redirect(url_for('main.customEmpRole',empId=empId))

    return render_template('employee.html', legend='Add Employee',empTableList=empTableList,
                           form=form, resPermList=resPermList, str=str, onlyActive=onlyActive)


@main.route('/editEmployee', methods=["GET","POST"])
@login_required
def customEmpRole():
    form=AddRoleForm()
    userObjList=[User.query.get(current_user.id)]
    userPermDict=buildUserPermDict(userObjList)
    resPermList = restrictedResList(userPermDict)
    if 'CBC Restaurants' in resPermList:
        resPermList.remove('CBC Restaurants')
    if 'Shipgarten' in resPermList:
        resPermList.remove('Shipgarten')
    empId=request.args.get('empId')
    stdWage=request.args.get('stdWage')
    userId=current_user.id
    
    fillInRole=addRoleFillStdWageUtil(stdWage)
    role=fillInRole[0]
    wage=fillInRole[1]
    tipPercentage=fillInRole[2]
    

    #get employee name and id from Employees table
    empObj = Employees.query.get(int(empId))
    legend ="Edit " + empObj.name +"'s Roles"
    employeeName =  '(employee ID: ' + empId +')'
    
    #get employee roles for table
    # empRolesListUtil returns a touple (empRoleIdList, datframe, column Names List) of roles associ with empId:
    #roleId(index), roleRole, roleWage, roleTipPercentage, roleRes, roleNotes
    empRolesDf = empRolesDfUtil(empId)
    tableData=empRolesDf[0].to_dict('records')
    empRolesCount=len(empRolesDf[0])
    if request.method == 'POST':
        formDict = request.form.to_dict()
        print('formDict::::',formDict)
        if formDict.get('addRole') == 'True':

            if addEmpValidationFlag(formDict,userPermDict):
                flash(f'Your employee has not been filled out correctly. {addEmpValidationFlag(formDict, userPermDict)}.', 'warning')
            else:
                addEmpRoleUtil(empId, userId, formDict)
                flash('Employee role added', 'success')
        
        elif formDict.get('deleteRole'):
            roleId=formDict.get('deleteRole')[11:]
            #check if role exists in a shift, if yes don't let delete
            if checkShifts(roleId):
                flash(f'Employee role cannot be deleted because it was used {checkShifts(roleId)}', 'warning')
                return redirect(url_for('main.customEmpRole',empId=empId))
            deleteRole = Employeeroles.query.filter_by(id=int(roleId)).delete()
            db.session.commit()
            flash('Your employee role has been deleted.', 'success')
            
        elif formDict.get('deactivateEmp'):

            if Shifts.query.filter_by(empId=empId).first():
                deactivateEmpUtil(empId)
                
                flash('Employee succesfully deactivated.', 'success')
                return redirect(url_for('main.addEmployee', legend='Add Employee',onlyActive='True'))
            else:
                #delete all empllyee roles and employee from table
                Employees.query.filter_by(id=empId).delete()
                Employeeroles.query.filter_by(empId=empId).delete()
                db.session.commit()
                flash('Employee succesfully deleted.', 'success')
                return redirect(url_for('main.addEmployee', legend='Add Employee',onlyActive='True'))

        return redirect(url_for('main.customEmpRole',empId=empId))
    return render_template('empCustomRole.html', legend=legend,employeeName=employeeName,
        str=str, len=len,tableData=tableData,columnNames=empRolesDf[1][1:],
        resPermList=resPermList, empRoleIdList=empRolesDf[2],zip=zip,empId=empId,
        form=form, role=role, wage=wage, tipPercentage=tipPercentage, empRolesCount=empRolesCount)

# @main.route('/addEmployeeDupName', methods=["GET","POST"])
# @login_required
# def addEmployeeDup():
    # userObjList=[User.query.get(current_user.id)]
    # userPermDict=buildUserPermDict(userObjList)
    # resPermList = restrictedResList(userPermDict)
    # empName=request.args['empName']
    # userId=current_user.id

    ##get employees viewable by user through employeeroles table
    # viewableEmpIds=Employeeroles.query.filter(Employeeroles.restaurantId.in_(
        # list(userPermDict.values())[0])).with_entities(Employeeroles.empId).distinct().all()
    # viewableEmpIds=[i[0] for i in viewableEmpIds]

    # employeeData = Employees.query.filter(Employees.id.in_(viewableEmpIds)&
        # (Employees.name==empName)).with_entities(Employees.id, Employees.name).all()
    # empTableList = empTableListUtil(employeeData)
    
    # if request.method == 'POST':
        # formDict = request.form.to_dict()
        # resName=formDict.get('resName')
        # roleList=['Bartender', 'Apprentice','Security','Driver','Kitchen']
        # customEmpId=formDict.get('customEmpId')
        # if formDict.get('addEmployee') == 'True':
            # addEmployeeUtility(empName,userId, resName, roleList, formDict,customEmpId)
            # flash('Your employee has been added!', 'success')
            # return redirect(url_for('main.addEmployee',  legend='Add Employee',
                                    # empTableList=empTableList, onlyActive='True'))
    
    # return render_template('employeeDupName.html', legend='Employee Potentially a Duplicate?',
                            # empTableList=empTableList, resPermList=resPermList)


@main.route('/addRestaurant', methods=["GET","POST"])
@login_required
def addRestaurant():
    form=AddRestaurantForm()
    restaurants=Restaurants.query.with_entities(Restaurants.id,Restaurants.name).all()
    if form.validate_on_submit():

        addRes=Restaurants(name=form.name.data)
        db.session.add(addRes)
        db.session.commit()
        flash('Your restaurant has been added!', 'success')
        return redirect(url_for('main.addRestaurant',  legend='Add Restaurant',
                                form=form, restaurants=restaurants))

    return render_template('restaurant.html', legend='Add Restaurant',
                           form=form, restaurants=restaurants)


@main.route('/reports', methods=["GET","POST"])
@login_required
def reports():
    legend='Manager Reports'
    userObjList=[User.query.get(current_user.id)]
    userPermDict=buildUserPermDict(userObjList)
    resPermList = restrictedResList(userPermDict)
    checks={'shiftReport':'','dmrReport':'','payrollReport':''}
    
    if request.method == 'POST':
        formDict = request.form.to_dict()
        dateFrom = formDict.get('reportFrom')
        dateTo = formDict.get('reportTo')
        if dateTo=='':
            now=datetime.datetime.now()
            dateTo=now.strftime('%Y-%m-%d')
        restaurant = formDict.get('restaurant')
        if restaurant:
            resId=Restaurants.query.filter_by(name=restaurant).with_entities(Restaurants.id).first()[0]
        else:
            resId=None
        if dateFrom:
            parseDateString=[int(x) for x in dateFrom.split('-')]
            dateFromObj=date(parseDateString[0],parseDateString[1],parseDateString[2])
        else:
            dateFromObj=None
        if dateTo:
            parseDateString=[int(x) for x in dateTo.split('-')]
            dateToObj=date(parseDateString[0],parseDateString[1],parseDateString[2])
        else:
            dateToObj=None
        
        colNamesShifts =['Date','Employee','Restaurant','Scheduled time','Start time',
            'Off time','Hours worked','Tips', 'Wages', 'Tips + Wages','Tips/Hour']

        colNamesDmrs = ['Date', 'Restaurant', 'Start Cash', 'Payout', 'Sales', 
            'Comp Sales', 'Void Sales', 'Cash Drop', 'Expected Cash', 
            'Number Hours Worked', 'Bartender Tips', 'Apprentice Tips', 
            'Credit Card Tips', 'Cash Tips', 'Sum of Tips', 'Sum of Wages']
        

        if formDict.get('viewReport') and formDict.get('shiftReport'):
            results = shiftDataReport(dateFromObj,dateToObj, resId,colNamesShifts).to_dict('records')
            #This formats dictionary values that are numbers to two decimals
            results = convertDictNumbersTwoDecimals(results)

            session['shiftResults']=results
            checks['shiftReport']='checked'
            return render_template('reports.html', legend='Reports', results = session['shiftResults'],
                columnNames=colNamesShifts, len=len, dateFrom=dateFrom, dateTo=dateTo,
                resPermList=resPermList,restaurant=restaurant, checks=checks, float=float)
        
        elif formDict.get('viewReport') and formDict.get('dmrReport'):
            results = dmrDataReport(dateFromObj,dateToObj,resId,colNamesDmrs).to_dict('records')
            session['dmrResults']=results
            checks['dmrReport']='checked'
            return render_template('reports.html', legend='Reports', results = session['dmrResults'],
                columnNames=colNamesDmrs, len=len, dateFrom=dateFrom, dateTo=dateTo,
                resPermList=resPermList,restaurant=restaurant, checks=checks, float=float)
        
        elif formDict.get('viewReport') and formDict.get('payrollReport'):
            checks['payrollReport']='checked'
            payrollReport=payrollReportUtil(dateFrom,dateTo,resId)
            if payrollReport==None:
                flash("""No shifts for selected dates or restaurants. If not date is selected we assume today.
                If no restaurant is selected we assume all restaruants""", 'warning')
                return render_template('reports.html', legend='ReportsCheck', len=len, dateFrom=dateFrom, dateTo=dateTo,
                    resPermList=resPermList,restaurant=restaurant, checks=checks, float=float)
            
            payrollReportDf=payrollReport[0].to_dict('records')
            #This formats dictionary values that are numbers to two decimals
            payrollReportDf=convertDictNumbersTwoDecimals(payrollReportDf)
            session['payrollReportDf']=payrollReportDf
            colNamesPayrollReport=payrollReport[1]
            
            return render_template('reports.html', legend='Reports', results = session['payrollReportDf'],
                columnNames=colNamesPayrollReport, len=len, dateFrom=dateFrom, dateTo=dateTo,
                resPermList=resPermList,restaurant=restaurant, checks=checks, float=float)

        elif formDict.get('viewReport') and formDict.get('payrollReportStubs'):
            flash("""This report is an Excel download only, no web report. Download to view.""", 'warning')
            return render_template('reports.html', legend='ReportsCheck', len=len, dateFrom=dateFrom, dateTo=dateTo,
                resPermList=resPermList,restaurant=restaurant, checks=checks, float=float)


        elif formDict.get('downloadReport'):
            filesForDelete=glob.glob(os.path.join(current_app.root_path, 'static/reports/*.xlsx'))
            for file in filesForDelete:
                os.remove(file)
            dateFromForName = datetime.datetime.strptime(dateFrom,'%Y-%m-%d') #converts string to datetime object
            dateFromForName = dateFromForName.strftime('%m.%d.%y')
            # print('dateTo:::',dateTo,type(dateTo))
            dateToForName = datetime.datetime.strptime(dateTo,'%Y-%m-%d') #converts string to datetime object
            dateToForName = dateToForName.strftime('%m.%d.%y')
            
            if restaurant:
                reportName=f"{restaurant}{dateFromForName}-{dateToForName}.xlsx"
            else:
                reportName=f"MultipleRestaurants{dateFromForName}-{dateToForName}.xlsx"
            
            excelObj=pd.ExcelWriter(os.path.join(current_app.root_path, 'static/reports/', reportName))
            workbook=excelObj.book
            formatDecimals = workbook.add_format({'num_format': '#,##0.00'})

            if formDict.get('shiftReport'):
                sheetName='Shift Report'
                shiftReportDf=shiftDataReport(dateFromObj,dateToObj, resId,colNamesShifts)
                
                shiftReportDf.to_excel(excelObj,sheet_name=sheetName, startrow=1,header=False, index=False)
                worksheet=excelObj.sheets[sheetName]
                formatExcelHeader(workbook,worksheet, shiftReportDf,0)
                worksheet.set_column(0,0, 11)#date width
                worksheet.set_column(2,2, 17)#restaurant column width
                worksheet.set_column(7,11, None,formatDecimals)#tips,wages, tips+ wages

            if formDict.get('dmrReport'):
                sheetName='DMR Report'
                dmrDataReportDf=dmrDataReport(dateFromObj,dateToObj,resId,colNamesDmrs)

                dmrDataReportDf.to_excel(excelObj,sheet_name=sheetName, startrow=1,header=False, index=False)
                worksheet=excelObj.sheets[sheetName]
                formatExcelHeader(workbook,worksheet, dmrDataReportDf,0)
                worksheet.set_column(0,0, 11)
                worksheet.set_column(2,15, None,formatDecimals)#tips,wages, tips+ wages
            
            if formDict.get('payrollReport'):
                sheetName='Payroll Report'
                payrollReportDf=payrollReportUtil(dateFrom,dateTo,resId)
                
                payrollReportDf[0].to_excel(excelObj,sheet_name=sheetName, startrow=1,header=False, index=False)
                worksheet=excelObj.sheets[sheetName]
                formatExcelHeader(workbook,worksheet, payrollReportDf[0],0)
                worksheet.set_column(3,14, None, formatDecimals)

            if formDict.get('payrollReportStubs'):
                sheetName='Payroll Stubs'
                
                payrollStubsDf, employeeCharMax=shiftDataPayStubReport(dateFrom,dateTo, resId, colNamesShifts)
                startRow=1
                for i in range(0,len(payrollStubsDf)):
                    payrollStubsDf[i].to_excel(excelObj,sheet_name=sheetName, startrow=startRow,header=False, index=False)
                    worksheet=excelObj.sheets[sheetName]
                    formatExcelHeader(workbook,worksheet, payrollStubsDf[i],startRow-1)
                    format1 = workbook.add_format()
                    format1.set_bottom(7)
                    endRow=startRow + len(payrollStubsDf[i])
                                        #(first_row, first_col, last_row, last_col)
                    
                    # worksheet.conditional_format(2,1,2,11, {'type': 'cell','value': '""','format':format1})
                    # borderFormat=workbook.add_format({'bottom':5})
                    for j in range(0,len(payrollStubsDf[i].columns)):
                        worksheet.write_blank(endRow, j, payrollStubsDf[i].iloc[len(payrollStubsDf[i])-1,j],format1)
                        # worksheet.write_blank(startRow-1, j, '',borderFormat)
                    startRow=startRow + len(payrollStubsDf[i])+2
                worksheet.set_column(0,0, 11)#date width
                worksheet.set_column(1,1, employeeCharMax)#emplpoyee width
                worksheet.set_column(2,2, 17)#restaurant column width
                
                worksheet.set_column(6,11, None,formatDecimals)#tips,wages, tips+ wages
                worksheet.set_column(6,6, 13)#hours worked column width


            excelObj.close()
            return send_from_directory(os.path.join(current_app.root_path, 'static/reports/'),reportName, as_attachment=True)
    return render_template('reports.html', legend=legend,resPermList=resPermList, checks=checks, float=float)


@main.route('/database', methods=["GET","POST"])
@login_required
def database():
    # form=DatabaseForm()
    tableNamesList= db.engine.table_names()
    legend='Database downloads'
    if request.method == 'POST':
        formDict = request.form.to_dict()
        if formDict.get('downloadTables')=="True":
            
            filesForDelete=glob.glob(os.path.join(current_app.root_path, 'static/reports/*.xlsx'))
            for file in filesForDelete:
                os.remove(file)
            
            timeStamp = datetime.datetime.now().strftime("%y%m%d_%H%M%S")
            reportName=f"database_tables{timeStamp}.xlsx"
            excelObj=pd.ExcelWriter(os.path.join(current_app.root_path, 'static/reports/', reportName),
                date_format='yyyy/mm/dd', datetime_format='yyyy/mm/dd')
            workbook=excelObj.book
            
            dictKeyList=[i for i in list(formDict.keys()) if i in tableNamesList]
            dfDictionary={h : pd.read_sql_table(h, db.engine) for h in dictKeyList}
            for name, df in dfDictionary.items():
                if len(df)>900000:
                    flash(f'Too many rows in {name} table', 'warning')
                    return render_template('database.html',legend=legend, tableNamesList=tableNamesList)
                df.to_excel(excelObj,sheet_name=name, index=False)
                worksheet=excelObj.sheets[name]
                formatExcelHeader(workbook,worksheet, df)
                if name=='dmrs':
                    dmrDateFormat = workbook.add_format({'num_format': 'yyyy-mm-dd'})
                    worksheet.set_column(1,1, 15, dmrDateFormat)
                
            print('path of reports:::',os.path.join(current_app.root_path, 'static/reports/'))
            excelObj.close()
            return send_from_directory(os.path.join(current_app.root_path, 'static/reports/'),reportName, as_attachment=True)

        # elif formDict.get('uploadExcel'):
            # formDict = request.form.to_dict()
            # print(formDict)
            # uploadData=request.files['excelFileUpload']
            # excelFileName=uploadData.filename
            # uploadData.save(os.path.join(current_app.root_path, 'static', excelFileName))
            # wb = openpyxl.load_workbook(uploadData)
            # sheetNames=json.dumps(wb.sheetnames)
            # tableNamesList=json.dumps(tableNamesList)

            # return redirect(url_for('main.databaseUpload',legend=legend,tableNamesList=tableNamesList,
                # sheetNames=sheetNames, excelFileName=excelFileName))
    return render_template('database.html', legend=legend, tableNamesList=tableNamesList)


@main.route('/databaseUpload', methods=["GET","POST"])
@login_required
def databaseUpload():
    tableNamesList=json.loads(request.args['tableNamesList'])
    sheetNames=json.loads(request.args['sheetNames'])
    excelFileName=request.args['excelFileName']
    legend='Upload Excel to Database'
    uploadFlag=True
    if request.method == 'POST':
        
        formDict = request.form.to_dict()
        if formDict.get('appendExcel'):
            wb=os.path.join(current_app.root_path, 'static', excelFileName)
            for sheet in sheetNames:                
                sheetUpload=pd.read_excel(wb,engine='openpyxl',sheet_name=sheet)
                if sheet=='dmrs':
                    sheetUpload["dmrDate"] = pd.to_datetime(sheetUpload["dmrDate"]).dt.strftime('%Y-%m-%d')
                if sheet=='shifts':
                    sheetUpload["shiftDate"] = pd.to_datetime(sheetUpload["shiftDate"]).dt.strftime('%Y-%m-%d')
                if sheet=='post':
                    sheetUpload=sheetUpload.replace(r'_x000D_','', regex=True) 
                try:
                    sheetUpload.to_sql(formDict.get(sheet),con=db.engine, if_exists='append', index=False)
                except IndexError:
                    pass
                except:
                    os.remove(os.path.join(current_app.root_path, 'static', excelFileName))
                    uploadFlag=False
                    flash(f"""Problem uploading {sheet} table. Check for uniquness make 
                        sure not duplicate ids are being added.""", 'warning')
                    return render_template('databaseUpload.html',  legend=legend,
                        tableNamesList=tableNamesList, sheetNames=sheetNames,uploadFlag=uploadFlag)
                        
            os.remove(os.path.join(current_app.root_path, 'static', excelFileName))
            print(excelFileName,' should be removed from static/')
            flash(f'Table(s) successfully uploaded to database!', 'success')

            return render_template('databaseUpload.html',  legend=legend,
                tableNamesList=tableNamesList, sheetNames=sheetNames,uploadFlag=uploadFlag)
                
    return render_template('databaseUpload.html',legend=legend,tableNamesList=tableNamesList,
                sheetNames=sheetNames, excelFileName=excelFileName,uploadFlag=uploadFlag)


@main.route('/databaseRemoveData', methods=["GET","POST"])
@login_required
def databaseRemoveData():
    legend='Clear Tables in Database'
    dbModelsList= [cls for cls in db.Model._decl_class_registry.values() if isinstance(cls, type) and issubclass(cls, db.Model)]
    dbModelsDict={str(h)[22:-2]:h for h in dbModelsList}
    tableNameList=[h for h in dbModelsDict.keys()]
    if request.method == 'POST':
        formDict = request.form.to_dict()
        if formDict.get('removeData'):
            print('formDict::::',formDict)
            for tableName in formDict.keys():
                if tableName in tableNameList:
                    db.session.query(dbModelsDict[tableName]).delete()
                    db.session.commit()
            flash(f'Selected tables succesfully deleted', 'success')
    return render_template('databaseRemoveData.html', legend=legend, tableNameList=tableNameList)
    
    
@main.route('/usersPermissions', methods=["GET","POST"])
@login_required
def userPermissions():
    legend='User Permission Assignments'
    userObjList=restrictedUserListObj()
    users=[i.username for i in userObjList]
    restaurantList=Restaurants.query.with_entities(Restaurants.name).all()
    permissionsList=[]
    
    #build a userPermDict of username : List of rest with access
    userPermDict=buildUserPermDict(userObjList)
    
    #build permDict from userPermDict that is userPermDict(key + value):'checked'
    permDict={}
    for h,i in userPermDict.items():
        if i != None:
            for z in i:
                permDict[h+'|'+str(z)]='checked'

    if request.method == 'POST':
        formDict = request.form.to_dict()
        if formDict.get('updatePermissions'):
            permDictNew={}
            for user in userObjList:
                firstFlag=True
                for resId_minusOne in range(len(restaurantList)):
                    if formDict.get(str(user.username)+'|'+str(resId_minusOne + 1)):
                        if firstFlag==True:
                            permDictNew[user.username] =str(resId_minusOne + 1)
                            firstFlag=False
                        else:
                            permDictNew[user.username]=permDictNew[user.username] +','+ str(resId_minusOne + 1)
                            
                user.permission=permDictNew[user.username]
                db.session.commit()

        return redirect(url_for('main.userPermissions'))
    return render_template('userPermissions.html',legend=legend,users=users,
        restaurantList=restaurantList, len=len, str=str, permDict=permDict)