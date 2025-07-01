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
from functools import partial
from itertools import chain
import numpy as np
import concurrent.futures

app = Flask(__name__)
CORS(app)

global week_names
global day_names

week_names = []
day_names = []

def my_max_min_function(somelist):
    if not somelist:
        return [0], [0], 0
    max_value = max(somelist)
    min_value = min(somelist)
    avg_value = sum(somelist) / len(somelist)
    max_indices = [i for i, val in enumerate(somelist) if val == max_value]
    min_indices = [i for i, val in enumerate(somelist) if val == min_value]
    return [max_value] + max_indices, [min_value] + min_indices, avg_value

def datetime_range(start, end, delta):
    current = start
    end = end + timedelta(days=1)
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
    except (ValueError, TypeError):
        return False

def isNaN(num):
    return pd.isna(num)

def changeToFloat(x):
    try:
        return float(x)
    except (ValueError, TypeError):
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

def names(startDate, endDate, blocks, error_percentage):
    folder = 'no'
    offset = 20

    global week_names

    if week_names and week_names[:5] == [week_names[0], startDate, endDate, blocks, error_percentage]:
        return week_names[0]

    def clean_keydata(keydata):
        return [item for item in keydata if item.get('Deleted', 'No') != "Yes"]

    def get_date_range(start, end):
        start_dt = datetime.strptime(start, "%Y-%m-%d")
        end_dt = datetime.strptime(end, "%Y-%m-%d")
        days = (end_dt - start_dt).days + 1
        return [start_dt + timedelta(days=x) for x in range(days)]

    def fetch_scada_data(code, date_range):
        filter = {
            'Date': {'$gte': datetime(date_range[0].year, date_range[0].month, date_range[0].day, 0, 0, 0, tzinfo=timezone.utc),
                     '$lte': datetime(date_range[-1].year, date_range[-1].month, date_range[-1].day, 0, 0, 0, tzinfo=timezone.utc)},
            'Code': code
        }
        project = {'_id': 0, 'Data': 1, 'Date': 1}
        cursor = Scada_database.find(filter=filter, projection=project).sort('Date', ASCENDING)
        date_map = {d['Date'].date(): d.get('Data', []) for d in cursor}
        # Use numpy for fast flattening and nan handling
        data = []
        for it in date_range:
            arr = date_map.get(it.date(), None)
            if arr:
                arr = np.array(arr, dtype=np.float32)
                arr = np.nan_to_num(arr, nan=0.0)
                arr = np.round(arr, 2)
                data.extend(arr.tolist())
            else:
                data.extend([0.0]*96)
        return data

    def fetch_meter_data(meter_id, date_range, db):
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
            for d in Data_Table.find(filter=filter, projection=project):
                date_map[d['date'].date()] = d.get('data', [])
        data = []
        for it in date_range:
            arr = date_map.get(it.date(), None)
            if arr:
                arr = np.array(arr, dtype=np.float32)
                arr = np.nan_to_num(arr, nan=0.0)
                arr = np.round(arr * 4, 2)
                data.extend(arr.tolist())
            else:
                data.extend([0.0]*96)
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
            file_path = os.path.join(full_path, meters)
            if os.path.isdir(full_path) and os.path.exists(file_path):
                dfEnd1 = pd.read_csv(file_path, header=None)[0]
                for i in range(1, len(dfEnd1)):
                    oneHourDataEnd1 = np.array([changeToFloat(x) for x in dfEnd1[i].split()[1:]], dtype=np.float32)
                    oneHourDataEnd1 = np.nan_to_num(oneHourDataEnd1, nan=0.0)
                    oneHourDataEnd1 = np.round(oneHourDataEnd1 * 4, 2)
                    data.extend(oneHourDataEnd1.tolist())
        return data

    CONNECTION_STRING = "mongodb://10.3.230.94:1434"
    client = MongoClient(CONNECTION_STRING)
    db = client['meterDataArchival']
    keydata = clean_keydata(list(mapping_table.find(filter={}, projection={'_id': 0})))
    final_data_to_send = {}
    constituent_keys = ['BH', 'DV', 'GR', 'JH', 'MIS_CALC_TO', 'NTPC_ER_1', 'NTPC_ODISHA', 'PG_ER1', 'PG_ER2', 'WB', 'SI', 'PG_odisha_project']
    lookupDictionary = defaultdict(list)
    date_range = get_date_range(startDate, endDate)
    scada_keys, meter_keys = set(), set()
    for item in keydata:
        for k in ['Key_To_End', 'Key_Far_End']:
            if item[k].split(":")[0] not in ["No Key", "Duplicate Key"]:
                scada_keys.add(item[k])
        for k in ['Meter_To_End', 'Meter_Far_End']:
            if item[k].split(":")[0] not in ["No Key", "Duplicate Key"]:
                meter_keys.add(item[k])

    # Parallel fetch for SCADA
    with ThreadPoolExecutor(max_workers=32) as executor:
        scada_data_dict = dict(zip(scada_keys, executor.map(lambda key: fetch_scada_data(key, date_range), scada_keys)))
    # Parallel fetch for Meter
    meter_func = partial(fetch_meter_data, db=db) if folder == "no" else fetch_meter_data_from_file
    with ThreadPoolExecutor(max_workers=32) as executor:
        meter_data_dict = dict(zip(meter_keys, executor.map(lambda key: meter_func(key, date_range), meter_keys)))

    drawal_feeders = {"BH_DRAWAL", "DV_DRAWAL", "GR_DRAWAL", "WB_DRAWAL", "JH_DRAWAL", "SI_DRAWAL"}
    total_count = 0

    def process_item(item):
        nonlocal total_count
        Feeder_Name = item['Feeder_Name']
        Key_To_End = item['Key_To_End']
        Key_Far_End = item['Key_Far_End']
        Meter_To_End = item['Meter_To_End']
        Meter_Far_End = item['Meter_Far_End']
        Feeder_From = item['Feeder_From']
        To_Feeder = item['To_Feeder']

        def get_data(key, data_dict):
            return np.array(data_dict.get(key, [0.0] * (len(date_range) * 96)), dtype=np.float32)

        valid_to_end = (Key_To_End.split(":")[0] not in ["No Key", "Duplicate Key"]) and (Meter_To_End.split(":")[0] not in ["No Key", "Duplicate Key"])
        scada_to = get_data(Key_To_End, scada_data_dict) if valid_to_end else np.zeros(len(date_range) * 96, dtype=np.float32)
        meter_to = get_data(Meter_To_End, meter_data_dict) if valid_to_end else np.zeros(len(date_range) * 96, dtype=np.float32)
        valid_far_end = (Key_Far_End.split(":")[0] not in ["No Key", "Duplicate Key"]) and (Meter_Far_End.split(":")[0] not in ["No Key", "Duplicate Key"])
        scada_far = get_data(Key_Far_End, scada_data_dict) if valid_far_end else np.zeros(len(date_range) * 96, dtype=np.float32)
        meter_far = get_data(Meter_Far_End, meter_data_dict) if valid_far_end else np.zeros(len(date_range) * 96, dtype=np.float32)

        if Feeder_Name in drawal_feeders or "ICT" in Feeder_Name.upper():
            # meter_to = np.abs(meter_to)
            # meter_far = np.abs(meter_far)
            return

        error_pct = int(error_percentage)
        block_limit = int(blocks)
        # Vectorized difference and mask
        idx = np.arange(1, len(meter_to))
        # To End
        mask_to = (
            (meter_to[1:] != meter_to[:-1]) &
            (scada_to[1:] != scada_to[:-1]) &
            (meter_to[1:] != 0) &
            (scada_to[1:] != 0) &
            (np.abs(meter_to[1:]) > offset) &
            (np.abs(scada_to[1:]) > offset)
        )
        x_to = np.abs(meter_to[1:][mask_to])
        y_to = np.abs(scada_to[1:][mask_to])
        diff_to = np.abs(x_to - y_to)
        percent_to = np.abs(np.round(100 * (x_to - y_to) / x_to, 2))
        count_to = np.sum((diff_to > 5) & (percent_to > error_pct))

        # Far End
        mask_far = (
            (meter_far[1:] != meter_far[:-1]) &
            (scada_far[1:] != scada_far[:-1]) &
            (meter_far[1:] != 0) &
            (scada_far[1:] != 0) &
            (np.abs(meter_far[1:]) > offset) &
            (np.abs(scada_far[1:]) > offset)
        )
        x_far = np.abs(meter_far[1:][mask_far])
        y_far = np.abs(scada_far[1:][mask_far])
        diff_far = np.abs(x_far - y_far)
        percent_far = np.abs(np.round(100 * (x_far - y_far) / x_far, 2))
        count_far = np.sum((diff_far > 5) & (percent_far > error_pct))

        if count_to > block_limit:
            constituent_name = Feeder_From
            if constituent_name in constituent_keys and [Feeder_Name, 0] not in lookupDictionary[constituent_name]:
                lookupDictionary[constituent_name].append([Feeder_Name, 0])
                if constituent_name != 'MIS_CALC_TO':
                    total_count += 1

        if count_far > block_limit:
            constituent_name = To_Feeder
            if constituent_name in constituent_keys and [Feeder_Name, 1] not in lookupDictionary[constituent_name]:
                lookupDictionary[constituent_name].append([Feeder_Name, 1])
                if constituent_name != 'MIS_CALC_TO':
                    total_count += 1

    with ThreadPoolExecutor(max_workers=32) as executor:
        list(executor.map(process_item, keydata))

    all_names= []

    for key in constituent_keys:
        final_data_to_send[key] = lookupDictionary[key]

        for item in lookupDictionary[key]:
            all_names.append(item[0])

    len(all_names)- len(set(all_names))

    final_data_to_send['total_count'] = [total_count-(len(all_names)- len(set(all_names))), len(keydata)-75]  # Assuming 41 is the number of non-constituent keys

    week_names = [final_data_to_send,startDate, endDate, blocks, error_percentage]
    return final_data_to_send


