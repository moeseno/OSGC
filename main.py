from flask_sock import Sock
from flask import Flask,render_template,request,redirect,session,jsonify
import jinja2
import csv
from datetime import timedelta
import json
import bleach
import sys
import random

settings={}
waiting_room=[]
active_matches={}

class Player():
    """Represents a player session in a match.

    Attributes:
        username (str)
        uid (str)
        cards_list (list): Card objects for the match.
        client: WebSocket connection.
    """
    def __init__(self,username,uid,cards_list,client):
        self.username=username
        self.uid=uid
        self.cards_list=cards_list
        self.client=client
        self.active_card_index=None



class Card():
    """Base object for game cards."""
    def __init__(self,name,hp,speed):
        self.name=name
        self.hp=hp
        self.speed=speed

    def death_check(self,target):
        if target.hp<=0:
            target.hp=0
            return True
        return False

    def ability1(self,caster,opponent,target):
        target.hp-=1
        death_status=self.death_check(target)
        return {
            "type":"action",
            "attacking_player_uid":caster.uid,
            "targeted_player_uid":opponent.uid,
            "attacking_card_index":caster.cards_list.index(self),
            "targeted_card_index":opponent.cards_list.index(target),
            "target_hp":target.hp,
            "death":death_status
        }

    def ability2(self,caster,opponent,target):
        target.hp-=2
        death_status=self.death_check(target)
        return {
            "type":"action",
            "attacking_player_uid":caster.uid,
            "targeted_player_uid":opponent.uid,
            "attacking_card_index":caster.cards_list.index(self),
            "targeted_card_index":opponent.cards_list.index(target),
            "target_hp":target.hp,
            "death":death_status
        }

    def ability3(self,caster,opponent,target):
        target.hp-=3
        death_status=self.death_check(target)
        return {
            "type":"action",
            "attacking_player_uid":caster.uid,
            "targeted_player_uid":opponent.uid,
            "attacking_card_index":caster.cards_list.index(self),
            "targeted_card_index":opponent.cards_list.index(target),
            "target_hp":target.hp,
            "death":death_status
        }



#Loads settings from settings.txt into the global 'settings' dictionary.
#Expects format: type.key.value (e.g., str.SECRET_KEY.mysecret) per line.
#Exits application if format is incorrect or file read fails.
def init():
    try:
        with open("settings.txt") as o:
            values=o.readlines()
            for value in values:
                split_value=value.split(".")
                if len(split_value)!=3:
                    sys.exit()
                if "" in split_value:
                    sys.exit()
                if split_value[0]=="str":
                    settings[split_value[1]]=str(split_value[2])
                if split_value[0]=="int":
                    settings[split_value[1]]=int(split_value[2])
    except Exception as e:
        #Re-raise exception on file read or processing error.
        raise e

init()

app=Flask(__name__)
sock=Sock(app)
#Set Flask secret key from loaded settings.
app.secret_key=settings["SECRET_KEY"]

@app.route("/",methods=["GET"])
def index():
    #Initialize session login status if not present.
    if "logged_in" not in session:
        session["logged_in"]=False
    return render_template("index.html")



#GET displays login form, POST handles login attempt.
@app.route("/login",methods=["GET","POST"])
def login():
    #Flags for form feedback.
    missing_value=False
    wrong_password=False
    nonexistent_user=False
    error=""

    #Handle form submission.
    if request.method=="POST":
        login_attempt={"username":request.form.get("username",""),"password":request.form.get("password","")}

        try:
            #Read user data.
            with open("users.csv","r",newline="",encoding="utf-8") as file:
                reader=csv.DictReader(file)
                users=[row for row in reader]

            #Check for empty fields.
            if "" in login_attempt.values():
                missing_value=True

            #Validate credentials if fields were provided.
            if not missing_value:
                for user in users:
                    if login_attempt["username"]==user["username"]:
                        #Username found, check password.
                        if login_attempt["password"]==user["password"]:
                            #Login successful.
                            session["username"]=user["username"]
                            session["uid"]=user["uid"]
                            session["logged_in"]=True
                            return redirect("/")
                        else:
                            wrong_password=True
                            #Stop search after finding user with wrong password.
                            break
                #Executes ONLY if the loop completes without 'break' (username not found).
                else:
                    nonexistent_user=True

        #Handle potential file/processing errors.
        except Exception as e:
            error=f"{e}"

    #Render login page with feedback.
    return render_template(
        "login.html",
        missing_value=missing_value,
        wrong_password=wrong_password,
        nonexistent_user=nonexistent_user,
        error=error
        )



