from flask import Flask, jsonify, request, g
import sqlite3, json
from datetime import datetime, timedelta

app = Flask(__name__)
app.config['DATABASE'] = 'calendar.db'

def get_db():
    if 'db' not in g:
        g.db = sqlite3.connect(app.config['DATABASE'])
        g.db.row_factory = sqlite3.Row
    return g.db

@app.teardown_appcontext
def close_db(error):
    if hasattr(g, 'db'):
        g.db.close()

def init_db():
    with app.app_context():
        db = get_db()
        with app.open_resource('schema.sql', mode='r') as f:
            db.cursor().executescript(f.read())
        db.commit()

def drop_db():
    with app.app_context():
        db = get_db()
        with app.open_resource('drop_tables.sql', mode='r') as f:
            db.cursor().executescript(f.read())
        db.commit()

@app.route('/users', methods=['POST'])
def create_user():
    db = get_db()
    cursor = db.cursor()

    # get the request data
    data = request.get_json()

    # check if the required fields are present
    try:
        name = data['name']
        email = data['email']
        password = data['password']
    except KeyError as e:
        return jsonify({'error': f'{e} is required'}), 400

    # check if the email is already taken
    if cursor.execute('SELECT * FROM users WHERE email = ?', (email,)).fetchone():
        return jsonify({'error': 'Email already taken'}), 409

    # create the new user
    cursor.execute('INSERT INTO users (name, email, password) VALUES (?, ?, ?)', (name, email, password))
    db.commit()

    return jsonify({'message': 'User created successfully'})

@app.route('/users', methods=['GET'])
def get_users():
    db = get_db()
    cursor = db.cursor()

    # get users
    users = [dict(row) for row in cursor.execute(
        'SELECT name, email FROM users',
    ).fetchall()]

    return jsonify(users)

def create_meetings_(series_data):
    db = get_db()
    cursor = db.cursor()

    for data in series_data:
        # create the new meeting
        cursor.execute(
            'INSERT INTO meetings (title, description, start_time, end_time, location, organizer_id, invited_users) VALUES (?, ?, ?, ?, ?, ?, ?)',
            (data['title'], data['description'], data['start_time'], data['end_time'], data['location'], data['organizer_id'], data['invited_users']))
        meeting_id = cursor.lastrowid

        # invite the users
        for user_id in json.loads(data['invited_users']):
            cursor.execute('INSERT INTO invitations (user_id, meeting_id, status) VALUES (?, ?, ?)',
                           (user_id, meeting_id, "pending"))
    db.commit()

    return jsonify({'message': 'Meeting created successfully'})

def create_series_of_meetings(data, num_of_repeats):
    meeting_series = []
    start_time = datetime.strptime(data['start_time'], '%Y-%m-%d %H:%M:%S')
    end_time = datetime.strptime(data['end_time'], '%Y-%m-%d %H:%M:%S')

    if data['repeat'] == 'daily':
        for i in range(num_of_repeats):
            data['start_time'] = start_time + i * timedelta(days=1)
            data['end_time'] = end_time + i * timedelta(days=1)
            meeting_series.append(data)
    elif data['repeat'] == 'weekly':
        for i in range(num_of_repeats):
            data['start_time'] = start_time + i * timedelta(weeks=1)
            data['end_time'] = end_time + i * timedelta(weeks=1)
            meeting_series.append(data)
    elif data['repeat'] == 'monthly':
        for i in range(num_of_repeats):
            data['start_time'] = start_time.replace(day=1) + timedelta(days=i*31)
            data['start_time'] = data['start_time'].replace(day=start_time.day)
            data['end_time'] = end_time.replace(day=1) + timedelta(days=i*31)
            data['end_time'] = data['end_time'].replace(day=end_time.day)
            meeting_series.append(data)
    elif data['repeat'] == 'yearly':
        for i in range(num_of_repeats):
            data['start_time'] = start_time.replace(year=start_time.year+i)
            data['end_time'] = end_time.replace(year=end_time.year+i)
            meeting_series.append(data)
    elif data['repeat'] == 'every weekday':
        i = 0
        j = 0
        while j < num_of_repeats:
            data['start_time'] = start_time + i * timedelta(days=1)
            data['end_time'] = end_time + i * timedelta(days=1)
            if data['start_time'].weekday() < 5:
                meeting_series.append(data)
                j += 1
            i += 1
    return meeting_series


