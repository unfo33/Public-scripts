#!/Library/ManagedFrameworks/Python/Python3.framework/Versions/Current/bin/python3
import requests
from local_credentials import jamf_user, jamf_password, jamf_hostname
import datetime
import json


mylabels = ["adobecreativeclouddesktop","adobereaderdc", "adobereaderdc-update", "asana", "dropbox", "figma", "firefox", "googlechromepkg", "googledrive", "gotomeeting", "grammarly", "lastpass", "microsoftoffice365", "notion", "r", "rstudio", "slack", "webex", "zoom" ]
labelsFriendly = ["Adobe Creative Cloud", "Adobe Reader", "Adobe Reader Update", "Asana", "Dropbox", "Figma", "Firefox", "Google Chrome", "Google Drive", "GoToMeeting", "Grammarly", "LastPass", "Microsoft Office", "Notion", "R", "R Studio", "Slack", "Webex", "Zoom"]

def write_Script():
    for i in range(len(mylabels)):
        script = f"/usr/local/Installomator/Installomator.sh {mylabels[i]} INSTALL=force LOGO=jamf notify=SILENT"
        f = open(f"{labelsFriendly[i]}.sh", "x")
        f.write(script)
        f.close()

def get_uapi_token():

    jamf_test_url = jamf_hostname + "/api/v1/auth/token"
    headers = {'Accept': 'application/json', }
    response = requests.post(url=jamf_test_url, headers=headers, auth=(jamf_user, jamf_password))
    response_json = response.json()

    return response_json['token']


def invalidate_uapi_token(uapi_token):

    jamf_test_url = jamf_hostname + "/api/v1/auth/invalidate-token"
    headers = {'Accept': '*/*', 'Authorization': 'Bearer ' + uapi_token}
    response = requests.post(url=jamf_test_url, headers=headers)

    if response.status_code == 204:
        print('Token invalidated!')
    else:
        print('Error invalidating token.')

def script_Upload(label, friendlylabel, uapi_token):
    headers = {'Accept': 'application/json', 'Authorization': 'Bearer ' + uapi_token}
    script = f"/usr/local/Installomator/Installomator.sh {label} INSTALL=force LOGO=jamf notify=SILENT"
    today = datetime.date.today()
    payload = {
    "name": f"{friendlylabel}.sh",
    "info": "Installomator script",
    "notes": f"Created {today} by Tom Bartlett via API",
    "priority": "AFTER",
    "categoryId": "1",
    "categoryName": "scripts",
    "parameter4": "",
    "parameter5": "",
    "parameter6": "",
    "parameter7": "",
    "parameter8": "",
    "parameter9": "",
    "parameter10": "",
    "parameter11": "",
    "osRequirements": "10.14.0",
    "scriptContents": f"{script}"
    }
    url = "https://venturewell.jamfcloud.com/api/v1/scripts"

    response = requests.request("POST", url, json=payload, headers=headers)
    print(response.text)

def get_Policy(uapi_token, name):
    headers = {'Accept': "application/json", 'Authorization': 'Bearer ' + uapi_token}
    url = f"https://venturewell.jamfcloud.com/JSSResource/policies/name/{name}"
    response = requests.request("GET", url, headers=headers)
    print(f"Get Policy exit code = {response.status_code}")
    if response.status_code == 200:
        dict = json.loads(response.text)
        return dict["policy"]["general"]["id"]
    else:
        return None

def upload_icon(uapi_token, friendly):
    icon = f"{friendly}.png"
    headers = {"Accept": "application/json", 'Authorization': 'Bearer ' + uapi_token}
    url = "https://venturewell.jamfcloud.com/api/v1/icon/"
    files = {"file": open(f"/Users/tbartlett/Library/AutoPkg/RecipeRepos/com.github.unfo33.autopkg/Icons/{friendly}.png", "rb")}
    response = requests.post(url, files=files, headers=headers)
    dict = json.loads(response.text)
    if response.status_code == 200:
        print("icon uploaded")
        return dict["id"]
    else:
        print("Upload failed")

def check_icon(uapi_token, friendly):
    icon = f"{friendly}.png"
    for i in range(5, 75):
        headers = {"Accept": "application/json", 'Authorization': 'Bearer ' + uapi_token}
        url = f"https://venturewell.jamfcloud.com/api/v1/icon/{i}"
        response = requests.get(url, headers=headers)
        dict = json.loads(response.text)
        #print (dict)
        if response.status_code == 200:
            if dict["name"] == icon:
                print("icon Found")
                return dict["id"]
    return None

