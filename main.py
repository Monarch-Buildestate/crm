from flask import Flask, request, render_template, redirect, url_for, session
from flask_login import (
    UserMixin,
    LoginManager,
    login_user,
    login_required,
    logout_user,
    current_user,
)
import requests
import sqlite3
from classes.User import User
from classes.Lead import Lead
from classes.Comment import Comment
from classes.FollowUp import FollowUp
from classes.Call import Call

from datetime import datetime
import os
import json

conn = sqlite3.connect("database.db", check_same_thread=False)

login_manager = LoginManager()
app = Flask(__name__)
app.secret_key = "12345abcdefgh"
login_manager.init_app(app)

try:
    os.chdir("/var/www/crm")
except FileNotFoundError:
    pass
try:
    with open("config.json", "r") as f:
        config = json.load(f)
    tatatelekey = config.get("tata_tele_api_key", None)
    did_number = config.get("did_number", None)
    if did_number:
        did_number = did_number.replace("+", "")
except FileNotFoundError:
    config = {}
    with open("config.json", "w+") as f:
        json.dump(config, f, indent=4)
    tatatelekey = None

with conn:
    cur = conn.cursor()
    cur.execute(
        "CREATE TABLE IF NOT EXISTS users (id INTEGER PRIMARY KEY, username TEXT, password TEXT, phone_number TEXT, email TEXT, position INTEGER)"
    )
    conn.commit()
    # add a user admin if not exists
    cur.execute("SELECT * FROM users WHERE username='admin'")
    if not cur.fetchone():
        cur.execute(
            "INSERT INTO users (username, password, email, position) VALUES ('admin', 'admin', 'admin@example.com', 1)"
        )
        conn.commit()
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS lead (
            id INTEGER PRIMARY KEY, 
            user_id INTEGER, 
            name TEXT, 
            phone_number TEXT, 
            email TEXT, 
            address TEXT, 
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP, 
            FOREIGN KEY(user_id) REFERENCES users(id)
        );"""
    )
    conn.commit()
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS comments (
            id INTEGER PRIMARY KEY, 
            user_id INTEGER, 
            lead_id INTEGER, 
            comment TEXT, 
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP, 
            FOREIGN KEY(user_id) REFERENCES users(id), 
            FOREIGN KEY(lead_id) REFERENCES lead(id)
        );
    """
    )
    conn.commit()
    # follow ups
    cur.execute(
        """CREATE TABLE IF NOT EXISTS follow_ups (
            id INTEGER PRIMARY KEY, 
            user_id INTEGER, 
            lead_id INTEGER, 
            follow_up_time TIMESTAMP,
            follow_up_user_id INTEGER, 
            remarks TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP, 
            FOREIGN KEY(user_id) REFERENCES users(id), 
            FOREIGN KEY(lead_id) REFERENCES lead(id)
        );"""
    )
    conn.commit()
    cur.execute(
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
    )

    conn.commit()


@app.route("/login", methods=["POST", "GET"])
def login():
    if request.method == "POST":
        remember = request.form.get("remember") == "remember"
        given_username = request.form["username"]
        given_password = request.form["password"]
        if "@" in given_username:
            compare_against = "email"
        elif any(char.isdigit() for char in given_username):
            compare_against = "phone_number"
        else:
            compare_against = "username"

        # set cookies to this password
        with conn:
            cur = conn.cursor()
            cur.execute(
                f"SELECT * FROM users WHERE {compare_against}=? AND password=?",
                (given_username, given_password),
            )
            user = cur.fetchone()
            if not user:
                return render_template("accounts/login.html", msg="INVALID PASSWORD")
            user = User.get(user[0], conn)
            login_user(user, remember=remember)
            next = request.args.get("next")
            return redirect(next or url_for("slash"))
    else:
        next = request.args.get('next', "")
        if next:
            next = f"?next={next}"
        message = f"Please login to continue ({len(User.get_all(conn))} users)"
        return render_template("accounts/login.html", next=next, msg=message)


@login_manager.user_loader
def load_user(user_id):
    return User.get(user_id, conn=conn)


@app.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for("login"))


@app.route("/")
def slash():
    if not current_user.is_authenticated:
        return redirect(url_for("login"))
    return render_template("home/index.html")


def create_timeline(lead: Lead):
    if not lead.events:
        return {}
    timeline = {}
    for event in lead.events[::-1]:  # reverse so that we see latest events first
        if event.created_at.date() not in timeline:
            timeline[event.created_at.date()] = []
        timeline[event.created_at.date()].append(event.json())
    return timeline

