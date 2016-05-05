# MoriSublimePlugin
A plugin for making mori development a happy enviroment

## Usage
'ctrl+shift+p' => global appRequire / require

provides a dropdown of local files, and dependencies defined in package.json.
MoriSublimePlugin will insert the appRequire / require line at the top of the file with other modules, in alphabetical order.
Will not move your cursor or view

'ctrl+shift+i' => inline appRequire / require

provides a dropdown of local files and dependencies defined in package.json.
MoriSublimePlug will insert the appRequire / require line at the cursor position.

## Installation
### Use [Sublime Package Manager](http://wbond.net/sublime_packages/package_control)

* 'Cmd+Shift+P'
* select Package Control: Add Repository
* type into dialog: https://github.com/overlookdev/MoriSublimePlugin
* 'Cmd+Shift+P' again
* select Package Control: Install Package
* find MoriSublimePlugin
* done!

## Options
### Change hotkeys:
Under preferences -> Package Settings -> Mori

