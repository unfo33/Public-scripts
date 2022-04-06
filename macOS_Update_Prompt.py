#!/Library/ManagedFrameworks/Python/Python3.framework/Versions/Current/bin/python3

import urllib.request
import datetime
import platform
import os
import json
import ssl
import subprocess

# add major OS logic
# optimize code to save line
# add logic to ensure update is actually available

# open software update pane
cmd = "open -b com.apple.systempreferences /System/Library/PreferencePanes/SoftwareUpdate.prefPane"
def run_cmd(cmd):
    """Run the cmd"""
    run = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    output, err = run.communicate()
    if err:
        print(err.decode("utf-8"))
    return output, err

# get info from apple
URL = "https://gdmf.apple.com/v2/pmv"
gcontext = ssl.SSLContext()
raw = urllib.request.urlopen(URL, context=gcontext).read()
list = json.loads(raw.decode("utf-8"))
# grab latest version of Monty and posting date
macOS_Latest = list["AssetSets"]["macOS"][0]["ProductVersion"]
posting_Date_STR = list["AssetSets"]["macOS"][0]["PostingDate"]
# convert to date and give 7 day grace period
posting_Date = datetime.datetime.strptime(posting_Date_STR, '%Y-%m-%d')
one_Week = datetime.timedelta(days=7)
start_Date = posting_Date + datetime.timedelta(days=7)
final_Date = posting_Date + datetime.timedelta(days=30)
infolink="https://support.apple.com/en-au/HT201222"
today = datetime.date.today()
days_Left = (final_Date.date() - today).days
days_Left = int(days_Left)
current_OS = platform.mac_ver()[0]
dialog="/usr/local/bin/dialog"

def run_dialog(contentDict):
    """Runs the SwiftDialog app and returns the exit code"""
    jsonString = json.dumps(contentDict)
    exit_code = os.system(f"{dialog} --jsonstring '{jsonString}' --button1shellaction '{cmd}'")
    return exit_code

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

final_content_dict = {
    "alignment": "center",
    "button1text": "Update Now",
    "centericon": 1,
    "icon": "/Library/Application Support/Dialog/VentureWell_logo_mark.png",
    "infobuttonaction": infolink,
    "infobuttontext": "More Info",
    "message": f"## Operating System Update Required\n\nYour Update Path: **{current_OS}** → **{macOS_Latest}**\n\nmacOS **{macOS_Latest}** was released on **{posting_Date_STR}**. It is a **{Update}** update and will require around **{time}** minutes downtime.\n\nDays Remaining to Update: **{days_Left}**\n\n*To begin the update, click on **Update Now** and follow the provided steps.*\n*You can also use the [Mac Manage App](https://docs.google.com/document/d/1oWuT7Tgsv-DHFNmivSc_Ibz61vtKKkRvqQoYmQsrKzI/edit?usp=sharing) to update at your convenience*.",
    "messagefont": "size=16",
    "title": "none",
    "height": "420",
    "width": "900",
    "ontop": 1,
    "moveable": 1,
}
if current_OS == macOS_Latest:
    print("On Latest Version")
else:
    if days_Left <= 23:
        while days_Left == 0:
            run_dialog(final_content_dict)
        else:
            run_dialog(content_dict)
    else:
        print("still in grace period")