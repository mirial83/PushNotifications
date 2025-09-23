//system tray icon and menu
//user interaction handling
//notification display management
//create_tray_icon() -> create system tray presence

//Tray icon paths
const TRAY_ICON_ACTIVE = 'assets/icons/pnicon.png';
const TRAY_ICON_INACTIVE = 'assets/icons/pnicon.png';
const MAIN_ICON = 'assets/icons/pnicon.png';

_view_notification() // show current notification
_snooze_5()
_snooze15()
_snooze30() // snooze functionality
_complete_notification() // mark notifications complete
_request_website() // request website access
_request_uninstall() // request app removal
_show_status() // display client status
_show_about() // show app information
_quit() // clean shutdown

//Website access requests
showWebsiteRequestWindow() //display URL entry dialog
createWebsiteEntryForm() //text box and submit button
submitWebsiteRequest(url) //send request to server
validateWebsiteURL(url) //basic URL validation

//Response handling
showWebsiteApprovalMessage(website) //display approval notification
showWebsiteDenialMessage(website) //display denial notifiation

//Menu state control
updateTrayMenuState() //enable/disable options based on notification state
handleTrayShutdownRequest() //process shutdown wiht server notification
preventUnautorizedExit() //block force quit without server notification

//Tray management
createTrayIcon() //initialize system tray
buildContextMenu() //create right-click menu
updateTrayState() //change icon based on notifications

//User interactions
handleViewNotification() //show notification dialog
handleSnoozeOptions() //manage snooze functionality
handleWebsiteRequest() //process access requests
handleUninstallRequest() //submit removal request
handleStatusView() //display system information