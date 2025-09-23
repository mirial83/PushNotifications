//Electron app lifecycle management
//Initial system integration
//Admin privilege maintenance
//process coordination
//_get_real_mac_address() -> hardware identification for server communications
//app initialization and shutdown handling
//inter-process communication setup
//error handling and crash recovery

//Application icon
const APP_ICON = 'assets/icons/pnicon.png';
const WINDOW_ICON = 'assets/icons/pnicon.png';

//App lifecycle
app.whenReady() //initialize system tray and background services
app.on('window-all-closed') //keep running in background
app.on('activate') //handle system activation

//System integration
interceptShutdownSignals() //catch system shutdown attempts
handleEmergencyQuit() //process emergency exits with logging
coordinateNotificationFlow() //orchestrate notification processing
manageProcessCommunication() //IPC between all components

//Startup and intitialization
initializeNotificationSystem() //set up all notification components
loadPendingNotifications() //check for offline notifications on startup
setupSystemMonitoring() //monitor power and network states

//System Integration
checkAdminPrivileges() //verify admin status
loadClientConfig() //load saved configuration
setupIPC() // communication between processes

_get_real_mac_address() //Hardware identification
check_admin_privileges() //Admin status verification
restart_with_admin() //Privilege escalation if needed
_get_username_with_number() //Client identification
loadClientConfig() //Configuration loading