#GET displays signup form, POST handles signup attempt.
@app.route("/signup",methods=["GET","POST"])
def signup():
    #Flags for form feedback.
    missing_value=False
    different_password=False
    username_exists=False
    username_too_long=False
    bad_username=False
    error=""

    #Handle form submission.
    if request.method=="POST":
        user={"username":request.form.get("username",""),"password":request.form.get("password","")}
        confirm=request.form.get("confirm","")

        #Sanitize and validate username against disallowed characters/names.
        if user["username"]!=bleach.clean(user["username"])or user["username"]==settings["DEFAULT_USERNAME"]:
            bad_username=True
        #Validate username length.
        if len(user["username"])>settings["USERNAME_CHAR_LIMIT"]:
            username_too_long=True
        #Check for empty fields.
        if "" in user.values():
            missing_value=True
        #Check password confirmation match.
        if user["password"]!=confirm:
            different_password=True

        #Proceed only if initial validations pass.
        if not any([missing_value,different_password,username_too_long,bad_username]):
            try:
                #Read existing usernames to check for duplicates.
                with open("users.csv","r",newline="",encoding="utf-8") as file:
                    reader=csv.DictReader(file)
                    usernames=[row["username"] for row in reader]

                if user["username"] in usernames:
                    username_exists=True

                #If username is available, create the user.
                if not username_exists:
                    #Generate next unique ID from a counter file.
                    with open("uid_counter.txt")as file:
                        uid=int(file.read())+1
                    with open("uid_counter.txt","w")as file:
                        file.write(str(uid))

                    user["uid"]=uid

                    #Append new user data to the CSV.
                    with open("users.csv","a",newline="",encoding="utf-8") as file:
                        fieldnames=["username","password","uid"]
                        writer=csv.DictWriter(file,fieldnames=fieldnames)
                        writer.writerow(user)

                    #Redirect to login page after successful signup.
                    return redirect("/login")

            #Handle potential file/processing errors.
            except Exception as e:
                error=f"{e}"

    #Render signup page with feedback.
    return render_template(
        "signup.html",
        missing_value=missing_value,
        different_password=different_password,
        username_exists=username_exists,
        username_too_long=username_too_long,
        bad_username=bad_username,
        error=error
        )



#Debugging route to check login status.
@app.route("/login_test",methods=["GET"])
def login_test():
    if "logged_in" not in session:
        session["logged_in"]=False
    logged_in=session["logged_in"]
    return render_template("login_test.html",logged_in=logged_in)



#Logs the user out.
@app.route("/logout",methods=["GET"])
def logout():
    session.clear()
    return redirect("/")



#Handles matchmaking: adds players to queue and creates matches.
@app.route("/matchmaking",methods=["GET"])
def matchmaking():
    #Ensure user is logged in.
    if "logged_in" not in session or not session["logged_in"]:
        return redirect("/")

    #User identifier for the waiting room.
    user_dict={session["uid"]:session["username"]}

    #Add user to queue if not already present.
    if user_dict not in waiting_room:
        waiting_room.append(user_dict)

    #Check if enough players are waiting to start a match.
    if len(waiting_room)>=2:
        #Generate the next unique match ID.
        with open("match_id_counter.txt") as file:
            content=file.read().strip()
            match_id=str(int(content)+1)
        with open("match_id_counter.txt","w") as file:
            file.write(match_id)

        #Extract details for the first two players in the queue.
        uid1=list(waiting_room[0].keys())[0]
        username1=waiting_room[0][uid1]
        uid2=list(waiting_room[1].keys())[0]
        username2=waiting_room[1][uid2]

        #Randomly determine which player acts first.
        player_uids=[uid1,uid2]
        next_actioning_player_uid=random.choice(player_uids)

        #Create the match state in the global dictionary.
        active_matches[match_id]={
            "players":{
                uid1:Player(username=username1,uid=uid1,cards_list=[Card(name="card1",hp=10,speed=10),Card(name="card2",hp=10,speed=10),Card(name="card3",hp=10,speed=10)],client=None),
                uid2:Player(username=username2,uid=uid2,cards_list=[Card(name="card4",hp=10,speed=10),Card(name="card5",hp=10,speed=10),Card(name="card6",hp=10,speed=10)],client=None)
            },
            "next_actioning_player_uid":next_actioning_player_uid
        }

        #Remove matched players from the waiting room.
        waiting_room.pop(0)
        waiting_room.pop(0)

        #Redirect both players to their match page.
        return redirect(f"/match/{match_id}")

    #If not enough players, render the waiting page.
    return render_template("matchmaking.html")



