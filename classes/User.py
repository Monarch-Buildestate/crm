from flask_login import UserMixin
from .Lead import Lead
from .Notification import Notification

import sqlite3


class User(UserMixin):

    def __init__(self, user_id, username, password, phone_number, email, position):
        self.id = user_id
        self.username = username
        self.name = username
        self.password = password
        self.phone_number = phone_number
        self.email = email
        self.position = position
        self.admin = True if self.id == 1 else False

    def get_id(self):
        return self.id

    def get_notifications(self, conn: sqlite3.Connection):
        return Notification.get_all(self.id, conn)
    
    def add_notification(self, content:str, href:str, resolved:bool, conn: sqlite3.Connection):
        with conn:
            cur = conn.cursor()
            cur.execute("INSERT INTO notifications (user_id, content, href, resolved) VALUES (?,?,?,?)", (self.id, content, href, resolved))
            conn.commit()
        return True
    
    @staticmethod
    def get(user_id, conn: sqlite3.Connection):
        # load the config file
        with conn:
            cur = conn.cursor()
            cur.execute("SELECT * FROM users WHERE id=?", (user_id,))
            user = cur.fetchone()
            if not user:
                return None
            user_id, username, password, phone_number, email, position = user
            user = User(user_id, username, password, phone_number, email, position)
            user.notifications = user.get_notifications(conn)[::-1] # reverse to get latest notification first
            user.unread_count = len([n for n in user.notifications if not n.resolved])
            for n in user.notifications:
                print(n.resolved)
            return user
        return None

    def get_leads(self, conn: sqlite3.Connection):
        return Lead.get_all(self.admin, self.id, conn)
    
    @staticmethod
    def get_by_phone_number(phone_number, conn:sqlite3.Connection):
        with conn:
            cur = conn.cursor()
            cur.execute("SELECT * FROM users WHERE phone_number LIKE ?", (f"%{phone_number}%",))
            user = cur.fetchone()
            if not user:
                return None
        return User(*user)

    @staticmethod
    def get_all(conn: sqlite3.Connection):
        with conn:
            cur = conn.cursor()
            cur.execute("SELECT * FROM users")
            users = cur.fetchall()
            us = []
            for u in users:
                us.append(User(*u))
        return us

    def delete(self, conn: sqlite3.Connection):
        with conn:
            cur = conn.cursor()
            cur.execute("DELETE FROM users WHERE id=?", (self.id,))
            conn.commit()
        return True
    
    def edit(self,username, password, phone_number, email, position, conn: sqlite3.Connection):
        with conn:
            cur = conn.cursor()
            cur.execute("UPDATE users SET username=?, password=?, phone_number=?, email=?, position=? WHERE id=?", (username, password, phone_number, email, position, self.id))
            conn.commit()
        return True
        
    @staticmethod
    def create(username, password, phone_number, email, position, conn: sqlite3.Connection):
        with conn:
            cur = conn.cursor()
            cur.execute("INSERT INTO users (username, password, phone_number, email, position) VALUES (?,?,?,?,?)", (username, password, phone_number, email, position))
            conn.commit()
        return True