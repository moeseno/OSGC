from flask_sock import Sock
from flask import Flask,render_template,request,redirect,session,jsonify
import jinja2
from datetime import timedelta
import json
import bleach
import sys
import random
import math
import os
import csv
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
    def __init__(self):
        self.name="Card"
        self.hp=10
        self.speed=10

    def death_check(self,target):
        if target.hp<=0:
            target.hp=0
            return True
        return False

    def damage_calc(self,opponent,target_index,damage_number):
        if opponent.active_card_index==target_index:
            return damage_number
        elif opponent.active_card_index==None:
            return 0
        else:
            return math.floor(damage_number/2)

    def ability1(self,caster,opponent,target,target_index):
        target.hp-=self.damage_calc(opponent,target_index,1)
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

    def ability2(self,caster,opponent,target,target_index):
        target.hp-=self.damage_calc(opponent,target_index,2)
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

    def ability3(self,caster,opponent,target,target_index):
        target.hp-=self.damage_calc(opponent,target_index,3)
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


card_finder={
    "Card":Card
}



#Loads settings from settings.json into the global 'settings' dictionary.
#Exits application if format is incorrect or file read fails.
def init():
    try: 
        settings_filepath="settings.json"
        with open(settings_filepath,'r',encoding='utf-8') as file:
            loaded_settings=json.load(file)
            settings.update(loaded_settings)
    except Exception as e:
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



