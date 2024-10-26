from flask import Flask, request, jsonify, render_template, redirect, url_for, session
from pymongo.mongo_client import MongoClient
from pymongo.server_api import ServerApi
from datetime import datetime
from bson import ObjectId

app = Flask(__name__)
app.secret_key = 'your-secret-key-here'  # Required for sessions

# MongoDB connection
uri = "mongodb+srv://mahendrac482:Mswjdi57WEjs6Lcq@eventease.8psy5.mongodb.net/?retryWrites=true&w=majority&appName=EventEase"
client = MongoClient(uri, server_api=ServerApi('1'))
db = client['EventEaseDB']
events_collection = db['events']
clubs_collection = db['clubs']
users_collection = db['users']
rsvp_collection = db['rsvp']

# Authentication routes
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        user_data = request.form
        user = users_collection.find_one({
            'email': user_data['email'],
            'password': user_data['password']  # In production, use proper password hashing
        })
        if user:
            session['user_id'] = str(user['_id'])
            session['user_type'] = user['user_type']  # 'student' or 'club'
            return redirect(url_for('home'))
        return render_template('login.html', message="Invalid credentials")
    return render_template('login.html')
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        user_data = {
            'email': request.form['email'],
            'password': request.form['password'],
            'user_type': request.form['user_type']
        }
        if users_collection.find_one({'email': user_data['email']}):
            return jsonify({"message": "Email already registered"}), 400

        # Ensure user_type is provided ('student' or 'club')
        if 'user_type' not in user_data or user_data['user_type'] not in ['student', 'club']:
            return jsonify({"message": "Invalid user type"}), 400
        
        # Insert user data with user_type into the database
        users_collection.insert_one(user_data)
        return jsonify({"message": "Registration successful"}), 201

    return render_template('register.html')


@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

# Home route based on user type
@app.route('/')
def home():
    if 'user_id' not in session:
        return redirect(url_for('login'))  # Redirect to login if user is not logged in
    
    if 'user_type' not in session:
        return redirect(url_for('login'))  # Redirect if user_type is missing in session
    
    # Proceed based on user type
    if session['user_type'] == 'student':
        upcoming_events = events_collection.find({'date': {'$gte': datetime.now().strftime('%Y-%m-%d')}})
        return render_template('student_home.html', events=upcoming_events)
    elif session['user_type'] == 'club':
        club_events = events_collection.find({'created_by': session['user_id']})
        return render_template('club_home.html', events=club_events)

# Event details and RSVP for students
@app.route('/event/<event_id>', methods=['GET', 'POST'])
def event_details(event_id):
    event = events_collection.find_one({'_id': ObjectId(event_id)})
    if session['user_type'] == 'student':
        if request.method == 'POST':
            rsvp_data = {
                'event_id': event_id,
                'student_id': session['user_id'],
                'name': request.form['name'],
                'email': request.form['email'],
                'mobile': request.form['mobile']
            }
            rsvp_collection.insert_one(rsvp_data)
            return render_template('event_details.html', event=event, message="RSVP successful!")
        return render_template('event_details.html', event=event)
    elif session['user_type'] == 'club':
        participants = rsvp_collection.find({'event_id': event_id})
        return render_template('event_participants.html', event=event, participants=participants)

# Create new event for clubs
@app.route('/create_event', methods=['GET', 'POST'])
def create_event():
    if 'user_id' not in session or session['user_type'] != 'club':
        return redirect(url_for('login'))
    
    if request.method == 'POST':
        event_data = {
            'title': request.form['title'],
            'description': request.form['description'],
            'date': request.form['date'],
            'location': request.form['location'],
            'created_by': session['user_id'],
            'created_at': datetime.now()
        }
        events_collection.insert_one(event_data)
        return redirect(url_for('home'))
    
    return render_template('create_event.html')

if __name__ == '__main__':
    app.run(debug=True)
