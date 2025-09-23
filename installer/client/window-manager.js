// Applciation control
minimizeAllApplications() //minimize all running programs to taskbar
preventWindowExpansion() //block taskbar restoration during notifications
allowBrowserWindows(allowedSites) //enable browser access for specific sites
createNewBrowserWindow(url) //open new browser instance for notifications

//Browser-specific handling
detectOpenBrowsers() //identify currently open browser windows
trackMinimizedBrowsers() //remember which browsers were minimized
manageBrowserWindowStacking() //allow notificaiton browsers over overlays

//Screen overlays
createGreyOverlays() //25% opacity grey overlay on all monitors
removeGreyOverlays() //clear overlays when notifications complete
detectAllMonitors() //get all connected displays

//Screen flashing
flashScreenEdges(timeRemaining) //flash at specified intervals
startFlashSchedule() //begin 5-minute countdown flashing sequence
stopFlashSchedule() //sop flashing when snooze ends