# rtm_import For Blender 2.8
Blender Addon for importing Arma 2/3 RTM files

meant to be used with:
* Macser's [ArmaRig for Blender](https://forums.bistudio.com/topic/161228-armarig-for-blender/)
* Alwarren's [Arma Toolbox for Blender](https://forums.bistudio.com/topic/145290-arma-toolbox-for-blender-arma-23-exporter-script/)

## Features ##

* import of RTM files in RTM_0101 format
* for each RTM frame a keyframe is added for every animated bone
* Motion vector now automatically added to RTM motion vector in Arma Object Properties (Thanks to Turmio)

## Known Issues ##

* all bone constraints get disabled for now
* therefore IK and other control bones won't work
* no support for binary RTMs

please report any other issue at https://github.com/4d4a5852/rtm_import/issues

## Installation ##

Blender:
* 'File' -> 'User Preferences'
* select the 'Add-ons' tab
* 'Install from File...'
* navigate to the 'rtm_import.py' file and select it
* install it by pressing 'Install from File...'
* enable the addon by setting the checkmark in front of it

## If Install Fails ##

* Navigate to "C:\Users\YOURNAME\AppData\Roaming\Blender Foundation\Blender\2.80\scripts\addons" and delete the rtm_import folder.
* Installing the rtm_import.py will now work after deleting above folder.

## Usage ##

Blender:
* open the ArmaRig
* 'File' -> 'Import' -> 'Arma 2/3 RTM (.rtm)'
* select the RTM file to be imported
* set the import options:
    * 'Start Frame': frame in timeline where the RTM frames will be imported to (starting with this frame existing keyframes will be OVERWRITTEN for the bones animated in the RTM
    * 'Set Frame Range': select to set the frame range to the newly imported keyframes
    * 'Disable Bone Constraints': needs to be set to get valid imports (for now)
* 'Import RTM'
* import will start - its progress will be shown at the mouse cursor
