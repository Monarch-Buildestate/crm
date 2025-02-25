import sqlite3
from .Comment import Comment
from .FollowUp import FollowUp

conn = sqlite3.connect("database.db", check_same_thread=False)


class Lead:
    def __init__(self, query):
        self.id = query[0]
        self.user_id = query[1]
        self.name = query[2]
        self.phone_number = query[3]
        self.email = query[4]
        self.address = query[5]
        with conn:
            self.comments = self.get_comments(conn)
            self.follow_ups = self.get_follow_ups(conn)
        self.events = sorted(self.comments + self.follow_ups, key=lambda x: x.time)
    
    def get_comments(self, conn:sqlite3.Connection):
        with conn:
            cur = conn.cursor()
            cur.execute("SELECT * FROM comments WHERE lead_id=?", (self.id,))
            comments = cur.fetchall()
            cs = []
            for c in comments:
                cs.append(Comment(c))
        return cs
    
    def get_follow_ups(self, conn:sqlite3.Connection):
        with conn:
            cur = conn.cursor()
            cur.execute("SELECT * FROM follow_ups WHERE lead_id=?", (self.id,))
            follow_ups = cur.fetchall()
            fus = []
            for fu in follow_ups:
                fus.append(FollowUp(fu))
        return fus  
    
    @staticmethod
    def get(lead_id, conn:sqlite3.Connection):
        with conn:
            cur = conn.cursor()
            cur.execute("SELECT * FROM lead WHERE id=?", (lead_id,))
            lead = cur.fetchone()
            if not lead:
                return None
            return Lead(lead)
        return None