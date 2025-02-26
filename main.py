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
    with open("config.json", "r") as f:
        config = json.load(f)
    tatatelekey = config.get("tata_tele_api_key", None)
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
        return render_template("accounts/login.html")


@login_manager.user_loader
def load_user(user_id):
    return User.get(user_id, conn=conn)


@app.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for("login"))


@app.route("/")
@login_required
def slash():
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


@app.route("/lead/<lead_id>", methods=["POST", "GET"])
@app.route("/lead")
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
        with conn:
            cur = conn.cursor()
            cur.execute(
                "UPDATE lead SET name=?, email=?, address=? WHERE id=?",
                (new_name, new_email, new_address, lead_id),
            )
            conn.commit()
        return redirect(url_for("lead", lead_id=lead_id))

    if not lead_id:
        leads = current_user.get_leads(conn)
        return render_template("lead/lead.html", leads=leads)
    else:
        lead = Lead.get(lead_id, conn)
        return render_template(
            "lead/details.html",
            lead=lead,
            events=create_timeline(lead),
            current_time=datetime.now().strftime("%Y-%m-%dT%H:%M"),
        )


@app.route("/lead/<lead_id>/comment", methods=["POST"])
@login_required
def comment(lead_id):
    comment = request.form["comment"]
    with conn:
        cur = conn.cursor()
        cur.execute(
            "INSERT INTO comments (user_id, lead_id, comment) VALUES (?,?,?)",
            (current_user.id, lead_id, comment),
        )
        conn.commit()
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
    with conn:
        cur = conn.cursor()
        cur.execute(
            "INSERT INTO follow_ups (user_id, lead_id, follow_up_time, follow_up_user_id, remarks) VALUES (?,?,?,?,?)",
            (current_user.id, lead_id, follow_up_time, follow_up_user_id, remarks),
        )
        conn.commit()
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
        with conn:
            cur = conn.cursor()
            cur.execute(
                "INSERT INTO lead (user_id, name, phone_number, email, address) VALUES (?,?,?,?,?)",
                (current_user.id, name, phone_number, email, address),
            )
            conn.commit()
        return redirect(url_for("lead"))
    return render_template("lead/create.html")


def get_call_details(agent_number=None):
    url = "https://api-smartflo.tatateleservices.com/v1/call/records"
    payload = {}
    headers = {
        "accept": "application/json",
        "content-type": "application/json",
        "Authorization": tatatelekey,
    }
    print(config.get("did_number"))
    response = requests.get(
        url,
        json=payload,
        headers=headers,
        params={"Authorization": tatatelekey, "did_number": config.get("did_number")},
    )
    if response.status_code != 200:
        return []
    with open("test.json", "w+") as f:
        json.dump(response.json(), f, indent=4)
    calls = response.json()
    calls = calls.get("results")
    calls = [Call(call) for call in calls]
    if agent_number:
        calls = [
            call
            for call in calls
            if agent_number in call.agent_number or agent_number in call.client_number
        ]
    return calls


def get_active_calls(): ...


@app.route("/calls/active")
def active_calls():
    calls = get_active_calls()
    return render_template("call/active.html", calls=calls)


@app.route("/calls")
@login_required
def calls():
    if current_user.admin:
        calls = get_call_details()
    else:
        calls = get_call_details(current_user.phone_number)
    return render_template("call/calls.html", calls=calls)


@app.route("/api/initiate_call", methods=["POST"])
def initiate_call():
    if not tatatelekey:
        return "No key found"
    agent_number = request.json.get("agent_number")
    destination_number = request.json.get("destination_number")
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

    print(response.text)


@app.route("/api/dialplan", methods=["POST"])
def dialplan():
    caller_id = request.args.get("caller_id_number")
    with conn:
        cur = conn.cursor()
        cur.execute("SELECT * FROM lead WHERE phone_number=?", (caller_id,))
        lead = cur.fetchone()
        if not lead:
            return "Failover"
        lead = Lead(lead)
        return [{"transfer": {"type": "number", "data": [lead.agent.phone_number]}}]


if __name__ == "__main__":
    app.run(debug=True, port=80, host="0.0.0.0")
