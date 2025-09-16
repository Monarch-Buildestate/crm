from time import sleep
from json import *
import sqlite3
import requests
from datetime import *
from discord_webhook import DiscordWebhook, DiscordEmbed
import sys

from classes.Call import Call

creds = load(open('config.json'))
conn = sqlite3.connect('database.db')

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
    interval = 120
    while True:
        take_backup()
        sleep(interval)

if __name__ == "__main__":
    # if "--single" or "-s" in sys.argv, run only once
    if "--single" in sys.argv or "-s" in sys.argv:
        take_backup()
    else:
        main()