#Displays the main game interface for a specific match.
@app.route("/match/<match_id>",methods=["GET"])
def match(match_id):
    #Redirect if not logged in.
    if "logged_in" not in session or not session["logged_in"]:
        return redirect("/")
    #Validate match_id format.
    if not match_id.isdigit():
         return redirect("/")
    #Check if the requested match actually exists.
    if match_id not in active_matches:
        return redirect("/")

    match_data=active_matches[match_id]
    players=match_data["players"]

    #Verify the logged-in user is a participant in this match.
    if session["uid"] not in players:
        return redirect("/")

    current_player=players[session["uid"]]
    username=current_player.username
    cards=current_player.cards_list

    #Iterate through players in the match to find the opponent's details.
    opponent_username=None
    opponent_uid=None
    opponent_cards=None
    for uid,player in players.items():
        if uid!=session["uid"]:
            opponent_username=player.username
            opponent_uid=player.uid
            opponent_cards=player.cards_list
            break

    next_actioning_player_uid=match_data["next_actioning_player_uid"]

    #Render the match interface with all necessary game state data.
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



#API endpoint for polling match status (used by waiting clients).
@app.route("/check_for_match",methods=["GET"])
def check_for_match():
    if "logged_in" not in session or not session["logged_in"]:
        return jsonify({"matched":False})

    for match_id,match_data in active_matches.items():
        if session["uid"] in match_data["players"]:
            #Match found for the user.
            return jsonify({"matched":True,"match_id":match_id})

    #No active match found for the user.
    return jsonify({"matched":False})



