#!/Library/ManagedFrameworks/Python/Python3.framework/Versions/Current/bin/python3

import requests
import datetime
import platform
import os
import json
import subprocess
from os.path import exists

# add major OS logic

# get info from apple
URL = "https://gdmf.apple.com/v2/pmv"
r = requests.get(URL, verify=False)
list = r.json()
macOS_Latest = list["AssetSets"]["macOS"][0]["ProductVersion"]
posting_Date_STR = list["AssetSets"]["macOS"][0]["PostingDate"]
# convert to date and give 7 day grace period
posting_Date = datetime.datetime.strptime(posting_Date_STR, '%Y-%m-%d')
start_Date = posting_Date + datetime.timedelta(days=7)
final_Date = posting_Date + datetime.timedelta(days=30)
infolink="https://support.apple.com/en-au/HT201222"
today = datetime.date.today()
days_Left = int((final_Date.date() - today).days)
# get current OS version
current_OS = platform.mac_ver()[0]
dialog="/usr/local/bin/dialog"

def run_dialog(contentDict):
    open_SU = "open -b com.apple.systempreferences /System/Library/PreferencePanes/SoftwareUpdate.prefPane"
    """Runs the SwiftDialog app and returns the exit code"""
    jsonString = json.dumps(contentDict)
    exit_code = os.system(f"{dialog} --jsonstring '{jsonString}' --button1shellaction '{open_SU}'")
    return exit_code

def icon_Check():
    icon_Path = "/Library/Application Support/Dialog/VentureWell_logo_mark.png"
    if os.path.exists(icon_Path):
        pass
    else:
        r = requests.get("https://raw.githubusercontent.com/unfo33/venturewell/main/VentureWell_logo_mark.png")
        open(icon_Path, 'wb').write(r.content)

def update_Check():
    # consider adding kickstart
    # check for updates
    update = ["softwareupdate", "-l"]
    test = subprocess.Popen(update, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    result = test.communicate()
    if result[1] == b'No new software available.\n':
        return False
    else:
        return True

# check type of update
if current_OS[0:1] == macOS_Latest[0:1]:
    Update = "feature"
    time = 40
    if current_OS[3] == macOS_Latest[3]:
        Update = "minor"
        time = 20
elif current_OS[0:1] != macOS_Latest[0:1]:
    Update = "major"
    time = "60+"

# main dialog content
content_dict = {
    "alignment": "center",
    "button1text": "Update Now",
    "centericon": 1,
    "icon": "/Library/Application Support/Dialog/VentureWell_logo_mark.png",
    "infobuttonaction": infolink,
    "infobuttontext": "More Info",
    "message": f"## Operating System Update Available\n\nYour Update Path: **{current_OS}** → **{macOS_Latest}**\n\nmacOS **{macOS_Latest}** was released on **{posting_Date_STR}**. It is a **{Update}** update and will require around **{time}** minutes downtime.\n\nDays Remaining to Update: **{days_Left}**\n\n*To begin the update, click on **Update Now** and follow the provided steps.*\n*You can also use the [Mac Manage App](https://docs.google.com/document/d/1oWuT7Tgsv-DHFNmivSc_Ibz61vtKKkRvqQoYmQsrKzI/edit?usp=sharing) to update at your convenience*.",
    "messagefont": "size=16",
    "title": "none",
    "button2text": "Defer",
    "height": "420",
    "width": "900",
    "moveable": 1,
}

icon_Check()

if current_OS == macOS_Latest:
    print("On Latest Version")
else:
    if update_Check():
        if days_Left <= 23:
            message = {"message": f"## Operating System Update Required\n\nYour Update Path: **{current_OS}** → **{macOS_Latest}**\n\nmacOS **{macOS_Latest}** was released on **{posting_Date_STR}**. It is a **{Update}** update and will require around **{time}** minutes downtime.\n\nDays Remaining to Update: **{days_Left}**\n\n*To begin the update, click on **Update Now** and follow the provided steps.*\n*You can also use the [Mac Manage App](https://docs.google.com/document/d/1oWuT7Tgsv-DHFNmivSc_Ibz61vtKKkRvqQoYmQsrKzI/edit?usp=sharing) to update at your convenience*."}
            while days_Left == 0:
                run = 0
                if run == 0:
                    ontop = {"ontop": 1}
                    content_dict.update(ontop)
                    content_dict.update(message)
                    del content_dict["button2text"]
                run_dialog(content_dict)
                run += 1
            run_dialog(content_dict)
        else:
            print("still in grace period")
    else:
        print ("New Update available on Apple website but not locally")