@app.route('/meetings', methods=['POST'])
def create_meeting():
    # get the request data
    data = request.get_json()

    # check if the required fields are present
    try:
        title = data['title']
        start_time = data['start_time']
        end_time = data['end_time']
        organizer_id = data['organizer_id']
        invited_users = data['invited_users']
    except KeyError as e:
        return jsonify({'error': f'{e} is required'}), 400

    if 'repeat' in data:
        try:
            repeat = data['repeat']
        except json.decoder.JSONDecodeError:
            return jsonify({'error': 'Invalid JSON in repeat field'}), 400

        allowed_repeats = {'daily', 'weekly', 'monthly', 'yearly', 'every weekday'}

        if repeat not in allowed_repeats:
            return jsonify({'error': 'Repeat can only be from "daily", "weekly", "monthly", "yearly", "every weekday"'}), 404

        # let's set default value 2 repeats and max 10 repeats
        if data['num_of_repeats'] > 10:
            raise ValueError("Number of repeats exceeds maximum allowed value of 10.")
        num_of_repeats = 2 if 'num_of_repeats' not in data else min(data['num_of_repeats'], 10)

        meeting_series = create_series_of_meetings(data, num_of_repeats)
        create_meetings_(meeting_series)
    else:
        create_meetings_([data])

    return jsonify({'message': 'Meeting created successfully'})


@app.route('/meetings/<int:meeting_id>', methods=['GET'])
def get_meeting(meeting_id):
    db = get_db()
    cursor = db.cursor()

    # get the meeting from the database
    meeting = cursor.execute('SELECT * FROM meetings WHERE id = ?', (meeting_id,)).fetchone()

    # check if the meeting exists
    if not meeting:
        return jsonify({'error': 'Meeting not found'}), 404

    # get the pending users
    pending_users = [dict(row) for row in cursor.execute(
            'SELECT users.email, users.name FROM users JOIN invitations ON users.id = invitations.user_id WHERE meeting_id = ? AND status = ?',
            (meeting_id, 'pending')
        ).fetchall()]

    # get the accepted users
    accepted_users = [dict(row) for row in cursor.execute(
            'SELECT users.email, users.name FROM users JOIN invitations ON users.id = invitations.user_id WHERE meeting_id = ? AND status = ?',
            (meeting_id, 'accepted')
        ).fetchall()]

    # get the declined users
    declined_users = [dict(row) for row in cursor.execute(
            'SELECT users.email, users.name FROM users JOIN invitations ON users.id = invitations.user_id WHERE meeting_id = ? AND status = ?',
            (meeting_id, 'declined')
        ).fetchall()]

    # create a dictionary with the meeting details and invited users
    result = {
        'id': meeting['id'],
        'title': meeting['title'],
        'description': meeting['description'],
        'start_time': meeting['start_time'],
        'end_time': meeting['end_time'],
        'location': meeting['location'],
        'pending_users': pending_users,
        'accepted_users': accepted_users,
        'declined_users': declined_users
    }

    return jsonify(result)


@app.route('/meetings', methods=['GET'])
def get_meetings():
    db = get_db()
    cursor = db.cursor()

    # get users
    meetings = [dict(row) for row in cursor.execute(
        'SELECT * FROM meetings',
    ).fetchall()]

    return jsonify(meetings)


@app.route('/invitations', methods=['GET'])
def get_invitations():
    db = get_db()
    cursor = db.cursor()

    # get invitations
    invitations = [dict(row) for row in cursor.execute(
        'SELECT * FROM invitations',
    ).fetchall()]

    return jsonify(invitations)


@app.route('/meeting/<int:meeting_id>/invite/<int:user_id>/accept', methods=['POST'])
def accept_invitation(meeting_id, user_id):
    db = get_db()
    cursor = db.cursor()

    # check if the meeting exists
    meeting = cursor.execute('SELECT * FROM meetings WHERE id = ?', (meeting_id,)).fetchone()
    if not meeting:
        return jsonify({'error': 'Meeting not found'}), 404

    # check if the user is invited to the meeting
    invitation = cursor.execute('SELECT * FROM invitations WHERE meeting_id = ? AND user_id = ?', (meeting_id, user_id)).fetchone()
    if not invitation:
        return jsonify({'error': 'Invitation not found'}), 404

    # accept the invitation
    cursor.execute('UPDATE invitations SET status = "accepted" WHERE meeting_id = ? AND user_id = ?', (meeting_id, user_id))
    db.commit()

    return jsonify({'message': 'Invitation accepted successfully'})

