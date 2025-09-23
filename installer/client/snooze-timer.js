//TImer management
createSnoozeTimer(duration) //show countdown in top-right corner
updateTimerDisplay() //update countdown every second
removeSnoozeTimer() //clear timer when complete
positionTimerTopRight() //place in screen corner

//Snooze State tracking
trackSnoozeUsage(notificationId) //mark notification as snoozed
preventMultipleSnooze(notificationID) //block second snooze attempt
handleSnoozeExpiry() //retore notification when timer ends

//Warning flashes
scheduleFlashIntervals() //set up flash timeing: 5 min, 4 min, 3 min, 2.5min, 2 min, 1.5min, 1min, 45s, 30s, 20s, 15s, 10s, 5s
triggerFlashWarning(timeRemaining) //execute flash at specific interval