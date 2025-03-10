from time import sleep
from json import *
import sqlite3
import requests
from datetime import *
from discord_webhook import DiscordWebhook, DiscordEmbed

from classes.Call import Call

creds = load(open('config.json'))
conn = sqlite3.connect('database.db')

def fetch_records(page=1):
    tatatelekey = creds.get("tata_tele_api_key")
    if not tatatelekey:
        print("Tata Tele key not found")
        exit(1)
    url = "https://api-smartflo.tatateleservices.com/v1/call/records?"+"did_numbers=" + creds.get("did_number")
    payload = {}
    headers = {
        "accept": "application/json",
        "content-type": "application/json",
        "Authorization": tatatelekey,
    }
    if page:
        url += "&page=" + str(page)
    response = requests.get(
        url,
        json=payload,
        headers=headers,
    )
    print("making a request to ")
    print(response.url)
    # write this response.json to a file
    with open("test.json", "w+") as f:
        dump(response.json(), f, indent=4)
    if response.status_code != 200:
        print("Error fetching calls")
        return []
    else:
        return response.json()

def take_backup():
    webhooks = creds.get("webhooks")
    if not webhooks:
        print("Webhooks not found")
        return
    maintainer_webhook_url = webhooks.get("maintainer")
    if not maintainer_webhook_url:
        print("Maintainer webhook url not found")
        return
    # send the database.db
    for file in ["database.db", "config.json"]:
        webhook = DiscordWebhook(url=maintainer_webhook_url)
        webhook.add_file(file=open(file, "rb"),filename=file)
        response = webhook.execute()
        print(response)
    print("Backup taken")



def main():
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
            if not records.get("results"):
                go_for_front = True
                print("No new records")
                continue
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
        take_backup()
        sleep(interval)



if __name__ == "__main__":
    main()	
