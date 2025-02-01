from flask import Flask, render_template, request
import sqlite3

app = Flask(__name__)

# Function to get a list of all team names from the database
def get_all_team_names():
    conn = sqlite3.connect('roster.db')
    cursor = conn.cursor()

    # Query to get all unique team names
    query = 'SELECT DISTINCT team FROM roster'
    cursor.execute(query)
    team_names = [row[0] for row in cursor.fetchall()]

    # Close the connection
    conn.close()
    return team_names

# Function to query the database for a team's information
def get_team_info(team_name):
    conn = sqlite3.connect('roster.db')
    cursor = conn.cursor()

    # Query to get team information
    query = '''
    SELECT * FROM roster WHERE team = ?
    '''
    cursor.execute(query, (team_name,))
    team_data = cursor.fetchall()
    
    # Close the connection
    conn.close()
    return team_data

@app.route('/')
def index():
    # Get all team names to display buttons
    team_names = get_all_team_names()
    return render_template('index.html', team_names=team_names)

@app.route('/team_info', methods=['POST'])
def team_info():
    team_name = request.form['team_name']  # Get team name from the button
    team_data = get_team_info(team_name)  # Fetch data from the database
    return render_template('team_info.html', team_data=team_data, team_name=team_name)

if __name__ == '__main__':
    app.run(debug=True)