#helpers for singup
def init_inventory(folderpath,filepaths):
    initial_cards={"Card":5}
    sorted_card_names=sorted(initial_cards.keys())
    os.makedirs(folderpath,exist_ok=True)
    for filepath in filepaths:
        with open(filepath,"w",encoding="utf-8")as file:
            if "inactive_cards" in filepath:
                json.dump(initial_cards,file,sort_keys=True,indent=None,separators=(',',':'))


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

                    #init inventory
                    player_dir=f"inventories/{uid}"
                    selected_cards_path=f"{player_dir}/active_cards.json"
                    non_selected_cards_path=f"{player_dir}/inactive_cards.json"
                    init_inventory(player_dir,[selected_cards_path,non_selected_cards_path])

                    #Redirect to login page after successful signup.
                    return redirect("/login")

            #Handle potential file/processing errors.
            except Exception as e:
                print(e)
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
        with open(f"./inventories/{uid1}/active_cards.json","r") as file:
            card_json1=json.load(file)
        card_list1=[card_finder[card_json1[slot]]() for slot in card_json1]
        uid2=list(waiting_room[1].keys())[0]
        username2=waiting_room[1][uid2]
        with open(f"./inventories/{uid2}/active_cards.json","r") as file:
            card_json2=json.load(file)
        card_list2=[card_finder[card_json2[slot]]() for slot in card_json2]

        #Randomly determine which player acts first.
        player_uids=[uid1,uid2]
        next_actioning_player_uid=random.choice(player_uids)

        #Create the match state in the global dictionary.
        active_matches[match_id]={
            "players":{
                uid1:Player(username=username1,uid=uid1,cards_list=card_list1,client=None),
                uid2:Player(username=username2,uid=uid2,cards_list=card_list2,client=None)
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

    

#helpers for inventory
def read_cards(filepath):
    read_cards_data = {}
    if os.path.exists(filepath) and os.path.getsize(filepath) > 0:
        with open(filepath,'r',encoding='utf-8') as file:
            read_cards_data = json.load(file)
    return read_cards_data

def write_cards(filepath,cards_to_write):
    os.makedirs(os.path.dirname(filepath),exist_ok=True)
    data_to_write={name: count for name, count in cards_to_write.items() if count > 0}
    with open(filepath,'w',encoding='utf-8') as file:
        if "inactive"in filepath:
            json.dump(data_to_write,file,sort_keys=True,indent=None,separators=(',',':'))
        else:
            json.dump(data_to_write,file,sort_keys=False,indent=None,separators=(',',':'))


@app.route('/inventory', methods=['GET','POST'])
def inventory():
    if "logged_in" not in session or not session["logged_in"]: return redirect("/")
    player_dir=f"inventories/{session['uid']}"
    selected_cards_path=f"{player_dir}/active_cards.json"
    non_selected_cards_path=f"{player_dir}/inactive_cards.json"
    if not os.path.isdir(player_dir): os.makedirs(player_dir)

    # Read current state from files
    current_selected_slots=read_cards(selected_cards_path) # Renamed for clarity: file holds slots
    current_inactive_cards=read_cards(non_selected_cards_path) # File holds inactive counts

    # --- CORRECTED: Calculate total owned cards ---
    all_owned_cards=current_inactive_cards.copy() # Start with inactive counts
    # Iterate through the slots read from the active_cards file
    for slot, card_key in current_selected_slots.items():
        if card_key!='None': # If a slot has a card (not 'None')
            # Increment the count for that card key in the total owned dictionary
            all_owned_cards[card_key]=all_owned_cards.get(card_key,0)+1 # Add 1 (integer)
    # --- End Correction ---

    if request.method=='POST':
        # --- POST Logic (Assumed okay from previous steps) ---
        data=request.get_json()
        if not data: return jsonify(False),400
        selected_slots_from_client=data.get('selected_cards')
        if not selected_slots_from_client or not isinstance(selected_slots_from_client,dict): return jsonify(False),400

        selected_cards={}
        num_slots_filled=0
        cleaned_selection_slots={}
        for slot, card_key in selected_slots_from_client.items():
             if not isinstance(card_key,str): return jsonify(False),400
             card_key=card_key.strip()
             cleaned_selection_slots[slot]=card_key
             if card_key!='None':
                 selected_cards[card_key]=selected_cards.get(card_key,0)+1
                 num_slots_filled+=1

        # if num_slots_filled!=3: return jsonify(False)

        for card_name, selected_count in selected_cards.items():
            # Use the correctly calculated all_owned_cards for validation
            if selected_count>all_owned_cards.get(card_name,0): return jsonify(False),400

        new_selected_slots_to_save=cleaned_selection_slots
        try:
            with open(selected_cards_path,'w',encoding='utf-8') as f:
                json.dump(new_selected_slots_to_save,f,indent=None,separators=(',',':'))
        except Exception:
            return jsonify(False),500

        new_non_selected_cards=all_owned_cards.copy()
        for name,count_to_subtract in selected_cards.items():
            new_non_selected_cards[name]=new_non_selected_cards.get(name,0)-count_to_subtract
        try:
            write_cards(non_selected_cards_path,new_non_selected_cards)
        except Exception:
            return jsonify(False),500

        return jsonify(True)

    else: # GET Request
        non_selected_for_display=all_owned_cards.copy()
        # Subtract cards currently in slots (use the data read earlier)
        for slot, card_key in current_selected_slots.items():
            if card_key!='None' and card_key in non_selected_for_display:
                 if non_selected_for_display[card_key]>0:
                     non_selected_for_display[card_key]-=1
        # Filter out zero counts for display
        non_selected_for_display={k:v for k,v in non_selected_for_display.items() if v>0}

        # Ensure default slots if file is empty/new user
        if not current_selected_slots:
             current_selected_slots={'slot1':'None','slot2':'None','slot3':'None'}

        # Pass the correct data structures to the template
        return render_template(
            'inventory.html',
            uid=session['uid'],
            all_owned_cards=all_owned_cards, # Correctly calculated total
            current_selected_cards=current_selected_slots, # Slot assignments for JS renderSelectedCards (if it expects slots)
            current_non_selected_cards=non_selected_for_display # Calculated available counts for JS renderNonSelectedCards
        )

def pull():
    return random.choice(list(card_finder.keys()))

@app.route("/gacha",methods=["GET","POST"])
def gacha():
    if "logged_in" not in session or not session["logged_in"]: return redirect("/")

    player_dir=f"inventories/{session["uid"]}"
    non_selected_cards_path=f"{player_dir}/inactive_cards.json"

    if request.method=="POST":
        data=request.get_json()
        if not data:return jsonify(False),400
        amount=data.get("amount")

        print(data)
        print(amount)
        print(type(amount))

        if amount!=1 and amount!=10:
            return jsonify(False),400

        pulled_cards={}
        print(amount)
        for x in range(amount):
            pulled_card=pull()
            if pulled_card in pulled_cards.keys():
                pulled_cards[pulled_card]+=1
            else:
                pulled_cards[pulled_card]=1

        print(pulled_cards)

        with open(non_selected_cards_path,"r")as file:
            owned_non_selected_cards=json.load(file)
            print(owned_non_selected_cards)

        for card in pulled_cards:
            if card in owned_non_selected_cards.keys():
                owned_non_selected_cards[card]+=pulled_cards[card]
            else:
                owned_non_selected_cards[card]=pulled_cards[card]

            print(owned_non_selected_cards)
        
        with open(non_selected_cards_path,"w")as file:
            json.dump(owned_non_selected_cards,file,sort_keys=True,indent=None,separators=(',',':'))

        return jsonify(True)

    return render_template(
        "gacha.html"
        )


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

                action_result=ability_method(attacking_player,targeted_player,targeted_card,targeted_card_index)
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