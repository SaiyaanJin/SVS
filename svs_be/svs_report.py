import os
import uuid
import threading
from datetime import date, timedelta, datetime, timezone
from collections import defaultdict

import pandas as pd
from pymongo import MongoClient, ASCENDING
from flask import Flask, jsonify, Response, send_file
from flask_cors import CORS
from docxtpl import DocxTemplate
import matplotlib
matplotlib.use('Agg')
from matplotlib.backends.backend_pdf import PdfPages
from concurrent.futures import ProcessPoolExecutor, ThreadPoolExecutor, as_completed
from PyPDF2 import PdfMerger
from matplotlib import pyplot as plt

app = Flask(__name__)
CORS(app)

# Global variables
Global_letter_data = ""
Global_data = ""
Global_date = ""
Global_error_list = []

def my_max_min_function(somelist):
    if not somelist:
        return [0], [0], 0
    max_value = max(somelist)
    min_value = min(somelist)
    avg_value = sum(somelist) / len(somelist)
    max_index = [i for i, val in enumerate(somelist) if val == max_value]
    min_index = [i for i, val in enumerate(somelist) if val == min_value]
    max_index.insert(0, max_value)
    min_index.insert(0, min_value)
    return max_index, min_index, avg_value

def datetime_range(start, end, delta):
    end = end + timedelta(days=1)
    current = start
    while current < end:
        yield current
        current += delta

def divide_chunks(l, n):
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
    try:
        return float(x)
    except Exception:
        return None

def remove_duplicate_objects(arr):
    seen = set()
    new_arr = []
    for obj in arr:
        key = tuple(sorted(obj.items()))
        if key not in seen:
            seen.add(key)
            new_arr.append(obj)
    return new_arr

def ScadaCollection():
    CONNECTION_STRING = "mongodb://mongodb0.erldc.in:27017,mongodb1.erldc.in:27017,mongodb10.erldc.in:27017/?replicaSet=CONSERV"
    client = MongoClient(CONNECTION_STRING)
    db = client['SemVsScada']
    return db['Scada_Data'], db['meter_name_code'], db['mapping_table']

Scada_database, meter_table, mapping_table = ScadaCollection()