@app.route("/lead/<lead_id>/assign", methods=["POST"])
@login_required
def assign_lead(lead_id):
    print(request.form)
    new_user_id = request.form.get("new_assignee")
    if not new_user_id:
        return redirect(url_for("lead", lead_id=lead_id))
    lead = Lead.get(lead_id, conn)
    lead.assign(new_user_id, conn)
    return redirect(url_for("lead", lead_id=lead_id))


@app.route("/lead")
@login_required
def leads():
    leads = current_user.get_leads(conn)
    for lead in leads:
        lead.assigned_to = User.get(lead.user_id, conn).username
    return render_template("lead/lead.html", leads=leads)

@app.route("/lead/<lead_id>", methods=["POST", "GET"])
@login_required
def lead(lead_id: int = None):
    if request.method == "POST":
        new_name = request.form["name"]
        """
        new_phone_number = request.form["number"]
        if len(new_phone_number) == 10:
            new_phone_number = "91" + new_phone_number"""  # phone number is not editable
        new_email = request.form["email"]
        new_address = request.form["address"]
        lead = Lead.get(lead_id, conn)
        lead.update(new_name, new_email, new_address, conn)
        return redirect(url_for("lead", lead_id=lead_id))
    
    lead = Lead.get(lead_id, conn)
    if not lead:
        return redirect(url_for("lead"))
    if not current_user.admin and lead.user_id != current_user.id:
        # don't allow access to other user's leads if not admin
        return redirect(url_for("lead"))
    lead_assigned_to = User.get(lead.user_id, conn)
    lead.assigned_to = lead_assigned_to.username
    users = User.get_all(conn)
    return render_template(
        "lead/details.html",
        lead=lead,
        events=create_timeline(lead),
        users= users,
        current_time=datetime.now().strftime("%Y-%m-%dT%H:%M"),
    )

@app.route("/lead/pending")
@login_required
def pending_leads():
    leads = current_user.get_leads(conn)
    for lead in leads:
        lead.assigned_to = User.get(lead.user_id, conn).username
    pending = []
    for lead in leads:
        if not lead.follow_ups:
            pending.append(lead)
            continue
        if lead.follow_ups[-1].follow_up_time < datetime.now(): # if time is gone then add to pending
            pending.append(lead)
    return render_template("lead/lead.html", leads=pending)

@app.route("/lead/<lead_id>/comment", methods=["POST"])
@login_required
def comment(lead_id):
    comment = request.form["comment"]
    Comment.create(comment, current_user.id, lead_id, conn)
    return redirect(url_for("lead", lead_id=lead_id))


@app.route("/lead/<lead_id>/followup", methods=["POST"])
@login_required
def followup(lead_id):
    follow_up_time = datetime.strptime(request.form["follow-up-time"], "%Y-%m-%dT%H:%M")
    follow_up_user_id = request.form.get("follow_up_user_id", None)
    if request.form.get("follow-up-select") == "no":
        follow_up_time = None
    if not follow_up_user_id:
        follow_up_user_id = current_user.id
    remarks = request.form["remarks"]
    FollowUp.create(
        current_user.id, lead_id, follow_up_time, follow_up_user_id, remarks, conn
    )
    return redirect(url_for("lead", lead_id=lead_id))


@app.route("/lead/create", methods=["POST", "GET"])
@login_required
def create_lead():
    if request.method == "POST":
        name = request.form["name"]
        phone_number = request.form["number"]
        if len(phone_number) == 10:
            phone_number = "91" + phone_number

        email = request.form["email"]
        address = request.form["city"]
        Lead.create(name=name, phone_number=phone_number, email=email, address=address, user_id=current_user.id, conn=conn)
        return redirect(url_for("leads"))
    return render_template("lead/create.html")


def get_call_details(agent_number=None):
    with conn:
        cur = conn.cursor()
        if agent_number is None:
            cur.execute("SELECT * FROM calls WHERE did_number=? ORDER BY call_time", (did_number,))
        else:
            cur.execute("SELECT * FROM calls WHERE agent_number=? AND did_number=? ORDER BY call_time", (agent_number,did_number,))
        calls = cur.fetchall()
        calls = [Call(call) for call in calls]
        # sort by call time
    return calls


def get_active_calls(): 
    url = "https://api-smartflo.tatateleservices.com/v1/live_calls"
    payload = {}
    headers = {
        "accept": "application/json",
        "Authorization": tatatelekey
    }
    params = {"did_number": config.get("did_number")}   
    response = requests.get(url, json=payload, headers=headers, params=params)
    if response.status_code != 200:
        return []
    active_calls = response.json()
    return active_calls

