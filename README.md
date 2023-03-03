# Calendar Service

This is a simple Flask-based REST API for managing a calendar service.

## Getting started

To get started, you'll need to install Flask and Sqlite.

    pip install Flask
    
    pip install pysqlite3
    
you need to clone project 

    git clone https://github.com/kimraisa/calendar-backend.git
    
Navigate to the project directory: 

    cd calendar-backend
    
Create the SQLite database: 
    
    sqlite3 calendar.db

You can try to run unittests

    pytest test_calendar_service.py
    
Start the Flask development server: 

    python app.py
    
The server should now be running on http://localhost:5000/.

Try to run curl queries

Create user

    curl -X POST -H "Content-Type: application/json" -d '{"name": "John Doe", "email": "johndoe@example.com", "password": "abc"}' http://127.0.0.1:5000/users
    
Create meeting

     curl -X POST -H "Content-Type: application/json" -d '{"title": "Project Meeting", "description": "Discussing project progress", "start_time": "2022-03-05 14:00:00", "end_time": "2022-03-05 15:00:00", "location": "Conference Room 1", "organizer_id": 1, "invited_users": "[2, 3]", "repeat": "daily", "num_of_repeats": 3}' http://127.0.0.1:5000/meetings

Get all meetings

    curl  http://127.0.0.1:5000/meetings

Get user's meetings in certain period

    curl -X GET "http://localhost:5000/users/1/meetings?start_time=2022-03-10%2000:00:00&end_time=2022-03-10%2023:59:59"

Find the closest time when the next meeting can be created
    
    curl -X GET -H "Content-Type: application/json" -d '{"users": [1, 2], "meeting_duration": 30}' http://localhost:5000/free_interval
    
## API Usage

### User endpoints

- POST /users - create a new user
- GET /users - get a list of all users
- GET /users/<user_id>/meetings - get all user's meetings, the list of meetings that user organized and accepted the invitations for the meetings

### Meeting endpoints

- POST /meetings - create a meeting you can set repeat, here are the options 'daily', 'weekly', 'monthly', 'yearly', 'every weekday'
- GET /meetings/<meeting_id> - get the meeting by id with information who accepted and declined invitations
- GET /meetings - get a list of all meetings
- GET /free_interval - get the nearest time slot for a meeting when every participant is free and it is at least for certain amount of time

### Invitation endpoints

- GET /invitations - get a list of all invitations
- POST /meeting/<meeting_id>/invite/<user_id>/accept - accept invitation for the meeting
- POST /meeting/<meeting_id>/invite/<user_id>/decline - decline invitation for the meeting







    
