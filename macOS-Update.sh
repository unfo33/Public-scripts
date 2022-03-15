#!/bin/zsh

#  nudge like script using dialog to prompt for an OS upgrade
# 
#  Created by Bart Reardon on 15/9/21.
#

requiredOSVer="12.4"
infolink="https://support.apple.com/en-au/HT201222"
persistant=0 # set this to 1 and the popup will persist until the update is performed

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

dialogCheck

OSVer=$(sw_vers | grep "ProductVersion" | awk '{print $NF}')
dialog="/usr/local/bin/dialog"


title="Operating System Update Available"
titlefont="size=30"
message="*A friendly reminder from the VentureWell Information Systems Team to keep your software up to date.*
    \nClick **Open Software Update** to be directed to the built in OS Update pane to perform the update or Click **Defer** to be reminded again later
    \n
    \nYou can also always update on your own from the Mac Manage application on your computer."
infotext="More Information"
icon="/Users/tbartlett/Downloads/VentureWell_logo_mark.png"
button1text="Open Software Update"
buttona1ction="open -b com.apple.systempreferences /System/Library/PreferencePanes/SoftwareUpdate.prefPane"
button2text="Defer"

# check the current version against the required version and exit if we're already at or exceded
autoload is-at-least
is-at-least $requiredOSVer $OSVer
if [[ $? -eq 0 ]]; then
	echo "You have v${OSVer}"
	exit 0
fi

runDialog () {
    ${dialog} -p -d \
    		--title "${title}" \
            --titlefont ${titlefont} \
            --icon "${icon}" \
            --listitem "Current version of macOS: ${OSVer}" \
            --listitem "Required version of macOS: ${requiredOSVer}" \
            --message "${message}" \
            --infobuttontext "${infotext}" \
            --infobuttonaction "${infolink}" \
            --button1text "${button1text}" \
            --button2text "${button2text}" \
            --width 800 \
            --height 400 \
            -o
    
    processExitCode $?
}

updateselected=0

processExitCode () {
    exitcode=$1
    if [[ $exitcode == 0 ]]; then
        updateselected=1
        open -b com.apple.systempreferences /System/Library/PreferencePanes/SoftwareUpdate.prefPane
    elif [[ $exitcode == 2 ]]; then
        currentUser=$(echo "show State:/Users/ConsoleUser" | scutil | awk '/Name :/ { print $3 }' )
        uid=$(id -u "$currentUser")
        echo "User deferred"
        exit 0
  	elif [[ $exitcode == 3 ]]; then
  		updateselected=1
    fi
}


# the main loop
while [[ ${persistant} -eq 1 ]] || [[ ${updateselected} -eq 0 ]]
do
    if [[ -e "${dialog}" ]]; then
        runDialog
    else
        # well something is up if dialog is missing - force an exit
        updateselected=1
    fi
done

exit 0