def svsreport(startDate, startDate_obj, endDate, time, folder, offset):
    import concurrent.futures

    def clean_keydata(keydata):
        return [item for item in keydata if item.get('Deleted', 'No') != "Yes"]

    def get_date_range(start, end):
        start_dt = datetime.strptime(start, "%Y-%m-%d")
        end_dt = datetime.strptime(end, "%Y-%m-%d")
        return [start_dt + timedelta(days=x) for x in range((end_dt - start_dt).days + 1)]

    def fetch_scada_data(code, date_range, db):
        filter = {
            'Date': {'$gte': datetime(date_range[0].year, date_range[0].month, date_range[0].day, 0, 0, 0, tzinfo=timezone.utc),
                     '$lte': datetime(date_range[-1].year, date_range[-1].month, date_range[-1].day, 0, 0, 0, tzinfo=timezone.utc)},
            'Code': code
        }
        project = {'_id': 0, 'Data': 1, 'Date': 1}
        cursor = Scada_database.find(filter=filter, projection=project).sort('Date', ASCENDING)
        date_map = {d['Date'].date(): d.get('Data', []) for d in cursor}
        data = []
        for it in date_range:
            vals = date_map.get(it.date(), [])
            if vals:
                data += [0 if pd.isna(val) else round(val, 2) for val in vals]
            else:
                data += [0] * 96
        return data

    def fetch_meter_data(meter_id, date_range, db):
        data = []
        years = sorted(set(it.year for it in date_range))
        date_map = {}
        for year in years:
            Data_Table = db["meterData" + str(year)]
            filter = {
                'date': {'$gte': datetime(year, 1, 1, 0, 0, 0, tzinfo=timezone.utc),
                         '$lte': datetime(year, 12, 31, 0, 0, 0, tzinfo=timezone.utc)},
                'meterID': meter_id
            }
            project = {'_id': 0, 'data': 1, 'date': 1}
            cursor = Data_Table.find(filter=filter, projection=project)
            for d in cursor:
                date_map[d['date'].date()] = d.get('data', [])
        for it in date_range:
            vals = date_map.get(it.date(), [])
            if vals:
                data += [0 if pd.isna(val) else round(4 * val, 2) for val in vals]
            else:
                data += [0] * 96
        return data

    def fetch_meter_data_from_file(meter_code, date_range):
        data = []
        filter = {'Meter_Code': meter_code}
        cursor2 = meter_table.find(filter=filter, projection={'_id': 0})
        cursor2_list = list(cursor2)
        if not cursor2_list:
            return data
        meters = cursor2_list[0]["Meter_Name"] + ".MWH"
        path = "Meter_Files/"
        for dates in date_range:
            full_path = os.path.join(path, dates.strftime("%d-%m-%y"))
            if os.path.isdir(full_path):
                file_path = os.path.join(full_path, meters)
                if os.path.exists(file_path):
                    dataEnd1 = pd.read_csv(file_path, header=None)
                    dfEnd1 = dataEnd1[0]
                    for i in range(1, len(dfEnd1)):
                        oneHourDataEnd1 = [changeToFloat(x) for x in dfEnd1[i].split()[1:]]
                        data += [0 if pd.isna(x) else round(4 * x, 2) for x in oneHourDataEnd1]
        return data

    def add_error(feeder_name, semvsscada_dict, error_names, Global_error_list, lock=None):
        if lock:
            with lock:
                if feeder_name not in error_names:
                    error_names.append(feeder_name)
                    xyz = semvsscada_dict.copy()
                    for k in ['Meter_Far_End_data', 'Meter_To_End_data', 'Scada_Far_End_data', 'Scada_To_End_data']:
                        xyz.pop(k, None)
                    Global_error_list.append(xyz)
        else:
            if feeder_name not in error_names:
                error_names.append(feeder_name)
                xyz = semvsscada_dict.copy()
                for k in ['Meter_Far_End_data', 'Meter_To_End_data', 'Scada_Far_End_data', 'Scada_To_End_data']:
                    xyz.pop(k, None)
                Global_error_list.append(xyz)

    startDateObj = datetime.strptime(startDate, "%Y-%m-%d")
    endDateObj = datetime.strptime(endDate, "%Y-%m-%d")
    global Global_date, Global_error_list, Global_letter_data, Global_data
    CONNECTION_STRING = "mongodb://10.3.230.94:1434"
    client = MongoClient(CONNECTION_STRING)
    db = client['meterDataArchival']
    cursor = mapping_table.find(filter={}, projection={'_id': 0})
    keydata = clean_keydata(list(cursor))
    allDateTime = [dt.strftime("%d-%m-%Y %H:%M:%S") for dt in datetime_range(startDateObj, endDateObj, timedelta(minutes=time))]
    final_data_to_send = {'Date_Time': allDateTime}
    final_data_to_send1 = []
    df1 = pd.DataFrame({'Date_Time': allDateTime})
    Global_date = df1

    lookupDictionary = defaultdict(list)
    error_names = []
    constituent_keys = ['BH', 'DV', 'GR', 'JH', 'MIS_CALC_TO', 'NTPC_ER_1', 'NTPC_ODISHA', 'PG_ER1', 'PG_ER2', 'WB', 'SI', 'PG_odisha_project']

    error_lock = threading.Lock()
    append_lock = threading.Lock()

    date_range = get_date_range(startDate, endDate)

    # Pre-fetch all SCADA and Meter data for all unique keys in parallel
    scada_keys = set()
    meter_keys = set()
    for item in keydata:
        if item['Key_To_End'].split(":")[0] not in ["No Key", "Duplicate Key"]:
            scada_keys.add(item['Key_To_End'])
        if item['Key_Far_End'].split(":")[0] not in ["No Key", "Duplicate Key"]:
            scada_keys.add(item['Key_Far_End'])
        if item['Meter_To_End'].split(":")[0] not in ["No Key", "Duplicate Key"]:
            meter_keys.add(item['Meter_To_End'])
        if item['Meter_Far_End'].split(":")[0] not in ["No Key", "Duplicate Key"]:
            meter_keys.add(item['Meter_Far_End'])

    # Parallel fetch for SCADA
    scada_data_dict = {}
    with ThreadPoolExecutor(max_workers=16) as executor:
        future_to_key = {executor.submit(fetch_scada_data, key, date_range, db): key for key in scada_keys}
        for future in as_completed(future_to_key):
            key = future_to_key[future]
            try:
                scada_data_dict[key] = future.result()
            except Exception:
                scada_data_dict[key] = [0] * (len(date_range) * 96)

    # Parallel fetch for Meter
    meter_data_dict = {}
    if folder == "no":
        with ThreadPoolExecutor(max_workers=16) as executor:
            future_to_key = {executor.submit(fetch_meter_data, key, date_range, db): key for key in meter_keys}
            for future in as_completed(future_to_key):
                key = future_to_key[future]
                try:
                    meter_data_dict[key] = future.result()
                except Exception:
                    meter_data_dict[key] = [0] * (len(date_range) * 96)
    else:
        with ThreadPoolExecutor(max_workers=16) as executor:
            future_to_key = {executor.submit(fetch_meter_data_from_file, key, date_range): key for key in meter_keys}
            for future in as_completed(future_to_key):
                key = future_to_key[future]
                try:
                    meter_data_dict[key] = future.result()
                except Exception:
                    meter_data_dict[key] = [0] * (len(date_range) * 96)

    def process_item(item):
        Feeder_Name = item['Feeder_Name']
        Feeder_Hindi = item['Feeder_Hindi']
        Key_To_End = item['Key_To_End']
        Key_Far_End = item['Key_Far_End']
        Meter_To_End = item['Meter_To_End']
        Meter_Far_End = item['Meter_Far_End']
        Feeder_From = item['Feeder_From']
        To_Feeder = item['To_Feeder']
        semvsscada_dict = {
            'Feeder_Name': Feeder_Name,
            'Feeder_Hindi': Feeder_Hindi,
            'Key_To_End': Key_To_End,
            'Key_Far_End': Key_Far_End,
            'Meter_To_End': Meter_To_End,
            'Meter_Far_End': Meter_Far_End,
            'Feeder_From': Feeder_From,
            'To_Feeder': To_Feeder
        }

        # To End Data
        valid_to_end = (Key_To_End.split(":")[0] not in ["No Key", "Duplicate Key"]) and (Meter_To_End.split(":")[0] not in ["No Key", "Duplicate Key"])
        if valid_to_end:
            try:
                scada_database_data_to = scada_data_dict.get(Key_To_End, [0] * (len(date_range) * 96))
                if not scada_database_data_to:
                    scada_database_data_to = [0] * (len(date_range) * 96)
                    add_error(Feeder_Name, semvsscada_dict, error_names, Global_error_list, error_lock)
                semvsscada_dict['Scada_To_End_data'] = scada_database_data_to

                meter_database_data_to = meter_data_dict.get(Meter_To_End, [0] * (len(date_range) * 96))
                if not meter_database_data_to:
                    meter_database_data_to = [0] * (len(date_range) * 96)
                    add_error(Feeder_Name, semvsscada_dict, error_names, Global_error_list, error_lock)
                semvsscada_dict['Meter_To_End_data'] = meter_database_data_to
            except Exception:
                semvsscada_dict['Scada_To_End_data'] = [0] * (len(date_range) * 96)
                semvsscada_dict['Meter_To_End_data'] = [0] * (len(date_range) * 96)
                add_error(Feeder_Name, semvsscada_dict, error_names, Global_error_list, error_lock)
        else:
            semvsscada_dict['Scada_To_End_data'] = [0] * (len(date_range) * 96)
            semvsscada_dict['Meter_To_End_data'] = [0] * (len(date_range) * 96)
            add_error(Feeder_Name, semvsscada_dict, error_names, Global_error_list, error_lock)

        # Far End Data
        valid_far_end = (Key_Far_End.split(":")[0] not in ["No Key", "Duplicate Key"]) and (Meter_Far_End.split(":")[0] not in ["No Key", "Duplicate Key"])
        if valid_far_end:
            try:
                scada_database_data_far = scada_data_dict.get(Key_Far_End, [0] * (len(date_range) * 96))
                if not scada_database_data_far:
                    scada_database_data_far = [0] * (len(date_range) * 96)
                    add_error(Feeder_Name, semvsscada_dict, error_names, Global_error_list, error_lock)
                semvsscada_dict['Scada_Far_End_data'] = scada_database_data_far

                meter_database_data_far = meter_data_dict.get(Meter_Far_End, [0] * (len(date_range) * 96))
                if not meter_database_data_far:
                    meter_database_data_far = [0] * (len(date_range) * 96)
                    add_error(Feeder_Name, semvsscada_dict, error_names, Global_error_list, error_lock)
                semvsscada_dict['Meter_Far_End_data'] = meter_database_data_far
            except Exception:
                semvsscada_dict['Scada_Far_End_data'] = [0] * (len(date_range) * 96)
                semvsscada_dict['Meter_Far_End_data'] = [0] * (len(date_range) * 96)
                add_error(Feeder_Name, semvsscada_dict, error_names, Global_error_list, error_lock)
        else:
            semvsscada_dict['Scada_Far_End_data'] = [0] * (len(date_range) * 96)
            semvsscada_dict['Meter_Far_End_data'] = [0] * (len(date_range) * 96)
            add_error(Feeder_Name, semvsscada_dict, error_names, Global_error_list, error_lock)

        # Calculate errors and statistics
        to_end_percent, far_end_percent = [], []
        actual_to_end_percent, actual_far_end_percent = [], []
        sem_percent, scada_percent = [], []
        count_sem = count_scada = 0

        scada_to = semvsscada_dict["Scada_To_End_data"]
        meter_to = semvsscada_dict["Meter_To_End_data"]
        scada_far = semvsscada_dict["Scada_Far_End_data"]
        meter_far = semvsscada_dict["Meter_Far_End_data"]

        if scada_to == "No Data Found" or meter_to == "No Data Found":
            to_end_percent = [0]
            actual_to_end_percent = [0]
            add_error(Feeder_Name, semvsscada_dict, error_names, Global_error_list, error_lock)
        else:
            count = total_val = nonzero_val = 0
            for item in scada_to:
                item = abs(item)
                if item != 0:
                    total_val += item
                    count += 1
                    nonzero_val = item
            avg_scada_to = round(abs(total_val / count), 2) if count else 0
            if (count and avg_scada_to == nonzero_val) or (count == 0):
                add_error(Feeder_Name, semvsscada_dict, error_names, Global_error_list, error_lock)

            count1 = total_val1 = nonzero_val1 = 0
            for item in meter_to:
                item = abs(item)
                if item != 0:
                    total_val1 += item
                    count1 += 1
                    nonzero_val1 = item
            avg_meter_to = round(abs(total_val1 / count1), 2) if count1 else 0
            if (count1 and avg_meter_to == nonzero_val1) or (count1 == 0):
                add_error(Feeder_Name, semvsscada_dict, error_names, Global_error_list, error_lock)

            for i in range(len(allDateTime)):
                x1 = meter_to[i]
                y1 = scada_to[i]
                x2 = meter_far[i]
                y2 = scada_far[i]
                if y1 != 0:
                    scada_block_wise = abs(round((100 * (abs(y1) - abs(y2)) / max(abs(y1), abs(y2))), 2))
                    count_scada += 1
                else:
                    scada_block_wise = 0
                if x1 != 0:
                    sem_block_wise = abs(round((100 * (abs(x1) - abs(x2)) / max(abs(x1), abs(x2))), 2))
                    count_sem += 1
                else:
                    sem_block_wise = 0
                scada_percent.append(scada_block_wise)
                sem_percent.append(sem_block_wise)
                # To End percent
                if i != 0:
                    if Feeder_Name in ["BH_DRAWAL", "DV_DRAWAL", "GR_DRAWAL", "WB_DRAWAL", "JH_DRAWAL", "SI_DRAWAL"]:
                        meter_to[i] = abs(meter_to[i])
                    if meter_to[i] == meter_to[i - 1] or scada_to[i] == scada_to[i - 1]:
                        to_end_percent.append(0)
                        actual_to_end_percent.append(0)
                    elif meter_to[i] == 0 or scada_to[i] == 0:
                        to_end_percent.append(0)
                        actual_to_end_percent.append(0)
                    elif (abs(meter_to[i]) <= abs(offset)) or (abs(scada_to[i]) <= abs(offset)):
                        to_end_percent.append(0)
                        actual_to_end_percent.append(0)
                    else:
                        x = abs(meter_to[i])
                        y = abs(scada_to[i])
                        if abs(x - y) <= 5:
                            to_percent = 0
                            actual_to_end_percent.append(0)
                        else:
                            to_percent = abs(round((100 * (x - y) / x), 2))
                            actual_to_end_percent.append(to_percent)
                            if to_percent >= 20:
                                to_percent = 0
                        to_end_percent.append(to_percent)
                else:
                    if Feeder_Name in ["BH_DRAWAL", "DV_DRAWAL", "GR_DRAWAL", "WB_DRAWAL", "JH_DRAWAL", "SI_DRAWAL"]:
                        meter_to[i] = abs(meter_to[i])
                    if meter_to[i] == 0 or scada_to[i] == 0:
                        to_end_percent.append(0)
                        actual_to_end_percent.append(0)
                    elif (abs(meter_to[i]) <= abs(offset)) or (abs(scada_to[i]) <= abs(offset)):
                        to_end_percent.append(0)
                        actual_to_end_percent.append(0)
                    else:
                        x = abs(meter_to[i])
                        y = abs(scada_to[i])
                        if abs(x - y) <= 5:
                            to_percent = 0
                            actual_to_end_percent.append(0)
                        else:
                            to_percent = abs(round((100 * (x - y) / x), 2))
                            actual_to_end_percent.append(to_percent)
                            if to_percent >= 20:
                                to_percent = 0
                        to_end_percent.append(to_percent)

        # Far End error calculation
        if scada_far == "No Data Found" or meter_far == "No Data Found":
            far_end_percent = [0]
            actual_far_end_percent = [0]
        else:
            count = total_val = nonzero_val = 0
            for item in scada_far:
                item = abs(item)
                if item != 0:
                    total_val += item
                    count += 1
                    nonzero_val = item
            avg_scada_far = round(abs(total_val / count), 2) if count else 0
            if (count and avg_scada_far == nonzero_val) or (count == 0):
                add_error(Feeder_Name, semvsscada_dict, error_names, Global_error_list, error_lock)

            count1 = total_val1 = nonzero_val1 = 0
            for item in meter_far:
                item = abs(item)
                if item != 0:
                    total_val1 += item
                    count1 += 1
                    nonzero_val1 = item
            avg_meter_far = round(abs(total_val1 / count1), 2) if count1 else 0
            if (count1 and avg_meter_far == nonzero_val1) or (count1 == 0):
                add_error(Feeder_Name, semvsscada_dict, error_names, Global_error_list, error_lock)

            for i in range(len(scada_far)):
                if i != 0:
                    if Feeder_Name in ["BH_DRAWAL", "DV_DRAWAL", "GR_DRAWAL", "WB_DRAWAL", "JH_DRAWAL", "SI_DRAWAL"]:
                        meter_far[i] = abs(meter_far[i])
                    if meter_far[i] == meter_far[i - 1] or scada_far[i] == scada_far[i - 1]:
                        far_end_percent.append(0)
                        actual_far_end_percent.append(0)
                    elif meter_far[i] == 0 or scada_far[i] == 0:
                        far_end_percent.append(0)
                        actual_far_end_percent.append(0)
                    elif (abs(meter_far[i]) <= abs(offset)) or (abs(scada_far[i]) <= abs(offset)):
                        far_end_percent.append(0)
                        actual_far_end_percent.append(0)
                    else:
                        x = abs(meter_far[i])
                        y = abs(scada_far[i])
                        if abs(x - y) <= 5:
                            far_percent = 0
                            actual_far_end_percent.append(0)
                        else:
                            far_percent = abs(round((100 * (x - y) / x), 2))
                            actual_far_end_percent.append(far_percent)
                            if far_percent > 20:
                                far_percent = 0
                        far_end_percent.append(far_percent)
                else:
                    if Feeder_Name in ["BH_DRAWAL", "DV_DRAWAL", "GR_DRAWAL", "WB_DRAWAL", "JH_DRAWAL", "SI_DRAWAL"]:
                        meter_far[i] = abs(meter_far[i])
                    if meter_far[i] == 0 or scada_far[i] == 0:
                        far_end_percent.append(0)
                        actual_far_end_percent.append(0)
                    elif (abs(meter_far[i]) <= abs(offset)) or (abs(scada_far[i]) <= abs(offset)):
                        far_end_percent.append(0)
                        actual_far_end_percent.append(0)
                    else:
                        x = abs(meter_far[i])
                        y = abs(scada_far[i])
                        if abs(x - y) <= 5:
                            far_percent = 0
                            actual_far_end_percent.append(0)
                        else:
                            far_percent = abs(round((100 * (x - y) / x), 2))
                            actual_far_end_percent.append(far_percent)
                            if far_percent > 20:
                                far_percent = 0
                        far_end_percent.append(far_percent)

        # Statistics
        to_max, to_min, to_avg = my_max_min_function(to_end_percent)
        far_max, far_min, far_avg = my_max_min_function(far_end_percent)
        actual_to_avg = sum(actual_to_end_percent) / len(actual_to_end_percent) if actual_to_end_percent else 0
        actual_far_avg = sum(actual_far_end_percent) / len(actual_far_end_percent) if actual_far_end_percent else 0
        sem_avg = min(round(sum(sem_percent) / count_sem, 2), 100) if count_sem else 0
        scada_avg = min(round(sum(scada_percent) / count_scada, 2), 100) if count_scada else 0

        if actual_to_avg >= 20 or actual_far_avg >= 20:
            add_error(Feeder_Name, semvsscada_dict, error_names, Global_error_list, error_lock)

        semvsscada_dict.update({
            'to_end_percent': actual_to_end_percent,
            'far_end_percent': actual_far_end_percent,
            'to_end_max_val': to_max[0],
            'to_end_min_val': to_min[0],
            'to_end_avg_val': min(round(actual_to_avg, 2), 100),
            'far_end_max_val': far_max[0],
            'far_end_min_val': far_min[0],
            'far_end_avg_val': min(round(actual_far_avg, 2), 100),
            'scada_error': scada_percent,
            'sem_error': sem_percent,
            'sem_avg': sem_avg,
            'scada_avg': scada_avg
        })

        # Constituent assignment
        with append_lock:
            if semvsscada_dict['to_end_avg_val'] > 3:
                constituent_name = semvsscada_dict['Feeder_From']
                if constituent_name in constituent_keys and [semvsscada_dict['Feeder_Name'], 0] not in lookupDictionary[constituent_name]:
                    lookupDictionary[constituent_name].append([semvsscada_dict['Feeder_Name'], 0])
            if semvsscada_dict['far_end_avg_val'] > 3:
                constituent_name = semvsscada_dict['To_Feeder']
                if constituent_name in constituent_keys and [semvsscada_dict['Feeder_Name'], 1] not in lookupDictionary[constituent_name]:
                    lookupDictionary[constituent_name].append([semvsscada_dict['Feeder_Name'], 1])
            final_data_to_send1.append(semvsscada_dict)

    with ThreadPoolExecutor(max_workers=16) as executor:
        list(executor.map(process_item, keydata))

    for key in constituent_keys:
        final_data_to_send[key] = lookupDictionary[key]

    Global_letter_data = final_data_to_send.copy()
    Global_data = final_data_to_send1
    final_data_to_send['Data'] = final_data_to_send1
    return [final_data_to_send, error_names]

