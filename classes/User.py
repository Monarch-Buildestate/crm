from flask_login import UserMixin   
import sqlite3


conn = sqlite3.connect("../database.db")

class User(UserMixin):

    def __init__(self, user_id, username, password, phone_number, email, position):
        self.id = user_id
        self.username = username
        self.name = username
        self.password = password
        self.phone_number = phone_number
        self.email = email
        self.position = position
        self.admin = True if self.id == 0 else False

    def get_id(self):
        return self.id

    @staticmethod
    def get(user_id):
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
    