def daywise_names(date, error_percentage):
    folder = 'no'
    offset = 20

    global day_names

    if len(day_names) > 0 and day_names[1]== date and day_names[2]== error_percentage:
        return day_names[0]

    def clean_keydata(keydata):
        return [item for item in keydata if item.get('Deleted', 'No') != "Yes"]

    def get_date_range(start, end):
        start_dt = datetime.strptime(start, "%Y-%m-%d")
        end_dt = datetime.strptime(end, "%Y-%m-%d")
        days = (end_dt - start_dt).days + 1
        return [start_dt + timedelta(days=x) for x in range(days)]

    def fetch_scada_data(code, date_range):
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
            arr = date_map.get(it.date(), None)
            if arr:
                arr = np.array(arr, dtype=np.float32)
                arr = np.nan_to_num(arr, nan=0.0)
                arr = np.round(arr, 2)
                data.extend(arr.tolist())
            else:
                data.extend([0.0]*96)
        return data

    def fetch_meter_data(meter_id, date_range, db):
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
            for d in Data_Table.find(filter=filter, projection=project):
                date_map[d['date'].date()] = d.get('data', [])
        data = []
        for it in date_range:
            arr = date_map.get(it.date(), None)
            if arr:
                arr = np.array(arr, dtype=np.float32)
                arr = np.nan_to_num(arr, nan=0.0)
                arr = np.round(arr * 4, 2)
                data.extend(arr.tolist())
            else:
                data.extend([0.0]*96)
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
            file_path = os.path.join(full_path, meters)
            if os.path.isdir(full_path) and os.path.exists(file_path):
                dfEnd1 = pd.read_csv(file_path, header=None)[0]
                for i in range(1, len(dfEnd1)):
                    oneHourDataEnd1 = np.array([changeToFloat(x) for x in dfEnd1[i].split()[1:]], dtype=np.float32)
                    oneHourDataEnd1 = np.nan_to_num(oneHourDataEnd1, nan=0.0)
                    oneHourDataEnd1 = np.round(oneHourDataEnd1 * 4, 2)
                    data.extend(oneHourDataEnd1.tolist())
        return data

    CONNECTION_STRING = "mongodb://10.3.230.94:1434"
    client = MongoClient(CONNECTION_STRING)
    db = client['meterDataArchival']
    keydata = clean_keydata(list(mapping_table.find(filter={}, projection={'_id': 0})))
    final_data_to_send = [[] for _ in range(96)]
    constituent_keys = ['BH', 'DV', 'GR', 'JH', 'MIS_CALC_TO', 'NTPC_ER_1', 'NTPC_ODISHA', 'PG_ER1', 'PG_ER2', 'WB', 'SI', 'PG_odisha_project']
    date_range = get_date_range(date, date)
    scada_keys, meter_keys = set(), set()
    for item in keydata:
        for k in ['Key_To_End', 'Key_Far_End']:
            if item[k].split(":")[0] not in ["No Key", "Duplicate Key"]:
                scada_keys.add(item[k])
        for k in ['Meter_To_End', 'Meter_Far_End']:
            if item[k].split(":")[0] not in ["No Key", "Duplicate Key"]:
                meter_keys.add(item[k])

    # Parallel fetch for SCADA
    with ThreadPoolExecutor(max_workers=32) as executor:
        scada_data_dict = dict(zip(scada_keys, executor.map(lambda key: fetch_scada_data(key, date_range), scada_keys)))
    # Parallel fetch for Meter
    meter_func = partial(fetch_meter_data, db=db) if folder == "no" else fetch_meter_data_from_file
    with ThreadPoolExecutor(max_workers=32) as executor:
        meter_data_dict = dict(zip(meter_keys, executor.map(lambda key: meter_func(key, date_range), meter_keys)))

   

    drawal_feeders = {"BH_DRAWAL", "DV_DRAWAL", "GR_DRAWAL", "WB_DRAWAL", "JH_DRAWAL", "SI_DRAWAL"}

    def process_item(item):
        Feeder_Name = item['Feeder_Name']
        Key_To_End = item['Key_To_End']
        Key_Far_End = item['Key_Far_End']
        Meter_To_End = item['Meter_To_End']
        Meter_Far_End = item['Meter_Far_End']
        Feeder_From = item['Feeder_From']
        To_Feeder = item['To_Feeder']

        def get_data(key, data_dict):
            return np.array(data_dict.get(key, [0.0] * (len(date_range) * 96)), dtype=np.float32)

        valid_to_end = (Key_To_End.split(":")[0] not in ["No Key", "Duplicate Key"]) and (Meter_To_End.split(":")[0] not in ["No Key", "Duplicate Key"])
        scada_to = get_data(Key_To_End, scada_data_dict) if valid_to_end else np.zeros(len(date_range) * 96, dtype=np.float32)
        meter_to = get_data(Meter_To_End, meter_data_dict) if valid_to_end else np.zeros(len(date_range) * 96, dtype=np.float32)
        valid_far_end = (Key_Far_End.split(":")[0] not in ["No Key", "Duplicate Key"]) and (Meter_Far_End.split(":")[0] not in ["No Key", "Duplicate Key"])
        scada_far = get_data(Key_Far_End, scada_data_dict) if valid_far_end else np.zeros(len(date_range) * 96, dtype=np.float32)
        meter_far = get_data(Meter_Far_End, meter_data_dict) if valid_far_end else np.zeros(len(date_range) * 96, dtype=np.float32)

        if Feeder_Name in drawal_feeders:
            meter_to = np.abs(meter_to)
            meter_far = np.abs(meter_far)

        if Feeder_From == "MIS_CALC_TO" or To_Feeder == "MIS_CALC_TO":
            return

        error_pct = int(error_percentage)
        for i in range(len(meter_to)):
            # To End

            if i == 0:
                if (meter_to[i] != 0 and scada_to[i] != 0 and abs(meter_to[i]) > offset and abs(scada_to[i]) > offset):
                    x, y = abs(meter_to[i]), abs(scada_to[i])
                    if abs(x - y) > 5:
                        to_percent = abs(round((100 * (x - y) / abs(max(x, y))), 2))
                        if to_percent > error_pct:
                            final_data_to_send[i].append(Feeder_Name+" To End: "+ str(to_percent)+" %")
                # Far End
                if (meter_far[i] != 0 and scada_far[i] != 0 and abs(meter_far[i]) > offset and abs(scada_far[i]) > offset):
                    x, y = abs(meter_far[i]), abs(scada_far[i])
                    if abs(x - y) > 5:
                        far_percent = abs(round((100 * (x - y) / abs(max(x, y))), 2))
                        if far_percent > error_pct:
                            final_data_to_send[i].append(Feeder_Name+" Far End: "+ str(far_percent)+" %")
            else:
                if (meter_to[i] != meter_to[i-1] and scada_to[i] != scada_to[i-1] and meter_to[i] != 0 and scada_to[i] != 0 and abs(meter_to[i]) > offset and abs(scada_to[i]) > offset):
                    x, y = abs(meter_to[i]), abs(scada_to[i])
                    if abs(x - y) > 5:
                        to_percent = abs(round((100 * (x - y) / abs(max(x, y))), 2))
                        if to_percent > error_pct:
                            final_data_to_send[i].append(Feeder_Name+" To End: "+ str(to_percent)+" %")
                # Far End
                if (meter_far[i] != meter_far[i-1] and scada_far[i] != scada_far[i-1] and meter_far[i] != 0 and scada_far[i] != 0 and abs(meter_far[i]) > offset and abs(scada_far[i]) > offset):
                    x, y = abs(meter_far[i]), abs(scada_far[i])
                    if abs(x - y) > 5:
                        far_percent = abs(round((100 * (x - y) / abs(max(x, y))), 2))
                        if far_percent > error_pct:
                            if not any(region in Feeder_Name.upper() for region in ["(SR)", "(NR)", "(WR)", "(NER)", "(NEPAL)"]):
                                final_data_to_send[i].append(Feeder_Name+" Far End: "+ str(far_percent)+" %")

    with ThreadPoolExecutor(max_workers=32) as executor:
        list(executor.map(process_item, keydata))

    count_list = []
    percent_list = []
    base_list = list(range(1, 97))
    for i in range(len(final_data_to_send)):
        count_list.append(len(final_data_to_send[i]))
        final_data_to_send[i]= list(set(final_data_to_send[i]))
        def extract_percentage(s):
            try:
                return float(s.split(":")[-1].replace("%", "").strip())
            except Exception:
                return 0.0
        final_data_to_send[i] = sorted(final_data_to_send[i], key=extract_percentage, reverse=True)
        percent_list.append(extract_percentage(final_data_to_send[i][0]) if len(final_data_to_send[i])>0 else 0.0)

    day_names = [[final_data_to_send, count_list, base_list, percent_list],date, error_percentage]

    return [final_data_to_send, count_list, base_list, percent_list]