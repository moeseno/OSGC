from flask_sock import Sock
from flask import Flask,render_template,request,redirect,session,jsonify
import jinja2
import csv
from datetime import timedelta
import json
import bleach
import sys
import random

#global dictionary for settings
settings={}
#global list for matchmaking queue
waiting_room=[]
#global dictionary for active games
active_matches={}


#represents a player in a match
class Player():
    """
    Player object created when entering match

    Attributes:
        username (str): The player's username
        uid (str): The player's uid
        cards_list (list): The list of card objects the player is bringing into this match
        client (websocket client thingy): The websocket client of the player
    """
    #player attributes: username, unique id, list of cards, websocket connection
    def __init__(self,username,uid,cards_list,client):
        self.username=username
        self.uid=uid
        self.cards_list=cards_list
        #stores the websocket client object
        self.client=client



#represents a game card
class Card():
    """
    Base card object for all cards

    Attributes:
        name (str):
        hp (int):
        speed (int):

    Has 3 base abilities
    """
    #card attributes: name, health points, speed
    def __init__(self,name,hp,speed):
        self.name=name
        self.hp=hp
        self.speed=speed

    def death_check(self,target):
        if target.hp<=0:
            target.hp=0
            return True

    #ability 1: deals 1 damage
    def ability1(self,caster,opponent,target):
        target.hp-=1
        death_status=self.death_check(target)
        #returns action data for clients
        return {
            "type":"action",
            "attacking_player_uid":caster.uid,
            "targeted_player_uid":opponent.uid,
            "attacking_card_index":caster.cards_list.index(self),
            "targeted_card_index":opponent.cards_list.index(target),
            "target_hp":target.hp,
            "death":death_status
        }

    #ability 2: deals 2 damage
    def ability2(self,caster,opponent,target):
        target.hp-=2
        death_status=self.death_check(target)
        #returns action data for clients
        return {
            "type":"action",
            "attacking_player_uid":caster.uid,
            "targeted_player_uid":opponent.uid,
            "attacking_card_index":caster.cards_list.index(self),
            "targeted_card_index":opponent.cards_list.index(target),
            "target_hp":target.hp,
            "death":death_status
        }

    #ability 3: deals 3 damage
    def ability3(self,caster,opponent,target):
        target.hp-=3
        death_status=self.death_check(target)
        #returns action data for clients
        return {
            "type":"action",
            "attacking_player_uid":caster.uid,
            "targeted_player_uid":opponent.uid,
            "attacking_card_index":caster.cards_list.index(self),
            "targeted_card_index":opponent.cards_list.index(target),
            "target_hp":target.hp,
            "death":death_status
        }



#loads settings from settings.txt
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
                    sys.exit()
                if ""in split_value:
                    sys.exit()
                #interprets settings
                if split_value[0]=="str": #interprets as string
                    settings[split_value[1]]=str(split_value[2])
                if split_value[0]=="int": #interprets as int
                    settings[split_value[1]]=int(split_value[2])
    except Exception as e:
        #handle errors during initialization
        raise e

#run initialization
init()

#create flask app instance
app=Flask(__name__)
#initialize flask-sock
sock=Sock(app)
#set flask secret key from settings
app.secret_key=settings["SECRET_KEY"]

#route for the homepage
@app.route("/",methods=["GET"])
def index():
    #ensure logged_in status is in session
    if "logged_in" not in session:
        session["logged_in"]=False
    #render index page
    return render_template(
        "index.html"
        )



#route for login (GET displays form, POST handles submission)
@app.route("/login",methods=["GET","POST"])
def login():
    #initialize error flags
    missing_value=False
    wrong_password=False
    nonexistent_user=False
    error=""

    #handle form submission
    if request.method=="POST":
        #get form data
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
                            #store user info in session on success
                            session["username"]=user["username"]
                            session["uid"]=user["uid"]
                            session["logged_in"]=True
                            #redirect to homepage
                            return redirect("/")
                        #if password does not match
                        else:
                            #set wrong password flag
                            wrong_password=True
                            break #stop checking users
                #if loop finished without finding username/password match
                else:
                    nonexistent_user=True

        #if error
        except Exception as e:
            error=f"{e}"

    #render login page with appropriate error flags
    return render_template(
        "login.html",
        missing_value=missing_value,
        wrong_password=wrong_password,
        nonexistent_user=nonexistent_user,
        error=error
        )



