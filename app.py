import os
import random
import json
import socket
import time
from flask import Flask, request, make_response, render_template, redirect, url_for, g, session, flash
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.secret_key = 'your_secret_key'  # Necessary for session management

basedir = os.path.abspath(os.path.dirname(__file__))

# Database configurations for polls
dbhost = os.environ.get('ENDPOINT_ADDRESS', 'db')
dbport = os.environ.get('PORT', '3306')
dbname = os.environ.get('DB_NAME', 'vote')
dbuser = os.environ.get('MASTER_USERNAME', 'user')
dbpass = os.environ.get('MASTER_PASSWORD', 'password')
dbtype = os.environ.get('DB_TYPE', '')

# Main app database URI
if dbtype == 'mysql':
    dburi = f'{dbtype}://{dbuser}:{dbpass}@{dbhost}:{dbport}/{dbname}'
elif dbtype == 'postgresql':
    dburi = f'{dbtype}://{dbuser}:{dbpass}@{dbhost}:{dbport}/{dbname}'
else:
    dburi = 'sqlite:///' + os.path.join(basedir, 'data/app.db')

app.config['SQLALCHEMY_DATABASE_URI'] = dburi
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SQLALCHEMY_ECHO'] = False

# Database URI for user information
app.config['SQLALCHEMY_BINDS'] = {
    'users': 'sqlite:///' + os.path.join(basedir, 'data/users.db')
}

db = SQLAlchemy(app)


# Poll Models
class Poll(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(30), unique=True)
    question = db.Column(db.String(90))
    stamp = db.Column(db.DateTime)
    options = db.relationship('Option', backref='option', lazy='dynamic')

    def __init__(self, name, question, stamp=None):
        self.name = name
        self.question = question
        if stamp is None:
            stamp = datetime.utcnow()
        self.stamp = stamp


class Option(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    text = db.Column(db.String(30))
    poll_id = db.Column(db.Integer, db.ForeignKey('poll.id'))
    poll = db.relationship('Poll', backref=db.backref('poll', lazy='dynamic'))
    votes = db.Column(db.Integer)

    def __init__(self, text, poll, votes):
        self.text = text
        self.poll = poll
        self.votes = votes


# User Models
class User(db.Model):
    __bind_key__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50))
    email = db.Column(db.String(100), unique=True)
    password = db.Column(db.String(200))

    def __init__(self, name, email, password):
        self.name = name
        self.email = email
        self.password = generate_password_hash(password)


# Preload the poll into g to keep it within the session context
@app.before_request
def before_request():
    g.poll = Poll.query.first()


# Login Page (Index Page)
@app.route('/', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        user = User.query.filter_by(email=email).first()
        if user and check_password_hash(user.password, password):
            session['user_id'] = user.id
            session['user_name'] = user.name
            return redirect(url_for('index'))
        else:
            flash('Invalid email or password', 'danger')
    return render_template('login.html')


# Sign Up Page
@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        password = request.form['password']
        if User.query.filter_by(email=email).first():
            flash('Email already exists', 'danger')
        else:
            user = User(name, email, password)
            db.session.add(user)
            db.session.commit()
            flash('Sign up successful! Please log in.', 'success')
            return redirect(url_for('login'))
    return render_template('signup.html')


# Voting Home Page
@app.route('/index.html')
def index():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    poll = g.poll  # Rebind poll to a session-bound instance
    return render_template('index.html', hostname=hostname, poll=poll, user_name=session['user_name'])


@app.route('/vote.html', methods=['POST', 'GET'])
def vote():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    poll = g.poll  # Rebind poll to a session-bound instance
    has_voted = False
    vote_stamp = request.cookies.get('vote_stamp')

    if request.method == 'POST':
        has_voted = True
        vote = request.form['vote']
        if vote_stamp:
            print(f"This client has already voted! The vote stamp is: {vote_stamp}")
        else:
            print("This client has not voted yet!")
            voted_option = Option.query.filter_by(poll_id=poll.id, id=vote).first()
            if voted_option:
                try:
                    voted_option.votes += 1
                    db.session.commit()
                except Exception as e:
                    db.session.rollback()
                    print(f"Error during voting: {e}")

        # Redirect to the results page after voting
        return redirect(url_for('results'))

    options = Option.query.filter_by(poll_id=poll.id).all()
    resp = make_response(render_template('vote.html', hostname=hostname, poll=poll, options=options))

    if has_voted:
        vote_stamp = hex(random.getrandbits(64))[2:-1]
        print("Set cookie for voted")
        resp.set_cookie('vote_stamp', vote_stamp)

    return resp


@app.route('/results.html')
def results():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    poll = g.poll  # Rebind poll to a session-bound instance
    results = Option.query.filter_by(poll_id=poll.id).all()
    return render_template('results.html', hostname=hostname, poll=poll, results=results)


@app.route('/health')
def health():
    if cache['fail'] == 1:
        flask.abort('500')
    else:
        return 'ok'


@app.route('/fail')
def fail():
    cache['fail'] = 1
    return 'Server failing ...'


if __name__ == '__main__':
    with app.app_context():  # Ensure that we are in the app context
        print(("Connect to : " + dburi))

        # Keep trying to connect the DB, e.g., waiting for it to be reachable
        wait = 1
        while wait:
            try:
                db.create_all()
                wait = 0
            except Exception as e:
                print(e)
                print("Database connection failed ... sleep\n")
                time.sleep(wait)
                wait = 10

        print("Database connection ok")

        db.session.commit()
        hostname = socket.gethostname()

        print("Check if a poll already exists in the db")
        poll = Poll.query.first()

        if poll:
            print("Restart the poll")
            poll.stamp = datetime.utcnow()
            db.session.commit()

        else:
            print("Load seed data from file")
            try:
                with open(os.path.join(basedir, 'seeds/seed_data.json')) as file:
                    seed_data = json.load(file)
                    print("Start a new poll")
                    poll = Poll(seed_data['poll'], seed_data['question'])
                    db.session.add(poll)
                    for i in seed_data['options']:
                        option = Option(i, poll, 0)
                        db.session.add(option)
                    db.session.commit()

            except:
                print("Cannot load seed data from file")
                poll = Poll("", "")

        app.run(host='0.0.0.0', port=8080, debug=True)