def gen_error_excel():
    global Global_error_list
    name_list = remove_duplicate_objects(Global_error_list)
    try:
        os.remove('Excel_Files/ErrorNames.xlsx')
    except:
        pass
    if len(name_list) > 0:
        merged = pd.DataFrame(name_list)
        merged.to_excel("Excel_Files/ErrorNames.xlsx", index=None)
        path = "Excel_Files/ErrorNames.xlsx"
        if os.path.exists(path):
            return send_file(path, as_attachment=True, download_name='ErrorNames.xlsx')
        else:
            return Response('Some error occured!')
    else:
        return jsonify("No Data to Download")

def gen_all_letters():
    import concurrent.futures

    global Global_letter_data
    data_list = Global_letter_data

    dt = date.today()
    cur_dt = dt.strftime('%d-%m-%Y')
    start_dt_obj = datetime.strptime(data_list['Date_Time'][0], '%d-%m-%Y %H:%M:%S')
    end_dt_obj = datetime.strptime(data_list['Date_Time'][-1], '%d-%m-%Y %H:%M:%S')
    month_folder = start_dt_obj.strftime('%b %y')
    year_folder = start_dt_obj.strftime('%Y')
    start_dt = start_dt_obj.strftime('%d-%m-%Y')
    end_dt = end_dt_obj.strftime('%d-%m-%Y')

    # Extract constituent lists
    si_list = data_list['SI']
    gr_list = data_list["GR"]
    dvc_list = data_list["DV"]
    bh_list = data_list["BH"]
    wb_list = data_list["WB"]
    pg_er3_list = data_list["PG_odisha_project"]
    pg_er2_list = data_list["PG_ER2"]
    pg_er1_list = data_list["PG_ER1"]
    jh_list = data_list["JH"]

    cursor = mapping_table.find(filter={}, projection={'_id': 0, 'Feeder_Name': 1, 'Feeder_Hindi': 1})
    keydata = list(cursor)
    feeders = {row['Feeder_Name']: row['Feeder_Hindi'] for row in keydata}

    const_dict = {
        'si': [si_list, {}], 'gr': [gr_list, {}], 'dvc': [dvc_list, {}], 'bh': [bh_list, {}], 'wb': [wb_list, {}],
        'pg_er3': [pg_er3_list, {}], 'pg_er2': [pg_er2_list, {}], 'pg_er1': [pg_er1_list, {}], 'jh': [jh_list, {}]
    }

    def reverse_line(line, feeders):
        if "_ICT" not in line:
            line_var = line.split('_')
            if len(line_var) > 2:
                x = line_var[1]
                line_var[1], line_var[2] = line_var[2], x
                rev_line = '_'.join(line_var)
                line_var_h = feeders[line].split('_')
                x_h = line_var_h[1]
                line_var_h[1], line_var_h[2] = line_var_h[2], x_h
                rev_line_h = '_'.join(line_var_h)
                return rev_line, rev_line_h
        return None, None

    def process_constituent(constituent):
        const_lst, mapping = const_dict[constituent]
        for lines in const_lst:
            if lines[-1] == 0:
                line = lines[0]
                mapping[line] = feeders.get(line, "")
            else:
                line = lines[0]
                if "_ICT" not in line:
                    rev_line, rev_line_h = reverse_line(line, feeders)
                    if rev_line and rev_line_h:
                        mapping[rev_line] = rev_line_h
        return constituent, dict(sorted(mapping.items(), reverse=True))

    with ThreadPoolExecutor() as executor:
        results = list(executor.map(process_constituent, const_dict.keys()))
    for k, v in results:
        const_dict[k][1] = v

    base_path = f'output/letter doc/{year_folder}/{month_folder}/{start_dt}_to_{end_dt}'
    os.makedirs(base_path, exist_ok=True)

    letter_tasks = [
        (len(const_dict['pg_er1'][0]) > 0, "letters doc templates/Letter to  Powergrid_ER1.docx", 'pg_er1', 'Letter to Powergrid_ER1'),
        (len(const_dict['pg_er2'][0]) > 0, "letters doc templates/Letter to  Powergrid_ER2.docx", 'pg_er2', 'Letter to Powergrid_ER2'),
        (len(const_dict['pg_er3'][0]) > 0, "letters doc templates/Letter to Powergrid_Odisha_Project.docx", 'pg_er3', 'Letter to Powergrid_Odisha_Project'),
        (len(const_dict['bh'][0]) > 0, "letters doc templates/Letter to BSPTCL.docx", 'bh', 'Letter to BSPTCL'),
        (len(const_dict['wb'][0]) > 0, "letters doc templates/Letter to WBSETCL.docx", 'wb', 'Letter to WBSETCL'),
        (len(const_dict['jh'][0]) > 0, "letters doc templates/Letter to JUSNL.docx", 'jh', 'Letter to JUSNL'),
        (len(const_dict['dvc'][0]) > 0, "letters doc templates/Letter to DVC.docx", 'dvc', 'Letter to DVC'),
        (len(const_dict['gr'][0]) > 0, "letters doc templates/Letter to OPTCL.docx", 'gr', 'Letter to OPTCL'),
        (len(const_dict['si'][0]) > 0, "letters doc templates/Letter to Sikkim.docx", 'si', 'Letter to Sikkim'),
    ]

    def render_letter(args):
        cond, template_path, key, out_name = args
        if not cond:
            return
        doc = DocxTemplate(template_path)
        context = {
            "cur_date": cur_dt,
            "start_date": start_dt,
            "end_date": end_dt,
            "Lines_english": list(const_dict[key][1].keys()),
            "Lines_hindi": list(const_dict[key][1].values())
        }
        doc.render(context)
        doc.save(f'{base_path}/{out_name} {start_dt}_to_{end_dt}.docx')

    with ThreadPoolExecutor() as executor:
        executor.map(render_letter, letter_tasks)

