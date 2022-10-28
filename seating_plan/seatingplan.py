

class SeatingPlanInput():
    
    def __init__(self, event: Event):
        self.event = event

    def __str__(self):
        return self.identifier
