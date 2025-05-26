from flask_sock import Sock
from flask import Flask,render_template,request,redirect,session,jsonify
import jinja2
import json
import bleach
import sys
import random
import math
import os
import csv
import random
import cards

from routes.gacha import gacha_bp


#Initializes the Flask application.
app=Flask(__name__)
#Initializes Flask-Sock for WebSocket support.
sock=Sock(app)



#register blueprints
app.register_blueprint(gacha_bp)



#Stores application settings.
settings={}
#Queue for players waiting for a match.
waiting_room=[]
#Dictionary of active matches.
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
        #Index of the player's currently active card.
        self.active_card_index=None


#List of valid slot names for player decks.
valid_slot_names=["slot1","slot2","slot3"]


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

#Set Flask secret key from loaded settings.
app.secret_key=settings.get("SECRET_KEY")

#List of valid card identifiers.
valid_cards=settings.get("CARDS")

#Defines available card types and their properties/rarity.
card_finder={card:getattr(cards,card) for card in valid_cards} 

#Handles the main index page.
@app.route("/",methods=["GET"])
def index():
    #Initialize session login status if not present.
    if "logged_in" not in session:
        session["logged_in"]=False
    return render_template("index.html",logged_in=session.get("logged_in"))



#GET displays login form, POST handles login attempt.
@app.route("/login",methods=["GET","POST"])
def login():
    print(session)
    if session.get("logged_in",True): return redirect("/")

    #error for form feedback.
    error={}

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
                error["missing_value"]="Username or password missing"

            #Validate credentials if fields were provided.
            if not error:
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
                            error["wrong_password"]="Incorrect password"
                            #Stop search after finding user with wrong password.
                            break
                #Executes ONLY if the loop completes without 'break' (username not found).
                else:
                    error["nonexistent_user"]="User does not exist"

        #Handle potential file/processing errors.
        except Exception as e:
            error["error"]=f"{e}"

    #Render login page with feedback.
    return render_template(
        "login.html",
        error=error
        )


#Initializes a new player's inventory files with default cards.
#helpers for singup
def init_inventory(folderpath,filepaths,error):
    #Dictionary to store potential errors during inventory initialization.
    error={}
    #Default cards and quantities for a new player.
    initial_cards={"Card":5}
    #Sorted list of initial card names.
    sorted_card_names=sorted(initial_cards.keys())
    try: 
        os.makedirs(folderpath,exist_ok=True)
        for filepath in filepaths:
            with open(filepath,"w",encoding="utf-8")as file:
                if "inactive_cards" in filepath:
                    json.dump(initial_cards,file,sort_keys=True,indent=None,separators=(',',':'))
                else:
                    json.dump({},file)
    except Exception as e:
        error["inventory_error"]=f"An inventory related error occured: {e}"


