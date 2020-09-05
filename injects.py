import json
import sys
from datetime import datetime, timedelta, timezone
from os.path import dirname, exists
from time import sleep

import requests

standalone = len(sys.argv) == 1
print(f"Starting in {('stateless', 'standalone')[standalone]} mode")

dir = dirname(__file__)

injects = json.load(open(dir + "/injects.json", 'r'))
webhooks = json.load(open(dir + "/webhooks.json", 'r'))

if exists(dir + "/status.json"):
    status = json.load(open(dir + "/status.json", 'r'))
else:
    status = {"last_sent": 0}

TZinfo = timezone(datetime.now() - datetime.utcnow())

for num, inject in enumerate(injects["injects"]):

    # Skip if already sent
    if num <= status["last_sent"]:
        continue

    if standalone:
        target = datetime.strptime(inject["post"], "%Y-%m-%d %H:%M:%S")
        while target > datetime.now() + timedelta(minutes=1):
            sleep_sec = int((target - datetime.now() + timedelta(minutes=1)).total_seconds() / 2 + 1)
            print(f"Sleeping {sleep_sec} seconds before next check")
            sleep(sleep_sec)
    else:
        # Skip if it is for more than 1 minute from now
        if datetime.strptime(inject["post"], "%Y-%m-%d %H:%M:%S") > datetime.now() + timedelta(
                minutes=1):
            continue

    # Should send now
    discord = {
        "content": webhooks["discord_content"],
        "embeds": [
            {
                "title": inject["name"],
                "description": inject["desc"],
                "url": "http://scoring.engine/to/be/implemented/later/inject1.info",
                "color": 16711680,
                "author": {
                    "name": f"Inject #{num}",
                    "icon_url": "https://cdn.discordapp.com/attachments/406863862751690752/751889394910232626/assignment_late-24px.svg"
                },
                "footer": {
                    "text": "Due",
                    "icon_url": "https://media.discordapp.net/attachments/406863862751690752/751888201668624435/defseclogo.png?width=677&height=677"
                },
                "timestamp": datetime.strptime(inject["due"], '%Y-%m-%d %H:%M:%S').replace(tzinfo=TZinfo).isoformat()
            }
        ],
        "avatar_url": "https://media.discordapp.net/attachments/406863862751690752/751888201668624435/defseclogo.png?width=677&height=677"
    }

    print(f"{num} {inject}")

    print(requests.post(webhooks["discord"], data=json.dumps(discord), headers={"Content-Type": "application/json"}))
    status["last_sent"] = num
    # requests.post(webhooks["engine"], data=json.dumps({
    #     "idk_what": "to_put_here", "inject": num
    # }), headers={"Content-Type": "application/json"})
    json.dump(status, open("status.json", 'w'))
