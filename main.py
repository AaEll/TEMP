# Copyright 2015 Google Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import flask
from flask import Flask, Response, request, render_template, redirect, url_for
from flaskext.mysql import MySQL
import flask.ext.login as flask_login
import time 
#for image uploading
from werkzeug import secure_filename
import os, base64
import re

mysql = MySQL()
app = Flask(__name__)
app.secret_key = 'xxxx'  # Change this!
#app = bookshelf.create_app(config)

#These will need to be changed according to your creditionals
app.config['MYSQL_DATABASE_USER'] = 'root'
app.config['MYSQL_DATABASE_PASSWORD'] = '1212'
app.config['MYSQL_DATABASE_DB'] = "UMASS"
app.config['MYSQL_DATABASE_HOST'] = '127.0.0.1:3306'
mysql.init_app(app)

#begin code used for login
login_manager = flask_login.LoginManager()
login_manager.init_app(app)

conn = mysql.connect()
cursor = conn.cursor()
cursor.execute("SELECT email from Users") 
users = cursor.fetchall()

hash0 = int('E1F531E559C21',16)
hash1 = 1299869
hash2 = 1300751

def HASH(s):
    sum_char = 0
    for char in s:
        sum_char*= 128        
        sum_char += ord(s)
    return ((sum_char-hash0)*hash1)%hash2

def clean(s):
    return re.sub('[^A-Za-z0-9@,.]+', '', s)


def getUserList():
	cursor = conn.cursor()
	cursor.execute("SELECT email from Users") 
	return cursor.fetchall()

class User(flask_login.UserMixin):
	pass

@login_manager.user_loader
def user_loader(email):
	users = getUsers()
	if not(email) or email not in users:
		return
	user = User()
	user.email = email
	return user

@login_manager.request_loader
def request_loader(request):
	users = getUsers()
	email = request.form.get('email')
	if not(email) or email not in str(users):
		return
	user = User()
	user.id = email
	cursor = mysql.connect().cursor()
	cursor.execute("SELECT password_hash FROM Users WHERE email = '{0}'".format(email))
	passHash = int(cursor.fetchall()[0][0])
	user.is_authenticated = HASH(request.form['password']) == passHash
	return user


@app.route('/login', methods=['GET', 'POST'])
def login():
	if flask.request.method == 'GET':
		return '''
			   <form action='login' method='POST'>
				<input type='text' name='email' id='email' placeholder='email'></input>
				<input type='password' name='password' id='password' placeholder='password'></input>
				<input type='submit' name='submit'></input>
			   </form></br>
		   <a href='/'>Home</a>
			   '''
	email = flask.request.form['email']
	cursor = conn.cursor()
	if cursor.execute("SELECT password_hash FROM Users WHERE email = '{0}'".format(email)):
		passHash = int(cursor.fetchall()[0][0])
		if HASH(flask.request.form['password']) == passHash:
			user = User()
			user.id = email
			flask_login.login_user(user)
			return flask.redirect(flask.url_for('protected'))

	return render_template('home.html', message='Failed Login. Make an account?')

@app.route('/logout')
def logout():
	flask_login.logout_user()
	return render_template('home.html', message='Logged out')

@login_manager.unauthorized_handler
def unauthorized_handler():
	return render_template('home.html', message='Protected Page') 

#you can specify specific methods (GET/POST) in function header instead of inside the functions as seen earlier
@app.route("/register", methods=['GET'])
def register():
	return render_template('register.html', supress='True') 

@app.route("/register", methods=['POST'])
def register_user():
	try:
		email=clean(request.form.get('email'))
		password=HASH(request.form.get('password'))
		first_name=clean(request.form.get('first_name'))
		last_name=clean(request.form.get('last_name'))
        image = request.files['photo']
	except:
		print "couldn't find all tokens" #this prints to shell, end users will not see this (all print statements go to shell)
		return flask.redirect(flask.url_for('register'))
	cursor = conn.cursor()
	if isEmailUnique(email):
        cursor.execute("INSERT INTO Users (first_name, last_name, email, password) VALUES ('{0}', '{1}', '{2}', '{3}')"
        .format(first_name, last_name, email, password))
		conn.commit()
        uid = getUserIdFromEmail(email)
		photo_data = base64.standard_b64encode(imgfile.read())        
        cursor.execute("INSERT INTO Photos (photo, uid) VALUES ('{0}', '{1}')".format(photo_data, uid))
		conn.commit()

		#log user in
		user = User()
		user.id = email
		flask_login.login_user(user)
		return render_template('profile.html', name=first_name, message='Account Created!')
	else:
		print "couldn't find all tokens"
		return render_template("register.html", suppress=False)

