from datetime import datetime, timedelta
from zoneinfo import ZoneInfo


class FollowUp:
    def __init__(self, query):
        self.id = query[0]
        self.user_id = query[1]
        self.lead_id = query[2]
        if query[3] is None:
            self.follow_up_time = None
        else:
            self.follow_up_time = datetime.strptime(
                query[3], "%Y-%m-%d %H:%M:%S"
            )+ timedelta(
                hours=5, minutes=30
            )  # UTC+5:30
        self.follow_up_user_id = query[4]
        self.remarks = query[5]
        self.created_at = datetime.strptime(query[6], "%Y-%m-%d %H:%M:%S") + timedelta(
            hours=5, minutes=30
        )  # UTC+5:30
        self.time = self.created_at

    def json(self):
        return {
            "id": self.id,
            "user_id": self.user_id,
            "lead_id": self.lead_id,
            "follow_up_time": self.follow_up_time,
            "follow_up_user_id": self.follow_up_user_id,
            "remarks": self.remarks,
            "created_at": self.created_at,
        }

    def delete(self, conn):
        with conn:
            cur = conn.cursor()
            cur.execute("DELETE FROM follow_ups WHERE id = ?", (self.id,))
            conn.commit()
            return True
    
    @staticmethod
    def get(follow_up_id, conn):
        with conn:
            cur = conn.cursor()
            cur.execute("SELECT * FROM follow_ups WHERE id=?", (follow_up_id,))
            follow_up = cur.fetchone()
            return FollowUp(follow_up)
        
    @staticmethod
    def create(userid, lead_id, follow_up_time, follow_up_user_id, remarks, conn):
        with conn:
            cur = conn.cursor()
            cur.execute(
                "INSERT INTO follow_ups (user_id, lead_id, follow_up_time, follow_up_user_id, remarks) VALUES (?,?,?,?,?)",
                (userid, lead_id, follow_up_time, follow_up_user_id, remarks),
            )
            conn.commit()
