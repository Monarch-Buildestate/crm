from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
class Call:
    """CREATE TABLE IF NOT EXISTS calls (
            id TEXT PRIMARY KEY NOT NULL,
            call_id TEXT,
            uuid TEXT,
            description TEXT,
            call_time TIMESTAMP,
            call_duration INTEGER,
            agent_number TEXT,
            client_number TEXT,
            recording_url TEXT,
            did_number TEXT,
            status TEXT
        )"""
    def __init__(self, query):
        self.id = query[0]
        self.call_id = query[1]
        self.uuid = query[2]
        self.description = query[3]
        self.time = datetime.strptime(query[4], "%Y-%m-%d %H:%M:%S").replace(tzinfo=ZoneInfo("Asia/Kolkata")) + timedelta(hours=5, minutes=30) 
        self.duration = query[5]
        self.agent_number = query[6]
        self.client_number = query[7]
        self.recording_url = query[8]
        self.did_number = query[9]
        self.status = query[10]
        self.created_at = self.time
        
    @staticmethod
    def from_dict(data):
        description = data.get("description")
        if data.get("detailed_description"):
            description += " / "+data.get("detailed_description")
        agent_number = data.get("agent_number")
        if agent_number:
            agent_number = agent_number.replace("+", "")
        client_number = data.get("client_number")
        if client_number:
            client_number = client_number.replace("+", "")
        did_number = data.get("did_number")
        if did_number:
            did_number = did_number.replace("+", "")
        return Call(
            (
                data.get("id"),
                data.get("call_id"),
                data.get("uuid"),
                description,
                data.get("end_stamp"),
                data.get("call_duration"),
                agent_number,
                client_number,
                data.get("recording_url"),
                did_number,
                data.get("status"),
            )
        )
    
    def json(self):
        return {
            "id": self.id,
            "call_id": self.call_id,
            "uuid": self.uuid,
            "description": self.description,
            "time": self.time.strftime("%Y-%m-%d %H:%M:%S"),
            "duration": self.duration,
            "agent_number": self.agent_number,
            "client_number": self.client_number,
            "recording_url": self.recording_url,
            "did_number": self.did_number,
            "status": self.status,
            "created_at": self.created_at.strftime("%Y-%m-%d %H:%M:%S"),
        }
