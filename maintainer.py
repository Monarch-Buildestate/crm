from time import sleep
from json import *
import sqlite3
import requests
from datetime import *

from classes.Call import Call

creds = load(open('config.json'))
conn = sqlite3.connect('database.db')

def fetch_records(page=1):
    tatatelekey = creds.get("tata_tele_api_key")
    if not tatatelekey:
        print("Tata Tele key not found")
        exit(1)
    url = "https://api-smartflo.tatateleservices.com/v1/call/records?"
    payload = {}
    headers = {
        "accept": "application/json",
        "content-type": "application/json",
        "Authorization": tatatelekey,
    }
    params = {"Authorization": tatatelekey, "did_number": creds.get("did_number")}
    if page:
        params['page'] = str(page)
    response = requests.get(
        url,
        json=payload,
        headers=headers,
        params=params,
    )
    # write this response.json to a file
    with open("test.json", "w+") as f:
        dump(response.json(), f, indent=4)
    if response.status_code != 200:
        print("Error fetching calls")
        return []
    else:
        return response.json()

go_for_front = False
interval = 120
page_count = 0
while True:
    # get oldest record  and length of records
    page_count += 1 
    cursor = conn.cursor()
    if not go_for_front:
        cursor.execute("SELECT * FROM calls ORDER BY call_time DESC")
        last_record = cursor.fetchall()
        total_records_count= len(last_record)
        if last_record:
            last_record = last_record[0]
            last_record = Call(last_record)
        
        # if each page have 20 records. we will be requesting page number total_records/20 + 1 
        records = fetch_records(page_count)
        if total_records_count >= records.get('count'):
            go_for_front = True
            print("No new records")
            continue # make a request to front already without waiting anymore
    else:
        records = fetch_records(1)
        print("FETCHING FROM FRONT")
    with conn:
        cursor = conn.cursor()
        for record in records.get("results"):
            call = Call.from_dict(record)
            try:
                cursor.execute(
                    "INSERT INTO calls VALUES (?,?,?,?,?,?,?,?,?,?,?)",
                    (
                        call.id,
                        call.call_id,
                        call.uuid,
                        call.description,
                        call.time,
                        call.duration,
                        call.agent_number,
                        call.client_number,
                        call.recording_url,
                        call.did_number,
                        call.status,
                    ),
                )
            except sqlite3.IntegrityError:
                print("Record already exists")
                pass
        conn.commit()
    sleep(interval)