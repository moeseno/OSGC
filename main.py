from flask import Flask,render_template,request,redirect,session
import jinja2
import csv
from datetime import timedelta

settings={}
def init(): #init function
	with open("settings.txt") as o: #checks settings
		values=o.readlines()
		for value in values:
			split_value=value.split(".") #splits each line of settings
			if split_value[0]=="str": #interprets as string
				settings[split_value[1]]=str(split_value[2])
init()

app=Flask(__name__)
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

	if request.method=="POST":

		#creates user and password confirmation
		user={"username":request.form.get("username",""),"password":request.form.get("password","")}
		confirm=request.form.get("confirm","")

		#check if sth is missing, if yes, returns missing value true 
		if "" in user.values():
			missing_value=True
			return render_template(
				"signup.html",
				missing_value=missing_value,
				different_password=different_password,
				username_exists=username_exists
				)
		
		#check if password matches confirm, if not, return different password true
		if user["password"]!=confirm: 
			different_password=True
			return render_template(
				"signup.html",
				missing_value=missing_value,
				different_password=different_password,
				username_exists=username_exists
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
				username_exists=username_exists
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
		username_exists=username_exists
		)



@app.route("/login_test",methods=["GET"])
def login_test():
	logged_in=session["logged_in"]
	print(session)
	return render_template(	
		"login_test.html",
		logged_in=logged_in
		)

@app.route("/logout",methods=["GET"])
def logout():
	session.clear()
	return redirect("/")