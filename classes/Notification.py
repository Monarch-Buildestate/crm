import sqlite3



class Notification:
    def __init__(self, query):
        self.id =query[0]
        self.user_id = query[1]
        self.content = query[2]
        self.href = query[3]
        self.resolved = query[4]
        self.created_at = query[5]

    @staticmethod
    def get(notification_id: int, conn):
        with conn:
            cur = conn.cursor()
            cur.execute("SELECT * FROM notifications WHERE id=?", (notification_id,))
            query = cur.fetchone()
            if not query:
                return None
            return Notification(query)

    @staticmethod
    def get_all(user_id: int, conn):
        with conn:
            cur = conn.cursor()
            cur.execute("SELECT * FROM notifications WHERE user_id=?", (user_id,))
            query = cur.fetchall()
            if not query:
                return []
            return [Notification(q) for q in query]
    
    @staticmethod
    def add(user_id: int, content:str, href:str, resolved:bool, conn):
        with conn:
            cur = conn.cursor()
            cur.execute("INSERT INTO notifications (user_id, content, href, resolved) VALUES (?,?,?,?)", (user_id, content, href, resolved))
            conn.commit()
        return True