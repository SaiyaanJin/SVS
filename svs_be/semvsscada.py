from cmath import nan
# from unicodedata import name
# from matplotlib import projections
# from matplotlib.pyplot import table
import pandas as pd
import os
import glob
from pymongo import MongoClient, ASCENDING, DESCENDING, errors
from datetime import date, timedelta, datetime, timezone
from flask import Flask, jsonify, request, redirect, Response, send_file
from flask_cors import CORS
import json
import math
# from urllib.parse import urlparse
# from urllib. parse import parse_qs
from flask_cors import CORS, cross_origin
from flask import send_from_directory
from pandas.tseries.offsets import MonthEnd
from werkzeug .utils import secure_filename
from zipfile import ZipFile
from svs_report import svsreport
from svs_report import gen_all_letters
from svs_report import gen_excel
from svs_report import gen_error_excel
import shutil
from bson import json_util, ObjectId

app = Flask(__name__)

CORS(app)


def my_max_min_function(somelist):

    max_value = max(somelist)
    min_value = min(somelist)
    avg_value = 0 if len(somelist) == 0 else sum(somelist)/len(somelist)

    max_index = [i for i, val in enumerate(somelist) if val == max_value]
    min_index = [i for i, val in enumerate(somelist) if val == min_value]

    avg_value = round(avg_value, 3)
    max_value = round(max_value, 3)
    min_value = round(min_value, 3)

    max_index.insert(0, max_value)
    min_index.insert(0, min_value)

    return max_index, min_index, avg_value


def datetime_range(start, end, delta):
    end = end + timedelta(days=1)
    current = start
    while current < end:
        yield current
        current += delta

    return current


def divide_chunks(l, n):

    # looping till length l
    for i in range(0, len(l), n):
        yield l[i:i + n]


def isFloat(value):
    try:
        float(value)
        return True
    except ValueError:
        return False


def isNaN(num):
    return num != num


def changeToFloat(x):
    if (isFloat(x)):
        return float(x)
    else:
        return None


@app.route('/', methods=['GET', 'POST'])
def working():
    return jsonify("Working")


@app.route('/dashboard', methods=['GET', 'POST'])
def dashboard():

    CONNECTION_STRING = "mongodb://mongodb0.erldc.in:27017,mongodb1.erldc.in:27017/?replicaSet=CONSERV"
    client = MongoClient(CONNECTION_STRING)
    db = client['SemVsScada']
    User_Input_Table = db['Scada_Data']

    CONNECTION_STRING = "mongodb://10.3.101.179:1434"
    client = MongoClient(CONNECTION_STRING)
    db = client['meterDataArchival']
    current_year = datetime.now().year
    Data_Table = db["meterData"+str(current_year)]

    meter_date = Data_Table.find(filter={}, projection={
                                 '_id': 0, 'date': 1}, sort=list({'date': -1}.items()), limit=1)
    meter_date = list(meter_date)

    scada_db_date = User_Input_Table.find(filter={}, projection={
                                          '_id': 0, 'Date': 1}, sort=list({'Date': -1}.items()), limit=1)
    scada_db_date = list(scada_db_date)

    path = os.listdir("D:/Applications/SVS/svs_be/Meter_Files/")

    temp_path = []

    for i in range(len(path)):
        x = path[i].split('-')
        if len(x) == 3:
            temp_path.append(x[0]+'-'+x[1]+'-20'+x[2])

    meter_folder_date = sorted(
        temp_path, key=lambda x: datetime.strptime(x, '%d-%m-%Y'))

    meter_folder_list = []

    for i in range(1, len(meter_folder_date)+1):

        meter_folder_list.append(
            {"meter_folder_date": meter_folder_date[-1*i]})

    return jsonify([{
        'meter_date': meter_date,
        'scada_db_date': scada_db_date,
        'meter_folder_date': meter_folder_list
    }])

# /////////////////////////////////////////////////////////bashboard////////////////////////////////


def ScadaCollection():

    CONNECTION_STRING = "mongodb://mongodb0.erldc.in:27017,mongodb1.erldc.in:27017/?replicaSet=CONSERV"
    client = MongoClient(CONNECTION_STRING)
    db = client['SemVsScada']
    User_Input_Table = db['Scada_Data']
    meter_table = db['meter_name_code']
    mapping_table = db['mapping_table']
    return User_Input_Table, meter_table, mapping_table

Scada_database, meter_table, mapping_table = ScadaCollection()


@app.route('/getScadaCode', methods=['GET', 'POST'])
def getScadaCode():

    startDate = request.args['startDate']
    endDate = request.args['endDate']

    filter = {
        'Date': {
            '$gte': pd.to_datetime(startDate),
            '$lte': pd.to_datetime(endDate)
        }
    }

    cursor = Scada_database.find(
        filter=filter, projection={'_id': 0, 'Name': 1, 'Code': 1, })

    data = list(cursor)

    final_data = []
    for i in range(len(data)):
        if (data[i]['Name'] != data[i]['Name']):
            data[i]['Name'] = ""

        final_data.append(data[i]['Code']+" "+data[i]['Name'])

    final_data = list(set(final_data))

    return jsonify(final_data)


