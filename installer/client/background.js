//server communication loop
//notification processing
//update checking
//policy enforcement
//_make_api_request() -> HTTP requests with retry logic
//check_for_updates() -> version cchecking against server
//download_and_apply_udpate() -> client self-updating
//fetch_current_version_from_api() -> get latest version info
//heartbeat transmission
//notification polling -> check for new ntoifications
//policy enforcement -> apply server-side rules

//Core Notification handling
handleIncomingNotification(notification) //Process new notification
queueNotification(notification) //add to notification queue
processNotificationQueue() //handle notification priority
markNotificationComplete(notificationId) //send completion to server
handleNotificationDenial(notificationId) //process serrver denial
restoreFromOffline() //handle offline notification backlog

//System state management
disableVPNsAndProxies() //block network bypasses
enableVPNsAndProxies() //restore network access when all complete
monitorSystemPower() //detect power on/off states
monitorInternetConnection() //detect connection restore

//Server communication
startHeartbeat() //send periodic status updates
pollNotifications() //check for new messages
sendClientStatus() //report system state
handleServerCommands() //rpocess server instructions
sendCompletionToServer(notificationId) //submit completion for approval
pollOfflineNotifications() //check for missed notifications
sendShutdownNotification(Reason, logData) //alert server of client shutdown

//Client lifecycle
handleSystemStartup() //process startup notification queue
handleInternetRestore() //Process queued notifications
preventClientShutdown() //Block unauthorized shutdown attempts

//Update management
checkForUpdates() //compare versions with server
downloadUpdate() //fetch new client version
applyUpdate() //replace current client

//Policy enforcement
enforceWebsiteBlocking() //block unauthorized sites
applyNotificationRules() //handle notification display

//API request handling
makeApiRequestWithRetry() //Robust HTTP requests with exponential backoff
handleNetworkTimeout() //Timeout management
handleConnectionErrors() //Connection error recovery
validateApiResponse() //Response validation and parsing