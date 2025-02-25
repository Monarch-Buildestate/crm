
from datetime import datetime

class FollowUp:
    def __init__(self, query):
        #"CREATE TABLE IF NOT EXISTS follow_ups(id INTEGER PRIMARY KEY, user_id INTEGER, lead_id INTEGER, follow_up_date TEXT, follow_up_time TEXT, FOREIGN KEY(user_id) REFERENCES users(id), FOREIGN KEY(lead_id) REFERENCES lead(id))"
        self.id = query[0]
        self.user_id = query[1]
        self.lead_id = query[2]
        self.follow_up_date = query[3]
        self.follow_up_time = query[4]
        self.created_at = datetime.fromtimestamp(query[5])
        self.time = self.created_at
        
