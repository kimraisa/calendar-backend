import unittest
import json
from app import app, init_db, drop_db
from datetime import datetime

class TestCalendarService(unittest.TestCase):

    def setUp(self):
        app.testing = True
        drop_db()
        init_db()
        self.app = app.test_client()

        # create users
        data = {
            'name': 'Alice',
            'email': 'alice@example.com',
            'password': 'password'
        }
        response = self.app.post('/users', data=json.dumps(data), content_type='application/json')
        self.assertEqual(response.status_code, 200, response.data.decode())

        data = {
            'name': 'Bob',
            'email': 'bob@example.com',
            'password': 'password'
        }
        response = self.app.post('/users', data=json.dumps(data), content_type='application/json')
        self.assertEqual(response.status_code, 200, response.data.decode())

        data = {
            'name': 'Nick',
            'email': 'nick@example.com',
            'password': 'password'
        }
        response = self.app.post('/users', data=json.dumps(data), content_type='application/json')
        self.assertEqual(response.status_code, 200, response.data.decode())

        # create meeting
        data = {
            'title': 'Team Meeting',
            'description': 'Weekly team meeting',
            'start_time': '2022-03-01 10:00:00',
            'end_time': '2022-03-01 11:00:00',
            'location': 'Office',
            'organizer_id': 1,
            'invited_users': '[2,3]'
        }
        response = self.app.post('/meetings', data=json.dumps(data), content_type='application/json')
        self.assertEqual(response.status_code, 200, response.data.decode())


    def tearDown(self):
        drop_db()


    def test_create_user(self):
        # test creating a new user with valid data
        data = {
            'name': 'John Doe',
            'email': 'johndoe@example.com',
            'password': 'password'
        }
        response = self.app.post('/users', data=json.dumps(data), content_type='application/json')
        self.assertEqual(response.status_code, 200, response.data.decode())

        # test creating a new user with missing data
        data = {
            'name': 'John Doe',
            'email': 'johndoe@example.com'
        }
        response = self.app.post('/users', data=json.dumps(data), content_type='application/json')
        self.assertEqual(response.status_code, 400, response.data.decode())

        # test creating a new user with an already taken email
        data = {
            'name': 'Jane Doe',
            'email': 'johndoe@example.com',
            'password': 'password'
        }
        response = self.app.post('/users', data=json.dumps(data), content_type='application/json')
        self.assertEqual(response.status_code, 409, response.data.decode())


    def test_create_meeting(self):
        # test creating a new meeting with valid data
        data = {
            'title': 'Team Meeting',
            'description': 'Weekly team meeting',
            'start_time': '2022-03-01 10:00:00',
            'end_time': '2022-03-01 11:00:00',
            'location': 'Office',
            'organizer_id': 1,
            'invited_users': '[2,3]'
        }
        response = self.app.post('/meetings', data=json.dumps(data), content_type='application/json')
        self.assertEqual(response.status_code, 200, response.data.decode())

        # test creating a new meeting with missing data
        data = {
            'title': 'Team Meeting',
            'start_time': '2022-03-01 10:00:00',
            'location': 'Office',
            'organizer_id': 1,
            'invited_users': '[2,3]'
        }
        response = self.app.post('/meetings', data=json.dumps(data), content_type='application/json')
        self.assertEqual(response.status_code, 400, response.data.decode())

        # test creating series of meetings with valid data
        data = {
            'title': 'Team Meeting',
            'description': 'Weekly team meeting',
            'start_time': '2022-03-01 10:00:00',
            'end_time': '2022-03-01 11:00:00',
            'location': 'Office',
            'organizer_id': 1,
            'invited_users': '[2,3]',
            'repeat': 'daily',
            'num_of_repeats': 3
        }
        response = self.app.post('/meetings', data=json.dumps(data), content_type='application/json')
        self.assertEqual(response.status_code, 200, response.data.decode())

        # test creating series of meetings with incorrect repeat
        data = {
            'title': 'Team Meeting',
            'description': 'Weekly team meeting',
            'start_time': '2022-03-01 10:00:00',
            'end_time': '2022-03-01 11:00:00',
            'location': 'Office',
            'organizer_id': 1,
            'invited_users': '[2,3]',
            'repeat': 'every Monday',
            'num_of_repeats': 3
        }
        response = self.app.post('/meetings', data=json.dumps(data), content_type='application/json')
        self.assertEqual(response.status_code, 404, response.data.decode())

    def test_get_meeting(self):
        # test getting meeting
        meeting_id = 1
        response = self.app.get(f'/meetings/{meeting_id}')
        self.assertEqual(response.status_code, 200, response.data.decode())

        # test getting missing meeting
        meeting_id = 0
        response = self.app.get(f'/meetings/{meeting_id}')
        self.assertEqual(response.status_code, 404, response.data.decode())


    def test_accept_invitation(self):
        # test accept invitation
        meeting_id = 1
        user_id = 2
        response = self.app.post(f'/meeting/{meeting_id}/invite/{user_id}/accept')
        self.assertEqual(response.status_code, 200, response.data.decode())

        # test accepting missing meeting
        meeting_id = 0
        user_id = 2
        response = self.app.post(f'/meeting/{meeting_id}/invite/{user_id}/accept')
        self.assertEqual(response.status_code, 404, response.data.decode())

        # test accepting invitation for missing user
        meeting_id = 1
        user_id = 0
        response = self.app.post(f'/meeting/{meeting_id}/invite/{user_id}/accept')
        self.assertEqual(response.status_code, 404, response.data.decode())


    def test_decline_invitation(self):
        # test decline invitation
        meeting_id = 1
        user_id = 2
        response = self.app.post(f'/meeting/{meeting_id}/invite/{user_id}/decline')
        self.assertEqual(response.status_code, 200, response.data.decode())

        # test declining missing meeting
        meeting_id = 0
        user_id = 2
        response = self.app.post(f'/meeting/{meeting_id}/invite/{user_id}/decline')
        self.assertEqual(response.status_code, 404, response.data.decode())

        # test declining invitation for missing user
        meeting_id = 1
        user_id = 0
        response = self.app.post(f'/meeting/{meeting_id}/invite/{user_id}/decline')
        self.assertEqual(response.status_code, 404, response.data.decode())

    def test_get_user_meetings(self):
        # test get user's meetings
        user_id = 1
        start_time = '2022-03-01 00:00:00'
        end_time = '2022-03-01 23:99:99'
        expected_result = [{
            'description': 'Weekly team meeting',
            'end_time': '2022-03-01 11:00:00',
            'id': 1,
            'invited_users': '[2,3]',
            'location': 'Office',
            'organizer_id': 1,
            'start_time': '2022-03-01 10:00:00',
            'title': 'Team Meeting'
        }]

        response = self.app.get(f'/users/{user_id}/meetings?start_time={start_time}&end_time={end_time}')

        self.assertEqual(response.status_code, 200, response.data.decode())
        self.assertEqual(response.json, expected_result)

        # test get meetings for missing user
        user_id = 0
        start_time = '2022-03-01 00:00:00'
        end_time = '2022-03-01 23:99:99'
        response = self.app.get(f'/users/{user_id}/meetings?start_time={start_time}&end_time={end_time}')
        self.assertEqual(response.status_code, 404, response.data.decode())

    def test_find_free_interval(self):
        # test find free interval
        data = {'users': [1, 2], 'meeting_duration': 30};
        expected_result = 'Next meeting can be created at {time}'.format(time=datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
        response = self.app.get('/free_interval', data=json.dumps(data), content_type='application/json')
        self.assertEqual(response.status_code, 200, response.data.decode())
        self.assertEqual(response.json["message"], expected_result)

        # test find free interval with missing data
        data = {'users': [1, 2]};
        response = self.app.get('/free_interval', data=json.dumps(data), content_type='application/json')
        self.assertEqual(response.status_code, 400, response.data.decode())

if __name__ == '__main__':
    unittest.main()