def create_Policy(uapi_token, friendly, label, type, icon, policy_id = 0):
    data =  f"""
    <policy>
        <general>
            <name>{friendly}</name>
            <enabled>true</enabled>
            <trigger>EVENT</trigger>
            <trigger_checkin>false</trigger_checkin>
            <trigger_enrollment_complete>false</trigger_enrollment_complete>
            <trigger_login>false</trigger_login>
            <trigger_logout>false</trigger_logout>
            <trigger_network_state_changed>false</trigger_network_state_changed>
            <trigger_startup>false</trigger_startup>
            <trigger_other>{label}</trigger_other>
            <frequency>Ongoing</frequency>
            <location_user_only>false</location_user_only>
            <target_drive>/</target_drive>
            <offline>false</offline>
            <category>
                <name>Software</name>
            </category>
            <network_limitations>
                <minimum_network_connection>No Minimum</minimum_network_connection>
                <any_ip_address>true</any_ip_address>
            </network_limitations>
            <network_requirements>Any</network_requirements>
            <site>
                <id>-1</id>
                <name>None</name>
            </site>
        </general>
        <scope>
            <all_computers>true</all_computers>
            <computers/>
            <computer_groups/>
            <buildings/>
            <departments/>
            <limit_to_users>
                <user_groups/>
            </limit_to_users>
            <limitations>
                <users/>
                <user_groups/>
                <network_segments/>
                <ibeacons/>
            </limitations>
            <exclusions>
                <computers/>
                <computer_groups/>
                <buildings/>
                <departments/>
                <users/>
                <user_groups/>
                <network_segments/>
                <ibeacons/>
            </exclusions>
        </scope>
        <self_service>
            <use_for_self_service>true</use_for_self_service>
            <self_service_display_name>{friendly} - Latest Version</self_service_display_name>
            <install_button_text>Install</install_button_text>
            <reinstall_button_text>Reinstall</reinstall_button_text>
            <self_service_description>Automatically downloads and installs latest version of {friendly}. Can be used as a new install or to update existing software.</self_service_description>
            <force_users_to_view_description>false</force_users_to_view_description>
            <feature_on_main_page>false</feature_on_main_page>
            <self_service_categories>
                <category>
                    <id>2</id>
                    <display_in>true</display_in>
                    <feature_in>false</feature_in>
                </category>
            </self_service_categories>
            <self_service_icon>
                <id>{icon}</id>
            </self_service_icon>
            <notification>false</notification>
            <notification>Self Service</notification>
            <notification_subject>Install Firefox</notification_subject>
            <notification_message/>
        </self_service>
        <scripts>
            <size>1</size>
            <script>
                <id>33</id>
                <name>Installomator-9.1.sh</name>
                <priority>After</priority>
                <parameter4>{label}</parameter4>
                <parameter5>INSTALL=force</parameter5>
                <parameter6>LOGO=jamf</parameter6>
                <parameter7>NOTIFY=silent</parameter7>
                <parameter8 />
                <parameter9 />
                <parameter10 />
                <parameter11 />
            </script>
        </scripts>
    </policy>"""

    url = f"https://venturewell.jamfcloud.com/JSSResource/policies/id/{policy_id}"
    headers = {"Accept": "application/xml", 'Content-Type': 'application/xml', 'Authorization': 'Bearer ' + uapi_token}
    response = requests.request(type, url, headers = headers, data = data)
    data = response.text
    print(data)





def main():
    # fetch Jamf Pro (ex-universal) api token
    uapi_token = get_uapi_token()
    
    #iterate through labels
    #if it exists we do to do a put
    for i in range(len(mylabels)):
        icon = check_icon(uapi_token, labelsFriendly[i])
        print (icon)
        if not icon:
            icon = upload_icon(uapi_token, labelsFriendly[i])
            print(icon)
        policy_id = get_Policy(uapi_token, labelsFriendly[i])
        if policy_id:
            print ("updating policy")
            create_Policy(uapi_token, labelsFriendly[i], mylabels[i], "put", icon, policy_id)
        # if not we need to do a post
        else:
            print("Creating policy")
            create_Policy(uapi_token, labelsFriendly[i],mylabels[i], "post", icon)

    # invalidating token
    print('invalidating token...')
    invalidate_uapi_token(uapi_token)


if __name__ == '__main__':
    main()