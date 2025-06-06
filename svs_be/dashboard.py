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
import concurrent.futures

app = Flask(__name__)
CORS(app)

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
        data = list(chain.from_iterable(
            [0 if pd.isna(val) else round(val, 2) for val in date_map.get(it.date(), [])] if date_map.get(it.date(), []) else [0]*96
            for it in date_range
        ))
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
            for d in Data_Table.find(filter=filter, projection=project):
                date_map[d['date'].date()] = d.get('data', [])
        data = list(chain.from_iterable(
            [0 if pd.isna(val) else round(4 * val, 2) for val in date_map.get(it.date(), [])] if date_map.get(it.date(), []) else [0]*96
            for it in date_range
        ))
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
                    oneHourDataEnd1 = [changeToFloat(x) for x in dfEnd1[i].split()[1:]]
                    data.extend([0 if pd.isna(x) else round(4 * x, 2) for x in oneHourDataEnd1])
        return data

    startDateObj = datetime.strptime(startDate, "%Y-%m-%d")
    endDateObj = datetime.strptime(endDate, "%Y-%m-%d")
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
    with ThreadPoolExecutor(max_workers=16) as executor:
        scada_data_dict = dict(zip(scada_keys, executor.map(lambda key: fetch_scada_data(key, date_range), scada_keys)))
    # Parallel fetch for Meter
    meter_func = partial(fetch_meter_data, db=db) if folder == "no" else fetch_meter_data_from_file
    with ThreadPoolExecutor(max_workers=16) as executor:
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
            return data_dict.get(key, [0] * (len(date_range) * 96))

        valid_to_end = (Key_To_End.split(":")[0] not in ["No Key", "Duplicate Key"]) and (Meter_To_End.split(":")[0] not in ["No Key", "Duplicate Key"])
        scada_to = get_data(Key_To_End, scada_data_dict) if valid_to_end else [0] * (len(date_range) * 96)
        meter_to = get_data(Meter_To_End, meter_data_dict) if valid_to_end else [0] * (len(date_range) * 96)
        valid_far_end = (Key_Far_End.split(":")[0] not in ["No Key", "Duplicate Key"]) and (Meter_Far_End.split(":")[0] not in ["No Key", "Duplicate Key"])
        scada_far = get_data(Key_Far_End, scada_data_dict) if valid_far_end else [0] * (len(date_range) * 96)
        meter_far = get_data(Meter_Far_End, meter_data_dict) if valid_far_end else [0] * (len(date_range) * 96)

        if Feeder_Name in drawal_feeders:
            meter_to = [abs(x) for x in meter_to]
            meter_far = [abs(x) for x in meter_far]

        count_to = count_far = 0
        error_pct = int(error_percentage)
        block_limit = int(blocks)
        for i in range(len(meter_to)):
            x1, y1 = meter_to[i], scada_to[i]
            x2, y2 = meter_far[i], scada_far[i]
            # To End
            if i and meter_to[i] != meter_to[i-1] and scada_to[i] != scada_to[i-1] and meter_to[i] != 0 and scada_to[i] != 0 and abs(meter_to[i]) > offset and abs(scada_to[i]) > offset:
                x, y = abs(meter_to[i]), abs(scada_to[i])
                if abs(x - y) > 5:
                    to_percent = abs(round((100 * (x - y) / x), 2))
                    if to_percent > error_pct:
                        count_to += 1
            # Far End
            if i and meter_far[i] != meter_far[i-1] and scada_far[i] != scada_far[i-1] and meter_far[i] != 0 and scada_far[i] != 0 and abs(meter_far[i]) > offset and abs(scada_far[i]) > offset:
                x, y = abs(meter_far[i]), abs(scada_far[i])
                if abs(x - y) > 5:
                    far_percent = abs(round((100 * (x - y) / x), 2))
                    if far_percent > error_pct:
                        count_far += 1

        if count_to > block_limit:
            constituent_name = Feeder_From
            if constituent_name in constituent_keys and [Feeder_Name, 0] not in lookupDictionary[constituent_name]:
                lookupDictionary[constituent_name].append([Feeder_Name, 0])
                total_count += 1
        if count_far > block_limit:
            constituent_name = To_Feeder
            if constituent_name in constituent_keys and [Feeder_Name, 1] not in lookupDictionary[constituent_name]:
                lookupDictionary[constituent_name].append([Feeder_Name, 1])
                total_count += 1

    with ThreadPoolExecutor(max_workers=16) as executor:
        list(executor.map(process_item, keydata))

    for key in constituent_keys:
        final_data_to_send[key] = lookupDictionary[key]
    final_data_to_send['total_count'] = [total_count, len(keydata)]
    return final_data_to_send