def gen_excel():
    global Global_data
    global Global_date

    if isinstance(Global_date, pd.DataFrame):
        base_df = Global_date.copy()
    elif isinstance(Global_date, dict) and 'Date_Time' in Global_date:
        base_df = pd.DataFrame({'Date_Time': Global_date['Date_Time']})
    elif isinstance(Global_date, list):
        base_df = pd.DataFrame({'Date_Time': Global_date})
    else:
        return jsonify({"error": "Invalid Global_date format"})

    meter_to_dict = {'Date_Time': base_df['Date_Time']}
    meter_far_dict = {'Date_Time': base_df['Date_Time']}
    scada_to_dict = {'Date_Time': base_df['Date_Time']}
    scada_far_dict = {'Date_Time': base_df['Date_Time']}
    svs_to_dict = {'Date_Time': base_df['Date_Time']}
    svs_far_dict = {'Date_Time': base_df['Date_Time']}

    for item in Global_data:
        fname = item['Feeder_Name']
        meter_to_dict[fname] = item.get('Meter_To_End_data', [])
        meter_far_dict[fname] = item.get('Meter_Far_End_data', [])
        scada_to_dict[fname] = item.get('Scada_To_End_data', [])
        scada_far_dict[fname] = item.get('Scada_Far_End_data', [])
        svs_to_dict[fname] = item.get('to_end_percent', [])
        svs_far_dict[fname] = item.get('far_end_percent', [])

    meter_to = pd.DataFrame(meter_to_dict)
    meter_far = pd.DataFrame(meter_far_dict)
    scada_to = pd.DataFrame(scada_to_dict)
    scada_far = pd.DataFrame(scada_far_dict)
    svs_to = pd.DataFrame(svs_to_dict)
    svs_far = pd.DataFrame(svs_far_dict)

    path = "output/SVS.xlsx"
    with pd.ExcelWriter(path, engine='xlsxwriter') as writer:
        meter_to.to_excel(writer, sheet_name="SEM_To_End", index=False)
        meter_far.to_excel(writer, sheet_name="SEM_Far_End", index=False)
        scada_to.to_excel(writer, sheet_name="SCADA_To_End", index=False)
        scada_far.to_excel(writer, sheet_name="SCADA_Far_End", index=False)
        svs_to.to_excel(writer, sheet_name="SvS_To_End", index=False)
        svs_far.to_excel(writer, sheet_name="SvS_Far_End", index=False)

    if os.path.exists(path):
        return send_file(path, as_attachment=True, download_name='SVS')
    else:
        return jsonify({"error": "Excel file not created"})

