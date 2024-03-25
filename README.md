# TODOs

## Build Environment notes
* Nuitka only supports Python 3.4 — 3.11
* Cross-compiling not supported, must build on arm64e or x86_64 directly

## Documentation
* Slack setup: 
    - Install application in Slack Workspace
    - add the Bot as an app
    - invite to Channel by messaging '@Number Service', channel must be public, find Channel ID on channel about page
- ProPresenter: First message in the list, must have a token of 'Message', name doesn't matter, 'allow Web notif...' doesn't matter


## Coding
- Better error handling for ProPresenter password missing
- ProPresenter fails silently, if the first message type doesn't have a token
- Change Channel ID with an Input field
- Can we pull a list of available channels?
- Add logging level to config file, duplicate console out to log file for Debug level

