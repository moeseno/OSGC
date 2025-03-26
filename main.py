from flask_sock import Sock
from flask import Flask,render_template,request,redirect,session,jsonify
import jinja2
import csv
from datetime import timedelta
import json

settings={}
waiting_room=[]
active_matches={}

def init(): #init function
	with open("settings.txt") as o: #checks settings
		values=o.readlines()
		for value in values:
			split_value=value.split(".") #splits each line of settings
			if split_value[0]=="str": #interprets as string
				settings[split_value[1]]=str(split_value[2])

init()

app=Flask(__name__)
sock=Sock(app)
app.secret_key=settings["SECRET_KEY"]

@app.route("/",methods=["GET"])
def index():
	if "logged_in" not in session:
		session["logged_in"]=False
	return render_template(
		"index.html"
		)



@app.route("/login",methods=["GET","POST"])
def login():
	missing_value=False
	wrong_password=False
	nonexistent_user=False

	if request.method=="POST":

		login_attempt={"username":request.form.get("username",""),"password":request.form.get("password","")}

		#get users
		with open("users.csv","r",newline="",encoding="utf-8") as file:
			reader=csv.DictReader(file)
			users=[row for row in reader]

		#check if sth is missing, if yes, returns missing value true 
		if "" in login_attempt.values():
			missing_value=True
			return render_template(
				"login.html",
				missing_value=missing_value,
				wrong_password=wrong_password,
				nonexistent_user=nonexistent_user
				)

		#find user
		for user in users:
			#check if username and password matches
			if login_attempt["username"]==user["username"]:
				if login_attempt["password"]==user["password"]:
					session["username"]=user["username"]
					session["uid"]=user["uid"]
					session["logged_in"]=True
					return redirect("/")
				#if password does not match
				else:
					wrong_password=True
					return render_template(
						"login.html",
						missing_value=missing_value,
						wrong_password=wrong_password,
						nonexistent_user=nonexistent_user
						)
		#if user not in users list
		nonexistent_user=True
		return render_template(
			"login.html",
			missing_value=missing_value,
			wrong_password=wrong_password,
			nonexistent_user=nonexistent_user
			)

	return render_template(
		"login.html",
		missing_value=missing_value,
		wrong_password=wrong_password,
		nonexistent_user=nonexistent_user
		)



@app.route("/signup",methods=["GET","POST"])
def signup():
	missing_value=False
	different_password=False
	username_exists=False
	username_too_long=False

	if request.method=="POST":

		#creates user and password confirmation
		user={"username":request.form.get("username",""),"password":request.form.get("password","")}
		confirm=request.form.get("confirm","")

		#check if username is longer than 16 charaacters
		if len(user["username"])>16:
			username_too_long=True
			return render_template(
				"signup.html",
				missing_value=missing_value,
				different_password=different_password,
				username_exists=username_exists,
				username_too_long=username_too_long
				)

		#check if sth is missing, if yes, returns missing value true 
		if "" in user.values():
			missing_value=True
			return render_template(
				"signup.html",
				missing_value=missing_value,
				different_password=different_password,
				username_exists=username_exists,
				username_too_long=username_too_long
				)
		
		#check if password matches confirm, if not, return different password true
		if user["password"]!=confirm: 
			different_password=True
			return render_template(
				"signup.html",
				missing_value=missing_value,
				different_password=different_password,
				username_exists=username_exists,
				username_too_long=username_too_long
				)

		#get usernames
		with open("users.csv","r",newline="",encoding="utf-8") as file:
			reader=csv.DictReader(file)
			usernames=[row["username"] for row in reader]

		#check if username alr exists
		if user["username"] in usernames:
			username_exists=True
			return render_template(
				"signup.html",
				missing_value=missing_value,
				different_password=different_password,
				username_exists=username_exists,
				username_too_long=username_too_long
				)

		#get uid for user
		with open("uid_counter.txt")as file:
			uid=int(file.read())+1
		with open("uid_counter.txt","w")as file:
			file.write(str(uid))

		#give uid to user
		user["uid"]=uid

		#writes user into file
		with open("users.csv","a",newline="",encoding="utf-8") as file:
			fieldnames=["username","password","uid"]
			writer=csv.DictWriter(file,fieldnames=fieldnames)
			writer.writerow(user)

		#redirects to login
		return redirect("/login")

	return render_template(
		"signup.html",
		missing_value=missing_value,
		different_password=different_password,
		username_exists=username_exists,
		username_too_long=username_too_long
		)



@app.route("/login_test",methods=["GET"])
def login_test():
	#check if logged_in exists and set as false
	if "logged_in" not in session:
		session["logged_in"]=False

	logged_in=session["logged_in"]
	return render_template(	
		"login_test.html",
		logged_in=logged_in
		)



@app.route("/logout",methods=["GET"])
def logout():
	session.clear()
	return redirect("/")



@app.route("/matchmaking",methods=["GET"])
def matchmaking():
	#check if logged_in exists and set as false
	if "logged_in" not in session:
		session["logged_in"]=False

	#check if logged in
	if session["logged_in"]:
		#puts player in waiting room if they r not already in it
		if session["username"]not in waiting_room:
			waiting_room.append(session["username"])

		print(waiting_room)

		#check for other players in waiting room and puts them in a match
		if len(waiting_room)>=2:

			with open("match_id_counter.txt")as file:
				match_id=str(int(file.read())+1)
			with open("match_id_counter.txt","w")as file:
				file.write(str(match_id))

			#creates match and remove from waiting room
			active_matches[match_id]={"players":2,"player1":waiting_room[0],"player2":waiting_room[1],"clients":[]}
			waiting_room.pop(0)
			waiting_room.pop(0)
			return redirect(f"/match/{match_id}")
		return render_template(
			"matchmaking.html"
			)
	return redirect("/")



@app.route("/match/<match_id>",methods=["GET","POST"])
def match(match_id):
	#check if logged_in exists and set as false
	if "logged_in" not in session:
		session["logged_in"]=False

	#check if logged in
	if session["logged_in"]:
		#assigns current user and opponent
		username=session["username"]
		match_data=active_matches[match_id]

		#prevent unauthorized users from accessing match
		if username not in match_data.values():
			return redirect("/")

		#check which player is opponent
		if username==match_data["player1"]:
			opponent_name=match_data["player2"]
		elif username==match_data["player2"]:
			opponent_name=match_data["player1"]

		return render_template(
			"match.html",
			username=username,
			opponent_name=opponent_name,
			match_id=match_id
			)
	return redirect("/")



@app.route("/check_for_match",methods=["GET"])
def check_for_match():
	user=session["username"]
	#check if matched
	for match_id,match_data in active_matches.items():
		if user in match_data.values():
			return jsonify({"matched":True,"match_id":match_id})

	return jsonify({"matched":False})



@sock.route("/chat/match/<match_id>")
def chat(ws,match_id):
	while True:
		#try recieving message
		try:
			json_message=ws.receive()
			message=json.loads(json_message)

			#check if is initial connection
			if message=={'open':True}:
				active_matches[match_id]["clients"].append(ws)
			#formats the message and sends to all clients
			else:
				formatted_message=f"{message["user"]}: {message["text"]}"
				for client in active_matches[match_id]["clients"]:
					client.send(json.dumps(formatted_message))

		#error handling
		except (TypeError, json.JSONDecodeError) as e:
			print(f"Error: {e}")
			break