#!/bin/zsh

# variables 
requiredOSVer="12.3.1"
# use  date -v+30d +%s to get
requiredDate=1651352715
currentDate=$(date +%s)
daysLeft=$(( (requiredDate-currentDate)/86400 ))
echo "$daysLeft"
OSVer=$(sw_vers | grep "ProductVersion" | awk '{print $NF}')
dialog="/usr/local/bin/dialog"
infolink="https://support.apple.com/en-au/HT201222"
title="Operating System Update Available"
message="### Operating System Update Available
\n Days Remaining to Update: $daysLeft
\n *To begin the update, click on **Update Device** and follow the provided steps* 
\n *You can also use the [Mac Manage App](https://docs.google.com/document/d/1oWuT7Tgsv-DHFNmivSc_Ibz61vtKKkRvqQoYmQsrKzI/edit?usp=sharing) to update at your convenience*"
infotext="More Information"
icon="/Library/Application Support/Dialog/VentureWell_logo_mark.png"
button1text="Update Now"
button1action="open -b com.apple.systempreferences /System/Library/PreferencePanes/SoftwareUpdate.prefPane"
button2text="Defer"

# check if dialog is installed and install if not
function dialogCheck(){
  # Get the URL of the latest PKG From the Dialog GitHub repo
  dialogURL=$(curl --silent --fail "https://api.github.com/repos/bartreardon/swiftDialog/releases/latest" | awk -F '"' "/browser_download_url/ && /pkg\"/ { print \$4; exit }")
  # Expected Team ID of the downloaded PKG
  expectedDialogTeamID="PWA5E9TQ59"

  # Check for Dialog and install if not found
  if [ ! -e "/Library/Application Support/Dialog/Dialog.app" ]; then
    echo "Dialog not found. Installing..."
    # Create temporary working directory
    workDirectory=$( /usr/bin/basename "$0" )
    tempDirectory=$( /usr/bin/mktemp -d "/private/tmp/$workDirectory.XXXXXX" )
    # Download the installer package
    /usr/bin/curl --location --silent "$dialogURL" -o "$tempDirectory/Dialog.pkg"
    # Verify the download
    teamID=$(/usr/sbin/spctl -a -vv -t install "$tempDirectory/Dialog.pkg" 2>&1 | awk '/origin=/ {print $NF }' | tr -d '()')
    # Install the package if Team ID validates
    if [ "$expectedDialogTeamID" = "$teamID" ] || [ "$expectedDialogTeamID" = "" ]; then
      /usr/sbin/installer -pkg "$tempDirectory/Dialog.pkg" -target /
    fi
    # Remove the temporary working directory when done
    /bin/rm -Rf "$tempDirectory"  
  else echo "Dialog found. Proceeding..."
  fi
}

# creates typical dialog notifications
function runDialog () {
    ${dialog} -p -d \
    		--title "none" \
            --icon "${icon}" \
            --message "${message}" \
            --infobuttontext "${infotext}" \
            --infobuttonaction "${infolink}" \
            --button1text "${button1text}" \
            --button2text "${button2text}" \
            --centericon \
            --alignment center \
            -o
    
    processExitCode $?
}

# creates final dialog notifications
function finalDialog () {
    ${dialog} -p -d \
    		--title "none" \
            --icon "${icon}" \
            --message "${message}" \
            --infobuttontext "${infotext}" \
            --infobuttonaction "${infolink}" \
            --button1text "${button1text}" \
            --centericon \
            --alignment center \
            --ontop
    
    processExitCode $?
}

processExitCode () {
    exitcode=$1
    if [[ $exitcode == 0 ]]; then
        updateselected=1
        open -b com.apple.systempreferences /System/Library/PreferencePanes/SoftwareUpdate.prefPane
    elif [[ $exitcode == 2 ]]; then
       echo "user deferred"
       exit 1
  	elif [[ $exitcode == 3 ]]; then
  		updateselected=1
    fi
}

dialogCheck

# check the current version against the required version and exit if we're already at or exceded
autoload is-at-least
is-at-least $requiredOSVer $OSVer
if [[ $? -eq 0 ]]; then
	echo "You have v${OSVer}"
	exit 0
fi

updateselected=0

if [ $daysLeft -eq 0 ]; then
    persistant=1
else persistant=0
fi

while [[ ${persistant} -eq 1 ]] || [[ ${updateselected} -eq 0 ]]
do
    if [ $daysLeft -eq 0 ]; then
        finalDialog
    else runDialog
fi
done

exit 0