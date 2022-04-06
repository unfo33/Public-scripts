#!/bin/zsh

dialogApp="/usr/local/bin/dialog"
dialog_command_file="/var/tmp/dialog.log"
installomator="/usr/local/Installomator/Installomator.sh"

myapps=("adobereaderdc-update" "firefox" "slack")

# check we are running as root
if [[ $(id -u) -ne 0 ]]; then
	echo "This script should be run as root"
	exit 1
fi

# How we get version number from app
if [[ -z $versionKey ]]; then
    versionKey="CFBundleShortVersionString"
fi

# *** functions

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

function installomatorCheck(){
    # Get the URL of the latest PKG From the Installomator GitHub repo
    url=$(curl --silent --fail "https://api.github.com/repos/Installomator/Installomator/releases/latest" | awk -F '"' "/browser_download_url/ && /pkg\"/ { print \$4; exit }")
    # Expected Team ID of the downloaded PKG
    expectedTeamID="JME5BW3F3R"
    exitCode=0

    # Check for Installomator and install if not found
    if [ ! -e "/usr/local/Installomator/Installomator.sh" ]; then
    echo "Installomator not found. Installing."
    # Create temporary working directory
    workDirectory=$( /usr/bin/basename "$0" )
    tempDirectory=$( /usr/bin/mktemp -d "/private/tmp/$workDirectory.XXXXXX" )
    echo "Created working directory '$tempDirectory'"
    # Download the installer package
    echo "Downloading Installomator package"
    /usr/bin/curl --location --silent "$url" -o "$tempDirectory/Installomator.pkg"
    # Verify the download
    teamID=$(/usr/sbin/spctl -a -vv -t install "$tempDirectory/Installomator.pkg" 2>&1 | awk '/origin=/ {print $NF }' | tr -d '()')
    echo "Team ID for downloaded package: $teamID"
    # Install the package if Team ID validates
    if [ "$expectedTeamID" = "$teamID" ] || [ "$expectedTeamID" = "" ]; then
        echo "Package verified. Installing package Installomator.pkg"
        /usr/sbin/installer -pkg "$tempDirectory/Installomator.pkg" -target /
        exitCode=0
    else 
        echo "Package verification failed before package installation could start. Download link may be invalid. Aborting."
        exitCode=1
        exit $exitCode
    fi
    # Remove the temporary working directory when done
    echo "Deleting working directory '$tempDirectory' and its contents"
    /bin/rm -Rf "$tempDirectory"  
    else
    echo "Installomator already found."
    fi
}
# take an app label and output the full app name
function label_to_name(){
    #name=$(grep -A2 "${1})" "$installomator" | grep "name=" | head -1 | cut -d '"' -f2) # pre Installomator 9.0
    name=$(${installomator} ${1} RETURN_LABEL_NAME=1 LOGGING=REQ | tail -1)
    if [[ "$itemName" != "#" ]]; then
        echo $name
    else
        echo $1
    fi
}

# execute a dialog command
function dialog_command(){
	echo $1
	echo $1  >> $dialog_command_file
}

function finalise(){
	dialog_command "progresstext: Install of Applications complete"
	dialog_command "progress: complete"
	dialog_command "button1text: Done"
	dialog_command "button1: enable" 
	rm $dialog_command_file
	exit 0
}