def plot_feeder(feeder, x_labels, index):
    feeder_name = feeder.get("Feeder_Name", f"Feeder_{index}")
    file_path = f"output/tmp/{uuid.uuid4().hex}_feeder_{index}.pdf"

    def safe_plot(ax, x, y, label, style, lw, color=None):
        if y and len(y) > 0:
            n = min(len(x), len(y))
            ax.plot(x[:n], y[:n], label=label, linestyle=style, linewidth=lw, color=color)

    def draw_table(ax, data_dict, title):
        table_data = [[k, str(v)] for k, v in data_dict.items()]
        table = ax.table(cellText=table_data,
                         colLabels=["Field", "Value"],
                         cellLoc='left',
                         loc='center')
        table.scale(1, 1.2)
        ax.axis('off')
        ax.set_title(title, fontsize=10, fontweight='bold')

    with PdfPages(file_path) as pdf:
        # Page 1 – To End
        fig1, (ax1, ax1_table) = plt.subplots(2, 1, figsize=(14, 6), gridspec_kw={'height_ratios': [2, 1]})
        safe_plot(ax1, x_labels, feeder.get("Meter_To_End_data", []), "Meter To End", '-', 1)
        safe_plot(ax1, x_labels, feeder.get("Scada_To_End_data", []), "Scada To End", '--', 1)
        ax1b = ax1.twinx()
        safe_plot(ax1b, x_labels, feeder.get("to_end_percent", []), "To End % Error", '-.', 1, color='tab:red')
        ax1b.set_ylabel("% Error", fontsize=8, color='tab:red')
        ax1b.tick_params(axis='y', labelsize=6, colors='tab:red')
        tick_interval = 10
        xticks = list(range(0, len(x_labels), tick_interval))
        ax1.set_xticks(xticks)
        ax1.set_xticklabels([x_labels[i] for i in xticks], rotation=60, fontsize=5)
        ax1.set_title(f"{feeder_name} – To End", fontsize=11, fontweight='bold')
        ax1.set_xlabel("Date/Time", fontsize=8)
        ax1.set_ylabel("Values", fontsize=8)
        ax1.grid(True, linestyle='--', alpha=0.6)
        ax1.legend(fontsize=7)
        table_fields = {
            "Feeder Name": feeder.get("Feeder_Name", ""),
            "Meter To End": feeder.get("Meter_To_End", ""),
            "Key To End": feeder.get("Key_To_End", ""),
            "To End Avg": feeder.get("to_end_avg_val", ""),
            "To End Max": feeder.get("to_end_max_val", ""),
            "To End Min": feeder.get("to_end_min_val", ""),
            "SCADA Avg": feeder.get("scada_avg", ""),
            "SEM Avg": feeder.get("sem_avg", "")
        }
        draw_table(ax1_table, table_fields, "To End Summary")
        fig1.tight_layout(pad=1.5)
        pdf.savefig(fig1, dpi=72)
        plt.close(fig1)

        # Page 2 – Far End
        fig2, (ax2, ax2_table) = plt.subplots(2, 1, figsize=(14, 6), gridspec_kw={'height_ratios': [2, 1]})
        safe_plot(ax2, x_labels, feeder.get("Meter_Far_End_data", []), "Meter Far End", '-', 1)
        safe_plot(ax2, x_labels, feeder.get("Scada_Far_End_data", []), "Scada Far End", '--', 1)
        ax2b = ax2.twinx()
        safe_plot(ax2b, x_labels, feeder.get("far_end_percent", []), "Far End % Error", '-.', 1, color='tab:red')
        ax2b.set_ylabel("% Error", fontsize=8, color='tab:red')
        ax2b.tick_params(axis='y', labelsize=6, colors='tab:red')
        ax2.set_xticks(xticks)
        ax2.set_xticklabels([x_labels[i] for i in xticks], rotation=60, fontsize=5)
        ax2.set_title(f"{feeder_name} – Far End", fontsize=11, fontweight='bold')
        ax2.set_xlabel("Date/Time", fontsize=8)
        ax2.set_ylabel("Values", fontsize=8)
        ax2.grid(True, linestyle='--', alpha=0.6)
        ax2.legend(fontsize=7)
        table_fields_far = {
            "Feeder Name": feeder.get("Feeder_Name", ""),
            "Meter Far End": feeder.get("Meter_Far_End", ""),
            "Key Far End": feeder.get("Key_Far_End", ""),
            "Far End Avg": feeder.get("far_end_avg_val", ""),
            "Far End Max": feeder.get("far_end_max_val", ""),
            "Far End Min": feeder.get("far_end_min_val", ""),
            "SCADA Avg": feeder.get("scada_avg", ""),
            "SEM Avg": feeder.get("sem_avg", "")
        }
        draw_table(ax2_table, table_fields_far, "Far End Summary")
        fig2.tight_layout(pad=1.5)
        pdf.savefig(fig2, dpi=72)
        plt.close(fig2)

    return file_path

