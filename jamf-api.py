#!/Library/ManagedFrameworks/Python/Python3.framework/Versions/Current/bin/python3

import requests

jamf_user = 'jamfpro-api'
jamf_password = ''
jamf_hostname = 'https://venturewell.jamfcloud.com'

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

def main():
    pass
    # fetch Jamf Pro (ex-universal) api token
    uapi_token = get_uapi_token()

    # fetch sample Jamf Pro api call
    url = jamf_hostname + "/JSSResource/computers"
    headers = {'Accept': 'application/json', 'Authorization': 'Bearer ' + uapi_token}
    response = requests.get(url, headers=headers)

    print(response.text)

    # invalidating token
    print('invalidating token...')
    invalidate_uapi_token(uapi_token)


if __name__ == '__main__':
    main()