@app.route('/profile')
@flask_login.login_required
def profile():
	uid = getUserIdFromEmail(flask_login.current_user.id)
    photo_data = get_profile_photo(uid)
	return render_template('profile.html', name=getFirstName(uid),profile_photo = photo_data)

@app.route('/friends', methods=['GET', 'POST'])
@flask_login.login_required
def friends():
	uid = getUserIdFromEmail(flask_login.current_user.id)
	friends = getUsersFriends(uid)
	friends_names_photos = []
	for uid in friends:
		friends_names_photos += [getUserName(uid[0]),getProfilePhoto(uid[0])]
	else:
		return render_template('friend.html', friends_names_photos=friends_names_photos)

@app.route('/search_users', methods=['GET','POST'])
@flask_login.login_required
def searchUsers():
	uid = getUserIdFromEmail(flask_login.current_user.id)
	friends_names = []
	if request.method == 'POST':
		name = request.form.get('name')
        user_names_photos = []
        for uid in searchUsers(name):
    		user_names_photos += [getUserName(uid[0]),getProfilePhoto(uid[0])]
        return render_template('add_friends.html',user_names_photos = user_names_photos)
	else:
		return render_template('add_friends.html')

@app.route('/add_friends', methods=['GET'])
@flask_login.login_required
def addFriends():
	uid = getUserIdFromEmail(flask_login.current_user.id)
    email = request.form.get("email")
    new_uid = getUserIdFromEmail(email)
    addFriend(new_uid)
    return render_template('friend.html')

@app.route('/search_events', methods=['GET','POST'])
@flask_login.login_required
def searchEvents():
    try:
		priv=request.form.get('privacy')
		time_start=clean(request.form.get('start time'))
        time_end=clean(request.form.get('end end'))
        tags = []
        if request.form.get('tag 1'):
    		tags.append(clean(request.form.get('tag 1')))
        if request.form.get('tag 2'):
    		tags.append(clean(request.form.get('tag 2')))
        if request.form.get('tag 3'):
    		tags.append(clean(request.form.get('tag 3')))
	except:
		print "couldn't find all tokens" #this prints to shell, end users will not see this (all print statements go to shell)
		return flask.redirect(flask.url_for('search_events'))
    uid = getUserIdFromEmail(flask_login.current_user.id)
    event_info = searchEvents(uid,time_s,time_e,privacy,tags)
    return render_template('add_friends.html',event_info = event_info)

@app.route('/search', methods=['POST'])
@flask_login.login_required
def searchUsers():
	uid = getUserIdFromEmail(flask_login.current_user.id)
	friends_names = []
	if request.method == 'POST':
		name = request.form.get('name')
        user_names_photos = []
        for uid in searchUsers(name):
    		user_names_photos += [getUserName(uid[0]),getProfilePhoto(uid[0])]
        return render_template('add_friends.html',user_names_photos = user_names_photos)
	else:
		return render_template('home.html')

@app.route('/MakeEvent', methods=['GET', 'POST'])
@flask_login.login_required
def MakeEvent():
	uid = getUserIdFromEmail(flask_login.current_user.id)
	if request.method == 'POST':
		try:
			time_start = request.form.get('time_start')
			time_end = request.form.get('time_end')
			name = clean(request.form.get('title'))
			desc = clean(request.form.get('description'))
			contact= clean(request.form.get('contact info'))
			privacy = request.form.get('privacy')
			loc = request.form.get('location')
			tags = request.form.get('tags')
		except:
			print "couldn't find all tokens" #this prints to shell, end users will not see this (all print statements go to shell)
			return flask.redirect(flask.url_for('MakeEvent'))
		cursor = conn.cursor()
		cursor.execute("INSERT INTO Events(owner_uid, privacy,  name_e,  desc_e,  contact, time_start,time_end ,location_e) VALUES ('{0}', '{1}', '{2}', '{3}','{4}', DATETIME('{5}'),DATETIME('{6}'), '{7}')".format(uid, privacy,name,desc,contact,time_start,time_end,loc))
		conn.commit()
		eid = getMostRecentEid(uid)
		query  = ""
		i = 1
		for tag in tags:
			if i:
				query+="('{0}','{1}')".format(tag,eid)
			i=0
			query += " ,('{0},'{1}')".format(tag,eid)
		cursor.execute("INSERT INTO Tags(tag, eid) VALUES {0}".format(query))
		conn.commit()
		return render_template('profile.html', message="Event created.")
	else:
		return render_template('home.html', message="Event Failed")