def gen_graph_pdf():
    global Global_data
    global Global_date

    if isinstance(Global_date, pd.DataFrame):
        x_labels = Global_date['Date_Time'].tolist()
    elif isinstance(Global_date, dict) and 'Date_Time' in Global_date:
        x_labels = Global_date['Date_Time']
    elif isinstance(Global_date, list):
        x_labels = Global_date
    else:
        return jsonify({"error": "Invalid Global_date format"})

    if not Global_data or not isinstance(Global_data, list):
        return jsonify({"error": "Global_data is empty or invalid"})

    os.makedirs("output/tmp", exist_ok=True)
    output_pdf_path = "output/SVS_Graphs.pdf"

    try:
        if os.path.exists(output_pdf_path):
            os.remove(output_pdf_path)
    except PermissionError:
        return jsonify({"error": "Close 'SVS_Graphs.pdf' and try again."})

    feeder_paths = []
    with ProcessPoolExecutor(max_workers=12) as executor:
        futures = {
            executor.submit(plot_feeder, feeder, x_labels, idx): idx
            for idx, feeder in enumerate(Global_data)
        }
        for future in as_completed(futures):
            try:
                result = future.result()
                if result:
                    feeder_paths.append(result)
            except Exception as e:
                print(f"Error processing feeder: {e}")

    if not feeder_paths:
        return jsonify({"error": "No valid feeder data generated."})

    merger = PdfMerger()
    for pdf_path in feeder_paths:
        if pdf_path:
            merger.append(pdf_path)
    merger.write(output_pdf_path)
    merger.close()

    for f in feeder_paths:
        try:
            if f and os.path.exists(f):
                os.remove(f)
        except Exception as e:
            print(f"Failed to remove {f}: {e}")

    return send_file(output_pdf_path, as_attachment=True, download_name='SVS_Graphs.pdf')