@app.route('/meeting/<int:meeting_id>/invite/<int:user_id>/decline', methods=['POST'])
def decline_invitation(meeting_id, user_id):
    db = get_db()
    cursor = db.cursor()

    # check if the meeting exists
    meeting = cursor.execute('SELECT * FROM meetings WHERE id = ?', (meeting_id,)).fetchone()
    if not meeting:
        return jsonify({'error': 'Meeting not found'}), 404

    # check if the user is invited to the meeting
    invitation = cursor.execute('SELECT * FROM invitations WHERE meeting_id = ? AND user_id = ?', (meeting_id, user_id)).fetchone()
    if not invitation:
        return jsonify({'error': 'Invitation not found'}), 404

    # decline the invitation
    cursor.execute('UPDATE invitations SET status = "declined" WHERE meeting_id = ? AND user_id = ?', (meeting_id, user_id))
    db.commit()

    return jsonify({'message': 'Invitation declined successfully'})

def get_user_meetings_(user_id, start_time, end_time):
    db = get_db()
    cursor = db.cursor()

    # get the user's meetings, all the meetings user created and all the meetings user accepted
    meetings = [dict(row) for row in cursor.execute(
        'SELECT DISTINCT m.* FROM meetings as m JOIN invitations as i WHERE (i.user_id = ? AND i.status = "accepted" OR m.organizer_id = ?) AND m.start_time >= ? AND m.end_time <= ?',
        (user_id, user_id, start_time, end_time)
    ).fetchall()]

    return meetings


@app.route('/users/<int:user_id>/meetings', methods=['GET'])
def get_user_meetings(user_id):
    db = get_db()
    cursor = db.cursor()

    # check if the user exists
    user = cursor.execute('SELECT DISTINCT id FROM users WHERE id = ?',(user_id,)).fetchone()
    if not user:
        return jsonify({'error': 'User not found'}), 404

    # get the start_time and end_time parameters
    start_time = request.args.get('start_time')
    end_time = request.args.get('end_time')

    # validate the parameters
    if not start_time or not end_time:
        return jsonify({'error': 'start_time and end_time are required query parameters'}), 400

    return jsonify(get_user_meetings_(user_id, start_time, end_time))


@app.route('/free_interval', methods=['GET'])
def find_free_interval():
    # get the request data
    data = request.get_json()

    # check if the required fields are present
    try:
        users = data['users']
        meeting_duration = data['meeting_duration'] # I assume that meeting duration is in minutes
    except KeyError as e:
        return jsonify({'error': f'{e} is required'}), 400

    start_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    end_time = (datetime.now() + timedelta(weeks=520)).strftime('%Y-%m-%d %H:%M:%S')
    timestampts = [(0, start_time), (0, end_time)]

    # let's take wider window of time for looking for users' meetings
    # in order to take into account relevant meetings
    start_time = datetime.strptime(start_time, '%Y-%m-%d %H:%M:%S') - timedelta(days=1)
    for user in users:
        user_meetings = get_user_meetings_(user, start_time, end_time)
        for meeting in user_meetings:
            timestampts.append((1, meeting['start_time']))
            timestampts.append((-1, meeting['end_time']))

    start_time = (start_time + timedelta(days=1)).strftime('%Y-%m-%d %H:%M:%S')

    timestampts.sort(key=lambda x: x[1])

    prev_time = None
    cur_balance = 0

    # count a balance, if the balance is zero then it is a free slot
    for balance, time in timestampts:
        if prev_time is not None and cur_balance == 0 and prev_time >= start_time:
            diff_time = datetime.strptime(time, '%Y-%m-%d %H:%M:%S') - datetime.strptime(prev_time, '%Y-%m-%d %H:%M:%S')
            if diff_time.total_seconds() >= 60 * meeting_duration:
                return jsonify({'message': 'Next meeting can be created at {prev_time}'.format(prev_time=prev_time)})
        cur_balance += balance
        prev_time = time

    return jsonify({'message': 'No time for a new meeting'})


if __name__ == '__main__':
    init_db()
    app.run()