#! /usr/bin/python3
from datetime import datetime, timedelta, timezone
from json import load, dump, dumps
from os import getcwd
from os.path import dirname, exists, realpath, join
from sys import argv as sys_args
from time import sleep

from requests import post

try:
    import pytz
except ImportError:
    pytz = None
    print("pytz not installed. Assuming local tz")


def gettime():
    # Timezones are annoying
    if pytz:
        return datetime.now(pytz.timezone(config["comp_tz"])).replace(tzinfo=None)
    return datetime.now()


# Color codes for priorities
priority = {"critical": 16711680, "high": 16733440, "medium": 16759552, "low": 16776960, "info": 65535}

standalone = len(sys_args) == 1
print(f"Starting in {('stateless', 'standalone')[standalone]} mode")
specific = -1
send_all = False

if not standalone:
    if sys_args[1] == "all":
        if input("Send all injects? (yes):") != "yes": exit()
        send_all = True
    else:
        try:
            specific = int(sys_args[1])
            print(f"Posting only inject #{specific}")
        except ValueError:
            specific = -1

config_directory = realpath(join(getcwd(), dirname(__file__)))
injects = load(open(join(config_directory, "injects.json")))
config = load(open(join(config_directory, "config.json")))
if specific == -1 and exists(join(config_directory, "state.json")):
    status = load(open(join(config_directory, "state.json")))
else:
    status = {"last_sent": -1}

close_enough = timedelta(seconds=config["close_enough"])
local_timezone = timezone(gettime().replace(microsecond=0) - datetime.utcnow().replace(microsecond=0))

for inject_number, inject in enumerate(injects["injects"]):
    inject_post_time = datetime.strptime(config["comp_date"] + " " + inject["post"], "%Y-%m-%d %H:%M")
    if not send_all:
        # Skip if already sent
        if inject_number <= status["last_sent"]:
            continue

        if standalone:
            # Wait until time to send it
            # We assume injects are in chronological order
            while inject_post_time > gettime() + close_enough:
                sleep_sec = int((inject_post_time - gettime()).total_seconds() + 1)
                print(f"Sleeping {sleep_sec} seconds before next check")
                sleep(sleep_sec)

        else:  # not standalone
            if specific == -1:
                # Skip if it is not time yet
                if inject_post_time > gettime() + close_enough:
                    continue
            else:
                # If we want a specific one only send that one
                if inject_number != specific:
                    continue

    inject_due_time = datetime.strptime(config["comp_date"] + " " + inject["due"], "%Y-%m-%d %H:%M")
    inject_due_time = inject_due_time.replace(tzinfo=local_timezone)
    # Should send now
    discord = {
        "content": config["discord_content"],
        "embeds": [
            {
                "title": inject["name"],
                "description": inject["desc"] + f"""\n\nPriority: {inject['priority']}
Active: {inject_post_time.strftime('%H:%M')} - {inject_due_time.strftime('%H:%M')} {config['comp_tz'].split('/')[1]}""",
                "url": inject["link"] if "link" in inject else "",
                "color": priority[inject['priority']],
                "author": {
                    "name": f"Inject #{inject_number}",
                    "icon_url": "https://icon-library.net/images/icon-new/icon-new-23.jpg"
                },
                "footer": {
                    "text": "Due",
                    "icon_url": "https://defsec.club/defsec.png"
                },
                "timestamp": inject_due_time.isoformat()
            }
        ]
    }
    # print(dumps(discord))
    # print(f"Posting inject {inject_number}: {inject}")

    response = post(config["discord"], data=dumps(discord), headers={"Content-Type": "application/json"})
    if response.status_code == 204:
        print(f"Posted inject #{inject_number}")
    else:
        print(f"Error posting inject #{inject_number}: {response.status_code}")

    # print("====")
    # print(response.text)
    # print("====")
    # post(webhooks["engine"], data=json.dumps({
    #     "idk_what": "to_put_here", "inject": num
    # }), headers={"Content-Type": "application/json"})

    if not send_all and specific == -1:
        status["last_sent"] = inject_number
        dump(status, open("state.json", 'w'))

    # Keep discord from being mad at multiple injects (Ratelimit ~ 1/s)
    sleep(1)