#GET displays signup form, POST handles signup attempt.
@app.route("/signup",methods=["GET","POST"])
def signup():
    if session.get("logged_in",True): return redirect("/")

    #error for form feedback.
    error={}

    #Handle form submission.
    if request.method=="POST":
        user={"username":request.form.get("username",""),"password":request.form.get("password","")}
        confirm=request.form.get("confirm","")

        #Sanitize and validate username against disallowed characters/names.
        if user["username"]!=bleach.clean(user["username"]):
            error["bad_username"]="Bad username"
        #Validate username length.
        if len(user["username"])>settings.get("USERNAME_CHAR_LIMIT"):
            error["username_too_long"]="Username must be 16 characters or less"
        #Validate password length
        if len(user["password"])>settings.get("PASSWORD_CHAR_LIMIT"):
            error["password_too_long"]="Password must be 64 characters or less"
        #Check for empty fields.
        if "" in user.values():
            error["missing_value"]="Missing password or username"
        #Check password confirmation match.
        if user["password"]!=confirm:
            error["different_password"]="Passwordss are different"

        #Proceed only if initial validations pass.
        if not error:
            try:
                #Read existing usernames to check for duplicates.
                with open("users.csv","r",newline="",encoding="utf-8") as file:
                    reader=csv.DictReader(file)
                    usernames=[row["username"] for row in reader]

                username_exists=False
                if user["username"] in usernames:
                    username_exists=True
                    error["username_exists"]="Username already exists"

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
                    init_inventory(player_dir,[selected_cards_path,non_selected_cards_path],error)

                    #Redirect to login page after successful signup.
                    return redirect("/login")

            #Handle potential file/processing errors.
            except Exception as e:
                error=f"{e}"

    #Render signup page with feedback.
    return render_template(
        "signup.html",
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
    if not session.get("logged_in",False): return redirect("/")

    #for flagging errors
    error={}

    #User identifier for the waiting room.
    user_dict={session.get("uid"):session.get("username")}

    #Add user to queue if not already present.
    if user_dict not in waiting_room:
        waiting_room.append(user_dict)

    #Check if enough players are waiting to start a match.
    if len(waiting_room)>=2:

        try:
            #Generate the next unique match ID.
            with open("match_id_counter.txt") as file:
                content=file.read().strip()
                match_id=str(int(content)+1)
            with open("match_id_counter.txt","w") as file:
                file.write(match_id)
        except Exception as e:
            error["id_assignment"]=f"Error relating to match id assignment, matchmaking currently unavailable: {e}"
            return render_template(
                "matchmaking.html",
                error=error
                )

        try:
            #Extract details for the first two players in the queue.
            uid1=list(waiting_room[0].keys())[0]
            username1=waiting_room[0].get(uid1)
            with open(f"./inventories/{uid1}/active_cards.json","r") as file:
                card_json1=json.load(file)
            card_list1=[card_finder[card_json1[slot]]() if card_json1[slot] in valid_cards else card_finder[settings.get("DEFAULT_CARD")]() for slot in card_json1]

            uid2=list(waiting_room[1].keys())[0]
            username2=waiting_room[1].get(uid2)
            with open(f"./inventories/{uid2}/active_cards.json","r") as file:
                card_json2=json.load(file)
            card_list2=[card_finder[card_json2[slot]]() if card_json2[slot] in valid_cards else card_finder[settings.get("DEFAULT_CARD")]() for slot in card_json2]

        except Exception as e:
            error["inventory"]=f"Error relating to reading inventory, matchmaking currently unavailable: {e}"
            raise e
            return render_template(
                "matchmaking.html",
                error=error
                )

        #Randomly determine which player acts first.
        player_uids=[uid1,uid2]
        next_actioning_player_uid=random.choice(player_uids)

        #Create the match state in the global dictionary.
        if match_id not in active_matches.keys():
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
        else:
            error["match_id"]="Error related to match ID"

    #If not enough players or error, render the waiting page.
    return render_template(
        "matchmaking.html",
        error=error
        )



#Displays the main game interface for a specific match.
@app.route("/match/<match_id>",methods=["GET"])
def match(match_id):
    #Redirect if not logged in.
    if not session.get("logged_in",False): return redirect("/")
    #Validate match_id format.
    if not match_id.isdigit(): return redirect("/")
    #Check if the requested match actually exists.
    if match_id not in active_matches: return redirect("/")

    match_data=active_matches[match_id]
    players=match_data.get("players")

    #Verify the logged-in user is a participant in this match.
    if session.get("uid") not in players:
        return redirect("/")

    current_player=players[session.get("uid")]
    username=current_player.username
    cards=current_player.cards_list

    #Iterate through players in the match to find the opponent's details.
    opponent_username=None
    opponent_uid=None
    opponent_cards=None
    for uid,player in players.items():
        if uid!=session.get("uid"):
            opponent_username=player.username
            opponent_uid=player.uid
            opponent_cards=player.cards_list
            break

    next_actioning_player_uid=match_data.get("next_actioning_player_uid")

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
        next_actioning_player_uid=next_actioning_player_uid,
        default_card=settings.get("DEFAULT_CARD")
        )



#API endpoint for polling match status (used by waiting clients).
@app.route("/check_for_match",methods=["GET"])
def check_for_match():
    if not session.get("logged_in",False):
        return jsonify({"matched":False})

    try:
        for match_id,match_data in active_matches.items():
            if session.get("uid") in match_data.get("players"):
                #Match found for the user.
                return jsonify({"matched":True,"match_id":match_id})

        #No active match found for the user.
        return jsonify({"matched":False})
    except Exception as e:
        return jsonify({"matched":False,"error":e})

    

