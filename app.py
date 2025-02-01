from flask import Flask, render_template, request, redirect, url_for, session
from dotenv import load_dotenv
import sqlite3
import os

# Load environment variables from .env file (specify path if needed)
load_dotenv(os.path.join(os.path.dirname(__file__), '.env'))

app = Flask(__name__)

# Retrieve the password and secret key from environment variables
PASSWORD = os.getenv('PASSWORD')
app.secret_key = os.getenv('SECRET_KEY') or 'fallback-secret-key'  # Add fallback for local testing

def get_all_team_names():
    conn = sqlite3.connect('roster.db')
    cursor = conn.cursor()
    cursor.execute('SELECT DISTINCT team FROM roster')
    team_names = [row[0] for row in cursor.fetchall()]
    conn.close()
    return team_names

def get_team_info(team_name):
    conn = sqlite3.connect('roster.db')
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM roster WHERE team = ?', (team_name,))
    team_data = cursor.fetchall()
    conn.close()
    return team_data

@app.route('/')
def index():
    if not session.get('logged_in'):
        return redirect(url_for('login'))  # Force redirect to login if not authenticated
    team_names = get_all_team_names()
    return render_template('index.html', team_names=team_names)

@app.route('/team_info', methods=['POST'])
def team_info():
    if not session.get('logged_in'):
        return redirect(url_for('login'))
    team_name = request.form['team_name']
    team_data = get_team_info(team_name)
    return render_template('team_info.html', team_data=team_data, team_name=team_name)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        if request.form['password'] == PASSWORD:
            session['logged_in'] = True
            return redirect(url_for('index'))
        else:
            return "Incorrect password. Try again.", 403
    # Redirect to index if already logged in
    if session.get('logged_in'):
        return redirect(url_for('index'))
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.pop('logged_in', None)
    return redirect(url_for('login'))

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000, debug=True)