import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import pytest
from app import app, db, User

@pytest.fixture
def client():
    app.config['TESTING'] = True
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///eatsafe.db'
    app.config['UPLOAD_FOLDER'] = 'tests/uploads'
    app.config['WTF_CSRF_ENABLED'] = False
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

    with app.test_client() as client:
        with app.app_context():
            db.create_all()
            yield client

#guest

def test_root_redirects_to_guest(client):
    response = client.get('/')
    assert response.status_code == 200
    assert b"Try scanning a food label" in response.data

def test_guest_get(client):
    response = client.get('/guest')
    assert response.status_code == 200
    assert b"Try scanning a food label" in response.data
'''
def test_guest_post_no_file(client):
    response = client.post('/guest', data={}, follow_redirects=True)
    #need to implement this
'''
# auth

def test_signup_login_logout_flow(client):
    response = client.post('/signup', data={
        'username': 'testuser1',
        'password': 'testpass',
        'dietary': ['vegan']
    }, follow_redirects=True)

    assert b"Select your dietary preferences" in response.data

    response = client.post('/login', data={
        'username': 'testuser',
        'password': 'testpass'
    }, follow_redirects=True)
    assert b"Select your dietary preferences" in response.data or response.status_code == 200

    response = client.get('/logout', follow_redirects=True)
    assert b"Logged out successfully." in response.data

def test_login_with_wrong_credentials(client):
    user = User(username='invaliduser', password='hashed',diet_preferences='vegan')
    db.session.add(user)
    db.session.commit()

    response = client.post('/login', data={
        'username': 'invaliduser',
        'password': 'wrongpassword',
         'diet_preferences' : 'vegan'
    }, follow_redirects=True)
    db.session.delete(user) #the next time we run the test, user is still in the db, so we need to delete the user before we run the test again
    db.session.commit()

    assert b"Invalid username or password" in response.data


def test_index_requires_login(client):
    response = client.get('/index', follow_redirects=True)
    assert b"login" in response.data

def test_history_requires_login(client):
    response = client.get('/history', follow_redirects=True)
    assert b"Login" in response.data

def test_stats_requires_login(client):
    response = client.get('/stats', follow_redirects=True)
    assert b"Login" in response.data

def test_profile_requires_login(client):
    response = client.get('/profile', follow_redirects=True)
    assert b"Login" in response.data

# login

def test_login_user(client):
    client.post('/signup', data={
        'username': 'testuser',
        'password': 'testpass',
        'dietary': ['vegan']
    }, follow_redirects=True)
    client.post('/login', data={
        'username': 'testuser',
        'password': 'testpass'
    }, follow_redirects=True)

#authenticated user
'''
def test_index_post(client):
    test_login_user(client)
    #need to implement this
'''
def test_profile_update_preferences(client):
    test_login_user(client)
    client.get('/profile')#flushing the previous flash messages
    response = client.post('/profile', data={
        'form_type': 'preferences',
        'dietary': ['vegetarian']
    }, follow_redirects=True)
    assert b"Dietary preferences updated!" in response.data

def test_profile_update_account(client):
    test_login_user(client)
    client.get('/profile') #flushing the previous flash messages

    response = client.post('/profile', data={
    'form_type' : 'account',
    'new_username': 'newuser', 
    'new_password': 'newpass123'
    }, follow_redirects=True)
    user = User.query.filter_by(username='newuser').first()
    if user:
        db.session.delete(user)
        db.session.commit()
    
    
    assert b"Username updated!" in response.data or b"Password updated!" in response.data
   

def test_history_view(client):
    test_login_user(client)
    response = client.get('/history')
    assert response.status_code == 200

def test_stats_view(client):
    test_login_user(client)
    response = client.get('/stats')
    assert response.status_code == 200
