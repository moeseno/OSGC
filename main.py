from flask_sock import Sock
from flask import Flask,render_template,request,redirect,session,jsonify
import jinja2
import csv
from datetime import timedelta
import json
import bleach
import sys

settings={}
waiting_room=[]
active_matches={}

def init(): #init function
    try:
        #checks settings
        with open("settings.txt") as o: 
            values=o.readlines()
            for value in values:
                #splits each line of settings
                split_value=value.split(".") 
                #error checks
                if len(split_value)!=3:
                    print("ERROR: Settings formatted poorly")
                    sys.exit()
                if ""in split_value:
                    print("ERROR: Missing value in settings")
                    sys.exit()
                #interprets settings
                if split_value[0]=="str": #interprets as string
                    settings[split_value[1]]=str(split_value[2])
                if split_value[0]=="int": #interprets as int
                    settings[split_value[1]]=int(split_value[2])
    except Exception as e:
        raise e
    
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
    error=""

    if request.method=="POST":

        login_attempt={"username":request.form.get("username",""),"password":request.form.get("password","")}

        try:
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
                    nonexistent_user=nonexistent_user,
                    error=error
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
                            nonexistent_user=nonexistent_user,
                            error=error
                            )
            nonexistent_user=True
        #if error        
        except Exception as e:
            error=f"{e}"
            return render_template(
                "login.html",
                missing_value=missing_value,
                wrong_password=wrong_password,
                nonexistent_user=nonexistent_user,
                error=error
                )

        #if user not in users list
        return render_template(
            "login.html",
            missing_value=missing_value,
            wrong_password=wrong_password,
            nonexistent_user=nonexistent_user,
            error=error
            )

    return render_template(
        "login.html",
        missing_value=missing_value,
        wrong_password=wrong_password,
        nonexistent_user=nonexistent_user,
        error=error
        )



@app.route("/signup",methods=["GET","POST"])
def signup():
    missing_value=False
    different_password=False
    username_exists=False
    username_too_long=False
    bad_username=False
    error=""

    if request.method=="POST":

        #creates user and password confirmation
        user={"username":request.form.get("username",""),"password":request.form.get("password","")}
        confirm=request.form.get("confirm","")

        #check if theres a bad character
        if user["username"]!=bleach.clean(user["username"])or user["username"]==settings["DEFAULT_USERNAME"]:
            bad_username=True
            return render_template(
                "signup.html",
                missing_value=missing_value,
                different_password=different_password,
                username_exists=username_exists,
                username_too_long=username_too_long,
                bad_username=bad_username,
                error=error
                )

        #check if username is longer than 16 charaacters
        if len(user["username"])>settings["USERNAME_CHAR_LIMIT"]:
            username_too_long=True
            return render_template(
                "signup.html",
                missing_value=missing_value,
                different_password=different_password,
                username_exists=username_exists,
                username_too_long=username_too_long,
                bad_username=bad_username,
                error=error
                )

        #check if sth is missing, if yes, returns missing value true 
        if "" in user.values():
            missing_value=True
            return render_template(
                "signup.html",
                missing_value=missing_value,
                different_password=different_password,
                username_exists=username_exists,
                username_too_long=username_too_long,
                bad_username=bad_username,
                error=error
                )
        
        #check if password matches confirm, if not, return different password true
        if user["password"]!=confirm: 
            different_password=True
            return render_template(
                "signup.html",
                missing_value=missing_value,
                different_password=different_password,
                username_exists=username_exists,
                username_too_long=username_too_long,
                bad_username=bad_username,
                error=error
                )

        #get usernames
        try:
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
                    username_too_long=username_too_long,
                    bad_username=bad_username,
                    error=error
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

        except Exception as e:
            error=f"{e}"
            return render_template(
            "signup.html",
            missing_value=missing_value,
            different_password=different_password,
            username_exists=username_exists,
            username_too_long=username_too_long,
            bad_username=bad_username,
            error=error
            )

    return render_template(
        "signup.html",
        missing_value=missing_value,
        different_password=different_password,
        username_exists=username_exists,
        username_too_long=username_too_long,
        bad_username=bad_username,
        error=error
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
    error=""

    #check if logged_in exists and set as false
    if "logged_in" not in session:
        session["logged_in"]=False

    #check if logged in
    if session["logged_in"]:
        user={session["uid"]:session["username"]}
        #puts player in waiting room if they r not already in it
        if user not in waiting_room:
            waiting_room.append(user)

        #check for other players in waiting room and puts them in a match
        if len(waiting_room)>=2:

            try:
                #assigns match_id and counter +1
                with open("match_id_counter.txt")as file:
                    match_id=str(int(file.read())+1)
                with open("match_id_counter.txt","w")as file:
                    file.write(str(match_id))

                #assigns uid and username of players
                uid1=list(waiting_room[0].keys())[0]
                username1=waiting_room[0][uid1]

                uid2=list(waiting_room[1].keys())[0]
                username2=waiting_room[1][uid2]

                #creates match and remove from waiting room
                active_matches[match_id]={
                    "players":2,
                    uid1:username1,
                    uid2:username2,
                    "clients":[]
                }
                waiting_room.pop(0)
                waiting_room.pop(0)
                return redirect(f"/match/{match_id}")
            except Exception as e:
                error=f"An error occured: {e}"

        return render_template(
            "matchmaking.html",
            error=error
            )
    return redirect("/")



@app.route("/match/<match_id>",methods=["GET","POST"])
def match(match_id):
    #check if logged_in exists and set as false
    if "logged_in" not in session:
        session["logged_in"]=False

    #check if logged in
    if session["logged_in"]:
        #assign match data
        match_data=active_matches.get(match_id,{})

        #prevent unauthorized users from accessing match
        if session["uid"] not in match_data.keys():
            return redirect("/")

        #assign current user
        username=match_data[session["uid"]]

        #assign opponent 
        for uid in match_data.keys():
            if uid!="players"and uid!="clients"and uid!=session["uid"]:
                opponent_uid=uid
                break

        opponent_name=match_data[opponent_uid]

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
    #get current match's clients
    active_clients=active_matches[match_id]["clients"]

    #add client to active_clients
    if ws not in active_clients:
        active_clients.append(ws)

    try:
        while True:
            try:
                #recieve message, break if no message
                json_message=ws.receive()
                if json_message==None:
                    break

                message=json.loads(json_message)

                #check if message has keys text and user
                if "text" in message and "user" in message:
                    if not message["text"]:
                        message["text"]=" "
                    #clean message to prevent attacks
                    message["text"]=bleach.clean(message["text"])
                    #formats message
                    formatted_message=f"{message['user']}:{message['text']}"

                    #tries sending message to every client and if not successful, passes
                    for client in active_clients:
                        try:
                            client.send(json.dumps(formatted_message))
                        except Exception:
                            bad_clients.append(client)
                            pass

                else:
                    print("ERROR: Message missing 'text' or 'user' key.")
                    continue

            except Exception as e:
                print(f"ERROR: {e}")
                break
            
    finally:
        #sends message to connected clients
        for client in active_clients:
            try:
                client.send(json.dumps(f"SERVER: {session["username"]} has disconnected, redirecting in 5 seconds..."))
            except Exception as e:
                raise

        #remove from active clients
        active_clients.remove(ws)
        #remove match
        active_matches.pop(match_id)

