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


class Player():
    """
    Player object created when entering match

    Attributes:
        username (str): The player's username
        uid (str): The player's uid
        cards_list (list): The list of card objects the player is bringing into this match
        client (websocket client thingy): The websocket client of the player
    """
    def __init__(self,username,uid,cards_list,client):
        self.username=username
        self.uid=uid
        self.cards_list=cards_list
        self.client=client


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

            #find user
            if not missing_value:
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
                            break
                else:
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

        #check if username is longer than 16 charaacters
        if len(user["username"])>settings["USERNAME_CHAR_LIMIT"]:
            username_too_long=True

        #check if sth is missing, if yes, returns missing value true 
        if "" in user.values():
            missing_value=True
        
        #check if password matches confirm, if not, return different password true
        if user["password"]!=confirm: 
            different_password=True

        #check if any errors
        if not any([missing_value,different_password,username_too_long,bad_username]):
            #get usernames
            try:
                with open("users.csv","r",newline="",encoding="utf-8") as file:
                    reader=csv.DictReader(file)
                    usernames=[row["username"] for row in reader]

                #check if username alr exists
                    username_exists=True

                if not username_exists:
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
    if "logged_in" not in session or not session["logged_in"]:
        return redirect("/")

    user_dict={session["uid"]:session["username"]}

    if user_dict not in waiting_room:
        waiting_room.append(user_dict)

    if len(waiting_room)>=2:
        with open("match_id_counter.txt") as file:
            content=file.read().strip()
            match_id=str(int(content)+1)

        with open("match_id_counter.txt","w") as file:
            file.write(match_id)

        uid1=list(waiting_room[0].keys())[0]
        username1=waiting_room[0][uid1]
        uid2=list(waiting_room[1].keys())[0]
        username2=waiting_room[1][uid2]

        active_matches[match_id]={
            "players":{
                uid1:Player(username=username1,uid=uid1,cards_list=[],client=None),
                uid2:Player(username=username2,uid=uid2,cards_list=[],client=None)
            }
        }
 
        waiting_room.pop(0)
        waiting_room.pop(0)
 
        return redirect(f"/match/{match_id}")

    return render_template(
        "matchmaking.html"
        )

    return redirect("/")



@app.route("/match/<match_id>",methods=["GET"])
def match(match_id):
    if "logged_in" not in session or not session["logged_in"]:
        return redirect("/")

    if not match_id.isdigit():
         return redirect("/")

    match_data=active_matches[match_id]

    players=match_data["players"]

    if session["uid"] not in players:
        return redirect("/")

    current_player=players[session["uid"]]
    username=current_player.username

    for uid,player in players.items():
        if uid!=session["uid"]:
            opponent_username=player.username
            break

    return render_template(
        "match.html",
        username=username,
        opponent_username=opponent_username,
        match_id=match_id,
        uid=session["uid"]
        )



@app.route("/check_for_match",methods=["GET"])
def check_for_match():
    if "logged_in" not in session or not session["logged_in"]:
        return jsonify({"matched":False})

    for match_id,match_data in active_matches.items():
        if session["uid"] in match_data["players"]:
            return jsonify({"matched":True,"match_id":match_id})

    return jsonify({"matched":False})



@sock.route("/chat/match/<match_id>")
def chat(ws,match_id):
    try:
        if not match_id.isdigit() or match_id not in active_matches:
            return

        match_data=active_matches[match_id]
        players=match_data["players"]

        json_auth_message=ws.receive(timeout=10)
        if json_auth_message is None:
            ws.close()
            return

        auth_message=json.loads(json_auth_message)

        if not isinstance(auth_message,dict) or auth_message.get("type")!="auth" or "uid" not in auth_message:
            ws.close()
            return

        uid=auth_message["uid"]
        if uid not in players:
            ws.close()
            return

        player=players[uid]
        if player.client is not None:
            ws.close()
            return

        player.client=ws

        while True:
            json_message=ws.receive()
            if json_message is None: break

            message=json.loads(json_message)

            if isinstance(message,dict) and message.get("type")=="chat" and "text" in message:
                cleaned_text=bleach.clean(message["text"]).strip()

                username=player.username
                formatted_message=f"{username}: {cleaned_text}"

                message_to_send=json.dumps(formatted_message)

                current_clients=[p.client for p in players.values() if p.client is not None]
                for client in current_clients:
                    try:
                        client.send(message_to_send)
                    except Exception:
                        for p_obj in players.values():
                            if p_obj.client==client:
                                p_obj.client=None

    finally:
        try:
            match_data=active_matches[match_id]
            players=match_data["players"]
            player=players[uid]

            if player.client==ws:

                player.client=None
                disconnected_username=player.username

                disconnect_message=f"SERVER: {disconnected_username} has disconnected, redirecting in 5 seconds..."
                message_to_send=json.dumps(disconnect_message)

                for p_obj in players.values():
                    if p_obj.uid!=uid and p_obj.client is not None:
                        try:
                            p_obj.client.send(message_to_send)
                        except Exception:
                            p_obj.client=None
                    
                del active_matches[match_id]

        except Exception:
            pass