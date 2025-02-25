from flask import Flask, request, render_template, redirect, url_for, session
from flask_login import (
    UserMixin,
    LoginManager,
    login_user,
    login_required,
    logout_user,
    current_user,
)

import sqlite3
from classes.User import User
from classes.Lead import Lead
from classes.Comment import Comment 
from classes.FollowUp import FollowUp


conn = sqlite3.connect("database.db", check_same_thread=False)

login_manager = LoginManager()
app = Flask(__name__)
app.secret_key = "12345abcdefgh"
login_manager.init_app(app)


# login and registration

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
    cur.execute("""
        CREATE TABLE IF NOT EXISTS lead (
            id INTEGER PRIMARY KEY, 
            user_id INTEGER, 
            name TEXT, 
            phone_number TEXT, 
            email TEXT, 
            address TEXT, 
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP, 
            FOREIGN KEY(user_id) REFERENCES users(id)
        );""")    
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
        """CREATE TABLE IF NOT EXISTS follow_ups (id INTEGER PRIMARY KEY, 
            user_id INTEGER, 
            lead_id INTEGER, 
            follow_up_date TEXT, 
            follow_up_time TEXT, 
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

@app.route("/lead/<lead_id>")
@app.route("/lead")
@login_required
def lead(lead_id:int=None):
    if not lead_id:
        leads = current_user.get_leads(conn)
        return render_template("lead/lead.html", leads=leads)
    else:
        lead = Lead.get(lead_id, conn)
        return render_template("lead/lead.html", lead=lead)
    
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
            cur.execute("INSERT INTO lead (user_id, name, phone_number, email, address) VALUES (?,?,?,?,?)", (current_user.id, name, phone_number, email, address))
            conn.commit()
        return redirect(url_for("lead"))
    return render_template("lead/create.html")

if __name__ == "__main__":
    app.run(debug=True, port=80, host="0.0.0.0")
