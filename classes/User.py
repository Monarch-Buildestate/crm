from flask_login import UserMixin
from .Lead import Lead
from .Notification import Notification

import sqlite3


class User(UserMixin):

    def __init__(self, user_id, username, password, phone_number, email, position, available_for_lead, created_at):
        self.id = user_id
        self.username = username
        self.name = username
        self.password = password
        self.phone_number = phone_number
        self.email = email
        self.position = position
        self.admin = True if self.id == 1 else False
        self.available_for_lead = available_for_lead
        self.created_at = created_at
        self.logged_in = True


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
            user = User(*user)
            user.notifications = user.get_notifications(conn)[::-1] # reverse to get latest notification first
            user.unread_count = len([n for n in user.notifications if not n.resolved])
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

    def edit(self,username:str=None, password:str=None, phone_number:str=None, email:str=None, position:int=None, available_for_lead:bool=None, conn: sqlite3.Connection=None):
        if not conn:
            raise ValueError("Connection not provided")
        if username is None:
            username = self.username
        if password is None:
            password = self.password
        if phone_number is None:
            phone_number = self.phone_number
        if email is None:
            email = self.email
        if position is None:    
            position = self.position
        if available_for_lead is None:
            available_for_lead = self.available_for_lead
        
        with conn:
            cur = conn.cursor()
            cur.execute("UPDATE users SET username=?, password=?, phone_number=?, email=?, position=?, available_for_lead=? WHERE id=?", (username, password, phone_number, email, position, available_for_lead, self.id))
            self.username = username
            self.name = username
            self.password = password
            self.phone_number = phone_number
            self.email = email
            self.position = position
            self.available_for_lead = available_for_lead
            conn.commit()
        return True
        
    @staticmethod
    def create(username, password, phone_number, email, position, conn: sqlite3.Connection):
        with conn:
            cur = conn.cursor()
            cur.execute("INSERT INTO users (username, password, phone_number, email, position, available_for_lead) VALUES (?,?,?,?,?, True)", (username, password, phone_number, email, position)) # True for available_for_lead
            conn.commit()
        return True