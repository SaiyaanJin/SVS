from cmath import nan
from unicodedata import name
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
import shutil
from flask_cors import CORS, cross_origin
from flask import send_from_directory
from pandas.tseries.offsets import MonthEnd
from werkzeug .utils import secure_filename
from zipfile import ZipFile
import numpy as np
from docxtpl import DocxTemplate

app = Flask(__name__)

CORS(app)

Global_letter_data = ""

Global_data = ""

Global_date = ""

Global_error_list = []

def my_max_min_function(somelist):

    max_value = max(somelist)
    min_value = min(somelist)
    avg_value = 0 if len(somelist) == 0 else sum(somelist)/len(somelist)

    max_index = [i for i, val in enumerate(somelist) if val == max_value]
    min_index = [i for i, val in enumerate(somelist) if val == min_value]

    avg_value = avg_value
    max_value = max_value
    min_value = min_value

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
    
def remove_duplicate_objects(arr):
  seen = set()
  new_arr = []
  for obj in arr:
    # Create a hashable representation of the object
    key = tuple(sorted(obj.items())) 
    if key not in seen:
      seen.add(key)
      new_arr.append(obj)
  return new_arr


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


# /////////////////////////////////////////////SEM vs SCADA///////////////////////////////////////////////////

def svsreport(startDate, startDate_obj, endDate, time, folder, offset):

    startDateObj = datetime.strptime(startDate, "%Y-%m-%d")
    endDateObj = datetime.strptime(endDate, "%Y-%m-%d")

    global Global_date
    global Global_error_list
    global Global_letter_data
    global Global_data

    CONNECTION_STRING = "mongodb://10.3.101.179:1434"
    client = MongoClient(CONNECTION_STRING)
    db = client['meterDataArchival']
    

    cursor = mapping_table.find(
        filter={}, projection={'_id': 0})

    keydata = list(cursor)

    i = 0

    for item in range(len(keydata)):
        try:
            if keydata[item+i]['Deleted'] == "Yes":
                keydata.pop(item+i)
                i -= 1
        except:
            pass

    allDateTime = [dt.strftime("%d-%m-%Y %H:%M:%S") for dt in
                datetime_range(startDateObj, endDateObj,
                                timedelta(minutes=time))]

    final_data_to_send = {'Date_Time': allDateTime}
    final_data_to_send1 = []

    df1 = pd.DataFrame.from_dict({'Date_Time': allDateTime})

    Global_date = df1

    BH = []
    DV = []
    GR = []

    JH = []
    MIS_CALC_TO = []
    NTPC_ER_1 = []

    NTPC_ODISHA = []
    PG_ER1 = []
    PG_ER2 = []

    WB = []
    SI = []
    PG_odisha_project = []

    error_names= []

    for item in keydata:

        Feeder_Name = item['Feeder_Name']
        Feeder_Hindi = item['Feeder_Hindi']
        Key_To_End = item['Key_To_End']
        Key_Far_End = item['Key_Far_End']
        Meter_To_End = item['Meter_To_End']
        Meter_Far_End = item['Meter_Far_End']
        Feeder_From = item['Feeder_From']
        To_Feeder = item['To_Feeder']

        semvsscada_dict = {
            'Feeder_Name': item['Feeder_Name'],
            'Feeder_Hindi': item['Feeder_Hindi'],
            'Key_To_End': item['Key_To_End'],
            'Key_Far_End': item['Key_Far_End'],
            'Meter_To_End': item['Meter_To_End'],
            'Meter_Far_End': item['Meter_Far_End'],
            'Feeder_From': item['Feeder_From'],
            'To_Feeder': item['To_Feeder']
        }

        scada_database_data_to = []
        meter_database_data_to = []
        scada_database_data_far = []
        meter_database_data_far = []

        startDateObj = datetime.strptime(startDate, "%Y-%m-%d")
        endDateObj = datetime.strptime(endDate, "%Y-%m-%d")

        date_range = [startDateObj+timedelta(days=x)
                    for x in range((endDateObj-startDateObj).days+1)]

        if ((Key_To_End.split(":")[0] != "No Key" or Key_To_End.split(":")[0] != "Duplicate Key") and (Meter_To_End.split(":")[0] != "No Key" or Meter_To_End.split(":")[0] != "Duplicate Key")):
            try:

                for it in date_range:

                    filter = {
                        'Date': {
                            '$gte': datetime(it.year, it.month, it.day, 0, 0, 0, tzinfo=timezone.utc),
                            '$lte': datetime(it.year, it.month, it.day, 0, 0, 0, tzinfo=timezone.utc)
                        },
                        'Code': Key_To_End
                    }
                    project = {
                        '_id': 0,
                        'Data': 1,
                        'Date': 1,
                    }

                    cursor1 = Scada_database.find(
                        filter=filter, projection=project)

                    data1 = list(cursor1)

                    if len(data1[0]['Data']) > 0:
                        for ite in range(len(data1[0]['Data'])):
                            if data1[0]['Data'][ite] != data1[0]['Data'][ite]:
                                data1[0]['Data'][ite] = 0

                            else:
                                data1[0]['Data'][ite] = round(
                                    data1[0]['Data'][ite], 2)

                        scada_database_data_to = scada_database_data_to + \
                            data1[0]['Data']

                    else:
                        scada_database_data_to = scada_database_data_to + \
                            [0]*96
                        
                        if Feeder_Name not in error_names:
                            error_names.append(Feeder_Name)
                            xyz = semvsscada_dict.copy()

                            try:
                                xyz.pop('Meter_Far_End_data', None)
                            except:
                                pass
                            try:
                                xyz.pop('Meter_To_End_data', None)
                            except:
                                pass
                            try:
                                xyz.pop('Scada_Far_End_data', None)
                            except:
                                pass
                            try:
                                xyz.pop('Scada_To_End_data', None)
                            except:
                                pass
                            Global_error_list.append(xyz)

                semvsscada_dict['Scada_To_End_data'] = scada_database_data_to

                if folder == "no":

                    for it in date_range:

                        filter = {
                            'date': {
                                '$gte': datetime(it.year, it.month, it.day, 0, 0, 0, tzinfo=timezone.utc),
                                '$lte': datetime(it.year, it.month, it.day, 0, 0, 0, tzinfo=timezone.utc)
                            },
                            'meterID': Meter_To_End
                        }
                        project = {
                            '_id': 0,
                            'data': 1,
                            'date': 1,
                        }

                        Data_Table = db["meterData"+str(it.year)]

                        cursor2 = Data_Table.find(
                            filter=filter, projection=project)

                        data2 = list(cursor2)

                        if len(data2[0]['data']) > 0:
                            for item in range(len(data2[0]['data'])):
                                if data2[0]['data'][item] != data2[0]['data'][item]:
                                    data2[0]['data'][item] = 0

                                else:
                                    data2[0]['data'][item] = 4 * \
                                        data2[0]['data'][item]

                                    data2[0]['data'][item] = round(
                                        data2[0]['data'][item], 2)

                            meter_database_data_to = meter_database_data_to + \
                                data2[0]['data']

                        else:
                            meter_database_data_to = meter_database_data_to + \
                                [0]*96
                            
                            if Feeder_Name not in error_names:
                                error_names.append(Feeder_Name)
                                xyz = semvsscada_dict.copy()

                                try:
                                    xyz.pop('Meter_Far_End_data', None)
                                except:
                                    pass
                                try:
                                    xyz.pop('Meter_To_End_data', None)
                                except:
                                    pass
                                try:
                                    xyz.pop('Scada_Far_End_data', None)
                                except:
                                    pass
                                try:
                                    xyz.pop('Scada_To_End_data', None)
                                except:
                                    pass
                                Global_error_list.append(xyz)

                    semvsscada_dict['Meter_To_End_data'] = meter_database_data_to

                if folder == "yes":

                    path = "D:/Applications/SVS/svs_be/Meter_Files/"

                    filter = {'Meter_Code': Meter_To_End}

                    cursor2 = meter_table.find(
                        filter=filter, projection={'_id': 0})

                    cursor2_list = list(cursor2)

                    meters = cursor2_list[0]["Meter_Name"]+".MWH"

                    for dates in ([startDateObj+timedelta(days=x) for x in range((endDateObj-startDateObj).days+1)]):

                        full_path = path+dates.strftime("%d-%m-%y")

                        if (os.path.isdir(full_path)):

                            full_path = full_path+"/"+meters

                            dataEnd1 = pd.read_csv(full_path, header=None)
                            dfSeriesEnd1 = pd.DataFrame(dataEnd1)
                            dfEnd1 = dfSeriesEnd1[0]

                            for i in range(1, len(dfEnd1)):
                                oneHourDataEnd1 = [changeToFloat(
                                    x) for x in dfEnd1[i].split()[1:]]

                                for item in range(len(oneHourDataEnd1)):
                                    if oneHourDataEnd1[item] != oneHourDataEnd1[item]:
                                        oneHourDataEnd1[item] = 0

                                    else:
                                        oneHourDataEnd1[item] = 4 * \
                                            oneHourDataEnd1[item]

                                        oneHourDataEnd1[item] = round(
                                            oneHourDataEnd1[item], 2)

                                meter_database_data_to = meter_database_data_to + oneHourDataEnd1

                    semvsscada_dict['Meter_To_End_data'] = meter_database_data_to

            except:
                semvsscada_dict['Scada_To_End_data'] = [0]*(len(date_range)*96)
                semvsscada_dict['Meter_To_End_data'] = [0]*(len(date_range)*96)

                if Feeder_Name not in error_names:
                    error_names.append(Feeder_Name)
                    xyz = semvsscada_dict.copy()

                    try:
                        xyz.pop('Meter_Far_End_data', None)
                    except:
                        pass
                    try:
                        xyz.pop('Meter_To_End_data', None)
                    except:
                        pass
                    try:
                        xyz.pop('Scada_Far_End_data', None)
                    except:
                        pass
                    try:
                        xyz.pop('Scada_To_End_data', None)
                    except:
                        pass
                    Global_error_list.append(xyz)

        else:
            semvsscada_dict['Scada_To_End_data'] = [0]*(len(date_range)*96)
            semvsscada_dict['Meter_To_End_data'] = [0]*(len(date_range)*96)

            if Feeder_Name not in error_names:
                error_names.append(Feeder_Name)
                xyz = semvsscada_dict.copy()

                try:
                    xyz.pop('Meter_Far_End_data', None)
                except:
                    pass
                try:
                    xyz.pop('Meter_To_End_data', None)
                except:
                    pass
                try:
                    xyz.pop('Scada_Far_End_data', None)
                except:
                    pass
                try:
                    xyz.pop('Scada_To_End_data', None)
                except:
                    pass
                Global_error_list.append(xyz)

        if ((Key_Far_End.split(":")[0] != "No Key" or Key_Far_End.split(":")[0] != "Duplicate Key") and (Meter_Far_End.split(":")[0] != "No Key" or Meter_Far_End.split(":")[0] != "Duplicate Key")):

            try:

                scada_database_data_to = []
                meter_database_data_to = []

                for it in date_range:

                    filter = {
                        'Date': {
                            '$gte': datetime(it.year, it.month, it.day, 0, 0, 0, tzinfo=timezone.utc),
                            '$lte': datetime(it.year, it.month, it.day, 0, 0, 0, tzinfo=timezone.utc)
                        },
                        'Code': Key_Far_End
                    }
                    project = {
                        '_id': 0,
                        'Data': 1,
                        'Date': 1,
                    }

                    cursor1 = Scada_database.find(
                        filter=filter, projection=project)

                    data1 = list(cursor1)

                    if len(data1[0]['Data']) > 0:
                        for ite in range(len(data1[0]['Data'])):
                            if data1[0]['Data'][ite] != data1[0]['Data'][ite]:
                                data1[0]['Data'][ite] = 0

                            else:
                                data1[0]['Data'][ite] = round(
                                    data1[0]['Data'][ite], 2)

                        scada_database_data_far = scada_database_data_far + \
                            data1[0]['Data']

                    else:
                        scada_database_data_far = scada_database_data_far + \
                            [0]*96
                        
                        if Feeder_Name not in error_names:
                            error_names.append(Feeder_Name)
                            xyz = semvsscada_dict.copy()

                            try:
                                xyz.pop('Meter_Far_End_data', None)
                            except:
                                pass
                            try:
                                xyz.pop('Meter_To_End_data', None)
                            except:
                                pass
                            try:
                                xyz.pop('Scada_Far_End_data', None)
                            except:
                                pass
                            try:
                                xyz.pop('Scada_To_End_data', None)
                            except:
                                pass
                            Global_error_list.append(xyz)

                semvsscada_dict['Scada_Far_End_data'] = scada_database_data_far

                if folder == "no":

                    for it in date_range:

                        filter = {
                            'date': {
                                '$gte': datetime(it.year, it.month, it.day, 0, 0, 0, tzinfo=timezone.utc),
                                '$lte': datetime(it.year, it.month, it.day, 0, 0, 0, tzinfo=timezone.utc)
                            },
                            'meterID': Meter_Far_End
                        }
                        project = {
                            '_id': 0,
                            'data': 1,
                            'date': 1,
                        }

                        Data_Table = db["meterData"+str(it.year)]

                        cursor2 = Data_Table.find(
                            filter=filter, projection=project)

                        data2 = list(cursor2)

                        if len(data2[0]['data']) > 0:
                            for item in range(len(data2[0]['data'])):
                                if data2[0]['data'][item] != data2[0]['data'][item]:
                                    data2[0]['data'][item] = 0

                                else:
                                    data2[0]['data'][item] = 4 * \
                                        data2[0]['data'][item]

                                    data2[0]['data'][item] = round(
                                        data2[0]['data'][item], 2)

                            meter_database_data_far = meter_database_data_far + \
                                data2[0]['data']

                        else:
                            meter_database_data_far = meter_database_data_far + \
                                [0]*96
                            
                            if Feeder_Name not in error_names:
                                error_names.append(Feeder_Name)
                                xyz = semvsscada_dict.copy()

                                try:
                                    xyz.pop('Meter_Far_End_data', None)
                                except:
                                    pass
                                try:
                                    xyz.pop('Meter_To_End_data', None)
                                except:
                                    pass
                                try:
                                    xyz.pop('Scada_Far_End_data', None)
                                except:
                                    pass
                                try:
                                    xyz.pop('Scada_To_End_data', None)
                                except:
                                    pass
                                Global_error_list.append(xyz)

                    semvsscada_dict['Meter_Far_End_data'] = meter_database_data_far

                if folder == "yes":

                    path = "D:/Applications/SVS/svs_be/Meter_Files/"

                    filter = {'Meter_Code': Meter_Far_End}

                    cursor2 = meter_table.find(
                        filter=filter, projection={'_id': 0})

                    cursor2_list = list(cursor2)

                    meters = cursor2_list[0]["Meter_Name"]+".MWH"

                    for dates in ([startDateObj+timedelta(days=x) for x in range((endDateObj-startDateObj).days+1)]):

                        full_path = path+dates.strftime("%d-%m-%y")

                        if (os.path.isdir(full_path)):

                            full_path = full_path+"/"+meters

                            dataEnd1 = pd.read_csv(full_path, header=None)
                            dfSeriesEnd1 = pd.DataFrame(dataEnd1)
                            dfEnd1 = dfSeriesEnd1[0]

                            for i in range(1, len(dfEnd1)):
                                oneHourDataEnd1 = [changeToFloat(
                                    x) for x in dfEnd1[i].split()[1:]]

                                for item in range(len(oneHourDataEnd1)):
                                    if oneHourDataEnd1[item] != oneHourDataEnd1[item]:
                                        oneHourDataEnd1[item] = 0

                                    else:
                                        oneHourDataEnd1[item] = 4 * \
                                            oneHourDataEnd1[item]

                                        oneHourDataEnd1[item] = round(
                                            oneHourDataEnd1[item], 2)
                                meter_database_data_far = meter_database_data_far + oneHourDataEnd1

                    semvsscada_dict['Meter_Far_End_data'] = meter_database_data_far

            except:
                semvsscada_dict['Scada_Far_End_data'] = [
                    0]*(len(date_range)*96)
                semvsscada_dict['Meter_Far_End_data'] = [
                    0]*(len(date_range)*96)
                
                if Feeder_Name not in error_names:
                    error_names.append(Feeder_Name)
                    xyz = semvsscada_dict.copy()

                    try:
                        xyz.pop('Meter_Far_End_data', None)
                    except:
                        pass
                    try:
                        xyz.pop('Meter_To_End_data', None)
                    except:
                        pass
                    try:
                        xyz.pop('Scada_Far_End_data', None)
                    except:
                        pass
                    try:
                        xyz.pop('Scada_To_End_data', None)
                    except:
                        pass
                    Global_error_list.append(xyz)

        else:
            semvsscada_dict['Scada_Far_End_data'] = [0]*(len(date_range)*96)
            semvsscada_dict['Meter_Far_End_data'] = [0]*(len(date_range)*96)

            if Feeder_Name not in error_names:
                error_names.append(Feeder_Name)
                xyz = semvsscada_dict.copy()

                try:
                    xyz.pop('Meter_Far_End_data', None)
                except:
                    pass
                try:
                    xyz.pop('Meter_To_End_data', None)
                except:
                    pass
                try:
                    xyz.pop('Scada_Far_End_data', None)
                except:
                    pass
                try:
                    xyz.pop('Scada_To_End_data', None)
                except:
                    pass
                Global_error_list.append(xyz)

        to_end_percent = []
        far_end_percent = []

        sem_percent = []
        scada_percent = []

        actual_to_end_percent = []
        actual_far_end_percent = []

        if (semvsscada_dict["Scada_To_End_data"] == "No Data Found" or semvsscada_dict["Meter_To_End_data"] == "No Data Found"):

            to_end_percent.append(0)
            actual_to_end_percent.append(0)

            if Feeder_Name not in error_names:
                error_names.append(Feeder_Name)
                xyz = semvsscada_dict.copy()

                try:
                    xyz.pop('Meter_Far_End_data', None)
                except:
                    pass
                try:
                    xyz.pop('Meter_To_End_data', None)
                except:
                    pass
                try:
                    xyz.pop('Scada_Far_End_data', None)
                except:
                    pass
                try:
                    xyz.pop('Scada_To_End_data', None)
                except:
                    pass
                Global_error_list.append(xyz)

        else:

            count = 0
            total_val = 0
            nonzero_val= 0

            # scada_max_value = round(
            #     (abs(max(semvsscada_dict["Scada_To_End_data"])))*0.3, 2)

            for item in semvsscada_dict["Scada_To_End_data"]:
                item = abs(item)

                if item != 0:
                    total_val = item+total_val
                    count += 1
                    nonzero_val= item

            if count != 0:
                avg_scada_to = round(abs(total_val/count), 2)
                
                if avg_scada_to== nonzero_val:
                    if Feeder_Name not in error_names:
                        error_names.append(Feeder_Name)
                        xyz = semvsscada_dict.copy()

                        try:
                            xyz.pop('Meter_Far_End_data', None)
                        except:
                            pass
                        try:
                            xyz.pop('Meter_To_End_data', None)
                        except:
                            pass
                        try:
                            xyz.pop('Scada_Far_End_data', None)
                        except:
                            pass
                        try:
                            xyz.pop('Scada_To_End_data', None)
                        except:
                            pass
                        Global_error_list.append(xyz)

            else:
                avg_scada_to = 0
                if Feeder_Name not in error_names:
                    error_names.append(Feeder_Name)
                    xyz = semvsscada_dict.copy()

                    try:
                        xyz.pop('Meter_Far_End_data', None)
                    except:
                        pass
                    try:
                        xyz.pop('Meter_To_End_data', None)
                    except:
                        pass
                    try:
                        xyz.pop('Scada_Far_End_data', None)
                    except:
                        pass
                    try:
                        xyz.pop('Scada_To_End_data', None)
                    except:
                        pass
                    Global_error_list.append(xyz)

            count1 = 0
            total_val1 = 0
            nonzero_val1= 0

            # scada_max_value = round(
            #     (abs(max(semvsscada_dict["Scada_To_End_data"])))*0.3, 2)

            for item in semvsscada_dict["Meter_To_End_data"]:
                item = abs(item)

                if item != 0:
                    total_val1 = item+total_val1
                    count1 += 1
                    nonzero_val1= item

            if count1 != 0:
                avg_meter_to = round(abs(total_val1/count1), 2)
                
                if avg_meter_to== nonzero_val1:
                    if Feeder_Name not in error_names:
                        error_names.append(Feeder_Name)
                        xyz = semvsscada_dict.copy()

                        try:
                            xyz.pop('Meter_Far_End_data', None)
                        except:
                            pass
                        try:
                            xyz.pop('Meter_To_End_data', None)
                        except:
                            pass
                        try:
                            xyz.pop('Scada_Far_End_data', None)
                        except:
                            pass
                        try:
                            xyz.pop('Scada_To_End_data', None)
                        except:
                            pass
                        Global_error_list.append(xyz)

            else:
                avg_meter_to = 0
                if Feeder_Name not in error_names:
                    error_names.append(Feeder_Name)
                    xyz = semvsscada_dict.copy()

                    try:
                        xyz.pop('Meter_Far_End_data', None)
                    except:
                        pass
                    try:
                        xyz.pop('Meter_To_End_data', None)
                    except:
                        pass
                    try:
                        xyz.pop('Scada_Far_End_data', None)
                    except:
                        pass
                    try:
                        xyz.pop('Scada_To_End_data', None)
                    except:
                        pass
                    Global_error_list.append(xyz)

            count_scada=0
            count_sem=0
            
            for i in range(len(allDateTime)):

                x1 = semvsscada_dict["Meter_To_End_data"][i]
                y1 = semvsscada_dict["Scada_To_End_data"][i]
                x2 = semvsscada_dict["Meter_Far_End_data"][i]
                y2 = semvsscada_dict["Scada_Far_End_data"][i]

                if y1!=0:
                    scada_block_wise= abs(round(
                                    (100*(abs(y1) - abs(y2))/max(abs(y1),abs(y2))), 2))
                    count_scada+=1
                else:
                    scada_block_wise= 0

                if x1!=0:
                    sem_block_wise= abs(round(
                                    (100*(abs(x1) - abs(x2))/max(abs(x1),abs(x2))), 2))
                    count_sem+=1
                else:
                    sem_block_wise= 0
                
                scada_percent.append(scada_block_wise)
                sem_percent.append(sem_block_wise)

                if i != 0:

                    if Feeder_Name == "BH_DRAWAL" or Feeder_Name == "DV_DRAWAL" or Feeder_Name == "GR_DRAWAL" or Feeder_Name == "WB_DRAWAL" or Feeder_Name == "JH_DRAWAL" or Feeder_Name == "SI_DRAWAL":
                        semvsscada_dict["Meter_To_End_data"][i] = abs(
                            semvsscada_dict["Meter_To_End_data"][i])

                    if semvsscada_dict["Meter_To_End_data"][i] == semvsscada_dict["Meter_To_End_data"][i-1] or semvsscada_dict["Scada_To_End_data"][i] == semvsscada_dict["Scada_To_End_data"][i-1]:
                        to_end_percent.append(0)
                        actual_to_end_percent.append(0)

                    elif semvsscada_dict["Meter_To_End_data"][i] == 0 or semvsscada_dict["Scada_To_End_data"][i] == 0:
                        to_end_percent.append(0)
                        actual_to_end_percent.append(0)

                    # elif (abs(semvsscada_dict["Scada_To_End_data"][i]) <= scada_max_value):
                    #     to_end_percent.append(0)

                    elif (abs(semvsscada_dict["Meter_To_End_data"][i]) <= abs(offset)) or (abs(semvsscada_dict["Scada_To_End_data"][i]) <= abs(offset)):
                        to_end_percent.append(0)
                        actual_to_end_percent.append(0)

                    else:

                        x = abs(semvsscada_dict["Meter_To_End_data"][i])
                        y = abs(semvsscada_dict["Scada_To_End_data"][i])

                        if abs(x-y) <= 5:
                            to_percent = 0
                            actual_to_end_percent.append(0)
                        else:
                            to_percent = abs(round(
                                (100*(x - y)/x), 2))
                            actual_to_end_percent.append(to_percent)
                            if to_percent >= 20:
                                to_percent = 0

                        to_end_percent.append(to_percent)

                else:

                    if Feeder_Name == "BH_DRAWAL" or Feeder_Name == "DV_DRAWAL" or Feeder_Name == "GR_DRAWAL" or Feeder_Name == "WB_DRAWAL" or Feeder_Name == "JH_DRAWAL" or Feeder_Name == "SI_DRAWAL":
                        semvsscada_dict["Meter_To_End_data"][i] = abs(
                            semvsscada_dict["Meter_To_End_data"][i])

                    elif semvsscada_dict["Meter_To_End_data"][i] == 0 or semvsscada_dict["Scada_To_End_data"][i] == 0:
                        to_end_percent.append(0)
                        actual_to_end_percent.append(0)

                    elif (abs(semvsscada_dict["Meter_To_End_data"][i]) <= abs(offset)) or (abs(semvsscada_dict["Scada_To_End_data"][i]) <= abs(offset)):
                        to_end_percent.append(0)
                        actual_to_end_percent.append(0)

                    else:

                        x = abs(semvsscada_dict["Meter_To_End_data"][i])
                        y = abs(semvsscada_dict["Scada_To_End_data"][i])

                        if abs(x-y) <= 5:
                            to_percent = 0
                            actual_to_end_percent.append(0)
                        else:
                            to_percent = abs(round(
                                (100*(x - y)/x), 2))
                            actual_to_end_percent.append(to_percent)
                            if to_percent >= 20:
                                to_percent = 0

                        to_end_percent.append(to_percent)

        if (semvsscada_dict["Scada_Far_End_data"] == "No Data Found" or semvsscada_dict["Meter_Far_End_data"] == "No Data Found"):
            
            far_end_percent.append(0)
            actual_far_end_percent.append(0)

        else:

            count = 0
            total_val = 0
            nonzero_val= 0

            # scada_max_value = round(
            #     (abs(max(semvsscada_dict["Scada_To_End_data"])))*0.3, 2)

            for item in semvsscada_dict["Scada_Far_End_data"]:
                item = abs(item)

                if item != 0:
                    total_val = item+total_val
                    count += 1
                    nonzero_val= item

            if count != 0:
                avg_scada_to = round(abs(total_val/count), 2)
                
                if avg_scada_to== nonzero_val:
                    if Feeder_Name not in error_names:
                        error_names.append(Feeder_Name)
                        xyz = semvsscada_dict.copy()

                        try:
                            xyz.pop('Meter_Far_End_data', None)
                        except:
                            pass
                        try:
                            xyz.pop('Meter_To_End_data', None)
                        except:
                            pass
                        try:
                            xyz.pop('Scada_Far_End_data', None)
                        except:
                            pass
                        try:
                            xyz.pop('Scada_To_End_data', None)
                        except:
                            pass
                        Global_error_list.append(xyz)

            else:
                avg_scada_to = 0
                if Feeder_Name not in error_names:
                    error_names.append(Feeder_Name)
                    xyz = semvsscada_dict.copy()

                    try:
                        xyz.pop('Meter_Far_End_data', None)
                    except:
                        pass
                    try:
                        xyz.pop('Meter_To_End_data', None)
                    except:
                        pass
                    try:
                        xyz.pop('Scada_Far_End_data', None)
                    except:
                        pass
                    try:
                        xyz.pop('Scada_To_End_data', None)
                    except:
                        pass
                    Global_error_list.append(xyz)

            count1 = 0
            total_val1 = 0
            nonzero_val1= 0

            # scada_max_value = round(
            #     (abs(max(semvsscada_dict["Scada_To_End_data"])))*0.3, 2)

            for item in semvsscada_dict["Meter_Far_End_data"]:
                item = abs(item)

                if item != 0:
                    total_val1 = item+total_val1
                    count1 += 1
                    nonzero_val1= item

            if count1 != 0:
                avg_meter_to = round(abs(total_val1/count1), 2)
                
                if avg_meter_to== nonzero_val1:
                    if Feeder_Name not in error_names:
                        error_names.append(Feeder_Name)
                        xyz = semvsscada_dict.copy()

                        try:
                            xyz.pop('Meter_Far_End_data', None)
                        except:
                            pass
                        try:
                            xyz.pop('Meter_To_End_data', None)
                        except:
                            pass
                        try:
                            xyz.pop('Scada_Far_End_data', None)
                        except:
                            pass
                        try:
                            xyz.pop('Scada_To_End_data', None)
                        except:
                            pass
                        Global_error_list.append(xyz)

            else:
                avg_meter_to = 0
                if Feeder_Name not in error_names:
                    error_names.append(Feeder_Name)
                    xyz = semvsscada_dict.copy()

                    try:
                        xyz.pop('Meter_Far_End_data', None)
                    except:
                        pass
                    try:
                        xyz.pop('Meter_To_End_data', None)
                    except:
                        pass
                    try:
                        xyz.pop('Scada_Far_End_data', None)
                    except:
                        pass
                    try:
                        xyz.pop('Scada_To_End_data', None)
                    except:
                        pass
                    Global_error_list.append(xyz)
                    

            for i in range(len(semvsscada_dict["Scada_Far_End_data"])):

                if i != 0:

                    if Feeder_Name == "BH_DRAWAL" or Feeder_Name == "DV_DRAWAL" or Feeder_Name == "GR_DRAWAL" or Feeder_Name == "WB_DRAWAL" or Feeder_Name == "JH_DRAWAL" or Feeder_Name == "SI_DRAWAL":
                        semvsscada_dict["Meter_Far_End_data"][i] = abs(
                            semvsscada_dict["Meter_Far_End_data"][i])

                    if semvsscada_dict["Meter_Far_End_data"][i] == semvsscada_dict["Meter_Far_End_data"][i-1] or semvsscada_dict["Scada_Far_End_data"][i] == semvsscada_dict["Scada_Far_End_data"][i-1]:
                        far_end_percent.append(0)
                        actual_far_end_percent.append(0)

                    elif semvsscada_dict["Meter_Far_End_data"][i] == 0 or semvsscada_dict["Scada_Far_End_data"][i] == 0:
                        far_end_percent.append(0)
                        actual_far_end_percent.append(0)

                    # elif (abs(semvsscada_dict["Scada_Far_End_data"][i]) <= scada_max_value):
                    #     far_end_percent.append(0)

                    elif (abs(semvsscada_dict["Meter_Far_End_data"][i]) <= abs(offset)) or (abs(semvsscada_dict["Scada_Far_End_data"][i]) <= abs(offset)):
                        far_end_percent.append(0)
                        actual_far_end_percent.append(0)

                    else:

                        x = abs(semvsscada_dict["Meter_Far_End_data"][i])
                        y = abs(semvsscada_dict["Scada_Far_End_data"][i])

                        if abs(x-y) <= 5:
                            far_percent = 0
                            actual_far_end_percent.append(0)
                        else:
                            far_percent = abs(round((100*(x - y)/x), 2))
                            actual_far_end_percent.append(far_percent)
                            if far_percent > 20:
                                far_percent = 0

                        far_end_percent.append(far_percent)

                else:

                    if Feeder_Name == "BH_DRAWAL" or Feeder_Name == "DV_DRAWAL" or Feeder_Name == "GR_DRAWAL" or Feeder_Name == "WB_DRAWAL" or Feeder_Name == "JH_DRAWAL" or Feeder_Name == "SI_DRAWAL":
                        semvsscada_dict["Meter_Far_End_data"][i] = abs(
                            semvsscada_dict["Meter_Far_End_data"][i])

                    if semvsscada_dict["Meter_Far_End_data"][i] == 0 or semvsscada_dict["Scada_Far_End_data"][i] == 0:
                        far_end_percent.append(0)
                        actual_far_end_percent.append(0)

                    elif (abs(semvsscada_dict["Meter_Far_End_data"][i]) <= abs(offset)) or (abs(semvsscada_dict["Scada_Far_End_data"][i]) <= abs(offset)):
                        far_end_percent.append(0)
                        actual_far_end_percent.append(0)

                    else:

                        x = abs(semvsscada_dict["Meter_Far_End_data"][i])
                        y = abs(semvsscada_dict["Scada_Far_End_data"][i])

                        if abs(x-y) <= 5:
                            far_percent = 0
                            actual_far_end_percent.append(0)
                        else:
                            far_percent = abs(round((100*(x - y)/x), 2))
                            actual_far_end_percent.append(far_percent)
                            if far_percent > 20:
                                far_percent = 0

                        far_end_percent.append(far_percent)

        to_max, to_min, to_avg = my_max_min_function(to_end_percent)
        far_max, far_min, far_avg = my_max_min_function(far_end_percent)

        # to_avg = sum(to_end_percent)/len(to_end_percent)
        # far_avg = sum(far_end_percent)/len(far_end_percent)

        actual_to_avg = sum(actual_to_end_percent)/len(actual_to_end_percent)
        actual_far_avg = sum(actual_far_end_percent)/len(actual_far_end_percent)

        if count_sem!=0:
            sem_avg= min(round(sum(sem_percent)/count_sem,2),100)
        else:
            sem_avg=0
        
        if count_scada!=0:
            scada_avg= min(round(sum(scada_percent)/count_scada,2),100)
        else:
            scada_avg=0

        if actual_to_avg>=20 or actual_far_avg>=20:
            if Feeder_Name not in error_names:
                error_names.append(Feeder_Name)
                xyz = semvsscada_dict.copy()

                try:
                    xyz.pop('Meter_Far_End_data', None)
                except:
                    pass
                try:
                    xyz.pop('Meter_To_End_data', None)
                except:
                    pass
                try:
                    xyz.pop('Scada_Far_End_data', None)
                except:
                    pass
                try:
                    xyz.pop('Scada_To_End_data', None)
                except:
                    pass
                Global_error_list.append(xyz)


        semvsscada_dict['to_end_percent'] = actual_to_end_percent
        semvsscada_dict['far_end_percent'] = actual_far_end_percent
        semvsscada_dict['to_end_max_val'] = to_max[0]
        semvsscada_dict['to_end_min_val'] = to_min[0]
        semvsscada_dict['to_end_avg_val'] = min(round(actual_to_avg, 2),100)
        semvsscada_dict['far_end_max_val'] = far_max[0]
        semvsscada_dict['far_end_min_val'] = far_min[0]
        semvsscada_dict['far_end_avg_val'] = min(round(actual_far_avg, 2),100)
        semvsscada_dict['scada_error'] = scada_percent
        semvsscada_dict['sem_error'] = sem_percent
        semvsscada_dict['sem_avg'] = sem_avg
        semvsscada_dict['scada_avg'] = scada_avg
        final_data_to_send1.append(semvsscada_dict)

        lookupDictionary = {
            'BH': BH,
            'DV': DV,
            'GR': GR,
            'JH': JH,
            'MIS_CALC_TO': MIS_CALC_TO,
            'NTPC_ER_1': NTPC_ER_1,
            'NTPC_ODISHA': NTPC_ODISHA,
            'PG_ER1': PG_ER1,
            'PG_ER2': PG_ER2,
            'WB': WB,
            'SI': SI,
            'PG_odisha_project': PG_odisha_project
        }

        if semvsscada_dict['to_end_avg_val'] > 3:
            constituent_name = semvsscada_dict['Feeder_From']
            constituent_list = lookupDictionary.get(constituent_name)
            if (constituent_list is not None) and (constituent_name not in lookupDictionary[constituent_name]):
                lookupDictionary[constituent_name].append(
                    [semvsscada_dict['Feeder_Name'],0])

        if semvsscada_dict['far_end_avg_val'] > 3:
            constituent_name = semvsscada_dict['To_Feeder']
            constituent_list = lookupDictionary.get(constituent_name)
            if (constituent_list is not None) and (constituent_name not in lookupDictionary[constituent_name]):
                lookupDictionary[constituent_name].append(
                    [semvsscada_dict['Feeder_Name'],1])

    final_data_to_send['BH'] = BH
    final_data_to_send['DV'] = DV
    final_data_to_send['GR'] = GR

    final_data_to_send['JH'] = JH
    final_data_to_send['MIS_CALC_TO'] = MIS_CALC_TO
    final_data_to_send['NTPC_ER_1'] = NTPC_ER_1

    final_data_to_send['NTPC_ODISHA'] = NTPC_ODISHA
    final_data_to_send['PG_ER1'] = PG_ER1
    final_data_to_send['PG_ER2'] = PG_ER2

    final_data_to_send['WB'] = WB
    final_data_to_send['SI'] = SI
    final_data_to_send['PG_odisha_project'] = PG_odisha_project

    Global_letter_data = final_data_to_send.copy()
    Global_data = final_data_to_send1

    final_data_to_send['Data'] = final_data_to_send1
    return ([final_data_to_send,error_names])
    

