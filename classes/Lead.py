import sqlite3
from .Comment import Comment
from .FollowUp import FollowUp
from .Call import Call
import os
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

try:
    os.chdir("/var/www/crm")
except:
    pass

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
            self.calls = self.get_calls(conn)
        self.events = sorted(self.comments + self.follow_ups + self.calls, key=lambda x: x.time)
        self.created_at = datetime.strptime(query[6], "%Y-%m-%d %H:%M:%S") + timedelta(
            hours=5, minutes=30
        )  # UTC+5:30
        if self.follow_ups:
            self.last_follow_up_time = self.follow_ups[-1].created_at
            self.next_follow_up_time = self.follow_ups[-1].follow_up_time
        else:
            self.last_follow_up_time = None
            self.next_follow_up_time = None

    def get_comments(self, conn: sqlite3.Connection):
        with conn:
            cur = conn.cursor()
            cur.execute("SELECT * FROM comments WHERE lead_id=?", (self.id,))
            comments = cur.fetchall()
            cs = []
            for c in comments:
                cs.append(Comment(c))
        return cs

    def get_follow_ups(self, conn: sqlite3.Connection):
        with conn:
            cur = conn.cursor()
            cur.execute("SELECT * FROM follow_ups WHERE lead_id=?", (self.id,))
            follow_ups = cur.fetchall()
            fus = []
            for fu in follow_ups:
                fus.append(FollowUp(fu))
        return fus

    def get_calls(self, conn: sqlite3.Connection):
        with conn:
            cur = conn.cursor()
            cur.execute("SELECT * FROM calls WHERE client_number=?", (self.phone_number,))
            calls = cur.fetchall()
            cs = []
            for c in calls:
                cs.append(Call(c))
        return cs
    
    @staticmethod
    def get(lead_id, conn: sqlite3.Connection):
        with conn:
            cur = conn.cursor()
            cur.execute("SELECT * FROM lead WHERE id=?", (lead_id,))
            lead = cur.fetchone()
            if not lead:
                return None
            return Lead(lead)
        return None
    
    @staticmethod
    def get_by_phone_number(phone_number, conn: sqlite3.Connection):
        with conn:
            cur = conn.cursor()
            # like 
            cur.execute("SELECT * FROM lead WHERE phone_number LIKE ?", (f"%{phone_number}%",))
            lead = cur.fetchone()
            if not lead:
                return None
            return Lead(lead)
        return None
    
    @staticmethod
    def get_by_email(email, conn: sqlite3.Connection):
        with conn:
            cur = conn.cursor()
            cur.execute("SELECT * FROM lead WHERE email LIKE ?", (f"%{email}%",))
            lead = cur.fetchone()
            if not lead:
                return None
            return Lead(lead)
        return None
    
    @staticmethod
    def get_by_name(name, conn: sqlite3.Connection):
        with conn:
            cur = conn.cursor()
            cur.execute("SELECT * FROM lead WHERE name LIKE ?", (f"%{name}%",))
            lead = cur.fetchone()
            if not lead:
                return None
            return Lead(lead)
        return None
    
    @staticmethod
    def create(name=None, phone_number=None, email=None, address=None, user_id=1, conn: sqlite3.Connection = None):
        with conn:
            cur = conn.cursor()
            cur.execute(
                "INSERT INTO lead (name, phone_number, email, address, user_id, created_at) VALUES (?, ?, ?, ?, ?, ?)",
                (name, phone_number, email, address, user_id, datetime.now().strftime("%Y-%m-%d %H:%M:%S")),
            )
            conn.commit()
            return Lead.get(cur.lastrowid, conn)
        return None

    def assign(self, user_id, conn: sqlite3.Connection):
        with conn:
            cur = conn.cursor()
            cur.execute("UPDATE lead SET user_id=? WHERE id=?", (user_id, self.id))
            conn.commit()
            return True
        return False
    def json(self):
        return {
            "id": self.id,
            "user_id": self.user_id,
            "name": self.name,
            "phone_number": self.phone_number,
            "email": self.email,
            "address": self.address,
            "comments": [c.json() for c in self.comments],
            "follow_ups": [fu.json() for fu in self.follow_ups],
            "calls": [c.json() for c in self.calls],
            "created_at": self.created_at,
        }

    def update_details(self, name=None, phone_number=None, email=None, address=None, conn: sqlite3.Connection = None):
        with conn:
            cur = conn.cursor()
            cur.execute(
                "UPDATE lead SET name=?, phone_number=?, email=?, address=? WHERE id=?",
                (name, phone_number, email, address, self.id),
            )
            conn.commit()
            return True
        return False
    
    @staticmethod
    def get_all(admin=False, user_id=None, conn: sqlite3.Connection = None):
        print(admin)
        with conn:
            cur = conn.cursor()
            if admin:
                cur.execute("SELECT * FROM lead")
            else:
                cur.execute("SELECT * FROM lead WHERE user_id=?", (user_id,))
            leads = cur.fetchall()
            ls = []
            for l in leads:
                ls.append(Lead(l))
        return ls