def getUserIdFromEmail(email):
	cursor = conn.cursor()
	if cursor.execute("SELECT user_id  FROM Users WHERE email = '{0}'".format(email)):
		return cursor.fetchone()[0]
	else:
		return None

def isEmailUnique(email):
	cursor = conn.cursor()
	if cursor.execute("SELECT email  FROM Users WHERE email = '{0}'".format(email)): 
		return False
	else:
		return True

def getFirstName(uid):
	cursor = conn.cursor()
	cursor.execute("SELECT first_name FROM Users WHERE uid ='{0}'".format(uid))
	return cursor.fetchall()[0][0]

def getProfilePhoto(uid):
    cursor = conn.cusor()
    cursor.execute("SELECT photo FROM Photos WHERE uid ='{0}'".format(uid))
    return cursor.fetchall()[0][0]

def getUsersFriends(uid):
	cursor = conn.cursor()
	cursor.execute("SELECT uid_friend FROM Friends WHERE uid = '{0}'".format(uid))
	return cursor.fetchall()

def getUserName(uid):
	cursor = conn.cursor()
	cursor.execute("SELECT first_name, last_name FROM Users where uid = '{0}'".format(uid))
	return cursor.fetchall()

def addFriend(friend_uid):
	uid = getUserIdFromEmail(flask_login.current_user.id)
	cursor = conn.cursor()
	if cursor.execute("SELECT uid FROM Users WHERE uid='{0}'".format(friend_uid)):
        if cursor.execute("SELECT uid FROM Friends WHERE uid='{0}' AND friend_uid = '{1}'"
                .format(friend_uid, uid)):
            return False
        else:
            cursor.execute("INSERT INTO Friends(uid, uid_friend) VALUES ('{0}', '{1}'), ('{1}', '{0}')"
                            .format(uid, friend_uid))
            conn.commit()
            print("friend added!")
            return True
	else:
		return False

def searchUsers(s=''):
	cursor = conn.cursor()
    s = clean(s)
    if s == '':
        cursor.execute("SELECT uid FROM Users")
    else:
        cursor.execute("SELECT uid FROM Users WHERE '%'+first_name+'%' LIKE '{0}' AND '%'+last_name+'%' LIKE '{0}'",format(s) )
	return cursor.fetchall()

def getTags(eid):
	cursor = conn.cursor()
	cursor.execute("SELECT tag FROM Tags WHERE eid = '{0}'".format(eid))
	return cursor.fetchall()

def searchEvents(uid,time_s,time_e,friends,tags):
    cursor = conn.cursor()
    Friends_Events = """(SELECT eid
                         FROM Events, Friends
                         WHERE DATETIME('{1}') > Events.time_start
                         AND DATETIME('{2}') < Events.time_end)
                         AND Events.privacy LIKE 'private'
                         AND ((Friends.uid = '{3}' AND Friends.friend_uid = Events.owner_uid) OR '{3}' = Events.owner_uid))"""
    Public_Events = """(SELECT eid
                         FROM Events
                         WHERE DATETIME('{1}') > Events.time_start
                         AND DATETIME('{2}') < Events.time_end)
                         AND Events.privacy LIKE 'public')"""

    additional_const = " "
    for tag in tags:
        additional_const+= "AND E.eid IN (SELECT eid FROM Tags WHERE Tags.tag = '{0}') ".format(tag))
	if friends:
		Query = """SELECT E.name_e,E.desc_e,E.contact,E.time_start,E.time_end,E.location_e
				FROM Events E
				WHERE  E.eid in {0}  {1}""".format(Friends_Events, additional_const)
	else:
		Query = """SELECT E.name_e,E.desc_e,E.contact,E.time_start,E.time_end,E.location_e
				FROM Events as E
				WHERE (E.eid in {0} OR E.eid in {1}) {2}""".format(Friends_Events, Public_Events, additional_const)
	cursor.execute(Query)
	return cursor.fetchall()
#default page  
@app.route("/", methods=['GET'])
def hello():
	return render_template('hello.html', message='Welcome to App', users=findTopUsers())

# This is only used when running locally. When running live, gunicorn runs
# the application.
if __name__ == '__main__':
    app.run(host='127.0.0.1', port=8080, debug=True)
