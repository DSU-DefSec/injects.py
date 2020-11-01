from datetime import datetime, timedelta, timezone
from json import load, dump, dumps
from os import getcwd
from os.path import dirname, exists, realpath, join
from sys import argv as sys_args
from time import sleep

from requests import post


def gettime():
    return datetime.now()


priority = {"critical": 16711680, "high": 16733440, "medium": 16759552, "low": 16776960, "info": 65535}

standalone = len(sys_args) == 1
print(f"Starting in {('stateless', 'standalone')[standalone]} mode")
specific = -1
send_all = False
if not standalone:
    if sys_args[1] == "all":
        if input("Send all injects? (yes):") != "yes":
            exit()
        send_all = True
    else:
        try:
            specific = int(sys_args[1])
            print(f"Posting only inject #{specific}")
        except ValueError:
            specific = -1

dir = realpath(join(getcwd(), dirname(__file__)))
injects = load(open(join(dir, "injects.json")))
config = load(open(join(dir, "config.json")))
if specific == -1 and exists(join(dir, "state.json")):
    status = load(open(join(dir, "state.json")))
else:
    status = {"last_sent": -1}

close_enough = timedelta(seconds=config["close_enough"])
local_timezone = timezone(datetime.now() - datetime.utcnow())

for inject_number, inject in enumerate(injects["injects"]):
    inject_post_time = datetime.strptime(inject["post"], "%Y-%m-%d %H:%M:%S")
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
        else:
            if specific == -1:
                # Skip if it is not time yet
                if inject_post_time > gettime() + close_enough:
                    continue
            else:
                # If we want a specific one only send that one
                if inject_number != specific:
                    continue

    inject_due_time = datetime.strptime(inject["due"], "%Y-%m-%d %H:%M:%S")
    # Should send now
    discord = {
        "content": config["discord_content"],
        "embeds": [
            {
                "title": inject["name"],
                "description": inject["desc"] + f"""\n\nPriority: {inject['priority']}
Active: {inject_post_time.strftime('%H:%M')} - {inject_due_time.strftime('%H:%M')}""",
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
                "timestamp": inject_due_time.replace(tzinfo=local_timezone).isoformat()
            }
        ]
    }
    print(dumps(discord))
    print(f"Posting inject {inject_number}: {inject}")

    response = post(config["discord"], data=dumps(discord), headers={"Content-Type": "application/json"})
    print(
        f"Posted inject #{inject_number}" if response.status_code == 204 else f"Error posting inject #{inject_number}: {response.status_code}\n{response.text}")
    # post(webhooks["engine"], data=json.dumps({
    #     "idk_what": "to_put_here", "inject": num
    # }), headers={"Content-Type": "application/json"})
    if not send_all and specific == -1:
        status["last_sent"] = inject_number
        dump(status, open("state.json", 'w'))

    # Keep discord from being mad at multiple injects
    sleep(1)