#Reads card data from a JSON file.
#helpers for inventory
def read_cards(filepath,error):
    try:
        #Dictionary to store read card data.
        read_cards_data={}
        if os.path.exists(filepath) and os.path.getsize(filepath)>0:
            with open(filepath,'r',encoding='utf-8') as file:
                read_cards_data=json.load(file)
        return read_cards_data
    except Exception as e:
        error["read_error"]=f"Error relating to reading card data: {e}"

#Writes card data (typically non-selected cards) to a JSON file.
def write_cards(filepath,cards_to_write,error):
    try:
        os.makedirs(os.path.dirname(filepath),exist_ok=True)
        #Filters out cards with zero count.
        data_to_write={name: count for name, count in cards_to_write.items() if count>0}
        with open(filepath,'w',encoding='utf-8') as file:
            if "inactive"in filepath:
                json.dump(data_to_write,file,sort_keys=True,indent=None,separators=(',',':'))
            else:
                json.dump(data_to_write,file,sort_keys=False,indent=None,separators=(',',':'))
        return True
    except Exception as e:
        error["write_error"]=f"Error relating to writing card data: {e}"
        return False

#Writes active card data (selected slots) to a JSON file.
def write_cards_active(filepath,cards_to_write,error):
    try:
        os.makedirs(os.path.dirname(filepath),exist_ok=True)
        with open(filepath,'w',encoding='utf-8') as file:
            json.dump(cards_to_write,file,sort_keys=True,indent=None,separators=(',',':'))
        return True
    except Exception as e:
        error["write_error"]=f"Error relating to writing card data: {e}"
        return False

#Manages player inventory, allowing viewing and updating selected cards.
@app.route('/inventory', methods=['GET','POST'])
def inventory():
    if not session.get("logged_in",False): return redirect("/")

    #Dictionary to store all cards owned by the player.
    all_owned_cards={}
    #Dictionary of cards currently in active slots.
    current_selected_cards={}
    #Dictionary of cards owned but not in active slots.
    current_non_selected_cards={}
    #Dictionary to store potential errors.
    error={}
    #Path to the player's inventory directory.
    player_dir=f"inventories/{session['uid']}"
    #Path to active cards file.
    selected_cards_path=f"{player_dir}/active_cards.json"
    #Path to inactive cards file.
    non_selected_cards_path=f"{player_dir}/inactive_cards.json"
    if not os.path.isdir(player_dir): os.makedirs(player_dir)

    # Read current state from files
    current_selected_cards=read_cards(selected_cards_path,error)
    current_non_selected_cards=read_cards(non_selected_cards_path,error)

    if error:
        all_owned_cards={}
        current_selected_cards={}
        current_non_selected_cards={}
        #Cards available for selection display.
        non_selected_for_display={}
        return render_template(
            'inventory.html',
            uid=session.get("uid"),
            all_owned_cards=all_owned_cards,
            current_selected_cards=current_selected_cards,
            current_non_selected_cards=non_selected_for_display,
            error=error
        )

    all_owned_cards=current_non_selected_cards.copy()
    # Iterate through the slots read from the active_cards file
    for slot, card_key in current_selected_cards.items():
        if card_key!='None':
            # Increment the count for that card key in the total owned dictionary
            all_owned_cards[card_key]=all_owned_cards.get(card_key,0)+1

    if request.method=='POST':
        try:
            data=request.get_json()
            if not data: return jsonify(False),400
            selected_slots_from_client=data.get('selected_cards')
            if not selected_slots_from_client or not isinstance(selected_slots_from_client,dict): return jsonify(False),400
            #Temporary dictionary to count cards selected by the client.
            selected_cards={}
            #Counter for filled slots.
            num_slots_filled=0
            #Validated slot selections from the client.
            cleaned_selection_slots={}
            for slot, card_key in selected_slots_from_client.items():
                if slot not in valid_slot_names: return jsonify(False),400
                if not isinstance(card_key,str): return jsonify(False),400
                card_key=card_key.strip()
                cleaned_selection_slots[slot]=card_key
                if card_key!='None':
                    if card_key not in valid_cards: return jsonify(False),400   
                    selected_cards[card_key]=selected_cards.get(card_key,0)+1
                    num_slots_filled+=1

            for card_name, selected_count in selected_cards.items():
                if selected_count>all_owned_cards.get(card_name,0): return jsonify(False),400
            #Final validated slots to save.
            new_selected_slots_to_save=cleaned_selection_slots

            write_cards_active(selected_cards_path,new_selected_slots_to_save,error)
            #Copy of all cards to calculate new non-selected.
            new_non_selected_cards=all_owned_cards.copy()
            for name,count_to_subtract in selected_cards.items():
                new_non_selected_cards[name]=new_non_selected_cards.get(name,0)-count_to_subtract

            write_cards(non_selected_cards_path,new_non_selected_cards,error)

            if error: return jsonify(False),500

            return jsonify(True),200

        except Exception as e:
            return jsonify(False),500

    else:
        #Cards available for selection display, initially all owned.
        non_selected_for_display=all_owned_cards.copy()
        # Subtract cards currently in slots (use the data read earlier)
        for slot, card_key in current_selected_cards.items():
            if card_key!='None' and card_key in non_selected_for_display:
                 if non_selected_for_display[card_key]>0:
                     non_selected_for_display[card_key]-=1
        # Filter out zero counts for display
        non_selected_for_display={k:v for k,v in non_selected_for_display.items() if v>0}

        # Ensure default slots if file is empty/new user
        if not current_selected_cards:
             current_selected_cards={'slot1':'None','slot2':'None','slot3':'None'}

        # Pass the correct data structures to the template
        return render_template(
            'inventory.html',
            uid=session.get("uid"),
            all_owned_cards=all_owned_cards, # Correctly calculated total
            current_selected_cards=current_selected_cards, # Slot assignments for JS renderSelectedCards (if it expects slots)
            current_non_selected_cards=non_selected_for_display, # Calculated available counts for JS renderNonSelectedCards
            error=error
        )



