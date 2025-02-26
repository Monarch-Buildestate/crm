from flask_login import UserMixin
from .Lead import Lead

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
            return User(user_id, username, password, phone_number, email, position)
        return None

    def get_leads(self, conn: sqlite3.Connection):
        with conn:
            cur = conn.cursor()
            cur.execute("SELECT * FROM lead WHERE user_id=?", (self.id,))
            leads = cur.fetchall()
            ls = []
            for l in leads:
                ls.append(Lead(l))
        return ls

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