@app.route('/getScadaData', methods=['GET', 'POST'])
def getScadaData():

    startDate = request.args['startDate']
    endDate = request.args['endDate']
    time = int(request.args['time'])
    code = request.args['code']
    code = code.split(',')

    data_to_send = []

    startDateObj = datetime.strptime(startDate, "%Y-%m-%d")
    endDateObj = datetime.strptime(endDate, "%Y-%m-%d")

    allDateTime = [dt.strftime("%d-%m-%Y %H:%M:%S") for dt in
                   datetime_range(startDateObj, endDateObj,
                                  timedelta(minutes=time))]

    data_to_send.append(allDateTime)

    for codes in code:

        final_data = []
        temp_final_data = []
        date_data = []

        codes = codes.split(' ')

        if codes[0] == "No":
            codes = codes[0]+" "+codes[1]
        else:
            codes = codes[0]

        startDateObj = datetime.strptime(startDate, "%Y-%m-%d")
        endDateObj = datetime.strptime(endDate, "%Y-%m-%d")

        date_range = [startDateObj+timedelta(days=x)
                      for x in range((endDateObj-startDateObj).days+1)]

        for it in date_range:

            # print(codes)

            filter = {
                'Date': {
                    '$gte': datetime(it.year, it.month, it.day, 0, 0, 0, tzinfo=timezone.utc),
                    '$lte': datetime(it.year, it.month, it.day, 0, 0, 0, tzinfo=timezone.utc)
                },
                'Code': codes
            }

            cursor = Scada_database.find(
                filter=filter, projection={'_id': 0, 'Name': 1, 'Code': 1, 'Data': 1, 'Date': 1})

            data = list(cursor)

            # print(data)

        # for for_date in pd.date_range(date(startDateObj.year, startDateObj.month, startDateObj.day), date(endDateObj.year, endDateObj.month, endDateObj.day)):

            for item in data:
                # print(item)

                if len(item["Data"]) != 0:
                    temp_final_data = temp_final_data+item["Data"]
                    date_data.append(item["Date"])
                else:
                    zero_val = [0]*96
                    temp_final_data = temp_final_data+zero_val
                    date_data.append(for_date)

                if item["Name"] != item["Name"]:
                    item["Name"] = ""

        x = list(divide_chunks(temp_final_data, time//15))

        for items in x:
            max_1, min_1, avg_1 = my_max_min_function(items)
            final_data.append(avg_1)

        final_dict = {"Name": item["Name"],
                      "Code": item["Code"],
                      "Data": final_data,
                      "Date": date_data}

        data_to_send.append(final_dict)

    return jsonify(data_to_send)

# /////////////////////////////////////////////////////Attachment File Upload & Download////////////


@app.route('/file_upload', methods=['GET', 'POST'])
def file_upload():

    file = request.files.getlist("demo[]")

    zip_handle = ZipFile(file[0].file)
    zip_handle.extractall("D:/Applications/SVS/svs_be/Meter_Files")
    zip_handle.close()

    return jsonify("final_output")


@app.route('/upload', methods=['GET', 'POST'])
def upload():

    startDate = request.args['startDate']
    endDate = request.args['endDate']

    startDateObj = datetime.strptime(startDate, "%Y-%m-%d")
    endDateObj = datetime.strptime(endDate, "%Y-%m-%d")

    PATH = "http://10.3.100.24/SCADA%20Vs%20SEM/"

    out_list = []

    for for_date in pd.date_range(date(startDateObj.year, startDateObj.month, startDateObj.day), date(endDateObj.year, endDateObj.month, endDateObj.day)):

        try:

            SCADA_FILE = PATH + \
                "SCADA_{}.xlsx".format(
                    for_date.strftime("%d%m%Y"))

            df = pd.read_excel(
                SCADA_FILE, sheet_name='Sheet7 (2)', header=[0, 1])

            cols = df.columns.to_list()
            df = df.drop(cols[0], axis=1)
            cols.pop(0)

            data_objects = []

            numb = 0

            for item in cols:
                x = df[item].to_list()

                for vals in range(len(x)):
                    if x[vals] != x[vals]:
                        x[vals] = 0

                    else:
                        x[vals] = round(x[vals], 2)

                if len(item[1]) < 3:
                    numb += 1
                    cod = "No Key:"+str(numb)

                else:
                    cod = item[1]

                temp = {
                    "Date": for_date,
                    "Name": item[0],
                    "Code": cod,
                    "Data": x
                }

                data_objects.append(temp)

            res = Scada_database.insert_many(data_objects)

        except errors.DuplicateKeyError as e:

            print("SCADA File reading Problem for "+str(for_date))
            print(e)
            # out_list.append(for_date)
            continue

        except:

            try:

                SCADA_FILE = PATH + \
                    "SCADA_{}.xlsx".format(
                        for_date.strftime("%d%m%Y"))

                df = pd.read_excel(SCADA_FILE, sheet_name=1, dtype='str',)

                df.columns = df.iloc[1]
                df = df.drop([1], axis=0)

                df1 = pd.read_excel(SCADA_FILE, sheet_name=1)
                df1.columns = df1.iloc[1]
                df1 = df1.drop([1], axis=0)

                code_val = df.columns

                list_of_data = (df.T.reset_index().values.tolist())
                date_list = list_of_data[0]
                date_list = date_list[2:]
                list_of_data = list_of_data[1:]

                list_of_data1 = (df1.T.reset_index().values.tolist())
                date_list1 = list_of_data1[0]
                date_list1 = date_list1[2:]
                list_of_data1 = list_of_data1[1:]

                data_objects = []
                headers_data = []

                for i in range(len(list_of_data)):
                    sub_code = list_of_data[i][0]
                    sub_name = list_of_data[i][1]
                    list_of_data1[i] = list_of_data1[i][2:]

                    if sub_code not in headers_data:
                        headers_data.append(sub_code)

                        if sub_name != sub_name:
                            sub_name = ""

                        temp = {
                            "Date": date_list1[0],
                            "Name": sub_name,
                            "Code": sub_code,
                            "Data": list_of_data1[i]
                        }
                        data_objects.append(temp)

                res = Scada_database.insert_many(data_objects)

            except errors.DuplicateKeyError as e:

                print("SCADA File reading Problem for "+str(for_date))
                print(e)

            except:
                out_list.append(for_date)
                continue

    if len(out_list) == 0:
        return jsonify("Done")

    else:
        return jsonify(out_list)


@app.route('/delete', methods=['GET', 'POST'])
def delete():

    startDate = request.args['startDate']
    endDate = request.args['endDate']
    code = request.args['code']

    if code == "all":

        filter = {
            'Date': {
                '$gte': pd.to_datetime(startDate),
                '$lte': pd.to_datetime(endDate)
            },
        }

        cursor = Scada_database.delete_many(
            filter=filter)

    else:

        filter = {
            'Date': {
                '$gte': pd.to_datetime(startDate),
                '$lte': pd.to_datetime(endDate)
            },
            'Code': code
        }

        cursor = Scada_database.delete_many(
            filter=filter)

    return jsonify("final_output")


@app.route('/folder_delete', methods=['GET', 'POST'])
def folder_delete():

    path = os.listdir("D:/Applications/SVS/svs_be/Meter_Files/")
    temp_path = "D:/Applications/SVS/svs_be/Meter_Files/"

    if len(path)!=0:
        for i in range(len(path)):
            shutil.rmtree(temp_path+str(path[i]))

        return jsonify("All Meter Folder Files Deleted")
    else:
        return jsonify("Nothing to Delete")

# ////////////////////////////////////////////////////////Meter Data/////////////////////////////////////////////////////////


@app.route('/meter_names', methods=['GET', 'POST'])
def meter_names():

    startDate = request.args['startDate']
    startDate_obj = datetime.strptime(startDate, '%Y-%m-%d')
    endDate = request.args['endDate']
    time = request.args['time']
    folder = request.args['folder']

    if (folder == "no"):

        CONNECTION_STRING = "mongodb://10.3.101.179:1434"
        client = MongoClient(CONNECTION_STRING)
        db = client['meterDataArchival']
        Data_Table = db["meterData"+str(startDate_obj.year)]

        filter = {
            'date': {
                '$gte': pd.to_datetime(startDate),
                '$lte': pd.to_datetime(endDate)
            }
        }

        cursor = Data_Table.find(
            filter=filter, projection={'_id': 0, 'meterID': 1, 'meterNO': 1})

        meter = list(cursor)

        meter_list = []

        for item in meter:
            x = item["meterNO"]+" ("+item["meterID"]+")"
            if x not in meter_list:
                meter_list.append(x)

        meter_list = list(set(meter_list))

        return jsonify(meter_list)

    elif folder == "yes":

        path = "D:/Applications/SVS/svs_be/Meter_Files/"

        startDate_obj = datetime.strptime(startDate, '%Y-%m-%d')
        endDate_obj = datetime.strptime(endDate, '%Y-%m-%d')

        count_flag = 0

        for dates in ([startDate_obj+timedelta(days=x) for x in range((endDate_obj-startDate_obj).days+1)]):

            full_path = path+dates.strftime("%d-%m-%y")

            if (os.path.isdir(full_path)):
                # f = open(os.path.join(full_path, file),'r')

                if count_flag == 0:
                    meter_list = os.listdir(full_path)
                    count_flag += 1

                else:
                    meter_list = [value for value in os.listdir(
                        full_path) if value in meter_list]

            else:
                meter_list = ["Please Upoad"]
                return jsonify(meter_list)

        for i in range(len(meter_list)):

            meter_list[i] = meter_list[i].split(".")[0]

        meter_list = list(set(meter_list))

        filter = {'Meter_Name': {'$in': meter_list}}

        cursor = meter_table.find(
            filter=filter, projection={'_id': 0, 'Meter_Name': 1, 'Meter_Code': 1})

        meter_list = list(cursor)

        for i in range(len(meter_list)):
            meter_list[i] = meter_list[i]["Meter_Name"] + \
                " ("+meter_list[i]["Meter_Code"]+")"

        return jsonify(meter_list)




@app.route('/meter_check', methods=['GET', 'POST'])
def meter_check():

    startDate = request.args['startDate']
    endDate = request.args['endDate']
    
    startDate_obj = datetime.strptime(startDate, '%Y-%m-%d')
    endDate_obj = datetime.strptime(endDate, '%Y-%m-%d')
    

    db_dates=[]
    meter_folder_dates=[]
    non_meter_folder_dates=[]
    path = "D:/Applications/SVS/svs_be/Meter_Files/"

    CONNECTION_STRING = "mongodb://10.3.101.179:1434"
    client = MongoClient(CONNECTION_STRING)
    db = client['meterDataArchival']
    Data_Table = db["meterData"+str(startDate_obj.year)]

    filter = {
        'date': {
            '$gte': pd.to_datetime(startDate),
            '$lte': pd.to_datetime(endDate)
        }
    }

    cursor = Data_Table.find(
        filter=filter, projection={'_id': 0, 'meterID': 1})

    meter = list(cursor)

    if len(meter)==0:
    
        for dates in ([startDate_obj+timedelta(days=x) for x in range((endDate_obj-startDate_obj).days+1)]):

            full_path = path+dates.strftime("%d-%m-%y")

            if (os.path.isdir(full_path)):
                
                meter_folder_dates.append(dates)
                
            else:
                non_meter_folder_dates.append(dates)

        if len(meter_folder_dates)==0:
            return jsonify(["Nowhere"])

        elif len(meter_folder_dates)>0 and len(non_meter_folder_dates)>0:
            return jsonify(["Some",non_meter_folder_dates])

        else:
            return jsonify(["Folder"])

    else:
        return jsonify(["Database"])

@app.route('/GetMeterData', methods=['GET', 'POST'])
def GetMeterData():

    startDate = request.args['startDate']
    startDate_obj = datetime.strptime(startDate, '%Y-%m-%d')
    endDate = request.args['endDate']
    time = int(request.args['time'])
    meter = request.args['meter']
    meter_list = meter.split(",")
    folder = request.args['folder']

    if (folder == "no"):

        CONNECTION_STRING = "mongodb://10.3.101.179:1434"
        client = MongoClient(CONNECTION_STRING)
        db = client['meterDataArchival']
        Data_Table = db["meterData"+str(startDate_obj.year)]

        startDateObj = datetime.strptime(startDate, "%Y-%m-%d")
        endDateObj = datetime.strptime(endDate, "%Y-%m-%d")

        allDateTime = [dt.strftime("%d-%m-%Y %H:%M:%S") for dt in
                       datetime_range(startDateObj, endDateObj,
                                      timedelta(minutes=time))]

        data_to_send = [allDateTime]

        for meters in meter_list:

            meters = meters.split("(")
            meterNO = meters[0][:-1]
            meterID = meters[1][:-1]

            meter_obj = {
                'meterNO': meterNO,
                'meterID': meterID
            }

            filter = {
                'date': {
                    '$gte': pd.to_datetime(startDate),
                    '$lte': pd.to_datetime(endDate)
                },
                'meterNO': meterNO,
                'meterID': meterID
            }

            cursor = Data_Table.find(
                filter=filter, projection={'_id': 0, 'data': 1, 'activeHigh': 1, 'reactiveHigh': 1, 'reactiveLow': 1, 'date': 1})

            cursor_list = list(cursor)

            data = []
            activeHigh = []
            reactiveHigh = []
            reactiveLow = []
            date_list = []

            for item in cursor_list:
                data = data+item['data']
                activeHigh.append(item['activeHigh'])
                reactiveHigh.append(item['reactiveHigh'])
                reactiveLow.append(item['reactiveLow'])
                date_list.append(item['date'].date())

            x = list(divide_chunks(data, time//15))

            final_data = []

            for items in x:
                max_1, min_1, avg_1 = my_max_min_function(items)
                final_data.append(avg_1)

            meter_obj['data'] = final_data

            for item in range(len(final_data)):
                final_data[item] = 4*final_data[item]

            meter_obj['modified_data'] = final_data
            meter_obj['activeHigh'] = activeHigh
            meter_obj['reactiveHigh'] = reactiveHigh
            meter_obj['reactiveLow'] = reactiveLow
            meter_obj['date'] = date_list

            data_to_send.append(meter_obj)

        return jsonify(data_to_send)

    elif folder == "yes":

        path = "D:/Applications/SVS/svs_be/Meter_Files/"

        startDateObj = datetime.strptime(startDate, "%Y-%m-%d")
        endDateObj = datetime.strptime(endDate, "%Y-%m-%d")

        allDateTime = [dt.strftime("%d-%m-%Y %H:%M:%S") for dt in
                       datetime_range(startDateObj, endDateObj,
                                      timedelta(minutes=time))]

        data_to_send = [allDateTime]

        for meters in meter_list:

            meters = meters.split("(")
            meters = meters[0][:-1]

            meters = meters+".MWH"
            count_flag = 0

            date_list = []
            end1Data = []

            for dates in ([startDateObj+timedelta(days=x) for x in range((endDateObj-startDateObj).days+1)]):

                date_list.append(dates)
                full_path = path+dates.strftime("%d-%m-%y")

                if (os.path.isdir(full_path)):
                    # f = open(os.path.join(full_path, file),'r')
                    full_path = full_path+"/"+meters

                    if count_flag == 0:

                        dataEnd1 = pd.read_csv(full_path, header=None)
                        dfSeriesEnd1 = pd.DataFrame(dataEnd1)
                        dfEnd1 = dfSeriesEnd1[0]

                        first_index = dfEnd1[0].split()

                        meter_obj = {
                            'meterNO': first_index[1],
                            'meterID': first_index[0]
                        }

                        total_active_high = [first_index[3]]
                        total_reactive_high = [first_index[4]]
                        total_reactive_low = [first_index[5]]

                        for i in range(1, len(dfEnd1)):
                            oneHourDataEnd1 = [changeToFloat(
                                x) for x in dfEnd1[i].split()[1:]]
                            end1Data = end1Data + oneHourDataEnd1

                        count_flag += 1

                    else:
                        dataEnd1 = pd.read_csv(full_path, header=None)
                        dfSeriesEnd1 = pd.DataFrame(dataEnd1)
                        dfEnd1 = dfSeriesEnd1[0]

                        first_index = dfEnd1[0].split()

                        total_active_high.append(first_index[3])
                        total_reactive_high.append(first_index[4])
                        total_reactive_low.append(first_index[5])

                        for i in range(1, len(dfEnd1)):
                            oneHourDataEnd1 = [changeToFloat(
                                x) for x in dfEnd1[i].split()[1:]]
                            end1Data = end1Data + oneHourDataEnd1

            x = list(divide_chunks(end1Data, time//15))

            final_data = []

            for items in x:
                max_1, min_1, avg_1 = my_max_min_function(items)
                final_data.append(avg_1)

            meter_obj['data'] = final_data

            for item in range(len(final_data)):
                final_data[item] = 4*final_data[item]

            meter_obj['modified_data'] = final_data
            meter_obj['activeHigh'] = total_active_high
            meter_obj['reactiveHigh'] = total_reactive_high
            meter_obj['reactiveLow'] = total_reactive_low
            meter_obj['date'] = date_list

            data_to_send.append(meter_obj)

        return jsonify(data_to_send)


@app.route('/MeterMapping', methods=['GET', 'POST'])
def MeterMapping():

    meter_path = "D:/master.dat"
    fict_meter_path = "D:/FICTMTRS.dat"

    meter_data = pd.read_csv(meter_path, header=None)
    dfSeriesEnd1 = pd.DataFrame(meter_data)
    dfEnd1 = dfSeriesEnd1[0]

    fict_meter_data = pd.read_csv(fict_meter_path, header=None)
    dfSeriesEnd2 = pd.DataFrame(fict_meter_data)
    dfEnd2 = dfSeriesEnd2[0]

    final_list = []
    meter_list = []

    for i in range(2, len(dfEnd1)):
        names = dfEnd1[i].split("  ")[-1]
        meter_name = dfEnd1[i].split()[1]
        meter_code = dfEnd1[i].split()[0]
        meter_list.append(meter_name)

        temp_dict = {
            "Meter_Name": meter_name,
            "Meter_Code": meter_code,
            "Name": names,
            "Type": "Real Meter"
        }
        final_list.append(temp_dict)

    for j in range(2, len(dfEnd2)-1):

        names = dfEnd2[j].split("  ")[-1]
        meter_name = dfEnd2[j].split()[1]
        meter_code = dfEnd2[j].split()[0]
        meter_list.append(meter_name)

        temp_dict = {
            "Meter_Name": meter_name,
            "Meter_Code": meter_code,
            "Name": names,
            "Type": "Fictitious Meter"
        }
        final_list.append(temp_dict)

    res = meter_table.insert_many(final_list)

    return jsonify(res)


# /////////////////////////////////////////////SEM vs SCADA///////////////////////////////////////////////////

@app.route('/SEMvsSCADA', methods=['GET', 'POST'])
def SEMvsSCADA():

    startDate = request.args['startDate']
    startDate_obj = datetime.strptime(startDate, '%Y-%m-%d')
    endDate = request.args['endDate']
    time = int(request.args['time'])
    meter = request.args['meter']
    meter_list = meter.split(",")
    code = request.args['code']
    code = code.split(',')
    folder = request.args['folder']
    offset = int(request.args['offset'])

    startDateObj = datetime.strptime(startDate, "%Y-%m-%d")
    endDateObj = datetime.strptime(endDate, "%Y-%m-%d")

    date_range = [startDateObj+timedelta(days=x)
                  for x in range((endDateObj-startDateObj).days+1)]

    startDateObj = datetime.strptime(startDate, "%Y-%m-%d")
    endDateObj = datetime.strptime(endDate, "%Y-%m-%d")

    allDateTime = [dt.strftime("%d-%m-%Y %H:%M:%S") for dt in
                   datetime_range(startDateObj, endDateObj,
                                  timedelta(minutes=time))]

    data_to_send = {'Date_Time': allDateTime}

    meter_data_list = []
    scada_data_list = []
    percentage_diff = []

    for meters in meter_list:

        meter_data = []

        meters = meters.split("(")
        meterNO = meters[0][:-1]
        meterID = meters[1][:-1]

        meter_obj = {
            'meterNO': meterNO,
            'meterID': meterID
        }

        for it in date_range:

            if (folder == "no"):

                CONNECTION_STRING = "mongodb://10.3.101.179:1434"
                client = MongoClient(CONNECTION_STRING)
                db = client['meterDataArchival']
                Data_Table = db["meterData"+str(it.year)]

                filter = {
                    'date': {
                        '$gte': datetime(it.year, it.month, it.day, 0, 0, 0, tzinfo=timezone.utc),
                        '$lte': datetime(it.year, it.month, it.day, 0, 0, 0, tzinfo=timezone.utc)
                    },
                    'meterNO': meterNO,
                    'meterID': meterID
                }

                cursor = Data_Table.find(
                    filter=filter, projection={'_id': 0, 'data': 1})

                cursor_list = list(cursor)

                if len(cursor_list) > 0:

                    for i in range(len(cursor_list[0]['data'])):
                        if (cursor_list[0]['data'][i] != cursor_list[0]['data'][i]):
                            cursor_list[0]['data'][i] = 0

                    meter_data = meter_data+cursor_list[0]['data']

                else:
                    meter_data = meter_data+[0]*96

            if (folder == "yes"):

                path = "D:/Applications/SVS/svs_be/Meter_Files/"
                mete = meterNO+".MWH"
                full_path = path+it.strftime("%d-%m-%y")

                if (os.path.isdir(full_path)):
                    # f = open(os.path.join(full_path, file),'r')
                    full_path = full_path+"/"+mete

                    dataEnd1 = pd.read_csv(full_path, header=None)
                    dfSeriesEnd1 = pd.DataFrame(dataEnd1)
                    dfEnd1 = dfSeriesEnd1[0]

                    first_index = dfEnd1[0].split()

                    for i in range(1, len(dfEnd1)):
                        oneHourDataEnd1 = [changeToFloat(
                            x) for x in dfEnd1[i].split()[1:]]

                        for i in range(len(oneHourDataEnd1)):
                            if oneHourDataEnd1[i] != oneHourDataEnd1[i]:
                                oneHourDataEnd1[i] = 0

                        meter_data = meter_data + oneHourDataEnd1

                else:
                    meter_data = meter_data+[0]*96

        x = list(divide_chunks(meter_data, time//15))

        final_data = []

        for items in x:
            max_1, min_1, avg_1 = my_max_min_function(items)
            final_data.append(avg_1)

        meter_obj['data'] = final_data

        modified_list = []

        for item in final_data:
            modified_list.append(round(item, 2)*4)

        meter_obj['modified_data'] = modified_list

        meter_data_list.append(meter_obj)

    data_to_send["Meter_data"] = meter_data_list

    for codes in code:

        codes = codes.split(' ')
        codes = codes[0]
        scada_data = []
        final_data = []

        final_dict = {"Code": codes}

        for it in date_range:

            temp_final_data = []
            date_data = []

            filter = {
                'Date': {
                    '$gte': datetime(it.year, it.month, it.day, 0, 0, 0, tzinfo=timezone.utc),
                    '$lte': datetime(it.year, it.month, it.day, 0, 0, 0, tzinfo=timezone.utc)
                },
                'Code': codes
            }

            cursor = Scada_database.find(
                filter=filter, projection={'_id': 0, 'Name': 1, 'Code': 1, 'Data': 1})

            cursor_list = list(cursor)

            if len(cursor_list) > 0:

                for ite in range(len(cursor_list[0]['Data'])):
                    if cursor_list[0]['Data'][ite] != cursor_list[0]['Data'][ite]:
                        cursor_list[0]['Data'][ite] = 0

                    else:
                        cursor_list[0]['Data'][i] = round(
                            cursor_list[0]['Data'][i], 2)

                scada_data = scada_data+cursor_list[0]['Data']

                names = cursor_list[0]['Name']

                if names != names:
                    names = ""

            else:
                scada_data = scada_data+[0]*96

        x = list(divide_chunks(scada_data, time//15))

        for items in x:
            max_1, min_1, avg_1 = my_max_min_function(items)
            final_data.append(avg_1)

        final_dict['Name'] = names

        for item in range(len(final_data)):
            final_data[item] = round(final_data[item], 2)

        final_dict['Data'] = final_data

        scada_data_list.append(final_dict)

    data_to_send["Scada_data"] = scada_data_list

    for o in range(len(data_to_send["Meter_data"][0]["modified_data"])):

        if (data_to_send["Meter_data"][0]["modified_data"][o] == 0):
            percentage_diff.append(0)

        else:

            meter_val = data_to_send["Meter_data"][0]["modified_data"][o]
            sacada_val = data_to_send["Scada_data"][0]["Data"][o]

            if offset >= 0:

                positive_offset = offset
                negative_offset = -1*offset

            else:
                positive_offset = -1*offset
                negative_offset = offset

            if (meter_val >= 0 and sacada_val >= 0):

                if (meter_val < positive_offset or sacada_val < positive_offset):
                    percentage_diff.append(0)

                else:
                    percentage_diff.append(round(100*(data_to_send["Meter_data"][0]["modified_data"][o] -
                                                      data_to_send["Scada_data"][0]["Data"][o])/data_to_send["Meter_data"][0]["modified_data"][o], 2))

            elif (meter_val < 0 and sacada_val < 0):

                if (meter_val > negative_offset or sacada_val > negative_offset):
                    percentage_diff.append(0)

                else:
                    percentage_diff.append(round(100*(data_to_send["Meter_data"][0]["modified_data"][o] -
                                                      data_to_send["Scada_data"][0]["Data"][o])/data_to_send["Meter_data"][0]["modified_data"][o], 2))

    data_to_send["Percentage_diff"] = percentage_diff

    max_diff, min_diff, avg_diff = my_max_min_function(percentage_diff)
    data_to_send["Percentage_max_min"] = [max_diff, min_diff, avg_diff]

    return jsonify(data_to_send)


# /////////////////////////////////////////////SEM vs SCADA///////////////////////////////////////////////////

@app.route('/SEMvsSCADAreport', methods=['GET', 'POST'])
def SEMvsSCADAreport():

    startDate = request.args['startDate']
    startDate_obj = datetime.strptime(startDate, '%Y-%m-%d')
    endDate = request.args['endDate']
    time = int(request.args['time'])
    folder = request.args['folder']
    offset = int(request.args['offset'])

    data_to_send = svsreport(startDate, startDate_obj,
                             endDate, time, folder, offset)

    return jsonify(data_to_send)


@app.route('/letters_zip', methods=['GET', 'POST'])
def letters_zip():

    gen_all_letters()

    # # Parent Directory
    # directory = "D:/Applications/SVS/svs_be/output/ZipFiles"
    # # Remove the Directory
    # try:
    #     print("start")
    #     shutil.rmtree(directory)
    #     print("Done")
    # except:
    #     pass

    startDate = request.args['startDate']
    startDate_obj = datetime.strptime(startDate, '%d-%m-%Y')
    endDate = request.args['endDate']
    endDate_obj = datetime.strptime(endDate, '%d-%m-%Y')

    month_folder = startDate_obj.strftime('%b %y')
    year_folder = startDate_obj.strftime('%Y')

    startDate_obj = startDate_obj.strftime('%d-%m-%Y')
    endDate_obj = endDate_obj.strftime('%d-%m-%Y')

    folder_path = 'output/letter doc/' + year_folder + '/' + \
        month_folder + '/' + startDate_obj + '_to_' + endDate_obj
    # dir_list = os.listdir(folder_path)

    archived = shutil.make_archive(
        "D:/Applications/SVS/svs_be/output/ZipFiles/"+year_folder+'/'+month_folder+'/'+startDate_obj+'_to_'+endDate_obj+"/Letters", 'zip', folder_path)

    return send_file('D:/Applications/SVS/svs_be/output/ZipFiles/'+year_folder+'/'+month_folder+'/'+startDate_obj+'_to_'+endDate_obj+'/Letters.zip', as_attachment=True, download_name='Sem vs Scada Letters '+startDate_obj + '_to_' + endDate_obj+".zip")
    # return ("hi")


@app.route('/GetSvSExcel', methods=['GET', 'POST'])
def GetSvSExcel():

    gen_excel()

    startDate = request.args['startDate']
    endDate = request.args['endDate']

    path = "D:/Applications/SVS/svs_be/output/SVS.xlsx"

    if os.path.exists(path):
        with open(path, "rb") as excel:
            data = excel.read()

        response = Response(
            data, content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')

    return send_file(path, as_attachment=True, download_name='SVS('+startDate+' to '+endDate+').xlsx')

@app.route('/GetErrorExcel', methods=['GET', 'POST'])
def GetErrorExcel():

    gen_error_excel()

    startDate = request.args['startDate']
    endDate = request.args['endDate']

    path = "D:/Applications/SVS/svs_be/Excel_Files/ErrorNames.xlsx"

    if os.path.exists(path):
        with open(path, "rb") as excel:
            data = excel.read()

        response = Response(
            data, content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')

    return send_file(path, as_attachment=True, download_name='SVS_ErrorNames('+startDate+' to '+endDate+').xlsx')


@app.route('/Scada_Delete', methods=['GET', 'POST'])
def Scada_Delete():

    startDate = request.args['startDate']
    endDate = request.args['endDate']

    startDateObj = datetime.strptime(startDate, "%Y-%m-%d")
    endDateObj = datetime.strptime(endDate, "%Y-%m-%d")

    date_range = [startDateObj+timedelta(days=x)
                  for x in range((endDateObj-startDateObj).days+1)]

    try:

        for it in date_range:

            filter = {
                'Date': {
                    '$gte': datetime(it.year, it.month, it.day, 0, 0, 0, tzinfo=timezone.utc),
                    '$lte': datetime(it.year, it.month, it.day, 0, 0, 0, tzinfo=timezone.utc)
                }

            }

            Scada_database.delete_many(filter)

        reply = "Success"

    except:
        reply = "Error"

    return jsonify(reply)


@app.route('/Mapping_Table', methods=['GET', 'POST'])
def Mapping_Table():

    CONNECTION_STRING = "mongodb://mongodb0.erldc.in:27017,mongodb1.erldc.in:27017/?replicaSet=CONSERV"
    client = MongoClient(CONNECTION_STRING)
    db = client['SemVsScada']
    mapping_table = db['mapping_table']

    cursor = mapping_table.find()

    cursor = json.loads(json_util.dumps(cursor))

    cursor_list = list(cursor)

    i = 0

    for item in range(len(cursor_list)):
        try:
            if cursor_list[item+i]['Deleted'] == "Yes":

                cursor_list.pop(item+i)
                i -= 1
        except:
            pass

    return jsonify(cursor_list)


@app.route('/Mapping_Table_Update', methods=['GET', 'POST'])
def Mapping_Table_Update():

    Data = request.json
    person_id= request.args['by']

    CONNECTION_STRING = "mongodb://mongodb0.erldc.in:27017,mongodb1.erldc.in:27017/?replicaSet=CONSERV"
    client = MongoClient(CONNECTION_STRING)
    db = client['SemVsScada']
    mapping_table = db['mapping_table']

    filter = {'_id': ObjectId(Data['_id']['$oid'])}

    Data.pop("_id")
    Data['Edited_by'] = person_id

    newvalues = {"$set": Data}

    try:

        cursor = mapping_table.update_one(filter, newvalues)
        return_val = 'Updated'

    except errors.DuplicateKeyError:

        return_val = 'failed'

    return jsonify(return_val)


@app.route('/Mapping_Table_Delete', methods=['GET', 'POST'])
def Mapping_Table_Delete():

    Data = request.json
    person_id= request.args['by']

    CONNECTION_STRING = "mongodb://mongodb0.erldc.in:27017,mongodb1.erldc.in:27017/?replicaSet=CONSERV"
    client = MongoClient(CONNECTION_STRING)
    db = client['SemVsScada']
    mapping_table = db['mapping_table']

    filter = {'_id': ObjectId(Data['_id']['$oid'])}

    Data.pop("_id")
    Data['Deleted'] = "Yes"
    Data['Deleted_by'] = person_id

    newvalues = {"$set": Data}

    try:

        cursor = mapping_table.update_one(filter, newvalues)
        return_val = 'Deleted'

    except:

        return_val = 'failed'

    return jsonify(return_val)


@app.route('/Mapping_Table_Add', methods=['GET', 'POST'])
def Mapping_Table_Add():

    Data = request.json
    person_id= request.args['by']

    Data['Added_by'] = person_id

    CONNECTION_STRING = "mongodb://mongodb0.erldc.in:27017,mongodb1.erldc.in:27017/?replicaSet=CONSERV"
    client = MongoClient(CONNECTION_STRING)
    db = client['SemVsScada']
    mapping_table = db['mapping_table']

    try:

        mapping_table.insert_one(Data)
        return_val = 'Inserted'

    except errors.DuplicateKeyError:

        return_val = 'duplicate'

    return jsonify(return_val)


if __name__ == '__main__':

    app.run(debug=True, host='0.0.0.0', port=5003)
