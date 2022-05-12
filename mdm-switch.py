#!/Library/ManagedFrameworks/Python/Python3.framework/Versions/Current/bin/python3
from SystemConfiguration import SCDynamicStoreCopyConsoleUser
import os
import plistlib
import subprocess
import sys
import json
import time
from Foundation import NSLog
import requests
import tempfile

#todo

############################################## Initial variables and  JSON ######################################
dialogApp = "/Library/Application Support/Dialog/Dialog.app/Contents/MacOS/Dialog"
dialogPath = "/Library/Application Support/Dialog/Dialog.app"
dialog_command_file="/var/tmp/dialog.log"
infolink = ""
dep_nag = "https://github.com/unfo33/Public-scripts/blob/main/dep-nag.png?raw=true"
dep_allow = "https://github.com/unfo33/Public-scripts/blob/main/dep-approve.png?raw=true"
content_base = {
        "button1text": "Send Notification",
        "button2text": "Defer",
        "centericon": 1,
        "alignment": "center",
        "icon": "https://github.com/unfo33/Public-scripts/blob/main/dm_update.jpeg?raw=true",
        "infobuttonaction": infolink,
        "infobuttontext": "More Info",
        "message": "## Device Management Update Needed\n\nVentureWell is migrating Device Management tools which requires manual user approval - don't worry it will only take a second!\n\nPlease click **Send Notification** below to kick off the process.\n\nIf you have any questions or concerns please feel free to reach out in Slack or email support@venturewell.org",
        "messagefont": "size=16",
        "title": "none",
        "moveable": 1,
}

