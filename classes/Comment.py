from datetime import datetime

class Comment:
    def __init__(self, query):
        self.id = query[0]
        self.user_id = query[1]
        self.lead_id = query[2]
        self.comment = query[3]
        self.created_at = datetime.fromtimestamp(query[4])
        self.time = self.created_at
    
    def json(self):
        return {
            "id": self.id,
            "user_id": self.user_id,
            "lead_id": self.lead_id,
            "comment": self.comment,
            "created_at": self.created_at
        }
        
    