def gen_error_excel():

    global Global_error_list
    name_list= Global_error_list

    try:
        os.remove('D:/Applications/SVS/svs_be/Excel_Files/ErrorNames.xlsx')
    except:
        pass

    name_list= remove_duplicate_objects(name_list)

    # print(pd.DataFrame(name_list))
    if len(name_list) > 0:
        merged = pd.DataFrame(name_list)
        merged.to_excel(
            "D:/Applications/SVS/svs_be/Excel_Files/ErrorNames.xlsx", index=None)

        path = "D:/Applications/SVS/svs_be/Excel_Files/ErrorNames.xlsx"

        if os.path.exists(path):
            with open(path, "rb") as excel:
                data = excel.read()

            response = Response(
                data, content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
            return send_file('D:/Applications/SVS/svs_be/Excel_Files/ErrorNames.xlsx', as_attachment=True, download_name='ErrorNames.xlsx')
        else:
            return Response('Some error occured!')

    else:
        return jsonify("No Data to Download")


def gen_all_letters():

    global Global_letter_data

    data_list = Global_letter_data

    dt = date.today()
    cur_dt = dt.strftime('%d-%m-%Y')
    start_dt = datetime.strptime(
        data_list['Date_Time'][0], '%d-%m-%Y %H:%M:%S')
    end_dt = datetime.strptime(data_list['Date_Time'][-1], '%d-%m-%Y %H:%M:%S')
    month_folder = start_dt.strftime('%b %y')
    year_folder = start_dt.strftime('%Y')

    start_dt = (datetime.strptime(
        data_list['Date_Time'][0], '%d-%m-%Y %H:%M:%S')).strftime('%d-%m-%Y')
    end_dt = (datetime.strptime(
        data_list['Date_Time'][-1], '%d-%m-%Y %H:%M:%S')).strftime('%d-%m-%Y')

    si_list = data_list['SI']
    gr_list = data_list["GR"]
    dvc_list = data_list["DV"]
    bh_list = data_list["BH"]
    wb_list = data_list["WB"]
    pg_er3_list = data_list["PG_odisha_project"]
    pg_er2_list = data_list["PG_ER2"]
    pg_er1_list = data_list["PG_ER1"]
    jh_list = data_list["JH"]

    cursor = mapping_table.find(
        filter={}, projection={'_id': 0, 'Feeder_Name': 1, 'Feeder_Hindi': 1})

    keydata = list(cursor)

    feeders = {}

    for row in keydata:
        x = row['Feeder_Name']
        y = row['Feeder_Hindi']
        feeders[x] = y

    const_dict = {'si': [si_list, {}], 'gr': [gr_list, {}], 'dvc': [dvc_list, {}], 'bh': [bh_list, {}], 'wb': [
        wb_list, {}], 'pg_er3': [pg_er3_list, {}], 'pg_er2': [pg_er2_list, {}], 'pg_er1': [pg_er1_list, {}], 'jh': [jh_list, {}]}

    for constituent in const_dict.keys():
        const_lst = const_dict[constituent][0]

        for lines in const_lst:

            if lines[-1]== 0:
                lines= lines[0]
                const_dict[constituent][1][lines] = feeders[lines]
                    
            else:

                lines= lines[0]
                if "_ICT" not in lines:
                
                    line_var = lines.split('_')
                    x = line_var[1]
                    line_var[1], line_var[2] = line_var[2], x
                    rev_line = '_'.join(line_var)

                    line_var_h = feeders[lines].split('_')
                    x_h = line_var_h[1]
                    line_var_h[1], line_var_h[2] = line_var_h[2], x_h
                    rev_line_h = '_'.join(line_var_h)

                    const_dict[constituent][1][rev_line] = rev_line_h

                else:
                    continue
                    lines2= lines
                    lines = lines[:-8]
                    
                    line_var = lines.split('_')
                    if len(line_var)==1:
                        print(lines2)
                    x = line_var[1]
                    line_var[1], line_var[2] = line_var[2], x
                    rev_line = '_'.join(line_var)

                    line_var_h = feeders[lines].split('_')
                    x_h = line_var_h[1]
                    line_var_h[1], line_var_h[2] = line_var_h[2], x_h
                    rev_line_h = '_'.join(line_var_h)

                    const_dict[constituent][1][rev_line] = rev_line_h
        # for lines in const_lst:
        #     if lines[-7:] == "(other)" and "_ICT" not in lines:
        #         lines = lines[:-8]
        #         line_var = lines.split('_')
        #         x = line_var[1]
        #         line_var[1], line_var[2] = line_var[2], x
        #         rev_line = '_'.join(line_var)

        #         line_var_h = feeders[lines].split('_')
        #         x_h = line_var_h[1]
        #         line_var_h[1], line_var_h[2] = line_var_h[2], x_h
        #         rev_line_h = '_'.join(line_var_h)

        #         const_dict[constituent][1][rev_line] = rev_line_h
        #     else:
        #         const_dict[constituent][1][lines] = feeders[lines]

    for k in const_dict.keys():
        const_dict[k][1] = dict(sorted(const_dict[k][1].items(), reverse=True))

    try:
        os.makedirs('output/letter doc/{}'.format(year_folder))
    except FileExistsError:
        pass        # directory already exists

    try:
        os.makedirs('output/letter doc/{}/{}'.format(year_folder, month_folder))
    except FileExistsError:
        pass        # directory already exists

    try:
        try:
            os.rmdir('output/letter doc/{}/{}/{}_to_{}'.format(year_folder,
                                                               month_folder, start_dt, end_dt))

        except:

            pass

        os.makedirs('output/letter doc/{}/{}/{}_to_{}'.format(year_folder,
                    month_folder, start_dt, end_dt))

    except FileExistsError:
        pass

    if len(const_dict['pg_er1'][0]) > 0:
        doc_er1 = DocxTemplate(
            "D:/Applications/SVS/svs_be/letters doc templates/Letter to  Powergrid_ER1.docx")
        context_er1 = {"cur_date": cur_dt, "start_date": start_dt, "end_date": end_dt, "Lines_english": list(
            const_dict['pg_er1'][1].keys()), "Lines_hindi": list(const_dict['pg_er1'][1].values())}
        doc_er1.render(context_er1)
        doc_er1.save('output/letter doc/{}/{}/{}_to_{}/Letter to Powergrid_ER1 {}_to_{}.docx'.format(
            year_folder, month_folder, start_dt, end_dt, start_dt, end_dt))

    if len(const_dict['pg_er2'][0]) > 0:
        doc_er2 = DocxTemplate(
            "D:/Applications/SVS/svs_be/letters doc templates/Letter to  Powergrid_ER2.docx")
        context_er2 = {"cur_date": cur_dt, "start_date": start_dt, "end_date": end_dt, "Lines_english": list(
            const_dict['pg_er2'][1].keys()), "Lines_hindi": list(const_dict['pg_er2'][1].values())}
        doc_er2.render(context_er2)
        doc_er2.save('output/letter doc/{}/{}/{}_to_{}/Letter to Powergrid_ER2 {}_to_{}.docx'.format(
            year_folder, month_folder, start_dt, end_dt, start_dt, end_dt))

    if len(const_dict['pg_er3'][0]) > 0:
        doc_er3 = DocxTemplate(
            "D:/Applications/SVS/svs_be/letters doc templates/Letter to Powergrid_Odisha_Project.docx")
        context_er3 = {"cur_date": cur_dt, "start_date": start_dt, "end_date": end_dt, "Lines_english": list(
            const_dict['pg_er3'][1].keys()), "Lines_hindi": list(const_dict['pg_er3'][1].values())}
        doc_er3.render(context_er3)
        doc_er3.save('output/letter doc/{}/{}/{}_to_{}/Letter to Powergrid_Odisha_Project {}_to_{}.docx'.format(
            year_folder, month_folder, start_dt, end_dt, start_dt, end_dt))

    if len(const_dict['bh'][0]) > 0:

        doc_bh = DocxTemplate("D:/Applications/SVS/svs_be/letters doc templates/Letter to BSPTCL.docx")
        context_bh = {"cur_date": cur_dt, "start_date": start_dt, "end_date": end_dt, "Lines_english": list(
            const_dict['bh'][1].keys()), "Lines_hindi": list(const_dict['bh'][1].values())}
        doc_bh.render(context_bh)
        doc_bh.save('output/letter doc/{}/{}/{}_to_{}/Letter to BSPTCL {}_to_{}.docx'.format(
            year_folder, month_folder, start_dt, end_dt, start_dt, end_dt))

    if len(const_dict['wb'][0]) > 0:
        doc_wb = DocxTemplate("D:/Applications/SVS/svs_be/letters doc templates/Letter to WBSETCL.docx")
        context_wb = {"cur_date": cur_dt, "start_date": start_dt, "end_date": end_dt, "Lines_english": list(
            const_dict['wb'][1].keys()), "Lines_hindi": list(const_dict['wb'][1].values())}
        doc_wb.render(context_wb)
        doc_wb.save('output/letter doc/{}/{}/{}_to_{}/Letter to WBSETCL {}_to_{}.docx'.format(
            year_folder, month_folder, start_dt, end_dt, start_dt, end_dt))

    if len(const_dict['jh'][0]) > 0:
        doc_jh = DocxTemplate("D:/Applications/SVS/svs_be/letters doc templates/Letter to JUSNL.docx")
        context_jh = {"cur_date": cur_dt, "start_date": start_dt, "end_date": end_dt, "Lines_english": list(
            const_dict['jh'][1].keys()), "Lines_hindi": list(const_dict['jh'][1].values())}
        doc_jh.render(context_jh)
        doc_jh.save('output/letter doc/{}/{}/{}_to_{}/Letter to JUSNL {}_to_{}.docx'.format(
            year_folder, month_folder, start_dt, end_dt, start_dt, end_dt))

    if len(const_dict['dvc'][0]) > 0:
        doc_dvc = DocxTemplate("D:/Applications/SVS/svs_be/letters doc templates/Letter to DVC.docx")
        context_dvc = {"cur_date": cur_dt, "start_date": start_dt, "end_date": end_dt, "Lines_english": list(
            const_dict['dvc'][1].keys()), "Lines_hindi": list(const_dict['dvc'][1].values())}
        doc_dvc.render(context_dvc)
        doc_dvc.save('output/letter doc/{}/{}/{}_to_{}/Letter to DVC {}_to_{}.docx'.format(
            year_folder, month_folder, start_dt, end_dt, start_dt, end_dt))

    if len(const_dict['gr'][0]) > 0:
        doc_gr = DocxTemplate("D:/Applications/SVS/svs_be/letters doc templates/Letter to OPTCL.docx")
        context_gr = {"cur_date": cur_dt, "start_date": start_dt, "end_date": end_dt, "Lines_english": list(
            const_dict['gr'][1].keys()), "Lines_hindi": list(const_dict['gr'][1].values())}
        doc_gr.render(context_gr)
        doc_gr.save('output/letter doc/{}/{}/{}_to_{}/Letter to OPTCL {}_to_{}.docx'.format(
            year_folder, month_folder, start_dt, end_dt, start_dt, end_dt))

    if len(const_dict['si'][0]) > 0:
        doc_si = DocxTemplate("D:/Applications/SVS/svs_be/letters doc templates/Letter to Sikkim.docx")
        context_si = {"cur_date": cur_dt, "start_date": start_dt, "end_date": end_dt, "Lines_english": list(
            const_dict['si'][1].keys()), "Lines_hindi": list(const_dict['si'][1].values())}
        doc_si.render(context_si)
        doc_si.save('output/letter doc/{}/{}/{}_to_{}/Letter to Sikkim {}_to_{}.docx'.format(
            year_folder, month_folder, start_dt, end_dt, start_dt, end_dt))

    # print('Letter generation', 'All Letters have generated at output/letter doc/')


def gen_excel():

    global Global_data

    global Global_date

    meter_to = [Global_date]

    meter_far = [Global_date]

    scada_to = [Global_date]

    scada_far = [Global_date]

    svs_to = [Global_date]

    svs_far = [Global_date]

    for item in Global_data:

        df1 = pd.DataFrame.from_dict(
            {item['Feeder_Name']: item['Meter_To_End_data']})

        meter_to.append(df1)

        df2 = pd.DataFrame.from_dict(
            {item['Feeder_Name']: item['Meter_Far_End_data']})

        meter_far.append(df2)

        df3 = pd.DataFrame.from_dict(
            {item['Feeder_Name']: item['Scada_To_End_data']})

        scada_to.append(df3)

        df4 = pd.DataFrame.from_dict(
            {item['Feeder_Name']: item['Scada_Far_End_data']})

        scada_far.append(df4)

        df5 = pd.DataFrame.from_dict(
            {item['Feeder_Name']: item['to_end_percent']})

        svs_to.append(df5)

        df6 = pd.DataFrame.from_dict(
            {item['Feeder_Name']: item['far_end_percent']})

        svs_far.append(df6)

    meter_to = pd.concat(meter_to, axis=1, join="inner")
    meter_far = pd.concat(meter_far, axis=1, join="inner")
    scada_to = pd.concat(scada_to, axis=1, join="inner")
    scada_far = pd.concat(scada_far, axis=1, join="inner")
    svs_to = pd.concat(svs_to, axis=1, join="inner")
    svs_far = pd.concat(svs_far, axis=1, join="inner")

    path = "D:/Applications/SVS/svs_be/output/SVS.xlsx"

    # if len(meter_to) > 0:

    #     merged = pd.concat(meter_to, axis=1, join="inner")
    #     merged.to_excel(
    #         path, index=None, sheet_name="SEM_To_End")

    # if len(meter_far) > 0:

    #     merged = pd.concat(meter_far, axis=1, join="inner")
    #     merged.to_excel(
    #         path, index=None, sheet_name="SEM_Far_End")

    # if len(scada_to) > 0:

    #     merged = pd.concat(scada_to, axis=1, join="inner")
    #     merged.to_excel(
    #         path, index=None, sheet_name="SCADA_To_End")

    # if len(scada_far) > 0:

    #     merged = pd.concat(scada_far, axis=1, join="inner")
    #     merged.to_excel(
    #         path, index=None, sheet_name="SCADA_Far_End")

    # if len(svs_to) > 0:

    #     merged = pd.concat(svs_to, axis=1, join="inner")
    #     merged.to_excel(
    #         path, index=None, sheet_name="SvS_To_End")

    # if len(svs_far) > 0:

    #     merged = pd.concat(svs_far, axis=1, join="inner")
    #     merged.to_excel(
    #         path, index=None, sheet_name="SvS_Far_End")

    with pd.ExcelWriter(path) as writer:

        # use to_excel function and specify the sheet_name and index
        # to store the dataframe in specified sheet
        meter_to.to_excel(writer, sheet_name="SEM_To_End", index=False)
        meter_far.to_excel(writer, sheet_name="SEM_Far_End", index=False)
        scada_to.to_excel(writer, sheet_name="SCADA_To_End", index=False)
        scada_far.to_excel(writer, sheet_name="SCADA_Far_End", index=False)
        svs_to.to_excel(writer, sheet_name="SvS_To_End", index=False)
        svs_far.to_excel(writer, sheet_name="SvS_Far_End", index=False)

    if os.path.exists(path):
        with open(path, "rb") as excel:
            data = excel.read()

        response = Response(
            data, content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')

    return send_file(path, as_attachment=True, download_name='SVS')
