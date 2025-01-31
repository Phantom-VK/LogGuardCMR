class userData:
    def __init__(self,email="enter email", startingHours="", endingHours="", isLoggedIn=False,
                 notifyLogin=False, notifySummary=False):
        self.isLoggedIn = isLoggedIn
        self.notifyLogin = notifyLogin
        self.notifySummary = notifySummary
        self.email = email
        self.startingHours = startingHours
        self.endingHours = endingHours