################################################ Functions #####################################################
def swiftDialog_Install(url, name):
    # download Install to temp directory
    new = requests.get(url, stream=True)
    with tempfile.TemporaryDirectory() as tmpdirname:
        with open(f"{tmpdirname}/{name}", 'wb') as f:
            f.write(new.content)
            write_log("Downloaded new file to temp directory")
            # check signature
            command = ["/usr/sbin/spctl", "-a", "-vv", "-t", "install", dialogPath]
            result = subprocess.run(command, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            # if valid install
            if (str(result).find("PWA5E9TQ59") != "-1"):
                write_log("Verified signature and will now install")
                try:
                    command = ["/usr/sbin/installer", "-pkg", f"{tmpdirname}/{name}", "-target", "/"]
                    install = subprocess.run(command, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                    write_log(f"Install results: {install}")
                except Exception as e:
                    write_log(f"failed to install package with error: {e}")
                    exit
            else:
                write_log("Signature validation failed - will not install")
                exit

def swiftDialog_Check():
    response = requests.get("https://api.github.com/repos/bartreardon/swiftDialog/releases/latest")
    url = (response.json()["assets"][0]["browser_download_url"])
    name = (response.json()["assets"][0]["name"])
    latest_Version = response.json()["tag_name"][1:]
    write_log(f"Latest version of swiftdialog is: {name}")
    if os.path.exists(dialogPath):
        with open(f"{dialogPath}/Contents/Info.plist", 'rb') as fp:
            p1 = plistlib.load(fp)
            current_Version = p1["CFBundleShortVersionString"]
            write_log(f"Current version of swiftdialog is: {current_Version}")
            if current_Version != latest_Version:
                write_log("Not on latest version")
                return False, url, name
            else:
                write_log("On latest version")
                return True, url, name
    else:
        write_log("Swiftdialog not installed.")
        return False, url, name

# check if enrolled in Jamf / Addigy
def identity_check():
    #jamf = "ACCF01EA-A4FD-4758-B333-E3834BFF33EE"
    """Check for valid MDM identity will return"""
    cmd = ["/usr/bin/security", "find-identity", "-v"]
    output = run_cmd(cmd)[0].decode("utf-8")
    if "AddigyMDM Identity" in output:
        write_log("Addigy MDM detected")
        return False
    elif "ACCF01EA-A4FD-4758-B333-E3834BFF33EE" in output:
        write_log("found Jamf")
        return True
    else:
        return False

def content_step1():
    message = "## Notification has been sent\n\nIt is located in the Notification Center in the top right corner of your screen.\n\nClick on the notification and select **Allow** to finish device management setup.\n\nOnce completed you will be able to close this window."
    content_base.update({"button1text": "Send Notification"})
    content_base.update({"button2text": "Defer"})
    content_base.update({"message": message})
    content_base.update({"icon": dep_nag})
    content_base.update({"iconsize": "500"})
    

def content_Complete():
    message = "## Device has been updated, thanks!\n\nIf you have any questions or concerns please feel free to reach out in Slack or email support@venturewell.org"
    content_base.update({"button1text": "Close"})
    content_base.pop("button2text", None)
    content_base.update({"message": message})
    content_base.update({"icon": "SF=checkmark.circle.fill,weight=bold,colour1=#00ff44,colour2=#075c1e"})

def write_log(text):
    """logger for depnotify"""
    NSLog("[depnotify] " + text)

def content_Defer():
    message = "## Device update has been deferred or failed.\n\nWe will remind you again soon!"
    content_base.update({"button1text": "Close"})
    content_base.pop("button2text", None)
    content_base.update({"message": message})
    content_base.update({"icon": "SF=person.crop.circle.badge.moon.fill,weight=bold"})

# check if DEP enabled
def is_dep_enabled():
    """Check if DEP is enabled"""
    cloud_record_path = "/private/var/db/ConfigurationProfiles/Settings"
    good_record = os.path.join(cloud_record_path, ".cloudConfigRecordFound")
    bad_record = os.path.join(cloud_record_path, ".cloudConfigRecordNotFound")
    no_activation = os.path.join(cloud_record_path, ".cloudConfigNoActivationRecord")
    cmd = ["/usr/bin/profiles", "-e"]
    run_cmd(cmd)
    if os.path.exists(bad_record) or os.path.exists(no_activation):
        return False
    try:
        with open(good_record, "rb") as f:
            cloudConfigRecord = plistlib.load(f)
    except:
        return False
    if "CloudConfigFetchError" in cloudConfigRecord:
        return False
    return True


def get_logged_in_user():
    """Returns the UID of the current logged in user"""
    user, uid, gid = SCDynamicStoreCopyConsoleUser(None, None, None)
    return user, uid

def run_dialog(dialog):
    """Runs the SwiftDialog app and returns the exit code"""
    jsonString = json.dumps(dialog)
    result = subprocess.run([dialogApp, "--jsonstring", jsonString])
    return result

def run_cmd(cmd):
    """Run the cmd"""
    run = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    output, err = run.communicate()
    if err:
        write_log(err.decode("utf-8"))
    return output, err

def make_admin(user):
    makeadmin = ["dseditgroup", "-o", "edit", "-d", user, "-t", "user", "admin"]
    run_cmd(makeadmin)

def main():
    # Ensure Swift-Dialog is isntalled
    check = swiftDialog_Check()
    if check[0] == False:
        swiftDialog_Install(check[1], check[2])
    
    # Check if we are in Jamf
    if identity_check():
        write_log("Found Jamf, exiting.")
        sys.exit(0)
    
    # send initial dialog
    result = run_dialog(content_base)
    if result.returncode == 2:
        write_log("user deferred")
        content_Defer()
        run_dialog(content_base)
        sys.exit(0)

    # get user, make admin, and send them DEP nag command
    user_id = get_logged_in_user()
    makeadmin = ["dseditgroup", "-o", "edit", "-a", user_id[0], "-t", "user", "admin"]
    removeadmin = ["dseditgroup", "-o", "edit", "-d", user_id[0], "-t", "user", "admin"]
    depnag = ["/bin/launchctl", "asuser", str(user_id[1]), "/usr/bin/profiles", "renew", "-type", "enrollment"]
    run_cmd(makeadmin)
    run_cmd(depnag)
    
    # send dialog step 2
    content_step1()
    exit = run_dialog(content_base)
    if exit.returncode == 2:
        write_log("user deferred")
        content_Defer()
        run_dialog(content_base)
        sys.exit(0)
    
    # leave dialog and script running until we determine they are enrolled in Jamf.
    mdm = identity_check()
    i = 0
    while mdm == False and i < 5:
        result = run_dialog(content_base)
        run_cmd(depnag)
        time.sleep(1) 
        identity_check()
        i+=1
    if mdm == True:
        run_cmd(removeadmin)
        content_Complete()
        run_dialog(content_base)
    else:
        run_cmd(removeadmin)
        content_Defer()
        run_dialog(content_base)

main()
    