#route for signup (GET displays form, POST handles submission)
@app.route("/signup",methods=["GET","POST"])
def signup():
    #initialize error flags
    missing_value=False
    different_password=False
    username_exists=False
    username_too_long=False
    bad_username=False
    error=""

    #handle form submission
    if request.method=="POST":
        #creates user and password confirmation
        user={"username":request.form.get("username",""),"password":request.form.get("password","")}
        confirm=request.form.get("confirm","")

        #check if theres a bad character
        if user["username"]!=bleach.clean(user["username"])or user["username"]==settings["DEFAULT_USERNAME"]:
            bad_username=True
        #check if username is longer than 16 characters
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
                if user["username"] in usernames:
                    username_exists=True

                #if username is available
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

            #handle file/processing errors
            except Exception as e:
                error=f"{e}"

    #render signup page with appropriate error flags
    return render_template(
        "signup.html",
        missing_value=missing_value,
        different_password=different_password,
        username_exists=username_exists,
        username_too_long=username_too_long,
        bad_username=bad_username,
        error=error
        )



#route for login test page (debugging)
@app.route("/login_test",methods=["GET"])
def login_test():
    #check if logged_in exists and set as false
    if "logged_in" not in session:
        session["logged_in"]=False
    logged_in=session["logged_in"]
    #render test page
    return render_template(
        "login_test.html",
        logged_in=logged_in
        )



#route for logging out
@app.route("/logout",methods=["GET"])
def logout():
    #clear session data
    session.clear()
    #redirect to homepage
    return redirect("/")



#route for matchmaking page
@app.route("/matchmaking",methods=["GET"])
def matchmaking():
    #redirect if not logged in
    if "logged_in" not in session or not session["logged_in"]:
        return redirect("/")

    #prepare user data for waiting room
    user_dict={session["uid"]:session["username"]}

    #add user to waiting room if not already there
    if user_dict not in waiting_room:
        waiting_room.append(user_dict)

    #check if enough players are waiting
    if len(waiting_room)>=2:
        #generate new match id
        with open("match_id_counter.txt") as file:
            content=file.read().strip()
            match_id=str(int(content)+1)
        with open("match_id_counter.txt","w") as file:
            file.write(match_id)

        #get the first two players from the waiting room (original way)
        uid1=list(waiting_room[0].keys())[0]
        username1=waiting_room[0][uid1]
        uid2=list(waiting_room[1].keys())[0]
        username2=waiting_room[1][uid2]

        #Determine who goes first randomly
        player_uids=[uid1,uid2]
        next_actioning_player_uid=random.choice(player_uids)

        #create match entry in active_matches
        active_matches[match_id]={
            "players":{
                #initialize player 1 object
                uid1:Player(username=username1,uid=uid1,cards_list=[Card(name="card1",hp=10,speed=10),Card(name="card2",hp=10,speed=10),Card(name="card3",hp=10,speed=10)],client=None),
                #initialize player 2 object
                uid2:Player(username=username2,uid=uid2,cards_list=[Card(name="card4",hp=10,speed=10),Card(name="card5",hp=10,speed=10),Card(name="card6",hp=10,speed=10)],client=None)
            },
            "next_actioning_player_uid":next_actioning_player_uid
        }

        waiting_room.pop(0)
        waiting_room.pop(0)

        #redirect players to the created match
        return redirect(f"/match/{match_id}")

    #render waiting page if not enough players
    return render_template(
        "matchmaking.html"
        )



#route for the match page itself
@app.route("/match/<match_id>",methods=["GET"])
def match(match_id):
    #redirect if not logged in
    if "logged_in" not in session or not session["logged_in"]:
        return redirect("/")
    #validate match_id format (original check)
    if not match_id.isdigit():
         return redirect("/")
    #check if match exists (added check for safety, wasn't explicitly in original but good practice)
    if match_id not in active_matches:
        return redirect("/") # Or handle error appropriately

    #get match data
    match_data=active_matches[match_id]
    players=match_data["players"]

    #verify user is part of this match
    if session["uid"] not in players:
        return redirect("/")

    #get current player details
    current_player=players[session["uid"]]
    username=current_player.username
    cards=current_player.cards_list

    #find opponent details (original way)
    #initialize opponent variables
    opponent_username=None
    opponent_uid=None
    opponent_cards=None
    for uid,player in players.items():
        if uid!=session["uid"]:
            opponent_username=player.username
            opponent_uid=player.uid
            opponent_cards=player.cards_list
            break

    #Get the UID of the player whose turn it is
    next_actioning_player_uid=match_data["next_actioning_player_uid"]

    #render match page with necessary data
    return render_template(
        "match.html",
        username=username,
        opponent_username=opponent_username,
        match_id=match_id,
        uid=session["uid"],
        cards=cards,
        opponent_cards=opponent_cards,
        opponent_uid=opponent_uid,
        next_actioning_player_uid=next_actioning_player_uid
        )



#api endpoint for clients polling for match status
@app.route("/check_for_match",methods=["GET"])
def check_for_match():
    #return false if not logged in
    if "logged_in" not in session or not session["logged_in"]:
        return jsonify({"matched":False})

    #search active matches for the user's uid (original way)
    for match_id,match_data in active_matches.items():
        if session["uid"] in match_data["players"]:
            #return match found status and id
            return jsonify({"matched":True,"match_id":match_id})

    #return false if user not found in any active match
    return jsonify({"matched":False})