#Checks if any player has lost all their cards (all card HPs are zero or less).
def death_check(players):
    dead_players=[]
    for player in players:
        #List of HPs for the current player's cards.
        player_cards_hps=[card.hp for card in players[player].cards_list]
        if not any(player_cards_hps):
            dead_players.append(players[player].username)
    if len(dead_players)==2:
        return True
    elif len(dead_players)==1:
        return dead_players[0]
    return None

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
        #Retrieves data for the current match.
        match_data=active_matches[match_id]
        #Dictionary of player objects in the match.
        players=match_data["players"]

        #Authenticate the connecting client via UID.
        #Receives authentication message from client.
        json_auth_message=ws.receive(timeout=10)
        if json_auth_message is None:
            ws.close()
            return
        #Parses the JSON authentication message.
        auth_message=json.loads(json_auth_message)
        if not isinstance(auth_message,dict)or auth_message.get("type")!="auth"or"uid"not in auth_message:
            ws.close()
            return
        #Extracts UID from the authenticated message.
        uid=auth_message["uid"]
        if uid not in players:
            ws.close()
            return
        #Player object for the authenticated client.
        player=players[uid]
        #Prevent multiple connections for the same player.
        if player.client is not None:
            ws.close()
            return

        #Associate this WebSocket connection with the player object.
        player.client=ws

        #Main loop processing incoming messages.
        while True:
            #Receives a message from the client.
            json_message=ws.receive()
            #Client disconnected if message is None.
            if json_message is None:
                break
            #Parses the incoming JSON message.
            message=json.loads(json_message)

            #Handle chat messages.
            if isinstance(message,dict)and message.get("type")=="chat"and"text"in message:
                #Sanitizes chat message text.
                cleaned_text=bleach.clean(message["text"]).strip()
                #Username of the sender.
                username=player.username
                #Formats the message for display.
                formatted_message=f"{username}: {cleaned_text}"
                #Serializes message for sending.
                message_to_send=json.dumps(formatted_message)

                #Broadcast chat message to all currently connected clients in this match.
                #List of active WebSocket clients in the match.
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
                #Ability number used (1-3).
                #int or None
                ability_number=message.get("abilityNumber") if isinstance(message.get("abilityNumber"),int) and 1<=message.get("abilityNumber")<=3 else ""
                #UID of the attacking player.
                #str
                attacking_player_uid=message.get("attackingPlayerUid") if message.get("attackingPlayerUid") in players.keys() else ""
                #Index of the attacking card.
                #int
                attacking_card_index=message.get("attackingCardIndex") if isinstance(message.get("attackingCardIndex"),int) and 0<=message.get("attackingCardIndex")<=2 else ""
                #UID of the targeted player.
                #str
                targeted_player_uid=message.get("targetedPlayerUid") if message.get("targetedPlayerUid") in players.keys() and message.get("targetedPlayerUid")!=message.get("attackingPlayerUid") else ""
                #Index of the targeted card.
                #int or None
                targeted_card_index=message.get("targetedCardIndex") if isinstance(message.get("targetedCardIndex"),int) and 0<=message.get("targetedCardIndex")<=2 else ""
                #Index of the attacker's active card.
                #int or None
                active_card_index=message.get("activeCardIndex") if isinstance(message.get("activeCardIndex"),int) and 0<=message.get("activeCardIndex")<=2 else ""

                #List of values for validation.
                values_to_check=[ability_number,attacking_player_uid,attacking_card_index,targeted_player_uid,targeted_card_index,active_card_index]
                #ignore action if a value was not properly assigned
                if any(isinstance(value,str)and value=="" for value in values_to_check):
                    continue # Ignore the action if an empty string is found

                #Ignore action if it's not the sending player's turn.
                if attacking_player_uid!=match_data.get("next_actioning_player_uid"):
                    continue
                #The attacking card object.
                attacking_card=players[attacking_player_uid].cards_list[attacking_card_index]
                #The targeted card object.
                targeted_card=players[targeted_player_uid].cards_list[targeted_card_index]
                #The attacking player object.
                attacking_player=players[attacking_player_uid]
                #The targeted player object.
                targeted_player=players[targeted_player_uid]

                #Ignore action if attacking card index is not player's active card index
                if active_card_index!=attacking_player.active_card_index:
                    continue

                #Dynamically call the specified ability method on the card.
                #Name of the ability method to call.
                ability_name=f"ability{ability_number}"
                #Gets the ability method from the card object.
                ability_method=getattr(attacking_card,ability_name)
                #Result of the ability execution.
                action_result=ability_method(attacking_player,targeted_player,targeted_card,targeted_card_index)
                #Serializes action result for sending.
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
                #UID of the next player to act.
                next_actioning_player_uid=targeted_player_uid
                match_data["next_actioning_player_uid"]=next_actioning_player_uid

                #Prepare and broadcast the turn update message.
                #Message detailing the turn change.
                turn_update_message={
                    "type":"turn",
                    "next_actioning_player_uid":next_actioning_player_uid,
                    "losing_player":death_check(players)
                }
                #Serializes turn update for sending.
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
                #UID of the player performing the swap.
                swapping_player_uid=message["swappingPlayerUid"]
                #UID of the opponent.
                opponent_uid=message["opponentUid"]
                #Index of the card to swap to.
                swap_target_card_index=message["swapTargetCardIndex"]

                #Ignore swap if it's not the sending player's turn.
                if swapping_player_uid!=match_data.get("next_actioning_player_uid"):
                    continue

                #Ignore swap if bad index
                if swap_target_card_index>2 or swap_target_card_index<0 or not isinstance(swap_target_card_index,int):
                    continue
                #Player object performing the swap.
                swapping_player=players[swapping_player_uid]
                #Opponent player object.
                opponent=players[opponent_uid]

                #Ignore swap if swap target card is active card
                if swap_target_card_index==swapping_player.active_card_index:
                    continue
                
                #Set player's active card index as the one they swapped to
                swapping_player.active_card_index=swap_target_card_index

                #Construct message
                #Swap action message to broadcast.
                message={
                    "type":"swap",
                    "swapping_player_uid":swapping_player.uid,
                    "opponent_uid":opponent.uid,
                    "swap_target_card_index":swapping_player.active_card_index
                }
                #Serializes swap message for sending.
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
                    "next_actioning_player_uid":next_actioning_player_uid,
                    "losing_player":death_check(players)
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
                        #Username of the disconnected player.
                        disconnected_username=player.username

                        #Notify the remaining player, if any, about the disconnection.
                        #Message to notify other player.
                        disconnect_message=f"SERVER: {disconnected_username} has disconnected, redirecting in 5 seconds..."
                        message_to_send=json.dumps(disconnect_message)
                        #Flag if the other player also disconnected during notification.
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