from datetime import datetime

class Comment:
    def __init__(self, query):
        self.id = query[0]
        self.lead_id = query[1]
        self.text = query[2]
        self.time = datetime.fromtimestamp(query[3])
    