#WebSocket route for match communication (authentication, chat, actions).
@sock.route("/chat/match/<match_id>")
def chat(ws,match_id):
    #Will be populated after successful authentication.
    uid=None

    try:
        #Initial validation of match ID and existence.
        if not match_id.isdigit()or match_id not in active_matches:
            ws.close()
            return

        match_data=active_matches[match_id]
        players=match_data["players"]

        #Authenticate the connecting client via UID.
        json_auth_message=ws.receive(timeout=10)
        if json_auth_message is None:
            ws.close()
            return
        auth_message=json.loads(json_auth_message)
        if not isinstance(auth_message,dict)or auth_message.get("type")!="auth"or"uid"not in auth_message:
            ws.close()
            return

        uid=auth_message["uid"]
        if uid not in players:
            ws.close()
            return

        player=players[uid]
        #Prevent multiple connections for the same player.
        if player.client is not None:
            ws.close()
            return

        #Associate this WebSocket connection with the player object.
        player.client=ws

        #Main loop processing incoming messages.
        while True:
            json_message=ws.receive()
            #Client disconnected if message is None.
            if json_message is None:
                break

            message=json.loads(json_message)

            #Handle chat messages.
            if isinstance(message,dict)and message.get("type")=="chat"and"text"in message:
                cleaned_text=bleach.clean(message["text"]).strip()
                username=player.username
                formatted_message=f"{username}: {cleaned_text}"
                message_to_send=json.dumps(formatted_message)

                #Broadcast chat message to all currently connected clients in this match.
                current_clients=[p.client for p in players.values()if p.client is not None]
                for client in current_clients:
                    try:
                        client.send(message_to_send)
                    #Handle potential disconnection during broadcast.
                    except Exception:
                        for p_obj in players.values():
                            if p_obj.client==client:
                                p_obj.client=None

            #Handle game action messages.
            elif isinstance(message,dict)and message.get("type")=="action":
                ability_number=message["abilityNumber"]
                attacking_player_uid=message["attackingPlayerUid"]
                attacking_card_index=message["attackingCardIndex"]
                targeted_player_uid=message["targetedPlayerUid"]
                targeted_card_index=message["targetedCardIndex"]
                active_card_index=message["activeCardIndex"]

                #Ignore action if it's not the sending player's turn.
                if attacking_player_uid!=match_data.get("next_actioning_player_uid"):
                    continue

                attacking_card=players[attacking_player_uid].cards_list[attacking_card_index]
                targeted_card=players[targeted_player_uid].cards_list[targeted_card_index]
                attacking_player=players[attacking_player_uid]
                targeted_player=players[targeted_player_uid]

                #Ignore action if attacking card index is not player's active card index
                if active_card_index!=attacking_player.active_card_index:
                    continue

                #Dynamically call the specified ability method on the card.
                ability_name=f"ability{ability_number}"
                ability_method=getattr(attacking_card,ability_name)

                action_result=ability_method(attacking_player,targeted_player,targeted_card)
                message_to_send=json.dumps(action_result)

                #Broadcast action result to all connected clients.
                current_clients=[p.client for p in players.values()if p.client is not None]
                for client in current_clients:
                    try:
                        client.send(message_to_send)
                    #Handle potential disconnection during broadcast.
                    except Exception:
                        for p_obj in players.values():
                             if p_obj.client==client:
                                 p_obj.client=None



                #Update whose turn it is next (the player who was targeted).
                next_actioning_player_uid=targeted_player_uid
                match_data["next_actioning_player_uid"]=next_actioning_player_uid

                #Prepare and broadcast the turn update message.
                turn_update_message={
                    "type":"turn",
                    "next_actioning_player_uid":next_actioning_player_uid
                }
                turn_update_to_send=json.dumps(turn_update_message)

                #Re-fetch clients in case one disconnected during action broadcast.
                current_clients=[p.client for p in players.values()if p.client is not None]
                for client in current_clients:
                    try:
                        client.send(turn_update_to_send)
                    #Handle potential disconnection during broadcast.
                    except Exception:
                        for p_obj in players.values():
                            if p_obj.client==client:
                                p_obj.client=None

            #Handle card swap messages
            elif isinstance(message,dict)and message.get("type")=="swap":
                swapping_player_uid=message["swappingPlayerUid"]
                opponent_uid=message["opponentUid"]
                swap_target_card_index=message["swapTargetCardIndex"]

                #Ignore swap if it's not the sending player's turn.
                if swapping_player_uid!=match_data.get("next_actioning_player_uid"):
                    continue

                #Ignore swap if bad index
                if swap_target_card_index>2 or swap_target_card_index<0 or not isinstance(swap_target_card_index,int):
                    continue

                swapping_player=players[swapping_player_uid]
                opponent=players[opponent_uid]

                #Ignore swap if swap target card is active card
                if swap_target_card_index==swapping_player.active_card_index:
                    continue
                
                #Set player's active card index as the one they swapped to
                swapping_player.active_card_index=swap_target_card_index

                #Construct message
                message={
                    "type":"swap",
                    "swapping_player_uid":swapping_player.uid,
                    "opponent_uid":opponent.uid,
                    "swap_target_card_index":swapping_player.active_card_index
                }
                message_to_send=json.dumps(message)

                #Broadcast action result to all connected clients.
                current_clients=[p.client for p in players.values()if p.client is not None]
                for client in current_clients:
                    try:
                        client.send(message_to_send)
                    #Handle potential disconnection during broadcast.
                    except Exception:
                        for p_obj in players.values():
                             if p_obj.client==client:
                                 p_obj.client=None



                #Update whose turn it is next.
                next_actioning_player_uid=opponent_uid
                match_data["next_actioning_player_uid"]=next_actioning_player_uid

                #Prepare and broadcast the turn update message.
                turn_update_message={
                    "type":"turn",
                    "next_actioning_player_uid":next_actioning_player_uid
                }
                turn_update_to_send=json.dumps(turn_update_message)

                #Re-fetch clients in case one disconnected during action broadcast.
                current_clients=[p.client for p in players.values()if p.client is not None]
                for client in current_clients:
                    try:
                        client.send(turn_update_to_send)
                    #Handle potential disconnection during broadcast.
                    except Exception:
                        for p_obj in players.values():
                            if p_obj.client==client:
                                p_obj.client=None



    #Cleanup block: executes on disconnect or error within the try block.
    finally:
        try:
            #Ensure uid was set (i.e., authentication succeeded).
            if uid and match_id in active_matches:
                match_data=active_matches[match_id]
                players=match_data["players"]
                #Ensure player still exists in the potentially modified match_data.
                if uid in players:
                    player=players[uid]

                    #Only perform cleanup if the disconnecting ws is the one registered to the player.
                    if player.client==ws:
                        player.client=None #Mark player as disconnected in the game state.
                        disconnected_username=player.username

                        #Notify the remaining player, if any, about the disconnection.
                        disconnect_message=f"SERVER: {disconnected_username} has disconnected, redirecting in 5 seconds..."
                        message_to_send=json.dumps(disconnect_message)
                        other_player_disconnected=False
                        for p_obj in players.values():
                            if p_obj.uid!=uid and p_obj.client is not None:
                                try:
                                    p_obj.client.send(message_to_send)
                                except Exception:
                                    p_obj.client=None #Mark other player disconnected if send fails.
                                    other_player_disconnected=True

                        #Remove the match entirely if either player disconnects.
                        del active_matches[match_id]

        #Ignore any exceptions during the cleanup process itself.
        except Exception:
            pass