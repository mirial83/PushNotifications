//Window creation and management
createNotificaitonWindow(notificationData) //display notification with buttons
showNotificationText(message) //display notification content
createSnoozeButtons() //add "Snooze 5/15/30 Minutes" buttons
createCompleteButton() //add "complete" button

//Button handlers
handleSnooze5Minutes() //Process 5 minute snooze
handleSnooze15Minutes() //process 15 minute snooze
handleSnooz30Minutes() //process 30 minute snooze
handleComplete() //process completion request

//Window positioning and behavior
positionNotificationWindow() //center on primary monitor
keeNotificationOnTop() //ensure notification stays visible
preventNotificationClose() //block unauthorized window closing