function getAppVersion() {
    # modified by: Søren Theilgaard (@theilgaard) and Isaac Ordonez

    # If label contain function appCustomVersion, we use that and return
    if type 'appCustomVersion' 2>/dev/null | grep -q 'function'; then
        appversion=$(appCustomVersion)
        echo "Custom App Version detection is used, found $appversion"
        return
    fi

    # pkgs contains a version number, then we don't have to search for an app
    if [[ $packageID != "" ]]; then
        appversion="$(pkgutil --pkg-info-plist ${packageID} 2>/dev/null | grep -A 1 pkg-version | tail -1 | sed -E 's/.*>([0-9.]*)<.*/\1/g')"
        if [[ $appversion != "" ]]; then
            echo "found packageID $packageID installed, version $appversion"
            updateDetected="YES"
            return
        else
            echo "No version found using packageID $packageID"
        fi
    fi

    # get app in /Applications, or /Applications/Utilities, or find using Spotlight
    if [[ -d "/Applications/$appName" ]]; then
        applist="/Applications/$appName"
    elif [[ -d "/Applications/Utilities/$appName" ]]; then
        applist="/Applications/Utilities/$appName"
    else
        applist=$(mdfind "kind:application $appName" -0 )
    fi
    if [[ -z $applist ]]; then
        echo "No previous app found"
    fi
   
    appPathArray=( ${(0)applist} )
   
    if [[ ${#appPathArray} -gt 0 ]]; then
        filteredAppPaths=( ${(M)appPathArray:#${targetDir}*} )
        if [[ ${#filteredAppPaths} -eq 1 ]]; then
            installedAppPath=$filteredAppPaths[1]
            #appversion=$(mdls -name kMDItemVersion -raw $installedAppPath )
            appversion=$(defaults read $installedAppPath/Contents/Info.plist $versionKey) #Not dependant on Spotlight indexing
            echo "found update for $appName, version $appversion"
            updateDetected="YES"
        else
            echo "could not determine location of $appName"
        fi
    else
        echo "could not find $appName"
    fi
}

dialogCheck
installomatorCheck

# get icon
icon="/Library/Application Support/Dialog/VentureWell_logo_mark.png"
if [ -f $icon ]; then
    echo "icon exists"
else
    curl -o "/Library/Application Support/Dialog/VentureWell_logo_mark.png" https://raw.githubusercontent.com/unfo33/venturewell/main/VentureWell_logo_mark.png
fi
#  Go through apps to see if they need update and if blocking processes
for label in "${myapps[@]}"; do
    echo "Label is $label"
    # lowercase the label
    label=${label:l}
    case $label in
        longversion)
            # print the script version
            echo "Installomater: version $VERSION ($VERSIONDATE)"
            exit 0
            ;;
        valuesfromarguments)
            if [[ -z $name ]]; then
                echo "need to provide 'name'"
                exit 1
            fi
            if [[ -z $type ]]; then
                echo "need to provide 'type'"
                exit 1
            fi
            if [[ -z $downloadURL ]]; then
                echo "need to provide 'downloadURL'"
                exit 1
            fi
            if [[ -z $expectedTeamID ]]; then
                echo "need to provide 'expectedTeamID'"
                exit 1
            fi
            ;;
        # label descriptions start here
        googlechromepkg)
            name="Google Chrome"
            type="pkg"
            #
            # Note: this url acknowledges that you accept the terms of service
            # https://support.google.com/chrome/a/answer/9915669
            #
            downloadURL="https://dl.google.com/chrome/mac/stable/accept_tos%3Dhttps%253A%252F%252Fwww.google.com%252Fintl%252Fen_ph%252Fchrome%252Fterms%252F%26_and_accept_tos%3Dhttps%253A%252F%252Fpolicies.google.com%252Fterms/googlechrome.pkg"
            expectedTeamID="EQHXZ8M8AV"
            if [[ $(arch) != "i386" ]]; then
                echo "Architecture: arm64 (not i386)"
                appNewVersion=$(curl -s https://omahaproxy.appspot.com/history | awk -F',' '/mac_arm64,stable/{print $3; exit}')
            else
                echo "Architecture: i386"
                appNewVersion=$(curl -s https://omahaproxy.appspot.com/history | awk -F',' '/mac,stable/{print $3; exit}')
            fi
            ;;
        firefox)
            name="Firefox"
            type="dmg"
            downloadURL="https://download.mozilla.org/?product=firefox-latest&os=osx&lang=en-US"
            appNewVersion=$(curl -fs https://www.mozilla.org/en-US/firefox/releases/ | grep '<html' | grep -o -i -e "data-latest-firefox=\"[0-9.]*\"" | cut -d '"' -f2)
            expectedTeamID="43AQ936H96"
            blockingProcesses="firefox" 
            ;;
        dropbox)
            name="Dropbox"
            type="dmg"
            downloadURL="https://www.dropbox.com/download?plat=mac&full=1"
            expectedTeamID="G7HH3F8CAK"
            ;;
        adobereaderdc-update)
            name="Adobe Acrobat Reader DC"
            type="pkgInDmg"
            downloadURL=$(adobecurrent=`curl --fail --silent https://armmf.adobe.com/arm-manifests/mac/AcrobatDC/reader/current_version.txt | tr -d '.'` && echo http://ardownload.adobe.com/pub/adobe/reader/mac/AcrobatDC/"$adobecurrent"/AcroRdrDCUpd"$adobecurrent"_MUI.dmg)
            appNewVersion=$(curl -s https://armmf.adobe.com/arm-manifests/mac/AcrobatDC/reader/current_version.txt)
            #appNewVersion=$(curl -s -H "User-Agent: Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15)" https://get.adobe.com/reader/ | grep ">Version" | sed -E 's/.*Version 20([0-9.]*)<.*/\1/g') # credit: Søren Theilgaard (@theilgaard)
            expectedTeamID="JQ525L2MZD"
            blockingProcesses="AdobeReader"
            ;;
        slack)
            name="Slack"
            type="dmg"
            downloadURL="https://slack.com/ssb/download-osx-universal" # Universal
            appNewVersion=$( curl -fsIL "${downloadURL}" | grep -i "^location" | cut -d "/" -f6 )
            expectedTeamID="BQR82RBBHL"
            ;;
    esac

    if [ -z "$appName" ]; then
        # when not given derive from name
        appName="$name.app"
    fi

    getAppVersion
    # Check for listed blocking processes and use name if none
    if [[ -z $blockingProcesses ]]; then
        echo "no blocking processes defined, using $name as default"
        blockingProcesses=$name
    fi
   # Check if latest version if specified 
    if [[ -n $appNewVersion ]]; then
    echo "Latest version of $name is $appNewVersion"
        # check if there is a new version
        if [[ $appversion == $appNewVersion ]]; then
            echo "There is no newer version available."
        # Ignore if software not installed such as Adobe Reader updates
        elif [[ -z $appversion ]]; then
            echo "Software not installed"
        # If blocking process found add to list to display notifications
        else
            if pgrep -xq "$blockingProcesses"; then
                echo "found blocking process $blockingProcesses"
                updateavailable+=("$name")
                updatelabels+=("$label")
            # If nothing blocking go ahead and install and kill open apps
            else
                /usr/local/Installomator/Installomator.sh "$label" BLOCKING_PROCESS_ACTION=kill NOTIFY=silent
            fi
        fi
    else
        echo "Latest version not specified."
    fi
    # Reset variables
    blockingProcesses=""
    appName=""
done

# If updates still need doing display notification
if [[ ${#updateavailable} -gt 0 ]]; then
    listitems=""
    for app in "${updateavailable[@]}"; do
        echo "apps label is $app"
        listitems="$listitems --listitem \"$app\""
    done

    title="Application Update Available"
    message="*A friendly reminder from the VentureWell Information Systems Team to keep your software up to date.*
    \n- Click **Update Now** to close and update the below app
    \n- Click **Defer** to be reminded again later
    \n- Use the [Mac Manage App](https://docs.google.com/document/d/1oWuT7Tgsv-DHFNmivSc_Ibz61vtKKkRvqQoYmQsrKzI/edit?usp=sharing) to update at your convenience
    \n
    \n**You have the following updates available:**
    "

    dialogCMD="$dialogApp --title \"$title\" \
    --message \"$message\" \
    --titlefont \"size=30\" \
    --icon \"$icon\" \ \
    --button1text \"Update Now\" \
    --button2text \"Defer\" \
    --infobutton \
    --moveable \
    --width 800 \
    --height 425"

    # final command to execute
    dialogCMD="$dialogCMD $listitems"

    # Launch dialog and run it in the background sleep for a second to let thing initialise
    eval "$dialogCMD"

    # check which button is pressed
    case $? in
        0)
        echo "Pressed OK"
        # Button 1 processing here
        # work out the number of increment steps based on the number of items
        # and the average # of steps per item (rounded up to the nearest 10)

        output_steps_per_app=30
        number_of_apps=${#updatelabels[@]}
        progress_total=$(( $output_steps_per_app * $number_of_apps ))


        # initial dialog starting arguments
        title="Installing Applications"
        message="Please wait while we download and install the following applications:"

# Removed extra spacing for dialog rendering purposes
dialogCMD="$dialogApp -p --title \"$title\" \
--message \"$message\" \
--icon \"$icon\" \
--progress $progress_total\
--button1text \"Please Wait\" \
--button1disabled \
--moveable"
        # create the list of labels
        listitems=""
        for label in "${updateavailable[@]}"; do
            #echo "apps label is $label"
            appname=$(label_to_name $label)
            listitems="$listitems --listitem \"$label\" "
        done

        # final command to execute
        dialogCMD="$dialogCMD $listitems"

        echo "$dialogCMD"
        # Launch dialog and run it in the background sleep for a second to let thing initialise
        eval $dialogCMD &
        sleep 2


        # now start executing installomator labels

        progress_index=0

        for label in "${updatelabels[@]}"; do
            step_progress=$(( $output_steps_per_app * $progress_index ))
            dialog_command "progress: $step_progress"
            appname=$(label_to_name $label | tr -d "\"")
            dialog_command "listitem: $appname: wait"
            dialog_command "progresstext: Installing $label" 
            installomator_error=0
            installomator_error_message=""
            while IFS= read -r line; do
                case $line in
                    *"DEBUG"*)
                    ;;
                    *"BLOCKING_PROCESS_ACTION"*)
                    ;;		
                    *"NOTIFY"*)
                    ;;
                    *"ERROR"*)
                        installomator_error=1
                        installomator_error_message=$(echo $line | awk -F "ERROR: " '{print $NF}')
                    ;;
                    *"##################"*)	
                    ;;
                    *)
                        # Installomator v8
                        #progress_text=$(echo $line | awk '{for(i=4;i<=NF;i++){printf "%s ", $i}; printf "\n"}')
                        
                        # Installomator v9
                        progress_text=$(echo $line | awk -F " : " '{print $NF}')
                        
                        if [[ ! -z  $progress_text ]]; then
                            dialog_command "progresstext: $progress_text"
                            dialog_command "progress: increment"
                        fi
                    ;;
                esac
            
            done < <($installomator $label BLOCKING_PROCESS_ACTION=kill NOTIFY=silent)
            
            if [[ $installomator_error -eq 1 ]]; then
                dialog_command "progresstext: Install Failed for $appname"
                dialog_command "listitem: $appname: $installomator_error_message ❌"
            else
                dialog_command "progresstext: Install of $appname complete"
                dialog_command "listitem: $appname: ✅"
            fi
            progress_index=$(( $progress_index + 1 ))
            echo "at item number $progress_index"
            
        done


        # all done. close off processing and enable the "Done" button
        finalise
    ;;
    2)
    echo "User deferred"
    # Button 2 processing here
    ;;
    esac
fi