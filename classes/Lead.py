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
        if len("".join(filter(str.isdigit, self.phone_number))) == 10:
            self.phone_number = "91" + "".join(filter(str.isdigit, self.phone_number))
        self.email = '' if str(query[4]) == "None" else query[4]
        self.address = '' if str(query[5]) == "None" else query[5]
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
        if self.follow_ups:
            self.status = self.follow_ups[-1].status
        else:
            self.status = "Not Connected"

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
            cur.execute("SELECT * FROM calls WHERE client_number LIKE ?", (f"%{self.phone_number}%",))
            calls = cur.fetchall()
            cs = []
            for c in calls:
                cs.append(Call(c))
        return cs
    
    def delete(self, conn: sqlite3.Connection):
        # delete all comments, follow_ups
        for c in self.comments:
            c.delete(conn)
        for fu in self.follow_ups:
            fu.delete(conn)
        # never delete calls
        with conn:
            cur = conn.cursor()
            cur.execute("DELETE FROM lead WHERE id=?", (self.id,))
            conn.commit()
            return True
        return False
    
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
        # strip phone number to be last 10 digits
        phone_number = "".join(filter(str.isdigit, phone_number))[-10:]
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
        older_lead = Lead.get_by_phone_number(phone_number, conn)
        if older_lead:
            return older_lead
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