#websocket route for handling match communication (chat and actions)
@sock.route("/chat/match/<match_id>")
def chat(ws,match_id):
    uid = None #will be set after authentication

    try:
        #validate match_id and check if match exists
        if not match_id.isdigit() or match_id not in active_matches:
            ws.close()
            return

        #get match data
        match_data=active_matches[match_id]
        players=match_data["players"]

        #receive and validate authentication message
        json_auth_message=ws.receive(timeout=10)
        if json_auth_message is None:
            ws.close()
            return
        auth_message=json.loads(json_auth_message)
        if not isinstance(auth_message,dict) or auth_message.get("type")!="auth" or "uid" not in auth_message:
            ws.close()
            return

        #get uid and verify player is in this match
        uid=auth_message["uid"]
        if uid not in players:
            ws.close()
            return

        #get player object and check for existing connection
        player=players[uid]
        if player.client is not None:
            ws.close()
            return #prevent multiple connections

        #assign websocket connection to player
        player.client=ws

        #main message loop
        while True:
            json_message=ws.receive()
            #client disconnected if message is None
            if json_message is None:
                break

            message=json.loads(json_message)

            #handle chat messages
            if isinstance(message,dict) and message.get("type")=="chat" and "text" in message:
                #sanitize and format chat message
                cleaned_text=bleach.clean(message["text"]).strip()
                username=player.username
                formatted_message=f"{username}: {cleaned_text}"
                message_to_send=json.dumps(formatted_message)

                #broadcast chat message to all connected clients in the match (original way)
                current_clients=[p.client for p in players.values() if p.client is not None]
                for client in current_clients:
                    try:
                        client.send(message_to_send)
                    except Exception: #handle potential disconnection during broadcast
                        for p_obj in players.values():
                            if p_obj.client==client:
                                p_obj.client=None

            #handle game actions
            elif isinstance(message,dict) and message.get("type")=="action":
                #extract action details (original way)
                ability_number=message["abilityNumber"]
                attacking_player_uid=message["attackingPlayerUid"]
                attacking_card_index=message["attackingCardIndex"]
                targeted_player_uid=message["targetedPlayerUid"]
                targeted_card_index=message["targetedCardIndex"]

                #Its not their turn, ignore the action
                if attacking_player_uid!=match_data.get("next_actioning_player_uid"):
                    #Skip to the next iteration of the loop
                    continue

                attacking_card=players[attacking_player_uid].cards_list[attacking_card_index]
                targeted_card=players[targeted_player_uid].cards_list[targeted_card_index]
                attacking_player=players[attacking_player_uid]
                targeted_player=players[targeted_player_uid]

                ability_name=f"ability{ability_number}"
                ability_method=getattr(attacking_card,ability_name)

                #execute ability and get result message
                message=ability_method(attacking_player,targeted_player,targeted_card)
                message_to_send=json.dumps(message)

                #broadcast action result to all connected clients
                current_clients=[p.client for p in players.values() if p.client is not None]
                for client in current_clients:
                    try:
                        client.send(message_to_send)
                    except Exception: #handle potential disconnection
                        for p_obj in players.values():
                             if p_obj.client==client:
                                 p_obj.client=None

                # Determine the next player (the one who was targeted)
                next_actioning_player_uid=targeted_player_uid
                match_data["next_actioning_player_uid"]=next_actioning_player_uid # Update server state

                # Prepare turn update message
                turn_update_message={
                    "type":"turn",
                    "next_actioning_player_uid":next_actioning_player_uid
                }
                turn_update_to_send=json.dumps(turn_update_message)

                # Broadcast turn update to all connected clients
                # Re-fetch clients in case one disconnected during action broadcast
                current_clients=[p.client for p in players.values() if p.client is not None]
                for client in current_clients:
                    try:
                        client.send(turn_update_to_send)
                    except Exception: # handle potential disconnection
                        for p_obj in players.values():
                            if p_obj.client==client:
                                p_obj.client=None

    #cleanup block, runs on disconnect or error
    finally:
        try:
            #re-fetch match data (original way)
            match_data=active_matches[match_id]
            players=match_data["players"]
            player=players[uid]

            #check if this is the active client for the player (original way)
            if player.client==ws:
                player.client=None #mark player as disconnected
                disconnected_username=player.username

                #notify other players (original way)
                disconnect_message=f"SERVER: {disconnected_username} has disconnected, redirecting in 5 seconds..."
                message_to_send=json.dumps(disconnect_message)
                for p_obj in players.values():
                    if p_obj.uid!=uid and p_obj.client is not None:
                        try:
                            p_obj.client.send(message_to_send)
                        except Exception:
                            p_obj.client=None #mark other player disconnected if send fails

                #delete the match from active matches (original way)
                del active_matches[match_id]

        except Exception:
            pass