@app.route("/calls/active")
def active_calls():
    calls =[{'id': 90143183, 'user_id': 45536, 'client_id': None, 'call_id': '8992c734-8807-42dc-9887-da5a1190b27d', 'direction': 2, 'source': '+916396614787', 'type': 'click-to-call', 'did': '+918069551858', 'multiple_destination_type': 'c2c', 'multiple_destination_name': 'PJSIP/917297915965', 'destination': '+917297915965', 'state': 'Answered', 'queue_state': None, 'channel_id': '8992c734-8807-42dc-9887-da5a1190b27d', 'created_at': '2025-02-27 11:52:09', 'sip_domain': '127.0.0.1', 'broadcast_id': None, 'broadcast_no': None, 'call_time': '00:00:19', 'agent_name': 'Monarch Admin', 'customer_number': '917297915965'}]
    can_be_transfered_to = User.get_all(conn)
    can_be_transfered_to = [user for user in can_be_transfered_to if user.phone_number and user.phone_number != current_user.phone_number]
    can_be_transfered_to = [{"id": user.id, "name": user.username, "phone_number": user.phone_number} for user in can_be_transfered_to]
    return render_template("call/active.html", active_calls=calls, transfer=can_be_transfered_to)

@app.route("/calls/transfer/<call_id>/<new_number>", methods=["POST"])
def transfer_call(call_id, new_number):
    call_id = request.args.get("call_id")
    url = "https://api-smartflo.tatateleservices.com/v1/call/options"
    payload = {
        "type": 4,
        "call_id": call_id,
        "intercom": new_number
    }
    headers = {
        "accept": "application/json",
        "content-type": "application/json",
        "Authorization": tatatelekey,
    }
    response = requests.post(url, json=payload, headers=headers)
    return redirect(url_for("active_calls"))


@app.route("/calls")
@login_required
def calls():
    if current_user.admin:
        calls = get_call_details()
    else:
        calls = get_call_details(current_user.phone_number)
    return render_template("call/calls.html", calls=calls)

@app.route("/api/webhook/event/call_answered")
def call_answered():
    caller_id_number = request.args.get("caller_id_number", None)
    if not caller_id_number:
        return "Invalid data"
    answered_agent_number = request.args.get("answered_agent_number", None)
    if not answered_agent_number:
        return "Invalid data"
    # get user of that agent
    # last 12 digits
    agent = User.get_by_phone_number(answered_agent_number[-12:], conn)
    if not agent:
        return "Agent not found"
    answered_agent_number = answered_agent_number[-12:]
    lead = Lead.get_by_phone_number(caller_id_number, conn)
    if not lead:
        lead = Lead.create(name="Incoming Call", phone_number=caller_id_number, conn=conn)
    lead.assign(agent.id, conn)
    return f"Assigned {agent.username} to {lead.phone_number}"


@app.route("/api/webhook/event/call_missed")
def call_missed():
    caller_id_number = request.args.get("caller_id_number", None)
    if not caller_id_number:
        return "Invalid data"
    # get user of that agent
    # last 12 digits
    lead = Lead.get_by_phone_number(caller_id_number, conn)
    if not lead:
        lead = Lead.create(name="Missed Call", phone_number=caller_id_number, conn=conn)
    else:
        return "Lead already exists"
    return f"Created lead for {lead.phone_number}"


@app.route("/api/initiate_call", methods=["POST"])
def initiate_call():
    if not tatatelekey:
        return "No key found"
    data = request.get_json()
    agent_number = data.get('agent_number')
    lead_id = data.get("lead_id")
    if not agent_number or not lead_id:
        return "Invalid data"
    destination_number = Lead.get(int(lead_id), conn).phone_number
    url = "https://api-smartflo.tatateleservices.com/v1/click_to_call"
    payload = {
        "async": 1,
        "agent_number": agent_number,
        "destination_number": destination_number,
        "get_call_id": 1,
    }
    headers = {
        "accept": "application/json",
        "content-type": "application/json",
        "Authorization": tatatelekey,
    }

    response = requests.post(url, json=payload, headers=headers)
    return response.json()


@app.route("/api/dialplan", methods=["POST"])
def dialplan():
    caller_id = request.args.get("caller_id_number")
    with conn:
        lead = Lead.get_by_phone_number(caller_id, conn)
        if not lead:
            return "Failover"
        return [{"transfer": {"type": "number", "data": [lead.agent.phone_number]}}]


if __name__ == "__main__":
    app.run(debug=True, port=80, host="0.0.0.0")
