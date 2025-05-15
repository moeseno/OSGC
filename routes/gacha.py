from flask import Blueprint,render_template,request,redirect,session,jsonify
import json
import random
import cards

gacha_bp=Blueprint('gacha_bp',__name__,url_prefix="/gacha")

pool1={
    "Card":[cards.Card,1],
    "Card2":[cards.Card2,0.1],
    "Card3":[cards.Card3,0.01],
}

pool2={
    "Card2":[cards.Card2,1],
    "Card3":[cards.Card3,0.1]
}

pools_dict={"gacha1":pool1,"gacha2":pool2}


@gacha_bp.route("/",methods=["GET"])
def gacha():
    if "logged_in" not in session or not session["logged_in"]: return redirect("/")

    return render_template(
        "gacha.html",
        pool_names=list(pools_dict.keys())
        )



#Simulates a single card pull based on defined rarities.
#helper for gacha
def pull(pool):
    #Generates a random float between 0.0 and 1.0.
    percentile=random.random()
    #Stores the ID of the card pulled.
    pulled_card=""
    for card in pool:
        if percentile<pool[card][1]:
            pulled_card=card
    return pulled_card

#Handles the gacha/card pulling mechanism for players.
#gacha route
@gacha_bp.route("/<pool_name>",methods=["GET","POST"])
def gacha1(pool_name):
    #check if logged in
    if "logged_in" not in session or not session["logged_in"] or pool_name not in pools_dict.keys(): return redirect("/")

    #set paths
    #Path to the player's inventory directory.
    player_dir=f"inventories/{session["uid"]}"
    #Path to inactive cards file.
    non_selected_cards_path=f"{player_dir}/inactive_cards.json"

    #handle posts
    if request.method=="POST":
        #get data
        #Retrieves JSON data from the POST request.
        data=request.get_json()
        if not data:return jsonify(False),400
        #Number of cards to pull.
        amount=data.get("amount")

        #only allow 1 pull and 10 pull
        if amount!=1 and amount!=10: return jsonify(False),400

        #pull cards
        #Dictionary to store counts of cards pulled in this transaction.
        pulled_cards={}
        for x in range(amount):
            pulled_card=pull(pools_dict[pool_name])
            if pulled_card in pulled_cards.keys():
                pulled_cards[pulled_card]+=1
            else:
                pulled_cards[pulled_card]=1

        #get already owned cards that are not selected
        with open(non_selected_cards_path,"r")as file:
            #Loads currently owned non-selected cards.
            owned_non_selected_cards=json.load(file)

        #add pulled cards to non selected cards
        for card in pulled_cards:
            if card in owned_non_selected_cards.keys():
                owned_non_selected_cards[card]+=pulled_cards[card]
            else:
                owned_non_selected_cards[card]=pulled_cards[card]
        
        #write to file
        with open(non_selected_cards_path,"w")as file:
            json.dump(owned_non_selected_cards,file,sort_keys=True,indent=None,separators=(',',':'))

        return jsonify(pulled_cards),200

    return render_template(
        "gacha1.html"
        )